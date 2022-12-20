CREATE EXTENSION IF NOT EXISTS "uuid-ossp" CASCADE;
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;


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


CREATE TABLE sensors (
    sensor_name TEXT UNIQUE NOT NULL,
    sensor_identifier UUID PRIMARY KEY,
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
CREATE UNIQUE INDEX sensor_identifier_revision_index ON configurations (sensor_identifier ASC, revision DESC);


CREATE TABLE measurements (
    sensor_identifier UUID NOT NULL REFERENCES sensors (sensor_identifier) ON DELETE CASCADE,
    revision INT NOT NULL,
    creation_timestamp TIMESTAMPTZ NOT NULL,
    receipt_timestamp TIMESTAMPTZ NOT NULL,
    -- Add position in transaction column?
    measurement JSONB NOT NULL
);

CREATE INDEX sensor_identifier_creation_timestamp_index ON measurements (sensor_identifier ASC, creation_timestamp DESC);

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


CREATE TABLE statuses (
    sensor_identifier UUID NOT NULL REFERENCES sensors (sensor_identifier) ON DELETE CASCADE,
    revision INT NOT NULL,
    creation_timestamp TIMESTAMPTZ NOT NULL,
    receipt_timestamp TIMESTAMPTZ NOT NULL,
    severity TEXT NOT NULL,
    subject TEXT NOT NULL,
    details TEXT
);

-- CREATE INDEX sensor_identifier_creation_timestamp_index ON statuses (sensor_identifier ASC, creation_timestamp DESC);

SELECT create_hypertable('statuses', 'creation_timestamp');

SELECT add_retention_policy(
    relation => 'statuses',
    drop_after => INTERVAL '120 days'
);
