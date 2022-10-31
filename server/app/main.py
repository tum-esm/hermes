import asyncio
import contextlib

import asyncio_mqtt as aiomqtt
import databases
import sqlalchemy as sa
import starlette.applications
import starlette.responses
import starlette.routing

import app.database as database
import app.errors as errors
import app.mqtt as mqtt
import app.settings as settings
import app.utils as utils
import app.validation as validation
from app.database import CONF, MEAS
from app.logs import logger


async def get_status(request):
    """Return some status information about the server."""

    # Send a test mqtt message
    import random

    payload = {
        "sensor_identifier": "kabuto",
        "timestamp": utils.timestamp(),
        "values": {"value": random.randint(0, 2**10)},
    }
    await mqtt.send(payload, "measurements", mqtt_client)

    return starlette.responses.JSONResponse(
        {
            "commit_sha": settings.COMMIT_SHA,
            "branch_name": settings.BRANCH_NAME,
            "start_time": settings.START_TIME,
        }
    )


async def get_sensors(request):
    """Return status and configuration of sensors."""
    request = await validation.validate(request, validation.GetSensorsRequest)

    # TODO Enrich with
    # V last measurement timestamp
    # - activity timeline
    # - last measurement
    # - last sensor health update

    # Define filter by sensor_identifier
    # TODO Duplicated from get_measurements -> move to some own query (builder) module?
    conditions = [
        sa.or_(
            MEAS.c.sensor_identifier == sensor_identifier
            for sensor_identifier in request.query.sensors
        ),
    ]
    # Build query
    latest_measurements = (
        sa.select(MEAS.c)
        .select_from(MEAS)
        .order_by(MEAS.c.sensor_identifier.asc(), MEAS.c.measurement_timestamp.asc())
        .distinct(MEAS.c.sensor_identifier)
    )
    query = (
        sa.select([*CONF.c, latest_measurements.c.measurement_timestamp])
        .select_from(
            CONF.join(
                latest_measurements,
                CONF.c.sensor_identifier == latest_measurements.c.sensor_identifier,
            )
        )
        .where(sa.and_(*conditions))
        .order_by(CONF.c.sensor_identifier.asc())
    )
    # Execute query and return results
    result = await database_client.fetch_all(query=query)
    return starlette.responses.JSONResponse(database.dictify(result))


async def get_measurements(request):
    """Return measurements sorted chronologically, optionally filtered."""
    request = await validation.validate(request, validation.GetMeasurementsRequest)

    # Define the returned columns
    columns = [
        MEAS.c.sensor_identifier,
        MEAS.c.measurement_timestamp,
        *[sa.column(value_identifier) for value_identifier in request.query.values],
    ]
    # Define filter by sensor_identifier
    conditions = [
        sa.or_(
            MEAS.c.sensor_identifier == sensor_identifier
            for sensor_identifier in request.query.sensors
        ),
    ]
    # Define filter by measurement_timestamp
    if request.query.start_timestamp is not None:
        conditions.append(
            MEAS.c.measurement_timestamp >= int(request.query.start_timestamp)
        )
    if request.query.end_timestamp is not None:
        conditions.append(
            MEAS.c.measurement_timestamp < int(request.query.end_timestamp)
        )
    # Build query
    query = (
        sa.select(columns)
        .select_from(MEAS)
        .where(sa.and_(*conditions))
        .order_by(MEAS.c.measurement_timestamp.asc())
        .offset(request.query.skip)
        .limit(request.query.limit)
    )
    # Execute query and return results
    # TODO Think about streaming here
    result = await database_client.fetch_all(query=query)
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
            path="/sensors",
            endpoint=get_sensors,
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
