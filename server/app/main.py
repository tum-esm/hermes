import asyncio
import contextlib

import asyncpg
import starlette.applications
import starlette.responses
import starlette.routing

import app.database as database
import app.errors as errors
import app.mqtt as mqtt
import app.settings as settings
import app.validation as validation
from app.logs import logger


async def get_status(request):
    """Return some status information about the server."""
    return starlette.responses.JSONResponse(
        status_code=200,
        content={
            "environment": settings.ENVIRONMENT,
            "commit_sha": settings.COMMIT_SHA,
            "branch_name": settings.BRANCH_NAME,
            "start_time": settings.START_TIME,
        },
    )


@validation.validate(schema=validation.PostSensorsRequest)
async def post_sensors(request):
    """Create a new sensor and configuration."""
    try:
        async with database_client.transaction():
            # Insert sensor
            query, parameters = database.build(
                template="insert-sensor.sql",
                template_parameters={},
                query_parameters={"sensor_name": request.body.sensor_name},
            )
            result = await database_client.fetch(query, *parameters)
            sensor_identifier = database.dictify(result)[0]["sensor_identifier"]
            # Insert configuration
            query, parameters = database.build(
                template="insert-configuration.sql",
                template_parameters={},
                query_parameters={
                    "sensor_identifier": sensor_identifier,
                    "configuration": request.body.configuration,
                },
            )
            result = await database_client.fetch(query, *parameters)
            revision = database.dictify(result)[0]["revision"]
        # Send MQTT message
        await mqtt_client.publish_configuration(
            sensor_identifier=sensor_identifier,
            revision=revision,
            configuration=request.body.configuration,
        )
    except asyncpg.exceptions.UniqueViolationError:
        logger.warning("[POST /sensors] Sensor already exists")
        raise errors.ConflictError()
    except Exception as e:
        logger.error(f"[POST /sensors] Unknown error: {repr(e)}")
        raise errors.InternalServerError()
    # Return successful response
    # TODO Return sensor_identifier and revision? Same for PUT?
    return starlette.responses.JSONResponse(status_code=201, content=None)


@validation.validate(schema=validation.PutSensorsRequest)
async def put_sensors(request):
    """Update an existing sensor's configuration."""
    try:
        async with database_client.transaction():
            # Update sensor
            query, parameters = database.build(
                template="update-sensor.sql",
                template_parameters={},
                query_parameters={
                    "sensor_name": request.path.sensor_name,
                    "new_sensor_name": request.body.sensor_name,
                },
            )
            result = await database_client.fetch(query, *parameters)
            sensor_identifier = database.dictify(result)[0]["sensor_identifier"]
            # Insert configuration
            query, parameters = database.build(
                template="insert-configuration.sql",
                template_parameters={},
                query_parameters={
                    "sensor_identifier": sensor_identifier,
                    "configuration": request.body.configuration,
                },
            )
            result = await database_client.fetch(query, *parameters)
            revision = database.dictify(result)[0]["revision"]
        # Send MQTT message
        await mqtt_client.publish_configuration(
            sensor_identifier=sensor_identifier,
            revision=revision,
            configuration=request.body.configuration,
        )
    except IndexError:
        logger.warning("[PUT /sensors] Sensor doesn't exist")
        raise errors.NotFoundError()
    except Exception as e:
        logger.error(f"[PUT /sensors] Unknown error: {repr(e)}")
        raise errors.InternalServerError()
    # Return successful response
    return starlette.responses.JSONResponse(status_code=204, content=None)


@validation.validate(schema=validation.GetSensorsRequest)
async def get_sensors(request):
    """Return status and configuration of sensors.

    The underlying database query is quite expensive, the best tactic would probably
    be to cache the results per sensor for a short time, invalidate them when a new
    measurement in received, and re-aggregate every few minutes.

    The best tactic for the frontend is probably to use websockets. This would allow
    us to send back cached results immediately and then update them as soon as new
    aggregations are available.

    To make this more performant on the database we should make sure to have the
    correct indexes in place. We should also consider using TimescaleDB.

    - Provide both: GET request and websocket?
    - fetch/cache/request aggregations/configurations/latest-measurement separately?

    """

    # TODO Enrich with
    # V last measurement timestamp
    # V activity timeline
    # - last measurement
    # - last sensor health update

    try:
        query, parameters = database.build(
            template="aggregate-sensor-information.sql",
            template_parameters={"request": request},
            query_parameters={
                "sensor_names": request.query.sensors,
                # TODO make this a query param; validate with `try: pendulum.timezone()`
                "timezone": "Europe/Berlin",
            },
        )
        result = await database_client.fetch(query, *parameters)
    except Exception as e:
        logger.error(f"[PUT /sensors] Unknown error: {repr(e)}")
        raise errors.InternalServerError()
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=200,
        content=database.dictify(result),
    )


@validation.validate(schema=validation.GetMeasurementsRequest)
async def get_measurements(request):
    """Return measurements sorted chronologically, optionally filtered."""
    try:
        query, parameters = database.build(
            template="fetch-measurements.sql",
            template_parameters={"request": request},
            query_parameters={
                "sensor_identifiers": request.query.sensors,
                "start_timestamp": request.query.start,
                "end_timestamp": request.query.end,
                "skip": request.query.skip,
                "limit": request.query.limit,
            },
        )
        # TODO limiting size and paginating is fine for now, but we should also
        # either implement streaming or some other way to export the data in different
        # formats (parquet, ...)
        result = await database_client.fetch(query, *parameters)
    except Exception as e:
        logger.error(f"[PUT /sensors] Unknown error: {repr(e)}")
        raise errors.InternalServerError()
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=200,
        content=database.dictify(result),
    )


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
    async with database.Client() as x:
        database_client = x
        # Create database tables if they don't exist yet
        await database.setup(database_client)
        async with mqtt.Client(database_client) as y:
            mqtt_client = y
            # Start MQTT listener in (unawaited) asyncio task
            loop = asyncio.get_event_loop()
            task = loop.create_task(mqtt_client.listen())

            # TODO Spawn tasks for configurations that have not yet been sent

            yield
            task.cancel()


app = starlette.applications.Starlette(
    routes=[
        starlette.routing.Route(
            path="/status",
            endpoint=get_status,
            methods=["GET"],
        ),
        starlette.routing.Route(
            path="/sensors",
            endpoint=post_sensors,
            methods=["POST"],
        ),
        starlette.routing.Route(
            path="/sensors/{sensor_name}",
            endpoint=put_sensors,
            methods=["PUT"],
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
    lifespan=lifespan,
)
