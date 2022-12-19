SELECT
    sensor_identifier,
    severity,
    subject,
    first(revision, creation_timestamp) as first_revision,
    last(revision, creation_timestamp) as last_revision,
    unixtime(min(creation_timestamp)) as first_creation_timestamp,
    unixtime(max(creation_timestamp)) as last_creation_timestamp,
    count(*) as count
FROM statuses
WHERE sensor_identifier = ANY({sensor_identifiers}) AND severity = ANY(ARRAY['warning', 'error'])
GROUP BY severity, subject;
