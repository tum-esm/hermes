import starlette.applications
import starlette.routing
import starlette.responses
import asyncio
import ssl
import json
import sqlalchemy as sqla

import app.asyncio_mqtt as aiomqtt
import app.settings as settings
import app.mqtt as mqtt
import app.utils as utils
import app.database as db
import app.errors as errors


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


async def get_measurements(request):
    """Return sensor measurements sorted chronologically, optionally filtered."""

    # TODO simplify this part somehow so that we don't have to duplicate it
    try:
        # TODO use one model for body/query/...
        request = models.GetMeasurementsRequest(**request.query_params)
    except pydantic.ValidationError:
        log.error.warning("GET /measurements: InvalidSyntaxError")
        raise errors.InvalidSyntaxError()

    # build query from query parameters
    columns = [db.measurements.c.measurement_timestamp]
    conditions = []

    if request.nodes is not None:
        # TODO add node identifier column to database table
        pass
    if request.values is not None:
        if "value" in request.values:
            columns.append(db.measurements.c.value)
    if request.start_timestamp is not None:
        conditions.append(
            db.measurements.c.measurement_timestamp >= int(request.start_timestamp)
        )
    if request.end_timestamp is not None:
        conditions.append(
            db.measurements.c.measurement_timestamp < int(request.end_timestamp)
        )

    async with db.conn.transaction():
        # TODO think about streaming results here
        measurements = await db.conn.fetch_all(
            query=(
                sqla.select(columns)
                .where(sqla.and_(*conditions))
                .order_by(sqla.asc(db.measurements.c.measurement_timestamp))
                .limit(request.limit)
            )
        )

    measurements = [dict(record) for record in measurements]
    return starlette.responses.JSONResponse(measurements)


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
    on_startup=[db.startup, mqtt.startup],
    on_shutdown=[db.shutdown],
)
