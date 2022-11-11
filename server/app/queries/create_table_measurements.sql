CREATE TABLE IF NOT EXISTS measurements (
    sensor_identifier TEXT NOT NULL REFERENCES sensors (sensor_identifier) ON UPDATE CASCADE ON DELETE CASCADE,
    measurement_timestamp TIMESTAMPTZ NOT NULL,
    receipt_timestamp TIMESTAMPTZ NOT NULL,
    -- Add position in transaction column?
    measurement JSONB NOT NULL
);
