CREATE TABLE IF NOT EXISTS sensors (
    sensor_identifier UUID PRIMARY KEY,
    sensor_name TEXT UNIQUE NOT NULL,
    creation_timestamp TIMESTAMPTZ NOT NULL,
    update_timestamp TIMESTAMPTZ,

    -- add index on sensor_name for quick lookups: sensor_name -> sensor_identifier
);
