import asyncio
import contextlib
import json
import logging
import ssl

import aiomqtt
import asyncpg
import pydantic

import app.database as database
import app.settings as settings
import app.validation as validation


def _encode_payload(payload):
    """Encode python dict into utf-8 JSON bytestring."""
    return json.dumps(payload).encode()


logger = logging.getLogger(__name__)
task_references = set()


@contextlib.asynccontextmanager
async def client():
    """Context manager to manage aiomqtt client with custom settings."""
    async with aiomqtt.Client(
        hostname=settings.MQTT_URL,
        port=settings.MQTT_PORT,
        protocol=aiomqtt.ProtocolVersion.V5,
        username=settings.MQTT_IDENTIFIER,
        password=settings.MQTT_PASSWORD,
        # TODO it would be nicer to use TLS here for local development as well
        tls_params=(
            aiomqtt.TLSParameters(tls_version=ssl.PROTOCOL_TLS)
            if settings.ENVIRONMENT == "production"
            else None
        ),
        # Make the MQTT connection persistent. The broker will retain messages on
        # topics we subscribed to in case we disconnect.
        clean_start=False,
        client_id="server",
    ) as x:
        yield x


async def publish_configuration(
    sensor_identifier, revision, configuration, mqttc, dbpool
):
    """Publish a configuration to the specified sensor."""

    async def helper(sensor_identifier, revision, configuration):
        backoff = 1
        query, arguments = database.parametrize(
            identifier="update-configuration-on-publication",
            arguments={
                "sensor_identifier": sensor_identifier,
                "revision": revision,
            },
        )
        while True:
            try:
                # Try to publish the configuration
                await mqttc.publish(
                    topic=f"configurations/{sensor_identifier}",
                    payload=_encode_payload(
                        {"revision": revision, "configuration": configuration}
                    ),
                    qos=1,
                    retain=True,
                )
                # Try to set the publication timestamp in the database
                await dbpool.execute(query, *arguments)
                logger.info(f"Published configuration {sensor_identifier}#{revision}")
                break
            except Exception as e:  # pragma: no cover
                # Retry if something fails. Duplicate messages are not a problem,
                # the sensor can ignore them based on the revision number.
                # The revision number only increases, never decreases.
                logger.warning(
                    f"Failed to publish configuration {sensor_identifier}#{revision},"
                    f" retrying in {backoff} seconds: {repr(e)}"
                )
                # Backoff exponentially, up until about 5 minutes
                if backoff < 256:
                    backoff *= 2
                await asyncio.sleep(backoff)

    # Fire-and-forget the retry task, save the reference, and return immediately
    task = asyncio.create_task(helper(sensor_identifier, revision, configuration))
    task_references.add(task)
    task.add_done_callback(task_references.remove)


async def _process_acknowledgments(sensor_identifier, payload, dbpool):
    query, arguments = database.parametrize(
        identifier="update-configuration-on-acknowledgment",
        arguments=[
            {
                "sensor_identifier": sensor_identifier,
                "revision": element.revision,
                "acknowledgment_timestamp": element.timestamp,
                "success": element.success,
            }
            for element in payload
        ],
    )
    try:
        await dbpool.executemany(query, arguments)
    except asyncpg.ForeignKeyViolationError:
        logger.warning(f"Failed to process; Sensor not found: {sensor_identifier}")


async def _process_measurements(sensor_identifier, payload, dbpool):
    query, arguments = database.parametrize(
        identifier="create-measurement",
        arguments=[
            {
                "sensor_identifier": sensor_identifier,
                "attribute": attribute,
                "value": value,
                "revision": element.revision,
                "creation_timestamp": element.timestamp,
            }
            for element in payload
            for attribute, value in element.value.items()
        ],
    )
    try:
        await dbpool.executemany(query, arguments)
    except asyncpg.ForeignKeyViolationError:
        logger.warning(f"Failed to process; Sensor not found: {sensor_identifier}")


async def _process_logs(sensor_identifier, payload, dbpool):
    query, arguments = database.parametrize(
        identifier="create-log",
        arguments=[
            {
                "sensor_identifier": sensor_identifier,
                "message": element.message,
                "revision": element.revision,
                "creation_timestamp": element.timestamp,
                "severity": element.severity,
            }
            for element in payload
        ],
    )
    try:
        await dbpool.executemany(query, arguments)
    except asyncpg.ForeignKeyViolationError:
        logger.warning(f"Failed to process; Sensor not found: {sensor_identifier}")


SUBSCRIPTIONS = {
    "acknowledgments/+": (
        _process_acknowledgments,
        validation.AcknowledgmentsValidator,
    ),
    "measurements/+": (
        _process_measurements,
        validation.MeasurementsValidator,
    ),
    "logs/+": (
        _process_logs,
        validation.LogsValidator,
    ),
}


async def listen(mqttc, dbpool):
    """Listen to and handle incoming MQTT messages from sensors."""
    async with mqttc.messages() as messages:
        # Subscribe to all topics
        for wildcard in SUBSCRIPTIONS.keys():
            await mqttc.subscribe(wildcard, qos=1, timeout=10)
            logger.info(f"Subscribed to: {wildcard}")
        # Loop through incoming messages
        async for message in messages:
            # TODO: Remove condition when there's no more logs limit
            if not message.topic.matches(list(SUBSCRIPTIONS.keys())[1]):
                logger.info(
                    f"Received message: {message.payload!r} on topic: {message.topic}"
                )
            # Get sensor identifier from the topic
            # TODO validate that identifier is a valid UUID format
            sensor_identifier = str(message.topic).split("/")[-1]
            # Call the appropriate processor; First match wins
            for wildcard, (process, validator) in SUBSCRIPTIONS.items():
                if message.topic.matches(wildcard):
                    try:
                        payload = validator.validate_json(message.payload)
                        await process(sensor_identifier, payload, dbpool)
                    # Errors are logged and ignored as we can't give feedback
                    except pydantic.ValidationError:
                        logger.warning(f"Malformed message: {message.payload!r}")
                    except Exception as e:  # pragma: no cover
                        logger.error(e, exc_info=True)
                    break
            else:  # Executed if no break is called
                logger.warning(f"Failed to match topic: {message.topic}")
