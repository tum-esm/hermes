import starlette.applications
import starlette.routing
import starlette.responses
import asyncio
import ssl
import json

import app.asyncio_mqtt as aiomqtt
import app.settings as settings
import app.mqtt as mqtt
import app.utils as utils
import app.database as database


async def get_status(request):
    """Return some status information about the server."""

    # send a test mqtt message
    import random

    payload = {"timestamp": utils.timestamp(), "value": random.randint(0, 2**10)}
    await mqtt.send(payload, "measurements")

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
    # startup MQTT client for listening to sensor measurements
    # TODO either limit to one for multiple workers, or use shared subscriptions
    on_startup=[database.startup, mqtt.startup],
    on_shutdown=[database.shutdown],
)
