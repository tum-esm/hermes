CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "timescaledb";


CREATE TABLE users (
    user_identifier UUID PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    creation_timestamp TIMESTAMPTZ NOT NULL,
    password_hash TEXT NOT NULL
);


CREATE TABLE networks (
    network_identifier UUID PRIMARY KEY,
    network_name TEXT NOT NULL,
    creation_timestamp TIMESTAMPTZ NOT NULL
);


CREATE TABLE sensors (
    sensor_identifier UUID PRIMARY KEY,
    sensor_name TEXT NOT NULL,
    network_identifier UUID NOT NULL REFERENCES networks (network_identifier) ON DELETE CASCADE,
    creation_timestamp TIMESTAMPTZ NOT NULL,

    UNIQUE (network_identifier, sensor_name)
);


CREATE TABLE permissions (
    user_identifier UUID NOT NULL REFERENCES users (user_identifier) ON DELETE CASCADE,
    network_identifier UUID NOT NULL REFERENCES networks (network_identifier) ON DELETE CASCADE,
    creation_timestamp TIMESTAMPTZ NOT NULL,
    -- Add permission levels here (e.g. owner, user, read-only)

    PRIMARY KEY (user_identifier, network_identifier)
);


CREATE TABLE sessions (
    access_token_hash TEXT PRIMARY KEY,
    user_identifier UUID NOT NULL REFERENCES users (user_identifier) ON DELETE CASCADE,
    creation_timestamp TIMESTAMPTZ NOT NULL
);


CREATE TABLE configurations (
    sensor_identifier UUID NOT NULL REFERENCES sensors (sensor_identifier) ON DELETE CASCADE,
    configuration JSONB NOT NULL,
    revision INT NOT NULL,
    creation_timestamp TIMESTAMPTZ NOT NULL,
    publication_timestamp TIMESTAMPTZ,
    acknowledgement_timestamp TIMESTAMPTZ,
    receipt_timestamp TIMESTAMPTZ,
    success BOOLEAN

    -- Add more pre-defined values here (needed if we want to visualize them in the dashboard)
    -- Something like: lat/long, notes, version commit hash -> most should still be nullable
    -- lat/long and notes should be in the sensors table though, the configurations table should
    -- only contain things that are actually sent to the sensor
    -- or user-configurable "metadata" that is not sent to the sensor -> better: extra tags table?
);

-- Defining the primary key manually with the sort order makes the query for the latest
-- revision faster
CREATE UNIQUE INDEX ON configurations (sensor_identifier ASC, revision DESC);


-- Measurements don't have a unique primary key. Enforcing that the combination of
-- sensor_identifier and creation_timestamp is unique could filter out duplicates
-- but could also incorrectly discard measurements that are actually different.
-- Instead, the server should store everything it receives and duplicates should be
-- filtered out during processing. Due to the missing primary key, the keyset pagination
-- can result in duplicates. We accept this trade-off in favor of performance.
-- If this ever becomes a problem, we can generate a column that reliably makes the
-- combination unique and use that for the keyset pagination. This way, we can
-- continue to do without an index. The same ideas apply to the logs table.
CREATE TABLE measurements (
    sensor_identifier UUID NOT NULL REFERENCES sensors (sensor_identifier) ON DELETE CASCADE,
    measurement JSONB NOT NULL,
    revision INT NOT NULL,
    creation_timestamp TIMESTAMPTZ NOT NULL,
    receipt_timestamp TIMESTAMPTZ NOT NULL,
    position_in_transmission INT NOT NULL
);

SELECT create_hypertable('measurements', 'creation_timestamp');


CREATE MATERIALIZED VIEW measurements_aggregation_4_hours
WITH (timescaledb.continuous, timescaledb.materialized_only = true) AS
    SELECT
        sensor_identifier,
        time_bucket('4 hours', creation_timestamp) AS bucket_timestamp,
        COUNT(*) AS measurements_count
    FROM measurements
    GROUP BY sensor_identifier, bucket_timestamp
WITH DATA;


SELECT add_continuous_aggregate_policy(
    continuous_aggregate => 'measurements_aggregation_4_hours',
    start_offset => '10 days',
    end_offset => '4 hours',
    schedule_interval => '2 hours'
);


CREATE TABLE logs (
    sensor_identifier UUID NOT NULL REFERENCES sensors (sensor_identifier) ON DELETE CASCADE,
    severity TEXT NOT NULL,
    subject TEXT NOT NULL,
    revision INT NOT NULL,
    creation_timestamp TIMESTAMPTZ NOT NULL,
    receipt_timestamp TIMESTAMPTZ NOT NULL,
    position_in_transmission INT NOT NULL,
    details TEXT
);

SELECT create_hypertable('logs', 'creation_timestamp');

SELECT add_retention_policy(
    relation => 'logs',
    drop_after => INTERVAL '8 weeks'
);
