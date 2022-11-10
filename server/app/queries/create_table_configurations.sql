CREATE TABLE IF NOT EXISTS configurations (
    sensor_identifier TEXT NOT NULL,
    creation_timestamp INT NOT NULL,
    update_timestamp INT NOT NULL,
    -- Add more pre-defined values here (needed if we want to visualize them in the dashboard)
    -- Something like: lat/long, notes -> should still be nullable
    configuration JSONB NOT NULL,
    PRIMARY KEY (sensor_identifier)
);

-- Check if CREATE returns saying that table already exists
-- Check if schema is equal, if not, error out (own .sql file as jinja template)
