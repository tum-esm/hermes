CREATE TABLE IF NOT EXISTS statuses (
    sensor_identifier TEXT NOT NULL REFERENCES sensors (sensor_identifier) ON UPDATE CASCADE ON DELETE CASCADE,
    publication_timestamp TIMESTAMPTZ NOT NULL,
    receipt_timestamp TIMESTAMPTZ NOT NULL,
    revision INT NOT NULL,

    -- metadata JSONB NOT NULL (something to report errors, etc.),
    -- keep only the last N statuses?
);