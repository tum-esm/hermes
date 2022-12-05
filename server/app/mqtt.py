import asyncio
import json
import ssl
import typing

import asyncio_mqtt as aiomqtt
import asyncpg
import pydantic

import app.database as database
import app.settings as settings
import app.validation as validation
from app.logs import logger


def _encode_payload(payload: dict[str, typing.Any]) -> bytes:
    """Encode python dict into utf-8 JSON bytestring."""
    return json.dumps(payload).encode()


def _decode_payload(payload: bytes) -> dict[str, typing.Any]:
    """Decode python dict from utf-8 JSON bytestring."""
    return json.loads(payload.decode())


task_references = set()


class Client(aiomqtt.Client):
    """MQTT client with some additional functionality."""

    def __init__(self, database_client: asyncpg.Connection) -> None:
        super().__init__(
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
        )
        self.database_client = database_client

    async def publish_configuration(
        self,
        sensor_identifier: str,
        revision: int,
        configuration: dict[str, typing.Any],
    ) -> None:
        """Publish a configuration to the specified sensor."""

        async def helper(
            sensor_identifier: str, revision: int, configuration: dict[str, typing.Any]
        ) -> None:
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
                    await self.publish(
                        topic=f"{sensor_identifier}/configuration",
                        payload=_encode_payload(configuration),
                        qos=1,
                        retain=True,
                    )
                    # Try to set the publication timestamp in the database
                    await self.database_client.execute(query, *arguments)
                    logger.info(
                        f"[MQTT] Published configuration #{revision} to:"
                        f" {sensor_identifier}"
                    )
                    break
                except Exception as e:
                    # Retry if something fails. Duplicate messages are not a problem,
                    # the sensor can ignore them based on the revision number.
                    # The revision number only increases, never decreases.
                    logger.warning(
                        f"[MQTT] Failed to publish configuration #{revision} to"
                        f" {sensor_identifier}, retrying in {backoff} seconds:"
                        f" {repr(e)}"
                    )
                    # Backoff exponentially, up until about 5 minutes
                    if backoff < 256:
                        backoff *= 2
                    await asyncio.sleep(backoff)

        # Fire-and-forget the retry task, save the reference, and return immediately
        task = asyncio.create_task(helper(sensor_identifier, revision, configuration))
        task_references.add(task)
        task.add_done_callback(task_references.remove)

    async def _process_heartbeats_message(
        self, sensor_identifier: str, message: validation.HeartbeatsMessage
    ) -> None:
        """Process incoming sensor heartbeats.

        Heartbeat messages are critical to the system working correctly. This is in
        contrast to status messages, which only fulfill a kind of logging functionality
        that allows us to see errors on the sensors straight from the dashboard.
        On receival of a heartbeat, we:

        1. Update configuration on acknowledgement success/failure
        2. TODO Update sensor's last seen
        """
        for heartbeat in message.heartbeats:
            # We process each heartheat individually in separate transactions
            try:
                with self.database_client.transaction():
                    # Write heartbeat as status message in the database
                    query, arguments = database.build(
                        template="insert-status.sql",
                        template_arguments={},
                        query_arguments={
                            "sensor_identifier": sensor_identifier,
                            "revision": heartbeat.revision,
                            "creation_timestamp": heartbeat.timestamp,
                            "severity": "system",
                            "subject": "Heartbeat",
                            "details": json.dumps({"success": heartbeat.success}),
                        },
                    )
                    await self.database_client.execute(query, *arguments)
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
                    await self.database_client.execute(query, *arguments)
            except Exception as e:
                # TODO divide into more specific exceptions
                logger.error(f"[MQTT] Unknown error: {repr(e)}")

    async def _process_statuses_message(
        self, sensor_identifier: str, message: validation.StatusesMessage
    ) -> None:
        """Write incoming sensor statuses to the database."""
        try:
            query, arguments = database.build(
                template="insert-status.sql",
                template_arguments={},
                query_arguments=[
                    {
                        "sensor_identifier": sensor_identifier,
                        "revision": status.revision,
                        "creation_timestamp": status.timestamp,
                        "severity": status.severity,
                        "subject": status.subject,
                        "details": status.details,
                    }
                    for status in message.statuses
                ],
            )
            await self.database_client.executemany(query, arguments)
        except Exception as e:
            # TODO divide into more specific exceptions
            logger.error(f"[MQTT] Unknown error: {repr(e)}")

    async def _process_measurements_message(
        self, sensor_identifier: str, message: validation.MeasurementsMessage
    ) -> None:
        """Write incoming sensor measurements to the database."""
        try:
            query, arguments = database.build(
                template="insert-measurement.sql",
                template_arguments={},
                query_arguments=[
                    {
                        "sensor_identifier": sensor_identifier,
                        "revision": measurement.revision,
                        "creation_timestamp": measurement.timestamp,
                        "measurement": measurement.value,
                    }
                    for measurement in message.measurements
                ],
            )
            await self.database_client.executemany(query, arguments)
        except Exception as e:
            # TODO divide into more specific exceptions
            logger.error(f"[MQTT] Unknown error: {repr(e)}")

    async def listen(self) -> None:
        """Listen to incoming sensor MQTT messages and process them."""
        wildcard_heartbeats = "heartbeats/+"
        wildcard_statuses = "statuses/+"
        wildcard_measurements = "measurements/+"

        async with self.messages() as messages:
            # Subscribe to all topics
            await self.subscribe(wildcard_heartbeats, qos=1, timeout=10)
            logger.info(f"[MQTT] Subscribed to: {wildcard_heartbeats}")
            await self.subscribe(wildcard_statuses, qos=1, timeout=10)
            logger.info(f"[MQTT] Subscribed to: {wildcard_statuses}")
            await self.subscribe(wildcard_measurements, qos=1, timeout=10)
            logger.info(f"[MQTT] Subscribed to: {wildcard_measurements}")

            async for message in messages:
                try:
                    logger.info(
                        f"[MQTT] Received message: {message.payload} on topic:"
                        f" {message.topic}"
                    )
                    # Get sensor identifier from the topic and decode the payload
                    sensor_identifier = str(message.topic).split("/")[-1]
                    payload = _decode_payload(message.payload)
                    # Match topic and process message
                    if message.topic.matches(wildcard_heartbeats):
                        await self._process_heartbeats_message(
                            sensor_identifier=sensor_identifier,
                            message=validation.HeartbeatsMessage(**payload),
                        )
                    if message.topic.matches(wildcard_statuses):
                        await self._process_statuses_message(
                            sensor_identifier=sensor_identifier,
                            message=validation.StatusesMessage(**payload),
                        )
                    if message.topic.matches(wildcard_measurements):
                        await self._process_measurements_message(
                            sensor_identifier=sensor_identifier,
                            message=validation.MeasurementsMessage(**payload),
                        )
                    else:
                        logger.warning(f"[MQTT] Failed to match topic: {message.topic}")

                except pydantic.ValidationError as e:
                    # TODO still save `sensor_identifier` and `receipt_timestamp` in
                    # database? -> works only if sensor_identifier is inferred from
                    # sender ID. Like this, we can show the timestamp of last message
                    # in the sensor status, even if it was invalid
                    logger.warning(f"[MQTT] Invalid message: {repr(e)}")
                except Exception as e:
                    logger.error(f"[MQTT] Unknown error: {repr(e)}")
