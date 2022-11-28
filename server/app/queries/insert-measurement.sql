INSERT INTO measurements (
    sensor_identifier,
    measurement_timestamp,
    receipt_timestamp,
    measurement
)
VALUES (
    {sensor_identifier},
    ('epoch'::TIMESTAMPTZ + {measurement_timestamp} * '1 second'::INTERVAL),
    now(),
    {measurement}
);
