import asyncio
import contextlib

import asyncpg
import starlette.applications
import starlette.middleware
import starlette.middleware.cors
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


@validation.validate(schema=validation.ReadStatusRequest)
async def read_status(request):
    """Return some status information about the server."""
    return starlette.responses.JSONResponse(
        status_code=200,
        content={
            "environment": settings.ENVIRONMENT,
            "commit_sha": settings.COMMIT_SHA,
            "branch_name": settings.BRANCH_NAME,
            "start_timestamp": settings.START_TIMESTAMP,
        },
    )


@validation.validate(schema=validation.CreateUserRequest)
async def create_user(request):
    """Create a new user from the given account data."""
    password_hash = auth.hash_password(request.body.password)
    access_token = auth.generate_token()
    access_token_hash = auth.hash_token(access_token)
    async with dbpool.acquire() as connection:
        async with connection.transaction():
            # Create new user
            query, arguments = database.build(
                template="create-user.sql",
                template_arguments={},
                query_arguments={
                    "username": request.body.username,
                    "password_hash": password_hash,
                },
            )
            try:
                result = await connection.fetch(query, *arguments)
            except asyncpg.exceptions.UniqueViolationError:
                logger.warning(
                    f"{request.method} {request.url.path} -- User already exists"
                )
                raise errors.ConflictError()
            except Exception as e:  # pragma: no cover
                logger.error(e, exc_info=True)
                raise errors.InternalServerError()
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
            try:
                await connection.execute(query, *arguments)
            except Exception as e:
                logger.error(e, exc_info=True)
                raise errors.InternalServerError()
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=201,
        content={"access_token": access_token, "user_identifier": user_identifier},
    )


@validation.validate(schema=validation.CreateSessionRequest)
async def create_session(request):
    """Authenticate a user from username and password and return access token."""
    # Read user
    query, arguments = database.build(
        template="read-user.sql",
        template_arguments={},
        query_arguments={"username": request.body.username},
    )
    try:
        result = await dbpool.fetch(query, *arguments)
    except Exception as e:  # pragma: no cover
        logger.error(e, exc_info=True)
        raise errors.InternalServerError()
    result = database.dictify(result)
    if len(result) == 0:
        logger.warning(f"{request.method} {request.url.path} -- User not found")
        raise errors.NotFoundError()
    user_identifier = result[0]["user_identifier"]
    password_hash = result[0]["password_hash"]
    # Check if password hashes match
    if not auth.verify_password(request.body.password, password_hash):
        logger.warning(f"{request.method} {request.url.path} -- Invalid password")
        raise errors.UnauthorizedError()
    access_token = auth.generate_token()
    # Create new session
    query, arguments = database.build(
        template="create-session.sql",
        template_arguments={},
        query_arguments={
            "access_token_hash": auth.hash_token(access_token),
            "user_identifier": user_identifier,
        },
    )
    try:
        await dbpool.execute(query, *arguments)
    except Exception as e:  # pragma: no cover
        logger.error(e, exc_info=True)
        raise errors.InternalServerError()
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=200,
        content={"access_token": access_token, "user_identifier": user_identifier},
    )


@validation.validate(schema=validation.CreateSensorRequest)
async def create_sensor(request):
    """Create a new sensor and configuration."""
    user_identifier, permissions = await auth.authenticate(request, dbpool)
    if request.body.network_identifier not in permissions:
        # TODO if user is read-only, return 403 -> "Insufficient authorization"
        logger.warning(f"{request.method} {request.url.path} -- Missing authorization")
        raise errors.NotFoundError()
    async with dbpool.acquire() as connection:
        async with connection.transaction():
            # Create new sensor
            query, arguments = database.build(
                template="create-sensor.sql",
                template_arguments={},
                query_arguments={
                    "sensor_name": request.body.sensor_name,
                    "network_identifier": request.body.network_identifier,
                },
            )
            try:
                result = await connection.fetch(query, *arguments)
            except asyncpg.ForeignKeyViolationError:
                logger.warning(
                    f"{request.method} {request.url.path} -- Network not found"
                )
                raise errors.NotFoundError()
            except asyncpg.exceptions.UniqueViolationError:
                logger.warning(f"{request.method} {request.url.path} -- Sensor exists")
                raise errors.ConflictError()
            except Exception as e:  # pragma: no cover
                logger.error(e, exc_info=True)
                raise errors.InternalServerError()
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
            try:
                result = await connection.fetch(query, *arguments)
            except Exception as e:  # pragma: no cover
                logger.error(e, exc_info=True)
                raise errors.InternalServerError()
            revision = database.dictify(result)[0]["revision"]
    # Send MQTT message with configuration
    await mqtt_client.publish_configuration(
        sensor_identifier=sensor_identifier,
        revision=revision,
        configuration=request.body.configuration,
    )
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=201,
        content={"sensor_identifier": sensor_identifier, "revision": revision},
    )


@validation.validate(schema=validation.UpdateSensorRequest)
async def update_sensor(request):
    """Update an existing sensor's configuration.

    TODO split in two: update sensor and update configuration
    """
    user_identifier, permissions = await auth.authenticate(request, dbpool)

    # TODO need to check if sensor is part of network, otherwise this checks nothing
    if request.body.network_identifier not in permissions:
        logger.warning(f"{request.method} {request.url.path} -- Missing authorization")
        raise errors.NotFoundError()

    async with dbpool.acquire() as connection:
        async with connection.transaction():
            # Update sensor
            query, arguments = database.build(
                template="update-sensor.sql",
                template_arguments={},
                query_arguments={
                    "sensor_identifier": request.path.sensor_identifier,
                    "sensor_name": request.body.sensor_name,
                },
            )
            try:
                result = await connection.execute(query, *arguments)

            # TODO catch asyncpg.UniqueViolationError

            except Exception as e:  # pragma: no cover
                logger.error(e, exc_info=True)
                raise errors.InternalServerError()
            if result != "UPDATE 1":
                logger.warning(
                    f"{request.method} {request.url.path} -- Sensor doesn't exist"
                )
                raise errors.NotFoundError()
            # Create new configuration
            query, arguments = database.build(
                template="create-configuration.sql",
                template_arguments={},
                query_arguments={
                    "sensor_identifier": request.path.sensor_identifier,
                    "configuration": request.body.configuration,
                },
            )
            try:
                result = await connection.fetch(query, *arguments)
            except Exception as e:  # pragma: no cover
                logger.error(e, exc_info=True)
                raise errors.InternalServerError()
            revision = database.dictify(result)[0]["revision"]
    # Send MQTT message with configuration
    await mqtt_client.publish_configuration(
        sensor_identifier=request.path.sensor_identifier,
        revision=revision,
        configuration=request.body.configuration,
    )
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=200,
        content={
            "sensor_identifier": request.path.sensor_identifier,
            "revision": revision,
        },
    )


async def read_sensors(request):
    """Return configurations of selected sensors."""
    raise errors.NotImplementedError()


@validation.validate(schema=validation.ReadMeasurementsRequest)
async def read_measurements(request):
    """Return pages of measurements sorted ascending by creation timestamp.

    When no query parameters are given, the latest N measurements are returned. When
    direction and creation_timestamp are given, the next/previous N measurements based
    on the given timestamp are returned.

    - maybe we can choose based on some header, if we page or export the data
    - for export, we can also offer start/end timestamps parameters
    - we should also be able to choose multiple sensors to return the data for
    -> it's probably best to have a separate endpoint for export

    - use status code 206 for partial content?
    """
    query, arguments = database.build(
        template="read-measurements.sql",
        template_arguments={},
        query_arguments={
            "sensor_identifier": request.path.sensor_identifier,
            "direction": request.query.direction,
            "creation_timestamp": request.query.creation_timestamp,
        },
    )
    try:
        result = await dbpool.fetch(query, *arguments)
    except Exception as e:  # pragma: no cover
        logger.error(e, exc_info=True)
        raise errors.InternalServerError()
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=200,
        content=database.dictify(result)[::-1],
    )


@validation.validate(schema=validation.ReadLogsAggregatesRequest)
async def read_log_message_aggregates(request):
    """Return aggregation of sensor log messages."""
    query, arguments = database.build(
        template="aggregate-logs.sql",
        template_arguments={},
        query_arguments={"sensor_identifier": request.path.sensor_identifier},
    )
    try:
        result = await dbpool.fetch(query, *arguments)
    except Exception as e:  # pragma: no cover
        logger.error(e, exc_info=True)
        raise errors.InternalServerError()
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=200,
        content=database.dictify(result),
    )


@validation.validate(schema=validation.StreamNetworkRequest)
async def stream_network(request):
    """Stream status of sensors in a network via Server Sent Events.

    This includes:
      - the number of measurements in 4 hour intervals over the last 28 days
    Ideas:
      - last sensor heartbeats
      - last measurement timestamps

    TODO offer choice between different time periods -> adapt interval accordingly (or
         better: let the frontend choose from a list of predefined intervals)
    TODO switch to simple HTTP GET requests with polling if we're not pushing
         based on events
    TODO use JSON array instead of nested lists, with naming of values
         [{timestamp: 123, value1: 456, value2: 252}, ...] instead of [[123, 456], ...]
    """

    async def stream(request):
        while True:
            query, arguments = database.build(
                template="aggregate-network.sql",
                template_arguments={},
                query_arguments={
                    "network_identifier": request.path.network_identifier,
                },
            )
            result = await dbpool.fetch(query, *arguments)
            # TODO handle exceptions
            yield sse.ServerSentEvent(data=database.dictify(result)).encode()
            await asyncio.sleep(10)

    # Return successful response
    return starlette.responses.StreamingResponse(
        content=stream(request),
        status_code=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


dbpool = None  # Database connection pool
mqtt_client = None


@contextlib.asynccontextmanager
async def lifespan(app):
    """Manage lifetime of database client and MQTT client."""
    global dbpool
    global mqtt_client
    async with database.pool() as x:
        async with mqtt.Client(dbpool=x) as y:
            # Make clients globally available
            dbpool = x
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


middleware = [
    starlette.middleware.Middleware(
        starlette.middleware.cors.CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]


app = starlette.applications.Starlette(
    routes=[
        starlette.routing.Route(
            path="/status",
            endpoint=read_status,
            methods=["GET"],
        ),
        starlette.routing.Route(
            path="/users",
            endpoint=create_user,
            methods=["POST"],
        ),
        starlette.routing.Route(
            path="/authentication",
            endpoint=create_session,
            methods=["POST"],
        ),
        starlette.routing.Route(
            path="/sensors",
            endpoint=create_sensor,
            methods=["POST"],
        ),
        starlette.routing.Route(
            path="/sensors/{sensor_identifier}",
            endpoint=update_sensor,
            methods=["PUT"],
        ),
        starlette.routing.Route(
            path="/sensors",
            endpoint=read_sensors,
            methods=["GET"],
        ),
        starlette.routing.Route(
            path="/sensors/{sensor_identifier}/measurements",
            endpoint=read_measurements,
            methods=["GET"],
        ),
        starlette.routing.Route(
            path="/sensors/{sensor_identifier}/logs/aggregates",
            endpoint=read_log_message_aggregates,
            methods=["GET"],
        ),
        starlette.routing.Route(
            path="/streams/{network_identifier}",
            endpoint=stream_network,
            methods=["GET"],
        ),
    ],
    lifespan=lifespan,
    middleware=middleware,
)
