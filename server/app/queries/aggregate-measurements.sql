WITH aggregation AS (
    SELECT
        sensor_identifier,
        array_agg(ARRAY[unixtime(bucket_timestamp), measurements_count]) AS measurements_counts
    FROM measurements_aggregation_4_hours
    WHERE bucket_timestamp > now() - INTERVAL '28 days'
    GROUP BY sensor_identifier
)

SELECT
    sensor_name,
    sensor_identifier,
    coalesce(measurements_counts, ARRAY[]::int[][]) AS measurements_counts
FROM sensors
LEFT JOIN aggregation USING (sensor_identifier)
WHERE sensor_name = ANY({sensor_names})

-- Also push the most recent measurement to the client?
