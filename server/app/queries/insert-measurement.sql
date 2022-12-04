INSERT INTO measurements (
    sensor_identifier,

    -- insert the revision number

    creation_timestamp,
    receipt_timestamp,
    measurement
)
VALUES (
    {sensor_identifier},
    ('epoch'::TIMESTAMPTZ + {creation_timestamp} * '1 second'::INTERVAL),
    now(),
    {measurement}
);
