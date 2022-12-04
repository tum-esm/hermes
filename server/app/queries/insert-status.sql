INSERT INTO statuses (
    sensor_identifier,
    revision,
    creation_timestamp,
    receipt_timestamp,
    severity,
    subject,
    details
)
VALUES (
    {sensor_identifier},
    {revision},
    ('epoch'::TIMESTAMPTZ + {creation_timestamp} * '1 second'::INTERVAL),
    now(),
    {severity},
    {subject},
    {details}
);
