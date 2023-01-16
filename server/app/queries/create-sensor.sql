INSERT INTO sensors (
    sensor_identifier,
    sensor_name,
    network_identifier,
    creation_timestamp
)
VALUES (
    uuid_generate_v4(),
    {sensor_name},
    {network_identifier},
    now()
)
RETURNING sensor_identifier;
