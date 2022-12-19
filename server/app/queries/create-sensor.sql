INSERT INTO sensors (
    sensor_identifier,
    sensor_name,
    creation_timestamp
)
VALUES (
    uuid_generate_v4(),
    {sensor_name},
    now()
)
RETURNING sensor_identifier;
