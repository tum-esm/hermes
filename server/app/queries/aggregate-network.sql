-- Aggregate information about sensors
WITH aggregation AS (
    SELECT
        sensor_identifier,
        array_agg(ARRAY[timestamptz_to_unixtime(bucket_timestamp), measurements_count]) AS measurements_counts
    FROM measurements_aggregation_4_hours
    WHERE bucket_timestamp > now() - INTERVAL '28 days'
    GROUP BY sensor_identifier
)
-- Filter by sensors belonging to the given network
SELECT
    sensor_identifier,
    sensor_name,
    coalesce(measurements_counts, ARRAY[]::int[][]) AS measurements_counts
FROM networks
JOIN sensors USING (network_identifier)
LEFT JOIN aggregation USING (sensor_identifier)
WHERE network_identifier = {network_identifier}
