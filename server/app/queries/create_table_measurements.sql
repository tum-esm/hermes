CREATE TABLE IF NOT EXISTS measurements (
    sensor_identifier TEXT NOT NULL REFERENCES sensors (sensor_identifier) ON UPDATE CASCADE ON DELETE CASCADE,
    measurement_timestamp TIMESTAMPTZ NOT NULL,
    receipt_timestamp TIMESTAMPTZ NOT NULL,
    measurement JSONB NOT NULL
);
