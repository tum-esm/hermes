SELECT
    sensor_identifier,
    timestamptz_to_unixtime(creation_timestamp) AS creation_timestamp,
    measurement
FROM measurements
WHERE
    sensor_identifier = {sensor_identifier}
    AND (
        CASE
            WHEN {direction} = 'next' THEN creation_timestamp > unixtime_to_timestamptz({creation_timestamp})
            WHEN {direction} = 'previous' THEN creation_timestamp < unixtime_to_timestamptz({creation_timestamp})
            ELSE TRUE
        END
    )
ORDER BY creation_timestamp DESC
LIMIT 64;
