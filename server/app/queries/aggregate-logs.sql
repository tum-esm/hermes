SELECT
    sensor_identifier,
    severity,
    subject,
    first(revision, creation_timestamp) as min_revision,
    last(revision, creation_timestamp) as max_revision,
    min(creation_timestamp) as min_creation_timestamp,
    max(creation_timestamp) as max_creation_timestamp,
    count(*) as count
FROM logs
WHERE sensor_identifier = {sensor_identifier} AND severity = ANY(ARRAY['warning', 'error'])
GROUP BY sensor_identifier, severity, subject;
