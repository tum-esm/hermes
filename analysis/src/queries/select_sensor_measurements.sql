SELECT *
FROM sensors
JOIN measurements USING (sensor_identifier)
WHERE (
    (sensors.sensor_name = '%SENSOR_ID%') AND
    (measurements.creation_timestamp > now() - interval '2 days')
)