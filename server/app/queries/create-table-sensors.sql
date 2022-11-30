CREATE TABLE IF NOT EXISTS sensors (
    sensor_identifier UUID NOT NULL,
    sensor_name TEXT NOT NULL,
    creation_timestamp TIMESTAMPTZ NOT NULL,

    PRIMARY KEY (sensor_identifier),
    UNIQUE (sensor_name)
);
