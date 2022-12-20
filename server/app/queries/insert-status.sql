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
    unixtime_to_timestamptz({creation_timestamp}),
    now(),
    {severity},
    {subject},
    {details}
);
