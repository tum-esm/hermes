CREATE EXTENSION IF NOT EXISTS "uuid-ossp" CASCADE;
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE TYPE IF NOT EXISTS severity AS ENUM ('system', 'info', 'warning', 'error');
