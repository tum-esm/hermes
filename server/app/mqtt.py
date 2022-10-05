import asyncio
import ssl

import app.asyncio_mqtt as amqtt
import app.settings as settings


async def startup():
    """Set up the MQTT client and start listening to incoming sensor measurements."""

    async def listen_and_write():
        async with amqtt.Client(
            hostname=settings.MQTT_URL,
            port=8883,
            protocol=amqtt.ProtocolVersion.V5,
            username=settings.MQTT_IDENTIFIER,
            password=settings.MQTT_PASSWORD,
            tls_params=amqtt.TLSParameters(
                tls_version=ssl.PROTOCOL_TLS,
            ),
        ) as client:
            async with client.unfiltered_messages() as messages:
                await client.subscribe("measurements")
                async for message in messages:
                    print(message.topic)
                    print(message.payload.decode())

    # wait for messages in (unawaited) asyncio task
    loop = asyncio.get_event_loop()
    loop.create_task(listen_and_write())
