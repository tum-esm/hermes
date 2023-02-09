SELECT
    sensor_identifier,
    creation_timestamp,
    measurement
FROM measurements
WHERE
    sensor_identifier = {sensor_identifier}
    AND (
        CASE
            WHEN {direction} = 'next' THEN creation_timestamp > {creation_timestamp}
            WHEN {direction} = 'previous' THEN creation_timestamp < {creation_timestamp}
            ELSE TRUE
        END
    )
ORDER BY creation_timestamp DESC
LIMIT 64;
