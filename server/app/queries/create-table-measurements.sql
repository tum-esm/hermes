CREATE TABLE IF NOT EXISTS measurements (
    sensor_identifier TEXT NOT NULL REFERENCES sensors (sensor_identifier) ON DELETE CASCADE,
    revision INT NOT NULL,
    measurement_timestamp TIMESTAMPTZ NOT NULL,
    receipt_timestamp TIMESTAMPTZ NOT NULL,
    -- Add position in transaction column?
    measurement JSONB NOT NULL
);
