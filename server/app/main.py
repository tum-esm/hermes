import starlette.applications
import starlette.routing
import starlette.responses
import asyncio
import sqlalchemy as sa
import pydantic
import contextlib
import databases

import app.asyncio_mqtt as aiomqtt
import app.settings as settings
import app.mqtt as mqtt
import app.utils as utils
import app.errors as errors
import app.models as models
import app.database as database

from app.logs import logger
from app.database import MEASUREMENTS


async def get_status(request):
    """Return some status information about the server."""

    # send a test mqtt message
    import random

    payload = {
        "node": "kabuto",
        "timestamp": utils.timestamp(),
        "value": random.randint(0, 2**10),
    }
    await mqtt.send(mqtt_client, payload, "measurements")

    return starlette.responses.JSONResponse(
        {
            "commit_sha": settings.COMMIT_SHA,
            "branch_name": settings.BRANCH_NAME,
            "start_time": settings.START_TIME,
        }
    )


async def get_measurements(request):
    """Return sensor measurements sorted chronologically, optionally filtered."""

    # TODO simplify this part somehow so that we don't have to duplicate it
    try:
        # TODO use one model for body/query/...
        request = models.GetMeasurementsRequest(**request.query_params)
    except pydantic.ValidationError:
        # TODO include specific pydantic error message
        logger.warning("GET /measurements: InvalidSyntaxError")
        raise errors.InvalidSyntaxError()

    # define default columns and conditions
    columns = [
        column
        for column in MEASUREMENTS.columns.keys()
        if column not in ["receipt_timestamp"]
    ]
    conditions = []

    # build customized database query from query parameters
    if request.nodes is not None:
        conditions.append(
            sa.or_(*[MEASUREMENTS.columns.node == node for node in request.nodes])
        )
    if request.values is not None:
        columns = [
            MEASUREMENTS.columns.node,
            MEASUREMENTS.columns.measurement_timestamp,
            *[
                sa.column(value)
                for value in request.values
                if value
                in set(MEASUREMENTS.columns.keys())
                - {"node", "measurement_timestamp", "receipt_timestamp"}
            ],
        ]
    if request.start_timestamp is not None:
        conditions.append(
            MEASUREMENTS.columns.measurement_timestamp >= int(request.start_timestamp)
        )
    if request.end_timestamp is not None:
        conditions.append(
            MEASUREMENTS.columns.measurement_timestamp < int(request.end_timestamp)
        )

    # execute query and return results
    # TODO think about streaming here
    result = await database_client.fetch_all(
        query=(
            sa.select(columns)
            .where(sa.and_(*conditions))
            .order_by(sa.asc(MEASUREMENTS.columns.measurement_timestamp))
            .offset(request.skip)
            .limit(request.limit)
        )
    )
    return starlette.responses.JSONResponse(database.dictify(result))


database_client = None
mqtt_client = None


@contextlib.asynccontextmanager
async def lifespan(app):
    global database_client
    global mqtt_client
    async with databases.Database(**database.CONFIGURATION) as x:
        async with aiomqtt.Client(**mqtt.CONFIGURATION) as y:
            database_client = x
            mqtt_client = y
            # start MQTT listener in (unawaited) asyncio task
            loop = asyncio.get_event_loop()
            loop.create_task(mqtt.listen_and_write(database_client, mqtt_client))
            yield


app = starlette.applications.Starlette(
    routes=[
        starlette.routing.Route(
            path="/status",
            endpoint=get_status,
            methods=["GET"],
        ),
        starlette.routing.Route(
            path="/measurements",
            endpoint=get_measurements,
            methods=["GET"],
        ),
    ],
    # TODO limit to one MQTT instance for multiple workers, or use shared subscriptions
    lifespan=lifespan,
)
