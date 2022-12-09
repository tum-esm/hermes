CREATE TABLE IF NOT EXISTS configurations (
    sensor_identifier UUID NOT NULL,
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

    configuration JSONB NOT NULL,

    FOREIGN KEY (sensor_identifier) REFERENCES sensors (sensor_identifier) ON DELETE CASCADE
);

-- Defining the primary key like this makes the query to get the latest revision faster
CREATE UNIQUE INDEX IF NOT EXISTS sensor_identifier_revision_index ON configurations (sensor_identifier ASC, revision DESC);

-- Check if CREATE returns saying that table already exists
-- Check if schema is equal, if not, error out (own .sql file as jinja template)
