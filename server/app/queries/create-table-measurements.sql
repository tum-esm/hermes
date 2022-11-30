CREATE TABLE IF NOT EXISTS measurements (
    sensor_identifier UUID NOT NULL,
    revision INT NOT NULL,
    measurement_timestamp TIMESTAMPTZ NOT NULL,
    receipt_timestamp TIMESTAMPTZ NOT NULL,
    -- Add position in transaction column?
    measurement JSONB NOT NULL,

    FOREIGN KEY (sensor_identifier) REFERENCES sensors (sensor_identifier) ON DELETE CASCADE
);
