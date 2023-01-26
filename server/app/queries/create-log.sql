INSERT INTO logs (
    sensor_identifier,
    revision,
    creation_timestamp,
    receipt_timestamp,
    position_in_transmission,
    severity,
    subject,
    details
)
VALUES (
    {sensor_identifier},
    {revision},
    unixtime_to_timestamptz({creation_timestamp}),
    now(),
    {position_in_transmission},
    {severity},
    {subject},
    {details}
);
