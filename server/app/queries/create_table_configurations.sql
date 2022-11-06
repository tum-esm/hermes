CREATE TABLE IF NOT EXISTS configurations (
    sensor_identifier TEXT NOT NULL,
    creation_timestamp INTEGER NOT NULL,
    update_timestamp INTEGER NOT NULL,
    configuration JSONB NOT NULL,
    PRIMARY KEY (sensor_identifier)
);

-- check if CREATE returns saying that table already exists
-- check if schema is equal, if not, error out (own .sql file as jinja template)
