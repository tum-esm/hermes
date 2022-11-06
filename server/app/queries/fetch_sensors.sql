WITH latest_measurements AS (
    SELECT DISTINCT ON (sensor_identifier) *
    FROM measurements
    ORDER BY sensor_identifier ASC, measurement_timestamp DESC
),

rounded_timestamps AS (
    SELECT
        sensor_identifier,
        DIV(measurement_timestamp, $1)::INTEGER AS bucket
    FROM measurements
    WHERE measurement_timestamp >= $2
),

buckets AS (
    SELECT
        sensor_identifier,
        bucket,
        COUNT(*) AS count
    FROM rounded_timestamps
    GROUP BY sensor_identifier, bucket
    ORDER BY bucket ASC
),

buckets_wd AS (
    SELECT
        sensor_identifier,
        bucket,
        COALESCE(count, 0) AS count
    FROM
        UNNEST(ARRAY[0, 1, 2, 3]) bucket
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
    {% if request.query.sensors %} WHERE configurations.sensor_identifier IN $1 {% endif %}
ORDER BY configurations.sensor_identifier ASC
