-- Most recent measurement for each sensor identifier
WITH most_recent_measurements AS (
    SELECT DISTINCT ON (sensor_identifier) *
    FROM measurements
    ORDER BY sensor_identifier ASC, measurement_timestamp DESC
),

-- Most recent configuration for each sensor identifier
most_recent_configurations AS (
    SELECT DISTINCT ON (sensor_identifier) *
    FROM configurations
    ORDER BY sensor_identifier ASC, revision DESC
),

-- Every start of the day for the last 28 days
dates AS (
    SELECT date_trunc('day', (now() - generate_series * '1 day'::INTERVAL), {timezone}) AS date
    FROM generate_series(27, 0, -1)
),

-- Every sensor identifier with every start of the day for the last 28 days
defaults AS (
    SELECT
        sensor_identifier,
        date
    FROM sensors
    CROSS JOIN dates
),

-- Every sensor identifier with the count of measurements per day for days where there was at least one measurement for the last 28 days
counts AS (
    SELECT
        sensor_identifier,
        date_trunc('day', measurement_timestamp, {timezone}) AS date,
        count(*) AS count
    FROM measurements
    GROUP BY (sensor_identifier, date)
),

-- Every sensor identifier with the count of measurements per day for the last 28 days
counts_with_defaults AS (
    SELECT
        sensor_identifier,
        date,
        coalesce(count, 0) AS count
    FROM defaults
    LEFT JOIN counts USING (sensor_identifier, date)
    ORDER BY date ASC
),

-- Every sensor identifier with the count of measurements per day for the last 28 days in an array
activity AS (
    SELECT
        sensor_identifier,
        array_agg(extract(epoch from date at time zone 'utc')::DOUBLE PRECISION) AS dates,
        array_agg(count) AS counts
    FROM counts_with_defaults
    GROUP BY sensor_identifier
)

SELECT
    sensor_identifier,
    revision,
    extract(epoch from acknowledgement_timestamp at time zone 'utc')::DOUBLE PRECISION AS acknowledgement_timestamp,
    configuration,
    extract(epoch from most_recent_measurements.measurement_timestamp at time zone 'utc')::DOUBLE PRECISION AS measurement_timestamp,
    activity.dates,
    activity.counts
FROM most_recent_configurations
LEFT JOIN most_recent_measurements USING (sensor_identifier)
JOIN activity USING (sensor_identifier)
{%- if request.query.sensors -%} WHERE sensor_identifier = ANY({sensor_identifiers}) {%- endif %}
ORDER BY sensor_identifier ASC
