UPDATE configurations
SET publication_timestamp = now()
WHERE
    sensor_identifier = {sensor_identifier}
    AND revision = {revision}
    AND publication_timestamp IS NULL;