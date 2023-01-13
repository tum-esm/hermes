CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "timescaledb";


-- Function to convert TIMESTAMPTZ into unix timestamp
CREATE FUNCTION timestamptz_to_unixtime (tstz TIMESTAMPTZ) RETURNS DOUBLE PRECISION
    LANGUAGE SQL
    IMMUTABLE
    RETURNS NULL ON NULL INPUT
    RETURN extract(epoch from tstz at time zone 'utc')::DOUBLE PRECISION;

-- Function to convert unix timestamp into TIMESTAMPTZ
CREATE FUNCTION unixtime_to_timestamptz (unixtime DOUBLE PRECISION) RETURNS TIMESTAMPTZ
    LANGUAGE SQL
    IMMUTABLE
    RETURNS NULL ON NULL INPUT
    RETURN ('epoch'::TIMESTAMPTZ + unixtime * '1 second'::INTERVAL);


CREATE TABLE users (
    user_identifier UUID PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    creation_timestamp TIMESTAMPTZ NOT NULL,
    password_hash TEXT NOT NULL
);


CREATE TABLE networks (
    network_identifier UUID PRIMARY KEY,
    network_name TEXT UNIQUE NOT NULL,
    creation_timestamp TIMESTAMPTZ NOT NULL
);


CREATE TABLE sensors (
    sensor_identifier UUID PRIMARY KEY,
    sensor_name TEXT UNIQUE NOT NULL,
    -- network_identifier UUID NOT NULL REFERENCES networks (network_identifier) ON DELETE CASCADE,
    creation_timestamp TIMESTAMPTZ NOT NULL
);


CREATE TABLE permissions (
    user_identifier UUID NOT NULL REFERENCES users (user_identifier) ON DELETE CASCADE,
    network_identifier UUID NOT NULL REFERENCES networks (network_identifier) ON DELETE CASCADE,
    creation_timestamp TIMESTAMPTZ NOT NULL,
    -- Add permission levels here (e.g. admin, read-only, etc.)?

    PRIMARY KEY (user_identifier, network_identifier)
);


CREATE TABLE sessions (
    access_token_hash TEXT PRIMARY KEY,
    user_identifier UUID NOT NULL REFERENCES users (user_identifier) ON DELETE CASCADE,
    creation_timestamp TIMESTAMPTZ NOT NULL
);


CREATE TABLE configurations (
    sensor_identifier UUID NOT NULL REFERENCES sensors (sensor_identifier) ON DELETE CASCADE,
    revision INT NOT NULL,
    creation_timestamp TIMESTAMPTZ NOT NULL,
    publication_timestamp TIMESTAMPTZ,
    acknowledgement_timestamp TIMESTAMPTZ,
    ack_reception_timestamp TIMESTAMPTZ,
    success BOOLEAN,

    -- Add more pre-defined values here (needed if we want to visualize them in the dashboard)
    -- Something like: lat/long, notes, version commit hash -> most should still be nullable
    -- lat/long and notes should be in the sensors table though, the configurations table should
    -- only contain things that are actually sent to the sensor
    -- or user-configurable "metadata" that is not sent to the sensor -> better: extra tags table?

    configuration JSONB NOT NULL
);

-- Defining the primary key like this (setting the sort order) makes the query to get the latest revision faster
CREATE UNIQUE INDEX ON configurations (sensor_identifier ASC, revision DESC);


CREATE TABLE measurements (
    sensor_identifier UUID NOT NULL REFERENCES sensors (sensor_identifier) ON DELETE CASCADE,
    revision INT NOT NULL,
    creation_timestamp TIMESTAMPTZ NOT NULL,
    receipt_timestamp TIMESTAMPTZ NOT NULL,
    position_in_transmission INT NOT NULL,
    measurement JSONB NOT NULL
);

CREATE UNIQUE INDEX ON measurements (sensor_identifier ASC, creation_timestamp DESC);

SELECT create_hypertable('measurements', 'creation_timestamp');


CREATE MATERIALIZED VIEW measurements_aggregation_4_hours
WITH (timescaledb.continuous) AS
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


CREATE TABLE log_messages (
    sensor_identifier UUID NOT NULL REFERENCES sensors (sensor_identifier) ON DELETE CASCADE,
    revision INT NOT NULL,
    creation_timestamp TIMESTAMPTZ NOT NULL,
    receipt_timestamp TIMESTAMPTZ NOT NULL,
    position_in_transmission INT NOT NULL,
    severity TEXT NOT NULL,
    subject TEXT NOT NULL,
    details TEXT
);

CREATE UNIQUE INDEX ON log_messages (sensor_identifier ASC, creation_timestamp DESC);

SELECT create_hypertable('log_messages', 'creation_timestamp');

SELECT add_retention_policy(
    relation => 'log_messages',
    drop_after => INTERVAL '120 days'
);
