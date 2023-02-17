SELECT *
FROM sensors
JOIN logs USING (sensor_identifier)
WHERE (
    (sensors.sensor_name = '%SENSOR_ID%') AND
    (logs.creation_timestamp > now() - interval '2 days')
)