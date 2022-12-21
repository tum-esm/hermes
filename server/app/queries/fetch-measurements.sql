SELECT
    sensor_identifier,
    timestamptz_to_unixtime(creation_timestamp) AS creation_timestamp,
    timestamptz_to_unixtime(receipt_timestamp) AS receipt_timestamp,
    position_in_transmission,
    measurement
FROM measurements
WHERE
    sensor_identifier = {sensor_identifier}
    AND (
        CASE
            WHEN {method} = 'next' THEN (creation_timestamp, receipt_timestamp, position_in_transmission) > (unixtime_to_timestamptz({creation_timestamp}), unixtime_to_timestamptz({receipt_timestamp}), {position_in_transmission})
            WHEN {method} = 'previous' THEN (creation_timestamp, receipt_timestamp, position_in_transmission) < (unixtime_to_timestamptz({creation_timestamp}), unixtime_to_timestamptz({receipt_timestamp}), {position_in_transmission})
            ELSE TRUE
        END
    )
ORDER BY creation_timestamp DESC, receipt_timestamp DESC, position_in_transmission DESC
LIMIT 32;
