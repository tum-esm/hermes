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
    {creation_timestamp},
    now(),
    {position_in_transmission},
    {severity},
    {subject},
    {details}
)
ON CONFLICT (sensor_identifier, creation_timestamp) DO NOTHING;
