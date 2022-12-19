-- Fetch the sensor identifier for a given sensor name
SELECT sensor_identifier, sensor_name
FROM sensors
WHERE sensor_name = ANY({sensor_names});
