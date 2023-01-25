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


@validation.validate(schema=validation.ReadStatusRequest)
async def read_status(request):
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
    async with database_client.transaction():
        try:
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
        except asyncpg.exceptions.UniqueViolationError:
            logger.warning(
                f"{request.method} {request.url.path} -- User already exists"
            )
            raise errors.ConflictError()
        except Exception as e:
            logger.error(
                f"{request.method} {request.url.path} -- Unknown error: {repr(e)}"
            )
            raise errors.InternalServerError()
        try:
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
        except Exception as e:
            logger.error(
                f"{request.method} {request.url.path} -- Unknown error: {repr(e)}"
            )
            raise errors.InternalServerError()
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=201,
        content={"access_token": access_token, "user_identifier": user_identifier},
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


@validation.validate(schema=validation.CreateSensorRequest)
async def create_sensor(request):
    """Create a new sensor and configuration."""
    user_identifier, permissions = await auth.authenticate(request, database_client)
    if request.body.network_identifier not in permissions:
        # TODO if user is read-only, return 403 -> "Insufficient authorization"
        logger.warning(f"{request.method} {request.url.path} -- Missing authorization")
        raise errors.NotFoundError()
    async with database_client.transaction():
        try:
            # Create new sensor
            query, arguments = database.build(
                template="create-sensor.sql",
                template_arguments={},
                query_arguments={
                    "sensor_name": request.body.sensor_name,
                    "network_identifier": request.body.network_identifier,
                },
            )
            result = await database_client.fetch(query, *arguments)
            sensor_identifier = database.dictify(result)[0]["sensor_identifier"]
        except asyncpg.ForeignKeyViolationError:
            logger.warning(f"{request.method} {request.url.path} -- Network not found")
            raise errors.NotFoundError()
        except asyncpg.exceptions.UniqueViolationError:
            logger.warning(f"{request.method} {request.url.path} -- Sensor exists")
            raise errors.ConflictError()
        except Exception as e:
            logger.error(
                f"{request.method} {request.url.path} -- Unknown error: {repr(e)}"
            )
            raise errors.InternalServerError()
        try:
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
        except Exception as e:
            logger.error(
                f"{request.method} {request.url.path} -- Unknown error: {repr(e)}"
            )
            raise errors.InternalServerError()
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
    user_identifier, permissions = await auth.authenticate(request, database_client)
    if request.body.network_identifier not in permissions:
        logger.warning(f"{request.method} {request.url.path} -- Missing authorization")
        raise errors.NotFoundError()
    async with database_client.transaction():
        try:
            # Update sensor
            query, arguments = database.build(
                template="update-sensor.sql",
                template_arguments={},
                query_arguments={
                    "sensor_identifier": request.path.sensor_identifier,
                    "sensor_name": request.body.sensor_name,
                },
            )
            result = await database_client.execute(query, *arguments)
        except Exception as e:
            logger.error(
                f"{request.method} {request.url.path} -- Unknown error: {repr(e)}"
            )
            raise errors.InternalServerError()
        if result != "UPDATE 1":
            logger.warning(
                f"{request.method} {request.url.path} -- Sensor doesn't exist"
            )
            raise errors.NotFoundError()
        try:
            # Create new configuration
            query, arguments = database.build(
                template="create-configuration.sql",
                template_arguments={},
                query_arguments={
                    "sensor_identifier": request.path.sensor_identifier,
                    "configuration": request.body.configuration,
                },
            )
            result = await database_client.fetch(query, *arguments)
            revision = database.dictify(result)[0]["revision"]
        except Exception as e:
            logger.error(
                f"{request.method} {request.url.path} -- Unknown error: {repr(e)}"
            )
            raise errors.InternalServerError()
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
    try:
        query, arguments = database.build(
            template="read-measurements.sql",
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
        content=database.dictify(result)[::-1],
    )


@validation.validate(schema=validation.ReadLogsAggregatesRequest)
async def read_log_message_aggregates(request):
    """Return aggregation of sensor log messages."""
    try:
        query, arguments = database.build(
            template="aggregate-logs.sql",
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


@validation.validate(schema=validation.StreamNetworkRequest)
async def stream_network(request):
    """Stream status of sensors in a network via Server Sent Events.

    This includes:
      - the number of measurements in 4 hour intervals over the last 28 days
    Ideas:
      - last sensor heartbeats
      - last measurement timestamps

    TODO offer choice between different time periods -> adapt interval accordingly (or
         better: let the frontend choose)
    TODO switch to simple HTTP GET requests with polling if we're not pushing
         based on events
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
            result = await database_client.fetch(query, *arguments)
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


database_client = None
mqtt_client = None


@contextlib.asynccontextmanager
async def lifespan(app):
    """Manage lifetime of database client and MQTT client."""
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
)
