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
            # Make the MQTT connection persistent
            # Broker retains messages on topics we subscribed to on disconnection
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
            query, parameters = database.build(
                template="update-configuration-on-publish.sql",
                template_parameters={},
                query_parameters={
                    "sensor_identifier": sensor_identifier,
                    "revision": revision,
                },
            )
            while True:
                try:
                    await self.publish(
                        topic=f"{sensor_identifier}/configuration",
                        payload=_encode_payload(configuration),
                        qos=1,
                        retain=True,
                    )
                    await self.database_client.execute(query, *parameters)
                    logger.info(
                        f"[MQTT] Published configuration #{revision} to:"
                        f" {sensor_identifier}"
                    )
                    break
                except Exception as e:
                    logger.warning(
                        f"[MQTT] Failed to publish configuration #{revision} to"
                        f" {sensor_identifier}, retrying in {backoff} seconds:"
                        f" {repr(e)}"
                    )
                    if backoff < 256:
                        backoff *= 2
                    await asyncio.sleep(backoff)

        # Fire-and-forget the retry task, save the reference, and return immediately
        task = asyncio.create_task(helper(sensor_identifier, revision, configuration))
        task_references.add(task)
        task.add_done_callback(task_references.remove)

    async def _process_measurement_payload(
        self, payload: dict[str, typing.Any]
    ) -> None:
        """Validate a measurement message and write it to the database."""
        try:
            # TODO Move validation/exception logic into validation module
            message = validation.MeasurementsMessage(**payload)
            # TODO Insert in a single execution call; must adapt templating for this
            for measurement in message.measurements:
                query, parameters = database.build(
                    template="insert-measurement.sql",
                    template_parameters={},
                    query_parameters={
                        "sensor_identifier": message.sensor_identifier,
                        "measurement_timestamp": measurement.timestamp,
                        "measurement": measurement.values,
                    },
                )
                await self.database_client.execute(query, *parameters)
        except pydantic.ValidationError as e:
            # TODO still save `sensor_identifier` and `receipt_timestamp` in database?
            # -> works only if sensor_identifier is inferred from sender ID
            # Like this, we can show the timestamp of last message in the sensor status,
            # even if it was invalid
            logger.warning(f"[MQTT] Invalid message: {e}")
        except Exception as e:
            # TODO divide into more specific exceptions
            logger.error(f"[MQTT] Database error: {e}")

    async def listen(self) -> None:
        """Listen to incoming sensor messages and process them."""
        wildcard_measurements = "+/measurements"
        async with self.messages() as messages:
            await self.subscribe(wildcard_measurements, qos=1, timeout=10)
            logger.info(f"[MQTT] Subscribed to: {wildcard_measurements}")
            # TODO subscribe to more topics here

            async for message in messages:
                payload = _decode_payload(message.payload)
                logger.info(
                    f"[MQTT] Received message: {payload} on topic: {message.topic}"
                )
                # TODO use + as sensor_identifier
                # instead of requiring it in the message
                if message.topic.matches(wildcard_measurements):
                    await self._process_measurement_payload(payload)
                else:
                    logger.warning(f"[MQTT] Failed to match topic: {message.topic}")
