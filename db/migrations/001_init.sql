-- Dedicated schema for outbox table
CREATE SCHEMA IF NOT EXISTS general;

-- Outbox mirrors a Kafka message + minimal bookkeeping
CREATE TABLE IF NOT EXISTS general.outbox (
  id SERIAL PRIMARY KEY,

  -- Copy of Kafka message structure
  topic     TEXT  NOT NULL,
  key       TEXT DEFAULT NULL,
  value     TEXT NOT NULL,
  headers   TEXT DEFAULT NULL,
  partition INT DEFAULT NULL,

  -- bookkeeping
  processed  BOOLEAN     NOT NULL DEFAULT FALSE
);
