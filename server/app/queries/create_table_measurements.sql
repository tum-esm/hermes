CREATE TABLE IF NOT EXISTS measurements (
    sensor_identifier TEXT NOT NULL REFERENCES configurations (sensor_identifier) ON UPDATE CASCADE ON DELETE CASCADE,
    measurement_timestamp INT NOT NULL,
    receipt_timestamp INT NOT NULL,
    measurement JSONB NOT NULL
);
