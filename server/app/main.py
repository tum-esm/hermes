import starlette.applications
import starlette.routing
import starlette.responses
import asyncio
import sqlalchemy as sa
import pydantic

import app.asyncio_mqtt as aiomqtt
import app.settings as settings
import app.mqtt as mqtt
import app.utils as utils
import app.errors as errors
import app.models as models
import app.data as data

from app.logs import logger
from app.data import database, MEASUREMENTS


async def get_status(request):
    """Return some status information about the server."""

    # send a test mqtt message
    import random

    payload = {
        "node": "kabuto",
        "timestamp": utils.timestamp(),
        "value": random.randint(0, 2**10),
    }
    await mqtt.send(payload, "measurements")

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
        for column in MEASUREMENTS.columns
        if column.key not in ["receipt_timestamp"]
    ]
    conditions = []

    # build customized database query from query parameters
    if request.nodes is not None:
        for node in request.nodes:
            conditions.append(MEASUREMENTS.columns.node == node)
    if request.values is not None:
        columns = [
            MEASUREMENTS.columns.measurement_timestamp,
            *[sa.column(value) for value in request.values],
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
    result = await database.fetch_all(
        query=(
            sa.select(columns)
            .where(sa.and_(*conditions))
            .order_by(sa.asc(MEASUREMENTS.columns.measurement_timestamp))
            .limit(request.limit)
        )
    )
    return starlette.responses.JSONResponse(data.dictify(result))


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
    # startup MQTT client for listening to sensor measurements
    # TODO either limit to one for multiple workers, or use shared subscriptions
    on_startup=[data.startup, mqtt.startup],
    on_shutdown=[data.shutdown],
)
