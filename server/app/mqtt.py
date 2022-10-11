import asyncio
import ssl
import asyncpg as pg
import json

import app.asyncio_mqtt as aiomqtt
import app.settings as settings
import app.logs as logs
import app.utils as utils


async def startup():
    """Set up the MQTT client and start listening to incoming sensor measurements."""

    async def listen_and_write():

        connection = await pg.connect(
            dsn=settings.POSTGRESQL_URL,
            user=settings.POSTGRESQL_IDENTIFIER,
            password=settings.POSTGRESQL_PASSWORD,
        )

        async with aiomqtt.Client(
            hostname=settings.MQTT_URL,
            port=8883,
            protocol=aiomqtt.ProtocolVersion.V5,
            username=settings.MQTT_IDENTIFIER,
            password=settings.MQTT_PASSWORD,
            tls_params=aiomqtt.TLSParameters(
                tls_version=ssl.PROTOCOL_TLS,
            ),
        ) as client:
            async with client.unfiltered_messages() as messages:
                await client.subscribe("measurements")
                async for message in messages:

                    payload = json.loads(message.payload.decode())

                    logs.logger.info(
                        f"Received message: {payload} (topic: {message.topic})"
                    )

                    # write to database
                    async with connection.transaction():
                        await connection.execute(
                            f"""
                            CREATE TABLE IF NOT EXISTS measurements (
                                timestamp_measurement   integer,
                                timestamp_receipt       integer,
                                value                   integer
                            );
                        """
                        )
                        await connection.execute(
                            f"""
                            INSERT INTO measurements VALUES(
                                {payload['timestamp']},
                                {utils.timestamp()},
                                {payload['value']}
                            );
                        """
                        )

        await connection.close()

    # wait for messages in (unawaited) asyncio task
    loop = asyncio.get_event_loop()
    loop.create_task(listen_and_write())
