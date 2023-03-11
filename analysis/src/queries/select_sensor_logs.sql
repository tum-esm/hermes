SELECT logs.creation_timestamp, logs.severity, logs.subject, logs.details
FROM sensors
JOIN logs USING (sensor_identifier)
WHERE (
    (sensors.sensor_name = '%SENSOR_NAME%') AND
    (logs.creation_timestamp > now() - interval '2 days')
)