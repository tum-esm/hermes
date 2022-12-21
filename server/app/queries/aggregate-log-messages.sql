SELECT
    sensor_identifier,
    severity,
    subject,
    first(revision, creation_timestamp) as first_revision,
    last(revision, creation_timestamp) as last_revision,
    timestamptz_to_unixtime(min(creation_timestamp)) as first_creation_timestamp,
    timestamptz_to_unixtime(max(creation_timestamp)) as last_creation_timestamp,
    count(*) as count
FROM log_messages
WHERE sensor_identifier = ANY({sensor_identifiers}) AND severity = ANY(ARRAY['warning', 'error'])
GROUP BY severity, subject;
