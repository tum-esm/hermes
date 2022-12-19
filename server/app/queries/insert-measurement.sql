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
    ('epoch'::TIMESTAMPTZ + {creation_timestamp} * '1 second'::INTERVAL),
    now(),
    {measurement}
);
