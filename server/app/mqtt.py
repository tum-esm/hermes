import json
import ssl
import typing

import asyncio_mqtt as aiomqtt
import databases

import app.settings as settings
import app.utils as utils
import app.models as models
from app.database import MEASUREMENTS
from app.logs import logger


def _encode_payload(payload: typing.Dict[str, typing.Any]) -> bytes:
    """Encode python dict into utf-8 JSON bytestring."""
    return json.dumps(payload).encode()


def _decode_payload(payload: bytes) -> typing.Dict[str, typing.Any]:
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
    mqtt_client: aiomqtt.Client,
    payload: typing.Dict[str, typing.Any],
    topic: str,
) -> None:
    """Publish a JSON message to the specified topic."""
    await mqtt_client.publish("measurements", payload=_encode_payload(payload))


async def _process_measurement_payload(
    database_client: databases.Database,
    payload: dict[str, typing.Any],
) -> None:
    """Validate a measurement message and write it to the database."""
    try:
        measurement = models.Measurement(**payload)
        receipt_timestamp = utils.timestamp()
        for key, value in measurement.values.items():
            # TODO choose corresponding table based on key
            await database_client.execute(
                query=MEASUREMENTS.insert(),
                values={
                    "node": measurement.node,
                    "measurement_timestamp": measurement.timestamp,
                    "receipt_timestamp": receipt_timestamp,
                    key: value,
                },
            )
    except:
        # TODO log validation/database error and rollback
        pass


async def listen_and_write(
    database_client: databases.Database,
    mqtt_client: aiomqtt.Client,
) -> typing.NoReturn:
    """Listen to incoming sensor measurements and write them to the database.

    - Measurements cannot really be meaningfully validated except for their schema
    - TODO Dump messages that don't pass validation > log > show in status as timestamp
      of last message, but also that last message was faulty
    - TODO Allow nodes to send measurements for only part of all values (e.g. when one
      of multiple sensors breaks, different node architectures, etc.)
    - TODO Use sender ID as "node" value?
    """
    async with mqtt_client.unfiltered_messages() as messages:

        await mqtt_client.subscribe("measurements")
        logger.info(f"[MQTT] Subscribed to topic: measurements")
        # TODO subscribe to more topics here

        async for message in messages:
            payload = _decode_payload(message.payload)
            logger.info(f"[MQTT] Received message on {message.topic}: {payload}")
            match message.topic:
                case "measurements":
                    await _process_measurement_payload(database_client, payload)
                case _:
                    logger.warning(f"[MQTT] Did not process message")
