-- name: aggregate-logs
SELECT
    sensor_identifier,
    severity,
    subject,
    first(revision, creation_timestamp) AS min_revision,
    last(revision, creation_timestamp) AS max_revision,
    min(creation_timestamp) AS min_creation_timestamp,
    max(creation_timestamp) AS max_creation_timestamp,
    count(*) AS count
FROM logs
WHERE
    sensor_identifier = ${sensor_identifier} AND severity = any(
        ARRAY['warning', 'error']
    )
GROUP BY sensor_identifier, severity, subject;


-- name: aggregate-network
-- Aggregate information about sensors
WITH aggregation AS (
    SELECT
        sensor_identifier,
        array_agg(bucket_timestamp) AS bucket_timestamps,
        array_agg(measurements_count) AS measurements_counts
    FROM measurements_aggregation_4_hours
    WHERE bucket_timestamp > now() - INTERVAL '28 days'
    GROUP BY sensor_identifier
)

-- Filter by sensors belonging to the given network
SELECT
    sensor_identifier,
    sensors.sensor_name,
    coalesce(
        aggregation.bucket_timestamps, ARRAY[]::TIMESTAMPTZ[]
    ) AS bucket_timestamps,
    coalesce(
        aggregation.measurements_counts, ARRAY[]::INT[]
    ) AS measurements_counts
FROM networks
INNER JOIN sensors USING (network_identifier)
LEFT JOIN aggregation USING (sensor_identifier)
WHERE network_identifier = ${network_identifier};


-- name: create-configuration
INSERT INTO configurations (
    sensor_identifier,
    revision,
    creation_timestamp,
    configuration
)
VALUES (
    ${sensor_identifier},
    (
        SELECT coalesce(max(revision) + 1, 0)
        FROM configurations WHERE sensor_identifier = ${sensor_identifier}
    ),
    now(),
    ${configuration}
)
RETURNING revision;


-- name: create-log
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
    ${sensor_identifier},
    ${revision},
    ${creation_timestamp},
    now(),
    ${position_in_transmission},
    ${severity},
    ${subject},
    ${details}
)
ON CONFLICT (sensor_identifier, creation_timestamp) DO NOTHING;


-- name: create-measurement
INSERT INTO measurements (
    sensor_identifier,
    revision,
    creation_timestamp,
    receipt_timestamp,
    position_in_transmission,
    measurement
)
VALUES (
    ${sensor_identifier},
    ${revision},
    ${creation_timestamp},
    now(),
    ${position_in_transmission},
    ${measurement}
)
ON CONFLICT (sensor_identifier, creation_timestamp) DO NOTHING;


-- name: create-sensor
INSERT INTO sensors (
    sensor_identifier,
    sensor_name,
    network_identifier,
    creation_timestamp
)
VALUES (
    uuid_generate_v4(),
    ${sensor_name},
    ${network_identifier},
    now()
)
RETURNING sensor_identifier;


-- name: create-session
INSERT INTO sessions (
    access_token_hash,
    user_identifier,
    creation_timestamp
)
VALUES (
    ${access_token_hash},
    ${user_identifier},
    now()
);


-- name: create-user
INSERT INTO users (
    user_identifier,
    username,
    creation_timestamp,
    password_hash
)
VALUES (
    uuid_generate_v4(),
    ${username},
    now(),
    ${password_hash}
)
RETURNING user_identifier;


-- name: read-measurements
SELECT
    sensor_identifier,
    creation_timestamp,
    measurement
FROM measurements
WHERE
    sensor_identifier = ${sensor_identifier}
    AND (
        CASE
            WHEN ${direction} = 'next' THEN creation_timestamp > ${creation_timestamp}  -- noqa: L016
            WHEN ${direction} = 'previous' THEN creation_timestamp < ${creation_timestamp}  -- noqa: L016
            ELSE TRUE
        END
    )
ORDER BY creation_timestamp DESC
LIMIT 64;


-- name: read-user
SELECT
    user_identifier,
    password_hash
FROM users
WHERE username = ${username};


-- name: read-permissions
-- Could be extended to support finer grained permissions
SELECT
    user_identifier,
    permissions.network_identifier
FROM sessions
LEFT JOIN permissions USING (user_identifier)
WHERE sessions.access_token_hash = ${access_token_hash};


-- name: update-configuration-on-acknowledgement
UPDATE configurations
SET
    acknowledgement_timestamp = ${acknowledgement_timestamp},
    ack_reception_timestamp = now(),
    success = ${success}
WHERE
    sensor_identifier = ${sensor_identifier}
    AND revision = ${revision}
    AND acknowledgement_timestamp IS NULL;


-- name: update-configuration-on-publication
UPDATE configurations
SET publication_timestamp = now()
WHERE
    sensor_identifier = ${sensor_identifier}
    AND revision = ${revision}
    AND publication_timestamp IS NULL;


-- name: update-sensor
-- Update general sensor information that is not relayed to the sensor
UPDATE sensors
SET sensor_name = ${sensor_name}
WHERE sensor_identifier = ${sensor_identifier};
