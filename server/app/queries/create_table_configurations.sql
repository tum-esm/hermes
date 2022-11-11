CREATE TABLE IF NOT EXISTS configurations (
    sensor_identifier TEXT NOT NULL REFERENCES sensors (sensor_identifier) ON UPDATE CASCADE ON DELETE CASCADE,
    revision SERIAL NOT NULL,
    creation_timestamp TIMESTAMPTZ NOT NULL,
    acknowledgement_timestamp TIMESTAMPTZ,
    -- Add more pre-defined values here (needed if we want to visualize them in the dashboard)
    -- Something like: lat/long, notes, version commit hash -> most should still be nullable
    configuration JSONB NOT NULL,
    PRIMARY KEY (sensor_identifier, revision)
);

-- Check if CREATE returns saying that table already exists
-- Check if schema is equal, if not, error out (own .sql file as jinja template)
