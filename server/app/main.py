import asyncio
import asyncpg
import contextlib
import itertools
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


import random


def get_data(stream_identifier: int, event_identifier: int) -> int:
    r = random.Random()
    r.seed(stream_identifier * event_identifier)
    return r.randrange(1000)


async def sse_generator(request):
    identifier = 0  # request.path_params["id"]
    for i in itertools.count():
        data = get_data(identifier, i)
        data = b"id: %d\ndata: %d\n\n" % (i, data)
        yield data
        await asyncio.sleep(1)


async def stream(request):
    """SSE test."""
    return starlette.responses.StreamingResponse(
        content=sse_generator(request),
        status_code=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@validation.validate(schema=validation.PostSensorsRequest)
async def post_sensors(request):
    """Create a new sensor and configuration."""
    try:
        async with database_client.transaction():
            # Insert sensor
            query, arguments = database.build(
                template="insert-sensor.sql",
                template_arguments={},
                query_arguments={"sensor_name": request.body.sensor_name},
            )
            result = await database_client.fetch(query, *arguments)
            sensor_identifier = database.dictify(result)[0]["sensor_identifier"]
            # Insert configuration
            query, arguments = database.build(
                template="insert-configuration.sql",
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
            # Insert configuration
            query, arguments = database.build(
                template="insert-configuration.sql",
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
    # - last sensor heartbeat
    # - aggregation of sensor statuses
    # - paging of
    #   - sensor statuses
    #   - sensor configurations
    #   - sensor measurements

    try:
        query, arguments = database.build(
            template="aggregate-sensor-information.sql",
            template_arguments={"request": request},
            query_arguments={
                "sensor_names": request.query.sensors,
                # TODO make this a query param; validate with `try: pendulum.timezone()`
                #
                # It's probably better to do everything in UTC and convert to the
                # user's offset on the frontend.
                #
                # This makes it easier to pre-compute and/or cache the results. The
                # only downside is that we cannot show aggregates over the time zone,
                # but only over offsets, because for a specific offset, time periods
                # will actually always span the same number of seconds, which is not
                # the case for time zones. What we also cannot do is aggregate over
                # periods like days, months, or years, because we cannot adapt them
                # from UTC to the user's time zone on the frontend
                "timezone": "Europe/Berlin",
            },
        )
        result = await database_client.fetch(query, *arguments)
    except Exception as e:
        logger.error(f"[GET /sensors] Unknown error: {repr(e)}")
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
        query, arguments = database.build(
            template="fetch-measurements.sql",
            template_arguments={"request": request},
            query_arguments={
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
        result = await database_client.fetch(query, *arguments)
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
            path="/stream",
            endpoint=stream,
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
