-- Update general sensor information that is not relayed to the sensor
UPDATE sensors
SET sensor_name = {new_sensor_name}
WHERE sensor_name = {sensor_name}
RETURNING sensor_identifier;
