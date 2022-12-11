CREATE TABLE IF NOT EXISTS statuses (
    sensor_identifier UUID NOT NULL,
    revision INT NOT NULL,
    creation_timestamp TIMESTAMPTZ NOT NULL,
    receipt_timestamp TIMESTAMPTZ NOT NULL,

    severity TEXT NOT NULL,
    subject TEXT NOT NULL,
    details TEXT,

    FOREIGN KEY (sensor_identifier) REFERENCES sensors (sensor_identifier) ON DELETE CASCADE

    -- keep only the last N statuses?
);
