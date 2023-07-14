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
import app.validation as validation
from app.logs import logger


@validation.validate(schema=validation.ReadStatusRequest)
async def read_status(request):
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
    password_hash = auth.hash_password(request.body.password)
    access_token = auth.generate_token()
    access_token_hash = auth.hash_token(access_token)
    async with dbpool.acquire() as connection:
        async with connection.transaction():
            # Create new user
            query, arguments = database.parametrize(
                identifier="create-user",
                arguments={
                    "user_name": request.body.user_name,
                    "password_hash": password_hash,
                },
            )
            try:
                elements = await connection.fetch(query, *arguments)
            except asyncpg.exceptions.UniqueViolationError:
                logger.warning(
                    f"{request.method} {request.url.path} -- Uniqueness violation"
                )
                raise errors.ConflictError()
            except Exception as e:  # pragma: no cover
                logger.error(e, exc_info=True)
                raise errors.InternalServerError()
            user_identifier = database.dictify(elements)[0]["user_identifier"]
            # Create new session
            query, arguments = database.parametrize(
                identifier="create-session",
                arguments={
                    "access_token_hash": access_token_hash,
                    "user_identifier": user_identifier,
                },
            )
            try:
                await connection.execute(query, *arguments)
            except Exception as e:  # pragma: no cover
                logger.error(e, exc_info=True)
                raise errors.InternalServerError()
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=201,
        content={"user_identifier": user_identifier, "access_token": access_token},
    )


@validation.validate(schema=validation.CreateSessionRequest)
async def create_session(request):
    # Read the user
    query, arguments = database.parametrize(
        identifier="read-user", arguments={"user_name": request.body.user_name}
    )
    try:
        elements = await dbpool.fetch(query, *arguments)
    except Exception as e:  # pragma: no cover
        logger.error(e, exc_info=True)
        raise errors.InternalServerError()
    elements = database.dictify(elements)
    if len(elements) == 0:
        logger.warning(f"{request.method} {request.url.path} -- User not found")
        raise errors.NotFoundError()
    user_identifier = elements[0]["user_identifier"]
    password_hash = elements[0]["password_hash"]
    # Check if password hashes match
    if not auth.verify_password(request.body.password, password_hash):
        logger.warning(f"{request.method} {request.url.path} -- Invalid password")
        raise errors.UnauthorizedError()
    access_token = auth.generate_token()
    # Create new session
    query, arguments = database.parametrize(
        identifier="create-session",
        arguments={
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
        status_code=201,
        content={"user_identifier": user_identifier, "access_token": access_token},
    )


@validation.validate(schema=validation.StreamNetworkRequest)
async def read_network(request):
    """Read information about the network and its sensors.

    This includes:
      - the identifiers of the sensors in the network
      - per sensor the number of measurements in 4 hour intervals over the last 28 days
    Ideas:
      - metadata about the network
        - name
        - how many sensors are online
        - description?
      - move aggregation to request per sensor instead of per network
        - last sensor heartbeats
        - last measurement timestamps

    TODO offer choice between different time periods -> adapt interval accordingly (or
         better: let the frontend choose from a list of predefined intervals)
    TODO use JSON array instead of nested lists, with naming of values
         [{timestamp: 123, value1: 456, value2: 252}, ...] instead of [[123, 456], ...]
    """

    query, arguments = database.parametrize(
        identifier="aggregate-network",
        arguments={"network_identifier": request.path.network_identifier},
    )
    try:
        elements = await dbpool.fetch(query, *arguments)
    except Exception as e:  # pragma: no cover
        logger.error(e, exc_info=True)
        raise errors.InternalServerError()
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=200,
        content=database.dictify(elements),
    )


@validation.validate(schema=validation.CreateSensorRequest)
async def create_sensor(request):
    user_identifier, permissions = await auth.authenticate(request, dbpool)
    if request.path.network_identifier not in permissions:
        # TODO if user is read-only, return 403 -> "Insufficient authorization"
        logger.warning(f"{request.method} {request.url.path} -- Missing authorization")
        raise errors.NotFoundError()
    query, arguments = database.parametrize(
        identifier="create-sensor",
        arguments={
            "network_identifier": request.path.network_identifier,
            "sensor_name": request.body.sensor_name,
        },
    )
    try:
        elements = await dbpool.fetch(query, *arguments)
    except asyncpg.ForeignKeyViolationError:
        # This can happen if the network is deleted after the permissions check
        logger.warning(f"{request.method} {request.url.path} -- Network not found")
        raise errors.NotFoundError()
    except asyncpg.exceptions.UniqueViolationError:
        logger.warning(f"{request.method} {request.url.path} -- Uniqueness violation")
        raise errors.ConflictError()
    except Exception as e:  # pragma: no cover
        logger.error(e, exc_info=True)
        raise errors.InternalServerError()
    sensor_identifier = database.dictify(elements)[0]["sensor_identifier"]
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=201,
        content={"sensor_identifier": sensor_identifier},
    )


@validation.validate(schema=validation.UpdateSensorRequest)
async def update_sensor(request):
    user_identifier, permissions = await auth.authenticate(request, dbpool)

    # TODO need to check if sensor is part of network, otherwise this checks nothing
    # TODO move logic into own module
    if request.path.network_identifier not in permissions:
        logger.warning(f"{request.method} {request.url.path} -- Missing authorization")
        raise errors.NotFoundError()

    query, arguments = database.parametrize(
        identifier="update-sensor",
        arguments={
            "sensor_identifier": request.path.sensor_identifier,
            "sensor_name": request.body.sensor_name,
        },
    )
    try:
        response = await dbpool.execute(query, *arguments)
    except asyncpg.exceptions.UniqueViolationError:
        logger.warning(f"{request.method} {request.url.path} -- Uniqueness violation")
        raise errors.ConflictError()
    except Exception as e:  # pragma: no cover
        logger.error(e, exc_info=True)
        raise errors.InternalServerError()
    if response != "UPDATE 1":
        logger.warning(f"{request.method} {request.url.path} -- Sensor not found")
        raise errors.NotFoundError()
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=200,
        content={"sensor_identifier": request.path.sensor_identifier},
    )


@validation.validate(schema=validation.CreateConfigurationRequest)
async def create_configuration(request):
    user_identifier, permissions = await auth.authenticate(request, dbpool)

    # TODO need to check if sensor is part of network, otherwise this checks nothing
    # TODO move logic into own module
    if request.path.network_identifier not in permissions:
        logger.warning(f"{request.method} {request.url.path} -- Missing authorization")
        raise errors.NotFoundError()

    query, arguments = database.parametrize(
        identifier="create-configuration",
        arguments={
            "sensor_identifier": request.path.sensor_identifier,
            "configuration": request.body.model_dump(),
        },
    )
    try:
        elements = await dbpool.fetch(query, *arguments)
    except asyncpg.ForeignKeyViolationError:
        logger.warning(f"{request.method} {request.url.path} -- Sensor not found")
        raise errors.NotFoundError()
    except Exception as e:  # pragma: no cover
        logger.error(e, exc_info=True)
        raise errors.InternalServerError()
    revision = database.dictify(elements)[0]["revision"]
    # Send MQTT message with configuration
    await mqtt.publish_configuration(
        sensor_identifier=request.path.sensor_identifier,
        revision=revision,
        configuration=request.body.model_dump(),
        mqttc=mqttc,
        dbpool=dbpool,
    )
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=201,
        content={"revision": revision},
    )


@validation.validate(schema=validation.ReadConfigurationsRequest)
async def read_configurations(request):
    query, arguments = database.parametrize(
        identifier="read-configurations",
        arguments={
            "sensor_identifier": request.path.sensor_identifier,
            "revision": request.query.revision,
            "direction": request.query.direction,
        },
    )
    try:
        elements = await dbpool.fetch(query, *arguments)
    except Exception as e:  # pragma: no cover
        logger.error(e, exc_info=True)
        raise errors.InternalServerError()
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=200,
        content=database.dictify(
            elements if request.query.direction == "next" else reversed(elements)
        ),
    )


@validation.validate(schema=validation.ReadMeasurementsRequest)
async def read_measurements(request):
    query, arguments = database.parametrize(
        identifier="read-measurements",
        arguments={
            "sensor_identifier": request.path.sensor_identifier,
            "creation_timestamp": request.query.creation_timestamp,
            "direction": request.query.direction,
        },
    )
    try:
        elements = await dbpool.fetch(query, *arguments)
    except Exception as e:  # pragma: no cover
        logger.error(e, exc_info=True)
        raise errors.InternalServerError()
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=200,
        content=database.dictify(
            elements if request.query.direction == "next" else reversed(elements)
        ),
    )


@validation.validate(schema=validation.ReadLogsRequest)
async def read_logs(request):
    query, arguments = database.parametrize(
        identifier="read-logs",
        arguments={
            "sensor_identifier": request.path.sensor_identifier,
            "creation_timestamp": request.query.creation_timestamp,
            "direction": request.query.direction,
        },
    )
    try:
        elements = await dbpool.fetch(query, *arguments)
    except Exception as e:  # pragma: no cover
        logger.error(e, exc_info=True)
        raise errors.InternalServerError()
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=200,
        content=database.dictify(
            elements if request.query.direction == "next" else reversed(elements)
        ),
    )


@validation.validate(schema=validation.ReadLogsAggregatesRequest)
async def read_log_message_aggregates(request):
    query, arguments = database.parametrize(
        identifier="aggregate-logs",
        arguments={"sensor_identifier": request.path.sensor_identifier},
    )
    try:
        elements = await dbpool.fetch(query, *arguments)
    except Exception as e:  # pragma: no cover
        logger.error(e, exc_info=True)
        raise errors.InternalServerError()
    # Return successful response
    return starlette.responses.JSONResponse(
        status_code=200,
        content=database.dictify(elements),
    )


dbpool = None  # Database connection pool
mqttc = None  # MQTT client


@contextlib.asynccontextmanager
async def lifespan(app):
    """Manage the lifetime of the database client and the MQTT client."""
    global dbpool
    global mqttc
    async with database.pool() as x:
        async with mqtt.client() as y:
            # Make clients globally available
            dbpool = x
            mqttc = y
            # Start MQTT listener in (unawaited) asyncio task
            loop = asyncio.get_event_loop()
            task = loop.create_task(mqtt.listen(mqttc, dbpool))

            # TODO Spawn tasks for configurations that have not yet been sent

            yield
            task.cancel()
            # Wait for the MQTT listener task to be cancelled
            try:
                await task
            except asyncio.CancelledError:
                pass


ROUTES = [
    # fmt: off
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
        path="/networks/{network_identifier}",
        endpoint=read_network,
        methods=["GET"],
    ),
    starlette.routing.Route(
        path="/networks/{network_identifier}/sensors",
        endpoint=create_sensor,
        methods=["POST"],
    ),
    starlette.routing.Route(
        path="/networks/{network_identifier}/sensors/{sensor_identifier}",
        endpoint=update_sensor,
        methods=["PUT"],
    ),
    starlette.routing.Route(
        path="/networks/{network_identifier}/sensors/{sensor_identifier}/configurations",
        endpoint=create_configuration,
        methods=["POST"],
    ),
    starlette.routing.Route(
        path="/networks/{network_identifier}/sensors/{sensor_identifier}/configurations",
        endpoint=read_configurations,
        methods=["GET"],
    ),
    starlette.routing.Route(
        path="/networks/{network_identifier}/sensors/{sensor_identifier}/measurements",
        endpoint=read_measurements,
        methods=["GET"],
    ),
    starlette.routing.Route(
        path="/networks/{network_identifier}/sensors/{sensor_identifier}/logs",
        endpoint=read_logs,
        methods=["GET"],
    ),
    starlette.routing.Route(
        path="/networks/{network_identifier}/sensors/{sensor_identifier}/logs/aggregates",
        endpoint=read_log_message_aggregates,
        methods=["GET"],
    ),
    # fmt: on
]


app = starlette.applications.Starlette(
    routes=ROUTES,
    lifespan=lifespan,
    middleware=[
        starlette.middleware.Middleware(
            starlette.middleware.cors.CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ],
)
