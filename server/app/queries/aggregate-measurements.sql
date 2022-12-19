SELECT
    sensor_identifier,
    array_agg(ARRAY[unixtime(bucket_timestamp), measurements_count]) AS measurement_counts
FROM measurements_aggregation_4_hours
WHERE bucket_timestamp > now() - INTERVAL '28 days' AND sensor_identifier = ANY({sensor_identifiers})
GROUP BY sensor_identifier
