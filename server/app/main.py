import asyncio
import contextlib

import asyncio_mqtt as aiomqtt
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
        {
            "environment": settings.ENVIRONMENT,
            "commit_sha": settings.COMMIT_SHA,
            "branch_name": settings.BRANCH_NAME,
            "start_time": settings.START_TIME,
        }
    )


@validation.validate(schema=validation.PostSensorsRequest)
async def post_sensors(request):
    """Create a new sensor and configuration."""
    try:
        async with database_client.transaction():
            # Insert sensor
            query, parameters = database.build(
                template="insert_sensor.sql",
                template_parameters={},
                query_parameters={"sensor_identifier": request.body.sensor_identifier},
            )
            await database_client.execute(query, *parameters)
            # Insert configuration
            query, parameters = database.build(
                template="insert_configuration.sql",
                template_parameters={},
                query_parameters={
                    "sensor_identifier": request.body.sensor_identifier,
                    "configuration": request.body.configuration,
                },
            )
            await database_client.execute(query, *parameters)
        # Send MQTT message
        # TODO implement acknowledgement and retry logic to avoid corrupted state
        await mqtt.publish(
            mqtt_client=mqtt_client,
            payload=request.body.configuration,
            topic=f"configurations/{request.body.sensor_identifier}",
            qos=1,
            retain=True,
        )
    except asyncpg.exceptions.UniqueViolationError:
        logger.warning("[POST /sensors] Configuration already exists")
        raise errors.ResourceExistsError()
    except aiomqtt.MqttError:
        logger.error("[POST /sensors] MQTT message could not be published")
        raise errors.InternalServerError()
    except Exception:
        logger.error("[POST /sensors] Unknown error")
        raise errors.InternalServerError()
    # Return successful response
    return starlette.responses.JSONResponse(status_code=201, content={})


@validation.validate(schema=validation.GetSensorsRequest)
async def get_sensors(request):
    """Return status and configuration of sensors."""

    # TODO Enrich with
    # V last measurement timestamp
    # V activity timeline
    # - last measurement
    # - last sensor health update

    # Parameterize database query
    query, parameters = database.build(
        template="fetch_sensors.sql",
        template_parameters={"request": request},
        query_parameters={
            "sensor_identifiers": request.query.sensors,
            # TODO make this a query parameter; validate with `try: pendulum.timezone()`
            "timezone": "Europe/Berlin",
        },
    )
    # Execute database query
    result = await database_client.fetch(query, *parameters)
    # Return successful response
    return starlette.responses.JSONResponse(database.dictify(result))


@validation.validate(schema=validation.GetMeasurementsRequest)
async def get_measurements(request):
    """Return measurements sorted chronologically, optionally filtered."""

    # Parameterize database query
    query, parameters = database.build(
        template="fetch_measurements.sql",
        template_parameters={"request": request},
        query_parameters={
            "sensor_identifiers": request.query.sensors,
            "start_timestamp": request.query.start,
            "end_timestamp": request.query.end,
            "skip": request.query.skip,
            "limit": request.query.limit,
        },
    )
    # Execute database query
    # TODO limiting size and paginating is fine for now, but we should also
    # either implement streaming or some other way to export the data in different
    # formats
    result = await database_client.fetch(query, *parameters)
    # Return successful response
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
    async with database.Client() as x:
        database_client = x
        # Create database tables if they don't exist yet
        await database.setup(database_client)
        async with mqtt.Client(database_client) as y:
            mqtt_client = y
            # Start MQTT listener in (unawaited) asyncio task
            loop = asyncio.get_event_loop()
            loop.create_task(mqtt_client.listen())
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
            endpoint=post_sensors,
            methods=["POST"],
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
    # TODO Use shared subscriptions for multiple workers
    lifespan=lifespan,
)
