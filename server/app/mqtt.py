import json
import ssl
import asyncio
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


class Client(aiomqtt.Client):
    """MQTT client with some additional functionality."""

    def __init__(self, database_client: asyncpg.Connection) -> None:
        super().__init__(
            hostname=settings.MQTT_URL,
            port=settings.MQTT_PORT,
            protocol=aiomqtt.ProtocolVersion.V5,
            username=settings.MQTT_IDENTIFIER,
            password=settings.MQTT_PASSWORD,
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

    async def _publish_json(
        self, topic: str, payload: dict[str, typing.Any], qos: int, retain: bool
    ) -> None:
        """Publish method for sending JSON payloads with added logging."""
        await super().publish(
            topic=topic,
            payload=_encode_payload(payload),
            qos=qos,
            retain=retain,
        )
        logger.info(f"[MQTT] Published message: {payload} to topic: {topic}")

    async def publish(self, *args, **kwargs) -> None:
        raise NotImplementedError

    async def publish_configuration(
        self, sensor_identifier: str, configuration: dict[str, typing.Any]
    ) -> None:
        """Publish a configuration to the specified sensor."""
        await self._publish_json(
            topic=f"configurations/{sensor_identifier}",
            payload=configuration,
            qos=1,
            retain=True,
        )

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
                    template="insert_measurement.sql",
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
        # TODO change to measurements/+ everywhere
        topic_measurements = "measurements"
        async with self.unfiltered_messages() as messages:
            await self.subscribe(topic_measurements, qos=1, timeout=10)
            logger.info(f"[MQTT] Subscribed to topic: {topic_measurements}")
            # TODO subscribe to more topics here

            async for message in messages:
                payload = _decode_payload(message.payload)
                logger.info(
                    f"[MQTT] Received message: {payload} on topic: {message.topic}"
                )
                # TODO match by measurements/+ wildcard here and use + as sensor_identifier
                # instead of requiring it in the message
                if message.topic == topic_measurements:
                    await self._process_measurement_payload(payload)
                else:
                    logger.warning(f"[MQTT] Could not match topic: {message.topic}")
