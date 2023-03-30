SELECT
    sensors.sensor_name,
    (configurations.configuration ->> 'version') as sensor_code_version,
    MIN(logs.creation_timestamp) as first_logs_timestamp,
    MAX(logs.creation_timestamp) as last_logs_timestamp
FROM sensors
JOIN configurations USING (sensor_identifier)
JOIN logs USING (sensor_identifier, revision)
WHERE (
    (NOT ((configurations.configuration ->> 'version') IS NULL)) AND
    (sensors.sensor_name LIKE 'tum-esm-midcost-raspi-%') AND
    (logs.creation_timestamp > now() - interval '6 days')
)
GROUP BY sensors.sensor_name, sensor_code_version
ORDER BY sensor_code_version DESC, sensors.sensor_name ASC;