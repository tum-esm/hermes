CREATE TABLE IF NOT EXISTS sensors (
    sensor_identifier TEXT NOT NULL,
    sensor_name TEXT NOT NULL,
    creation_timestamp TIMESTAMPTZ NOT NULL,
    update_timestamp TIMESTAMPTZ,
    PRIMARY KEY (sensor_identifier)
);
