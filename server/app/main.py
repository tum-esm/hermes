import asyncio
import contextlib

import asyncpg
import starlette.applications
import starlette.responses
import starlette.routing

import app.auth as auth
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


@validation.validate(schema=validation.CreateUserRequest)
async def create_user(request):
    """Create a new user from the given account data."""
    password_hash = auth.hash_password(request.body.password)
    access_token = auth.generate_token()
    access_token_hash = auth.hash_token(access_token)
    try:
        async with database_client.transaction():
            # Create new user
            query, arguments = database.build(
                template="create-user.sql",
                template_arguments={},
                query_arguments={
                    "username": request.body.username,
                    "password_hash": password_hash,
                },
            )
            result = await database_client.fetch(query, *arguments)
            user_identifier = database.dictify(result)[0]["user_identifier"]
            # Create new session
            query, arguments = database.build(
                template="create-session.sql",
                template_arguments={},
                query_arguments={
                    "access_token_hash": access_token_hash,
                    "user_identifier": user_identifier,
                },
            )
            await database_client.execute(query, *arguments)
    except asyncpg.exceptions.UniqueViolationError:
        logger.warning(f"{request.method} {request.url.path} -- User already exists")
        raise errors.ConflictError()
    except Exception as e:
        logger.error(f"{request.method} {request.url.path} -- Unknown error: {repr(e)}")
        raise errors.InternalServerError()
    return starlette.responses.JSONResponse(
        status_code=201,
        content={"access_token": access_token, "user_identifier": user_identifier},
    )


@validation.validate(schema=validation.PostSensorsRequest)
async def post_sensors(request):
    """Create a new sensor and configuration."""
    user_identifier = await auth.authenticate(request, database_client)
    try:
        async with database_client.transaction():
            # Create new sensor
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
        logger.warning(f"{request.method} {request.url.path} -- Sensor already exists")
        raise errors.ConflictError()
    except Exception as e:
        logger.error(f"{request.method} {request.url.path} -- Unknown error: {repr(e)}")
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
        logger.warning(f"{request.method} {request.url.path} -- Sensor doesn't exist")
        raise errors.NotFoundError()
    except Exception as e:
        logger.error(f"{request.method} {request.url.path} -- Unknown error: {repr(e)}")
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
        logger.error(f"{request.method} {request.url.path} -- Unknown error: {repr(e)}")
        raise errors.InternalServerError()
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=200,
        content=database.dictify(result),
    )


@validation.validate(schema=validation.GetLogMessagesAggregationRequest)
async def get_log_messages_aggregation(request):
    """Return aggregation of sensor log messages."""
    try:
        query, arguments = database.build(
            template="aggregate-log-messages.sql",
            template_arguments={},
            query_arguments={"sensor_identifier": request.path.sensor_identifier},
        )
        result = await database_client.fetch(query, *arguments)
    except Exception as e:
        logger.error(f"{request.method} {request.url.path} -- Unknown error: {repr(e)}")
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


@validation.validate(schema=validation.CreateSessionRequest)
async def create_session(request):
    """Authenticate a user from username and password and return access token."""
    try:
        # Read user
        query, arguments = database.build(
            template="read-user.sql",
            template_arguments={},
            query_arguments={"username": request.body.username},
        )
        result = await database_client.fetch(query, *arguments)
        user_identifier = database.dictify(result)[0]["user_identifier"]
        password_hash = database.dictify(result)[0]["password_hash"]
    except IndexError:
        logger.warning(f"{request.method} {request.url.path} -- User not found")
        raise errors.NotFoundError()
    except Exception as e:
        logger.error(f"{request.method} {request.url.path} -- Unknown error: {repr(e)}")
        raise errors.InternalServerError()
    # Check if password hashes match
    if not auth.verify_password(request.body.password, password_hash):
        logger.warning(f"{request.method} {request.url.path} -- Invalid password")
        raise errors.UnauthorizedError()
    access_token = auth.generate_token()
    try:
        # Create new session
        query, arguments = database.build(
            template="create-session.sql",
            template_arguments={},
            query_arguments={
                "access_token_hash": auth.hash_token(access_token),
                "user_identifier": user_identifier,
            },
        )
        await database_client.execute(query, *arguments)
    except Exception as e:
        logger.error(f"{request.method} {request.url.path} -- Unknown error: {repr(e)}")
        raise errors.InternalServerError()
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=200,
        content={"access_token": access_token, "user_identifier": user_identifier},
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
        async with mqtt.Client(database_client=x) as y:
            # Make clients globally available
            database_client = x
            mqtt_client = y
            # Start MQTT listener in (unawaited) asyncio task
            loop = asyncio.get_event_loop()
            task = loop.create_task(mqtt_client.listen())

            # TODO Spawn tasks for configurations that have not yet been sent

            yield
            task.cancel()
            # Wait for the MQTT listener task to be cancelled
            try:
                await task
            except asyncio.CancelledError:
                pass


app = starlette.applications.Starlette(
    routes=[
        starlette.routing.Route(
            path="/status",
            endpoint=get_status,
            methods=["GET"],
        ),
        starlette.routing.Route(
            path="/users",
            endpoint=create_user,
            methods=["POST"],
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
            path="/sensors/{sensor_identifier}/log-messages/aggregation",
            endpoint=get_log_messages_aggregation,
            methods=["GET"],
        ),
        starlette.routing.Route(
            path="/streams/sensors",
            endpoint=stream_sensors,
            methods=["GET"],
        ),
        starlette.routing.Route(
            path="/authentication",
            endpoint=create_session,
            methods=["POST"],
        ),
    ],
    lifespan=lifespan,
)
