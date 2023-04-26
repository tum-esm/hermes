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
        query, arguments = database.build(
            template="update-configuration-on-publish.sql",
            template_arguments={},
            query_arguments={
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


async def _handle_heartbeats(sensor_identifier, payload, dbpool):
    """Process incoming sensor heartbeats.

    Heartbeat messages are critical to the system working correctly. This is in
    contrast to logs, which only fulfill a logging functionality
    that allows us to see errors on the sensors straight from the dashboard.
    On receival of a heartbeat, we:

    1. Update configuration on acknowledgement success/failure
    2. TODO Update sensor's last seen
    """
    for i, heartbeat in enumerate(payload.heartbeats):
        # We process each heartheat individually in separate transactions
        async with dbpool.acquire() as connection:
            async with connection.transaction():
                # Write heartbeat as log in the database
                query, arguments = database.build(
                    template="create-log.sql",
                    template_arguments={},
                    query_arguments={
                        "sensor_identifier": sensor_identifier,
                        "revision": heartbeat.revision,
                        "creation_timestamp": heartbeat.timestamp,
                        "position_in_transmission": i,
                        "severity": "system",
                        "subject": "Heartbeat",
                        "details": json.dumps({"success": heartbeat.success}),
                    },
                )
                try:
                    await connection.execute(query, *arguments)
                except asyncpg.ForeignKeyViolationError:
                    logger.warning(
                        "[MQTT] Failed to handle; Sensor not found:"
                        f" {sensor_identifier}"
                    )
                except Exception as e:  # pragma: no cover
                    logger.error(e, exc_info=True)
                # Update configuration in the database
                query, arguments = database.build(
                    template="update-configuration-on-acknowledgement.sql",
                    template_arguments={},
                    query_arguments={
                        "sensor_identifier": sensor_identifier,
                        "revision": heartbeat.revision,
                        "acknowledgement_timestamp": heartbeat.timestamp,
                        "success": heartbeat.success,
                    },
                )
                try:
                    await connection.execute(query, *arguments)
                except Exception as e:  # pragma: no cover
                    logger.error(e, exc_info=True)
        logger.info(f"[MQTT] Processed heartbeat {heartbeat} from {sensor_identifier}")


async def _handle_logs(sensor_identifier, payload, dbpool):
    query, arguments = database.build(
        template="create-log.sql",
        template_arguments={},
        query_arguments=[
            {
                "sensor_identifier": sensor_identifier,
                "revision": log.revision,
                "creation_timestamp": log.timestamp,
                "position_in_transmission": i,
                "severity": log.severity,
                "subject": log.subject,
                "details": log.details,
            }
            for i, log in enumerate(payload.logs)
        ],
    )
    try:
        await dbpool.executemany(query, arguments)
    except asyncpg.ForeignKeyViolationError:
        logger.warning(
            f"[MQTT] Failed to handle; Sensor not found: {sensor_identifier}"
        )
    logger.info(f"[MQTT] Processed {len(payload.logs)} logs from {sensor_identifier}")


async def _handle_measurements(sensor_identifier, payload, dbpool):
    query, arguments = database.build(
        template="create-measurement.sql",
        template_arguments={},
        query_arguments=[
            {
                "sensor_identifier": sensor_identifier,
                "revision": measurement.revision,
                "creation_timestamp": measurement.timestamp,
                "position_in_transmission": i,
                "measurement": measurement.value,
            }
            for i, measurement in enumerate(payload.measurements)
        ],
    )
    try:
        await dbpool.executemany(query, arguments)
    except asyncpg.ForeignKeyViolationError:
        logger.warning(
            f"[MQTT] Failed to handle; Sensor not found: {sensor_identifier}"
        )
    """
    logger.info(
        f"[MQTT] Processed {len(payload.measurements)} measurements from"
        f" {sensor_identifier}"
    )
    """


WILDCARDS = {
    "heartbeats/+": (_handle_heartbeats, validation.HeartbeatsMessage),
    "logs/+": (_handle_logs, validation.LogsMessage),
    "measurements/+": (_handle_measurements, validation.MeasurementsMessage),
}


async def listen(mqttc, dbpool):
    """Listen to and handle incoming MQTT messages from sensor systems."""
    async with mqttc.messages() as messages:
        # Subscribe to all topics
        for wildcard in WILDCARDS.keys():
            await mqttc.subscribe(wildcard, qos=1, timeout=10)
            logger.info(f"[MQTT] Subscribed to: {wildcard}")
        # Loop through incoming messages
        async for message in messages:
            # TODO: Remove condition when there's no more logs limit
            if not message.topic.matches(list(WILDCARDS.keys())[-1]):
                logger.info(
                    f"[MQTT] Received message: {message.payload!r} on topic:"
                    f" {message.topic}"
                )
            # Get sensor identifier from the topic and decode the payload
            sensor_identifier = str(message.topic).split("/")[-1]
            try:
                payload = json.loads(message.payload.decode())
            except json.decoder.JSONDecodeError:
                logger.warning(f"[MQTT] Malformed message: {message.payload!r}")
                continue
            if not isinstance(payload, dict):
                logger.warning(f"[MQTT] Malformed message: {message.payload!r}")
                continue
            # Call the appropriate handler
            matched = False
            for wildcard, (handler, validator) in WILDCARDS.items():
                if message.topic.matches(wildcard):
                    try:
                        payload = validator(**payload)
                    except pydantic.ValidationError:
                        logger.warning(f"[MQTT] Malformed message: {message.payload!r}")
                    else:
                        try:
                            await handler(sensor_identifier, payload, dbpool)
                        except Exception as e:  # pragma: no cover
                            logger.error(e, exc_info=True)
                        matched = True
            if not matched:
                logger.warning(f"[MQTT] Failed to match topic: {message.topic}")
