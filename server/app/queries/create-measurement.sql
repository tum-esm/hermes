INSERT INTO measurements (
    sensor_identifier,
    revision,
    creation_timestamp,
    receipt_timestamp,
    position_in_transmission,
    measurement
)
VALUES (
    {sensor_identifier},
    {revision},
    unixtime_to_timestamptz({creation_timestamp}),
    now(),
    {position_in_transmission},
    {measurement}
)
ON CONFLICT (sensor_identifier, creation_timestamp) DO NOTHING;
