import json
import ssl
import typing

import asyncio_mqtt as aiomqtt
import databases

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


async def send(
    payload: dict[str, typing.Any],
    topic: str,
    mqtt_client: aiomqtt.Client,
) -> None:
    """Publish a JSON message to the specified topic."""
    await mqtt_client.publish(topic, payload=_encode_payload(payload))


async def _process_measurement_payload(
    payload: dict[str, typing.Any],
    database_client: databases.Database,
) -> None:
    """Validate a measurement message and write it to the database."""
    try:
        # TODO move validation/exception logic into validation module
        measurement = validation.MeasurementMessage(**payload)
        receipt_timestamp = utils.timestamp()
        for key, value in measurement.values.items():
            # TODO choose corresponding table based on key
            """
            await database_client.execute(
                query=MEASUREMENTS.insert(),
                values={
                    "sensor_identifier": measurement.sensor_identifier,
                    "measurement_timestamp": measurement.timestamp,
                    "receipt_timestamp": receipt_timestamp,
                    key: value,
                },
            )
            """
    except (TypeError, ValueError) as e:
        # TODO still save `sensor_identifier` and `receipt_timestamp` in database?
        # -> works only if sensor_identifier is inferred from sender ID
        # Like this, we can show the timestamp of last message in the sensor status,
        # even if it was invalid
        logger.warning(f"[MQTT] [TOPIC:measurements] Invalid message: {e}")
    except Exception as e:
        # TODO log database error and rollback
        logger.warning(f"[MQTT] [TOPIC:measurements] Failed to write: {e}")


async def listen_and_write(
    database_client: databases.Database,
    mqtt_client: aiomqtt.Client,
) -> typing.NoReturn:
    """Listen to incoming sensor measurements and write them to the database.

    - TODO Allow sensors to send measurements for only part of all values (e.g. when one
      of multiple sensors breaks, different sensor architectures, etc.)
    - TODO Use sender ID as "sensor" value?
    """
    async with mqtt_client.unfiltered_messages() as messages:
        await mqtt_client.subscribe("measurements", qos=1, timeout=10)
        logger.info(f"[MQTT] [TOPIC:measurements] Subscribed")
        # TODO subscribe to more topics here

        async for message in messages:
            payload = _decode_payload(message.payload)
            logger.info(f"[MQTT] [TOPIC:{message.topic}] Received message: {payload}")
            match message.topic:
                case "measurements":
                    await _process_measurement_payload(payload, database_client)
                case _:
                    logger.warning(
                        f"[MQTT] [TOPIC:{message.topic}] Could not match topic"
                    )
