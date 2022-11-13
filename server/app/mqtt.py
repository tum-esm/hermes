import json
import ssl
import typing

import asyncio_mqtt as aiomqtt
import asyncpg
import pydantic

import app.database as database
import app.settings as settings
import app.utils as utils
import app.validation as validation
from app.logs import logger


def _encode_payload(payload: dict[str, typing.Any]) -> bytes:
    """Encode python dict into utf-8 JSON bytestring."""
    return json.dumps(payload).encode()


def _decode_payload(payload: bytes) -> dict[str, typing.Any]:
    """Decode python dict from utf-8 JSON bytestring."""
    return json.loads(payload.decode())


CONFIGURATION = {
    "hostname": settings.MQTT_URL,
    "port": 8883,
    "protocol": aiomqtt.ProtocolVersion.V5,
    "username": settings.MQTT_IDENTIFIER,
    "password": settings.MQTT_PASSWORD,
    "tls_params": aiomqtt.TLSParameters(tls_version=ssl.PROTOCOL_TLS),
}


async def publish(
    mqtt_client: aiomqtt.Client,
    topic: str,
    payload: dict[str, typing.Any],
    qos: int = 0,
    retain: bool = False,
) -> None:
    """Publish a JSON message to the specified topic."""
    await mqtt_client.publish(
        topic=topic,
        payload=_encode_payload(payload),
        qos=qos,
        retain=retain,
    )
    logger.info(f"[MQTT] [PUB] [TOPIC:{topic}] Published message: {payload}")


async def _process_measurement_payload(
    payload: dict[str, typing.Any],
    database_client: asyncpg.connection.Connection,
) -> None:
    """Validate a measurement message and write it to the database."""
    try:
        # TODO Move validation/exception logic into validation module
        message = validation.MeasurementsMessage(**payload)
        # TODO Insert everything in one execution call
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
            await database_client.execute(query, *parameters)
    except pydantic.ValidationError as e:
        # TODO still save `sensor_identifier` and `receipt_timestamp` in database?
        # -> works only if sensor_identifier is inferred from sender ID
        # Like this, we can show the timestamp of last message in the sensor status,
        # even if it was invalid
        logger.warning(f"[MQTT] [SUB] [TOPIC:measurements] Invalid message: {e}")
    except Exception as e:
        # TODO divide into more specific exceptions
        logger.error(f"[MQTT] [SUB] [TOPIC:measurements] Database error: {e}")


async def listen(
    database_client: asyncpg.connection.Connection,
    mqtt_client: aiomqtt.Client,
) -> typing.NoReturn:
    """Listen to incoming sensor messages and process them."""
    async with mqtt_client.unfiltered_messages() as messages:
        await mqtt_client.subscribe("measurements", qos=1, timeout=10)
        logger.info(f"[MQTT] [SUB] [TOPIC:measurements] Subscribed")
        # TODO subscribe to more topics here

        async for message in messages:
            payload = _decode_payload(message.payload)
            logger.info(
                f"[MQTT] [SUB] [TOPIC:{message.topic}] Received message: {payload}"
            )
            # TODO match by measurements/+ wildcard here and use + as sensor_identifier
            # instead of requiring it in the message
            match message.topic:
                case "measurements":
                    await _process_measurement_payload(payload, database_client)
                case _:
                    logger.warning(
                        f"[MQTT] [SUB] [TOPIC:{message.topic}] Could not match topic"
                    )
