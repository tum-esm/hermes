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
import app.sse as sse
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
            query, arguments = database.build(
                template="create-sensor.sql",
                template_arguments={},
                query_arguments={"sensor_name": request.body.sensor_name},
            )
            result = await database_client.fetch(query, *arguments)
            sensor_identifier = database.dictify(result)[0]["sensor_identifier"]
            # Create new configuration
            query, arguments = database.build(
                template="create-configuration.sql",
                template_arguments={},
                query_arguments={
                    "sensor_identifier": sensor_identifier,
                    "configuration": request.body.configuration,
                },
            )
            result = await database_client.fetch(query, *arguments)
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
            query, arguments = database.build(
                template="update-sensor.sql",
                template_arguments={},
                query_arguments={
                    "sensor_name": request.path.sensor_name,
                    "new_sensor_name": request.body.sensor_name,
                },
            )
            result = await database_client.fetch(query, *arguments)
            sensor_identifier = database.dictify(result)[0]["sensor_identifier"]
            # Create new configuration
            query, arguments = database.build(
                template="create-configuration.sql",
                template_arguments={},
                query_arguments={
                    "sensor_identifier": sensor_identifier,
                    "configuration": request.body.configuration,
                },
            )
            result = await database_client.fetch(query, *arguments)
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


async def get_sensors(request):
    """Return configurations of selected sensors."""
    raise errors.NotImplementedError()


@validation.validate(schema=validation.GetMeasurementsRequest)
async def get_measurements(request):
    """Return pages of measurements sorted descending by creation timestamp.

    - maybe we can choose based on some header, if we page or export the data
    - for export, we can also offer start/end timestamps parameters
    - we should also be able to choose multiple sensors to return the data for
    -> it's probably best to have a separate endpoint for export

    - use status code 206 for partial content?
    """
    try:
        query, arguments = database.build(
            template="fetch-measurements.sql",
            template_arguments={},
            query_arguments={
                "sensor_identifier": request.path.sensor_identifier,
                "direction": request.query.direction,
                "creation_timestamp": request.query.creation_timestamp,
            },
        )
        result = await database_client.fetch(query, *arguments)
    except Exception as e:
        logger.error(f"[GET /measurements] Unknown error: {repr(e)}")
        raise errors.InternalServerError()
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=200,
        content=database.dictify(result),
    )


@validation.validate(schema=validation.GetLogMessagesAggregatesRequest)
async def get_log_messages_aggregates(request):
    """Return aggregation of sensor log messages."""
    try:
        query, arguments = database.build(
            template="aggregate-log-messages.sql",
            template_arguments={},
            query_arguments={"sensor_identifier": request.path.sensor_identifier},
        )
        result = await database_client.fetch(query, *arguments)
    except Exception as e:
        logger.error(f"[GET /log-messages] Unknown error: {repr(e)}")
        raise errors.InternalServerError()
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=200,
        content=database.dictify(result),
    )


@validation.validate(schema=validation.StreamSensorsRequest)
async def stream_sensors(request):
    """Stream aggregated information about sensors via Server Sent Events.

    This includes:
      - the number of measurements in 4 hour intervals over the last 28 days
    Ideas:
      - last sensor heartbeats
      - last measurement timestamps

    TODO choose sensors to stream based on user name and authorization
    """

    # first version: just return new aggregation in fixed interval
    # improvements:
    # - use a cache (redis?) to store the last aggregation?
    # - then we can return the cached value immediately and update the cache when a new
    #   measurement comes in
    # - or better: re-aggregate fixed interval, but only if there are new measurements

    async def stream(request):
        while True:
            query, arguments = database.build(
                template="aggregate-sensors.sql",
                template_arguments={},
                query_arguments={
                    "sensor_names": request.query.sensor_names,
                },
            )
            result = await database_client.fetch(query, *arguments)
            # TODO handle exceptions
            yield sse.ServerSentEvent(data=database.dictify(result)).encode()
            await asyncio.sleep(5)

    return starlette.responses.StreamingResponse(
        content=stream(request),
        status_code=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
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
        async with mqtt.Client(x) as y:
            # Make clients globally available
            database_client = x
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
            path="/sensors/{sensor_identifier}/measurements",
            endpoint=get_measurements,
            methods=["GET"],
        ),
        starlette.routing.Route(
            path="/sensors/{sensor_identifier}/log-messages/aggregates",
            endpoint=get_log_messages_aggregates,
            methods=["GET"],
        ),
        starlette.routing.Route(
            path="/streams/sensors",
            endpoint=stream_sensors,
            methods=["GET"],
        ),
    ],
    lifespan=lifespan,
)
