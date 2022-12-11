CREATE TABLE IF NOT EXISTS measurements (
    sensor_identifier UUID NOT NULL,
    revision INT NOT NULL,
    creation_timestamp TIMESTAMPTZ NOT NULL,
    receipt_timestamp TIMESTAMPTZ NOT NULL,
    -- Add position in transaction column?
    measurement JSONB NOT NULL,

    FOREIGN KEY (sensor_identifier) REFERENCES sensors (sensor_identifier) ON DELETE CASCADE
);

SELECT create_hypertable('measurements', 'creation_timestamp', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS sensor_identifier_creation_timestamp_index ON measurements (sensor_identifier ASC, creation_timestamp DESC);
