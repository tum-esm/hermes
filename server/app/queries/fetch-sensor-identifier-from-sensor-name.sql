-- Fetch the sensor identifier for a given sensor name
SELECT sensor_identifier
FROM sensors
WHERE sensor_name = {sensor_name};
