CREATE TABLE IF NOT EXISTS measurements (
    sensor_identifier TEXT NOT NULL REFERENCES configurations (sensor_identifier) ON UPDATE CASCADE ON DELETE CASCADE,
    measurement_timestamp INTEGER NOT NULL,
    receipt_timestamp INTEGER NOT NULL,
    measurement JSONB NOT NULL
);
