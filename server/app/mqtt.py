import asyncio
import contextlib
import json
import ssl

import asyncio_mqtt as aiomqtt
import asyncpg
import pydantic

import app.database as database
import app.settings as settings
import app.validation as validation
from app.logs import logger


def _encode_payload(payload):
    """Encode python dict into utf-8 JSON bytestring."""
    return json.dumps(payload).encode()


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
                logger.info(
                    f"[MQTT] Published configuration {sensor_identifier}#{revision}"
                )
                break
            except Exception as e:  # pragma: no cover
                # Retry if something fails. Duplicate messages are not a problem,
                # the sensor can ignore them based on the revision number.
                # The revision number only increases, never decreases.
                logger.warning(
                    "[MQTT] Failed to publish configuration"
                    f" {sensor_identifier}#{revision}, retrying in"
                    f" {backoff} seconds: {repr(e)}"
                )
                # Backoff exponentially, up until about 5 minutes
                if backoff < 256:
                    backoff *= 2
                await asyncio.sleep(backoff)

    # Fire-and-forget the retry task, save the reference, and return immediately
    task = asyncio.create_task(helper(sensor_identifier, revision, configuration))
    task_references.add(task)
    task.add_done_callback(task_references.remove)


async def _handle_acknowledgements(sensor_identifier, payload, dbpool):
    query, arguments = database.parametrize(
        identifier="update-configuration-on-acknowledgement",
        arguments=[
            {
                "sensor_identifier": sensor_identifier,
                "revision": acknowledgment.revision,
                "acknowledgement_timestamp": acknowledgment.timestamp,
                "success": acknowledgment.success,
            }
            for i, acknowledgment in enumerate(payload.heartbeats)
        ],
    )
    try:
        await dbpool.executemany(query, arguments)
    except asyncpg.ForeignKeyViolationError:
        logger.warning(
            f"[MQTT] Failed to handle; Sensor not found: {sensor_identifier}"
        )
    else:
        logger.info(
            f"[MQTT] Handled {len(payload.heartbeats)} acknowledgements from"
            f" {sensor_identifier}"
        )


async def _handle_measurements(sensor_identifier, payload, dbpool):
    query, arguments = database.parametrize(
        identifier="create-measurement",
        arguments=[
            {
                "sensor_identifier": sensor_identifier,
                "revision": measurement.revision,
                "creation_timestamp": measurement.timestamp,
                "index": index,
                "measurement": measurement.value,
            }
            for index, measurement in enumerate(payload.measurements)
        ],
    )
    try:
        await dbpool.executemany(query, arguments)
    except asyncpg.ForeignKeyViolationError:
        logger.warning(
            f"[MQTT] Failed to handle; Sensor not found: {sensor_identifier}"
        )
    """
    else:
        logger.info(
            f"[MQTT] Handled {len(payload.measurements)} measurements from"
            f" {sensor_identifier}"
        )
    """


async def _handle_logs(sensor_identifier, payload, dbpool):
    query, arguments = database.parametrize(
        identifier="create-log",
        arguments=[
            {
                "sensor_identifier": sensor_identifier,
                "revision": log.revision,
                "creation_timestamp": log.timestamp,
                "index": index,
                "severity": log.severity,
                "subject": log.subject,
                "details": log.details,
            }
            for index, log in enumerate(payload.logs)
        ],
    )
    try:
        await dbpool.executemany(query, arguments)
    except asyncpg.ForeignKeyViolationError:
        logger.warning(
            f"[MQTT] Failed to handle; Sensor not found: {sensor_identifier}"
        )
    else:
        logger.info(f"[MQTT] Handled {len(payload.logs)} logs from {sensor_identifier}")


SUBSCRIPTIONS = {
    "heartbeats/+": (_handle_acknowledgements, validation.AcknowledgementsMessage),
    "measurements/+": (_handle_measurements, validation.MeasurementsMessage),
    "logs/+": (_handle_logs, validation.LogsMessage),
}


async def listen(mqttc, dbpool):
    """Listen to and handle incoming MQTT messages from sensor systems."""
    async with mqttc.messages() as messages:
        # Subscribe to all topics
        for wildcard in SUBSCRIPTIONS.keys():
            await mqttc.subscribe(wildcard, qos=1, timeout=10)
            logger.info(f"[MQTT] Subscribed to: {wildcard}")
        # Loop through incoming messages
        async for message in messages:
            # TODO: Remove condition when there's no more logs limit
            if not message.topic.matches(list(SUBSCRIPTIONS.keys())[1]):
                logger.info(
                    f"[MQTT] Received message: {message.payload!r} on topic:"
                    f" {message.topic}"
                )
            # Get sensor identifier from the topic and decode the payload
            # TODO validate that identifier is a valid UUID format
            sensor_identifier = str(message.topic).split("/")[-1]
            try:
                payload = json.loads(message.payload.decode())
            except json.decoder.JSONDecodeError:
                logger.warning(f"[MQTT] Malformed message: {message.payload!r}")
                continue
            if not isinstance(payload, dict):
                logger.warning(f"[MQTT] Malformed message: {message.payload!r}")
                continue
            # Call the appropriate handler; First match wins
            for wildcard, (handler, validator) in SUBSCRIPTIONS.items():
                if message.topic.matches(wildcard):
                    try:
                        payload = validator(**payload)
                        await handler(sensor_identifier, payload, dbpool)
                    # Errors are logged and ignored as we can't give feedback
                    except pydantic.ValidationError:
                        logger.warning(f"[MQTT] Malformed message: {message.payload!r}")
                    except Exception as e:  # pragma: no cover
                        logger.error(e, exc_info=True)
                    break
            else:  # Executed if no break is called
                logger.warning(f"[MQTT] Failed to match topic: {message.topic}")
