import ssl
import json

import app.asyncio_mqtt as aiomqtt
import app.settings as settings
import app.utils as utils

from app.logs import logger
from app.database import MEASUREMENTS


CONFIGURATION = {
    "hostname": settings.MQTT_URL,
    "port": 8883,
    "protocol": aiomqtt.ProtocolVersion.V5,
    "username": settings.MQTT_IDENTIFIER,
    "password": settings.MQTT_PASSWORD,
    "tls_params": aiomqtt.TLSParameters(tls_version=ssl.PROTOCOL_TLS),
}


def _encode_payload(payload):
    """Encode python dict into utf-8 JSON bytestring."""
    return json.dumps(payload).encode()


def _decode_payload(payload):
    """Decode python dict from utf-8 JSON bytestring."""
    return json.loads(payload.decode())


async def send(mqtt_client, payload, topic):
    """Publish a JSON message to the specified topic."""
    await mqtt_client.publish("measurements", payload=_encode_payload(payload))


async def listen_and_write(database_client, mqtt_client):
    """Listen to incoming sensor measurements and write them to the database."""
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
