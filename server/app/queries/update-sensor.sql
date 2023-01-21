-- Update general sensor information that is not relayed to the sensor
UPDATE sensors
SET sensor_name = {sensor_name}
WHERE sensor_identifier = {sensor_identifier}
RETURNING sensor_identifier;
