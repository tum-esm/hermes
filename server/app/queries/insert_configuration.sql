INSERT INTO configurations (sensor_identifier, revision, creation_timestamp, configuration)
VALUES (
    {sensor_identifier},
    (SELECT COALESCE(MAX(revision) + 1, 0) FROM configurations WHERE sensor_identifier = {sensor_identifier}),
    now(),
    {configuration}
);
