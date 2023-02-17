SELECT
    sensors.sensor_name,
    (configurations.configuration ->> 'version') as sensor_code_version,
    MIN(measurements.creation_timestamp) as first_measurement_timestamp,
    MAX(measurements.creation_timestamp) as last_measurement_timestamp
FROM sensors
JOIN configurations USING (sensor_identifier)
JOIN measurements USING (sensor_identifier, revision)
WHERE (
    (NOT ((configurations.configuration ->> 'version') IS NULL)) AND
    (sensors.sensor_name LIKE 'tum-esm-midcost-raspi-%') AND
    (NOT ((configurations.configuration ->> 'version') IN (
        '0.1.0-alpha.5', '0.1.0-alpha.6', '0.1.0-alpha.7', '0.1.0-alpha.8', '0.1.0-alpha.9', '0.1.0-alpha.10'
    ))) AND
    (measurements.creation_timestamp > now() - interval '3 days')
)
GROUP BY sensors.sensor_name, sensor_code_version
ORDER BY sensor_code_version DESC, sensors.sensor_name ASC;