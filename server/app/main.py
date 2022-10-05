import starlette.applications
import starlette.routing
import starlette.responses
import asyncio_mqtt as amqtt

import app.settings as settings
import app.mqtt as mqtt


async def get_status(request):
    """Return some status information about the server."""

    # test mqtt message
    import asyncio
    import ssl
    import app.asyncio_mqtt as amqtt

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
        message = "test"
        await client.publish("measurements", payload=message.encode())

    return starlette.responses.JSONResponse(
        {
            "commit_sha": settings.COMMIT_SHA,
            "branch_name": settings.BRANCH_NAME,
            "start_time": settings.START_TIME,
        }
    )


app = starlette.applications.Starlette(
    routes=[
        starlette.routing.Route(
            path="/status",
            endpoint=get_status,
            methods=["GET"],
        ),
    ],
    # spawn MQTT client for listening in separate process
    # TODO either limit to one for multiple workers, or use shared subscriptions
    on_startup=[mqtt.startup],
    on_shutdown=[mqtt.shutdown],
)
