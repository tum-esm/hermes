CREATE TABLE IF NOT EXISTS sensors (
    sensor_name TEXT NOT NULL,
    sensor_identifier UUID NOT NULL,
    creation_timestamp TIMESTAMPTZ NOT NULL,

    PRIMARY KEY (sensor_identifier),
    UNIQUE (sensor_name)
);
