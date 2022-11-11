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
import app.utils as utils
import app.validation as validation
from app.logs import logger


async def get_status(request):
    """Return some status information about the server."""

    # Send a test mqtt message
    import random

    payload = {
        "sensor_identifier": "kabuto",
        "timestamp": utils.timestamp(),
        "measurement": {"value": random.randint(0, 2**10)},
    }
    await mqtt.send(payload, "measurements", mqtt_client)

    # Return successful response
    return starlette.responses.JSONResponse(
        {
            "commit_sha": settings.COMMIT_SHA,
            "branch_name": settings.BRANCH_NAME,
            "start_time": settings.START_TIME,
        }
    )


async def post_sensors(request):
    """Create a new sensor."""
    request = await validation.validate(request, validation.PostSensorsRequest)

    timestamp = utils.timestamp()

    # Parameterize database query
    query, parameters = database.build(
        template="insert_configuration.sql",
        template_parameters={},
        query_parameters={
            "sensor_identifier": request.body.sensor_identifier,
            "creation_timestamp": timestamp,
            "update_timestamp": timestamp,
            "configuration": request.body.configuration,
        },
    )
    try:
        # Execute database query
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
    # Return successful response
    return starlette.responses.JSONResponse(status_code=201, content={})


async def get_sensors(request):
    """Return status and configuration of sensors."""
    request = await validation.validate(request, validation.GetSensorsRequest)

    # TODO Enrich with
    # V last measurement timestamp
    # - activity timeline
    # - last measurement
    # - last sensor health update

    timestamp = utils.timestamp()
    window = 24 * 60 * 60  # We aggregate over 24 hour buckets

    # TODO buckets begin at UTC midnight -> maybe simply use last 24 hours?
    # oder stuendlich aggregieren und dann auf dem frontend an die timezone anpassen
    # oder bei request einfach die timezone mitgeben
    # Also: interpolate partial days?

    timestamps = list(range((timestamp // window - 27) * window, timestamp, window))

    # TODO remove
    timestamps[0] = 0

    # Parameterize database query
    query, parameters = database.build(
        template="fetch_sensors.sql",
        template_parameters={"request": request},
        query_parameters={
            "sensor_identifiers": request.query.sensors,
            "start_timestamp": timestamps[0],
            "window": window,
        },
    )
    # Execute database query
    result = await database_client.fetch(query, *parameters)
    # Return successful response
    return starlette.responses.JSONResponse(database.dictify(result))


async def get_measurements(request):
    """Return measurements sorted chronologically, optionally filtered."""
    request = await validation.validate(request, validation.GetMeasurementsRequest)

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
    async with database.Client(**database.CONFIGURATION) as x:
        async with aiomqtt.Client(**mqtt.CONFIGURATION) as y:
            database_client = x
            mqtt_client = y
            # Create database tables if they don't exist yet
            await database.initialize(database_client)
            # Start MQTT listener in (unawaited) asyncio task
            loop = asyncio.get_event_loop()
            loop.create_task(mqtt.listen(database_client, mqtt_client))
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
    # TODO Limit to one MQTT instance for multiple workers, or use shared subscriptions
    lifespan=lifespan,
)
