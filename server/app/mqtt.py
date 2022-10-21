import json
import ssl
import typing

import asyncio_mqtt as aiomqtt
import databases

import app.settings as settings
import app.utils as utils
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


async def listen_and_write(
    database_client: databases.Database,
    mqtt_client: aiomqtt.Client,
) -> typing.NoReturn:
    """Listen to incoming sensor measurements and write them to the database.

    - measurements cannot really be meaningfully validated except for their schema
    - TODO dump messages that don't pass validation > log > show in status as timestamp
      of last message, but also that last message was faulty
    - TODO allow nodes to send measurements for only part of all values (e.g. when one
      of multiple sensors breaks, different node architectures, etc.)
    - TODO use sender ID as "node" value?
    """
    async with mqtt_client.unfiltered_messages() as messages:
        await mqtt_client.subscribe("measurements")
        logger.info(f'Subscribed to MQTT topic "measurements"')
        async for message in messages:
            payload = _decode_payload(message.payload)
            logger.info(f"Received message: {payload} (topic: {message.topic})")
            # write measurement to database
            await database_client.execute(
                query=MEASUREMENTS.insert(),
                values={
                    "node": payload["node"],
                    "measurement_timestamp": payload["timestamp"],
                    "receipt_timestamp": utils.timestamp(),
                    "value": payload["value"],
                },
            )
