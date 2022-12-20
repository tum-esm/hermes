SELECT
    sensor_identifier,
    extract(epoch from creation_timestamp at time zone 'utc')::DOUBLE PRECISION AS creation_timestamp,
    measurement  -- implement selecting different values of this JSONB column, or not?
FROM measurements
{%- if request.query.sensors or request.query.start is not none or request.query.end is not none %}
WHERE
    TRUE
    {% if request.query.sensors -%} AND sensor_identifier = ANY({sensor_identifiers}) {%- endif -%}
    {% if request.query.start is not none -%} AND creation_timestamp >= ('epoch'::TIMESTAMPTZ + {start_timestamp} * '1 second'::INTERVAL) {%- endif -%}
    {% if request.query.end is not none -%} AND creation_timestamp < ('epoch'::TIMESTAMPTZ + {end_timestamp} * '1 second'::INTERVAL) {%- endif -%}
{%- endif %}
ORDER BY creation_timestamp ASC
OFFSET {skip}
LIMIT {limit};


-- fetch-latest-measurements.sql
SELECT
    sensor_identifier,
    timestamptz_to_unixtime(creation_timestamp) AS creation_timestamp,
    timestamptz_to_unixtime(receipt_timestamp) AS receipt_timestamp,
    position_in_transmission,
    measurement
FROM measurements
WHERE sensor_identifier = {sensor_identifier}
ORDER BY creation_timestamp DESC, receipt_timestamp DESC, position_in_transmission DESC
LIMIT 32;

-- fetch-previous-measurements.sql
SELECT
    sensor_identifier,
    timestamptz_to_unixtime(creation_timestamp) AS creation_timestamp,
    timestamptz_to_unixtime(receipt_timestamp) AS receipt_timestamp,
    position_in_transmission,
    measurement
FROM measurements
WHERE
    sensor_identifier = {sensor_identifier}
    AND (creation_timestamp, receipt_timestamp, position_in_transmission) > (unixtime_to_timestamptz({creation_timestamp}), unixtime_to_timestamptz({receipt_timestamp}), {position_in_transmission})
ORDER BY creation_timestamp DESC, receipt_timestamp DESC, position_in_transmission DESC
LIMIT 32;

-- fetch-next-measurements.sql
SELECT
    sensor_identifier,
    timestamptz_to_unixtime(creation_timestamp) AS creation_timestamp,
    timestamptz_to_unixtime(receipt_timestamp) AS receipt_timestamp,
    position_in_transmission,
    measurement
FROM measurements
WHERE
    sensor_identifier = {sensor_identifier}
    AND (creation_timestamp, receipt_timestamp, position_in_transmission) < (unixtime_to_timestamptz({creation_timestamp}), unixtime_to_timestamptz({receipt_timestamp}), {position_in_transmission})
ORDER BY creation_timestamp DESC, receipt_timestamp DESC, position_in_transmission DESC
LIMIT 32;
