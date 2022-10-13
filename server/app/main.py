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
    """Return sensor measurements sorted chronologically, optionally filtered.

    Valid query parameters are:
    ================================
    station
    timestamp_start
    timestamp_end
    limit
    values

    """

    # TODO validate query parameters

    async with db.conn.transaction():
        # build query from query parameters
        columns = [db.measurements.c.timestamp_measurement]
        conditions = []
        limit = None
        if "values" in request.query_params:
            if "value" in request.query_params["values"]:
                columns.append(db.measurements.c.value)
        if "station" in request.query_params:
            # TODO add station identifier column to database table
            pass
        if "timestamp_start" in request.query_params:
            conditions.append(
                db.measurements.c.timestamp_measurement
                >= int(request.query_params["timestamp_start"])
            )
        if "timestamp_end" in request.query_params:
            conditions.append(
                db.measurements.c.timestamp_measurement
                < int(request.query_params["timestamp_end"])
            )
        if "limit" in request.query_params:
            limit = int(request.query_params["limit"])

        # think about streaming results here
        measurements = await db.conn.fetch_all(
            query=(
                sqla.select(columns)
                .where(sqla.and_(*conditions))
                .order_by(sqla.asc(db.measurements.c.timestamp_measurement))
                .limit(limit)
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
