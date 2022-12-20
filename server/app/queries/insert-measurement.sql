INSERT INTO measurements (
    sensor_identifier,
    revision,
    creation_timestamp,
    receipt_timestamp,
    measurement
)
VALUES (
    {sensor_identifier},
    {revision},
    unixtime_to_timestamptz({creation_timestamp}),
    now(),
    {measurement}
);
