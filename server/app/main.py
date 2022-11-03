import asyncio
import contextlib

import asyncio_mqtt as aiomqtt
import databases
import sqlalchemy as sa
from sqlalchemy.sql import func
import starlette.applications
import starlette.responses
import starlette.routing

import app.database as database
import app.errors as errors
import app.mqtt as mqtt
import app.settings as settings
import app.utils as utils
import app.validation as validation
from app.database import CONFIGURATIONS, MEASUREMENTS
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

    # Define filters
    conditions = []
    conditions = database.filter_sensor_identifier(conditions, request)
    # Build query
    latest_measurements = (
        sa.select(MEASUREMENTS.c)
        .select_from(MEASUREMENTS)
        .order_by(
            MEASUREMENTS.c.sensor_identifier.asc(),
            MEASUREMENTS.c.measurement_timestamp.desc(),
        )
        .distinct(MEASUREMENTS.c.sensor_identifier)
    )

    timestamp = utils.timestamp()
    window = 24 * 60 * 60  # We aggregate over 24 hour buckets

    # TODO buckets begin at UTC midnight -> maybe simply use last 24 hours?
    # oder stuendlich aggregieren und dann auf dem frontend an die timezone anpassen
    # oder bei request einfach die timezone mitgeben

    timestamps = list(range((timestamp // window - 27) * window, timestamp, window))

    # TODO remove
    timestamps[0] = 0

    querygg = """
        WITH latest_measurements AS (
            SELECT DISTINCT ON (sensor_identifier) *
            FROM measurements
            ORDER BY sensor_identifier ASC, measurement_timestamp DESC
        ),
        rounded_timestamps AS (
            SELECT
                sensor_identifier,
                DIV(measurement_timestamp, :window)::INTEGER AS bucket
            FROM measurements
            WHERE measurement_timestamp >= :start
        ),
        buckets AS (
            SELECT sensor_identifier, bucket, COUNT(*) AS count
            FROM rounded_timestamps
            GROUP BY sensor_identifier, bucket
            ORDER BY bucket ASC
        ),
        buckets_wd AS (
            SELECT sensor_identifier, bucket, COALESCE(count, 0) AS count
            FROM
                UNNEST(ARRAY[0,1,2,3]) bucket
                CROSS JOIN (SELECT sensor_identifier FROM buckets GROUP BY sensor_identifier) sensors
                LEFT OUTER JOIN buckets USING (sensor_identifier, bucket)
        ),
        activity AS (
            SELECT
                buckets_wd.sensor_identifier,
                ARRAY_AGG(buckets_wd.bucket) AS buckets,
                ARRAY_AGG(buckets_wd.count) AS counts
            FROM buckets_wd
            GROUP BY buckets_wd.sensor_identifier
        )
        SELECT
            configurations.sensor_identifier,
            configurations.creation_timestamp,
            configurations.update_timestamp,
            configurations.configuration,
            latest_measurements.measurement_timestamp,
            activity.buckets,
            activity.counts
        FROM
            configurations
            LEFT OUTER JOIN latest_measurements USING (sensor_identifier)
            JOIN activity USING (sensor_identifier)
        --WHERE TODO
        ORDER BY configurations.sensor_identifier ASC
    """

    rounded_timestamps = (
        sa.select(
            MEASUREMENTS.c.sensor_identifier,
            sa.cast(
                func.div(MEASUREMENTS.c.receipt_timestamp, window),
                sa.Integer,
            ).label("bucket"),
        )
        .select_from(MEASUREMENTS)
        .where(MEASUREMENTS.c.receipt_timestamp >= timestamps[0])
    )
    buckets = (
        sa.select(
            rounded_timestamps.c.sensor_identifier,
            rounded_timestamps.c.bucket,
            func.count(rounded_timestamps.c.sensor_identifier).label("count"),
        )
        .select_from(rounded_timestamps)
        .group_by(rounded_timestamps.c.sensor_identifier, rounded_timestamps.c.bucket)
        .order_by(rounded_timestamps.c.bucket.asc())
    )

    activity = (
        sa.select(
            buckets.c.sensor_identifier,
            func.array_agg(buckets.c.bucket).label("buckets"),
            func.array_agg(buckets.c.count).label("counts"),
        )
        .select_from(buckets)
        .group_by(buckets.c.sensor_identifier)
    )
    query = (
        sa.select(
            *CONFIGURATIONS.c,
            latest_measurements.c.measurement_timestamp,
            activity.c.buckets,
            activity.c.counts,
        )
        .select_from(
            CONFIGURATIONS.join(
                latest_measurements,
                CONFIGURATIONS.c.sensor_identifier
                == latest_measurements.c.sensor_identifier,
                isouter=True,
            ).join(
                activity,
                CONFIGURATIONS.c.sensor_identifier == activity.c.sensor_identifier,
                isouter=True,
            )
        )
        .where(sa.and_(*conditions))
        .order_by(CONFIGURATIONS.c.sensor_identifier.asc())
    )

    # Execute query and return results
    result = await database_client.fetch_all(
        query=querygg,
        values={"window": window, "start": timestamps[0]},
    )
    return starlette.responses.JSONResponse(database.dictify(result))


async def get_measurements(request):
    """Return measurements sorted chronologically, optionally filtered."""
    request = await validation.validate(request, validation.GetMeasurementsRequest)

    # Define the returned columns
    columns = [
        MEASUREMENTS.c.sensor_identifier,
        MEASUREMENTS.c.measurement_timestamp,
        *[sa.column(value_identifier) for value_identifier in request.query.values],
    ]
    # Define filters
    conditions = []
    conditions = database.filter_sensor_identifier(conditions, request)
    conditions = database.filter_measurement_timestamp(conditions, request)
    # Build query
    query = (
        sa.select(columns)
        .select_from(MEASUREMENTS)
        .where(sa.and_(*conditions))
        .order_by(MEASUREMENTS.c.measurement_timestamp.asc())
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
