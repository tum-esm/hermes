import asyncio
import contextlib

import asyncio_mqtt as aiomqtt
import databases
import pydantic
import sqlalchemy as sa
import starlette.applications
import starlette.responses
import starlette.routing

import app.database as database
import app.errors as errors
import app.models as models
import app.mqtt as mqtt
import app.settings as settings
import app.utils as utils
from app.database import MEASUREMENTS
from app.logs import logger


async def get_status(request):
    """Return some status information about the server."""

    # Send a test mqtt message
    import random

    payload = {
        "node": "kabuto",
        "timestamp": utils.timestamp(),
        "values": {"value": random.randint(0, 2**10)},
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

    # TODO Simplify this part somehow so that we don't have to duplicate it
    try:
        # TODO Use one model for body/query/...
        request = models.GetMeasurementsRequest(**request.query_params)
    except pydantic.ValidationError:
        # TODO Include specific pydantic error message
        logger.warning("GET /measurements: InvalidSyntaxError")
        raise errors.InvalidSyntaxError()

    # Define default columns and conditions
    columns = [
        column
        for column in MEASUREMENTS.columns.keys()
        if column not in ["receipt_timestamp"]
    ]
    conditions = []

    # Build customized database query from query parameters
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

    # Execute query and return results
    # TODO Think about streaming here
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
    """Manage lifetime of database client and MQTT client.

    This creates the necessary database tables if they don't exist yet. It also starts
    a new asyncio task that listens for incoming sensor measurements over MQTT messages
    and stores them in the database.
    """
    global database_client
    global mqtt_client
    async with databases.Database(**database.CONFIGURATION) as x:
        async with aiomqtt.Client(**mqtt.CONFIGURATION) as y:
            database_client = x
            mqtt_client = y
            # Create database tables if they don't exist yet
            for table in database.metadata.tables.values():
                await database_client.execute(
                    query=database.compile(
                        sa.schema.CreateTable(table, if_not_exists=True)
                    )
                )
            # Start MQTT listener in (unawaited) asyncio task
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
    # TODO Limit to one MQTT instance for multiple workers, or use shared subscriptions
    lifespan=lifespan,
)
