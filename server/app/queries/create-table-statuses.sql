CREATE TYPE status AS ENUM ('info', 'warning', 'error');

CREATE TABLE IF NOT EXISTS statuses (
    sensor_identifier TEXT NOT NULL REFERENCES sensors (sensor_identifier) ON DELETE CASCADE,
    revision INT NOT NULL,
    publication_timestamp TIMESTAMPTZ NOT NULL,
    receipt_timestamp TIMESTAMPTZ NOT NULL,

    status status NOT NULL,
    message TEXT NOT NULL,
    details TEXT,

    -- keep only the last N statuses?
);
