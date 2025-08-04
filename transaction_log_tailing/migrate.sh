#!/bin/bash
QUERIES=(
    "CREATE SCHEMA IF NOT EXISTS general;"
    "CREATE TABLE IF NOT EXISTS general.outbox (
        id SERIAL PRIMARY KEY,
        topic VARCHAR(255) NOT NULL,
        key TEXT,
        value TEXT,
        headers TEXT DEFAULT NULL,
        partition INT DEFAULT NULL,
        processed BOOLEAN DEFAULT FALSE
    );"

    # Query to create a publication for the outbox table
    # This will ensure that the publication is created only if it does not already exist
    "DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'outbox') THEN
            EXECUTE 'CREATE PUBLICATION outbox FOR TABLE general.outbox';
        END IF;
    END \$\$;"

    # Query to create a logical replication slot for the outbox table
    # This will ensure that the slot is created only if it does not already exist
    "DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_replication_slots WHERE slot_name = 'outbox') THEN
            EXECUTE 'SELECT pg_create_logical_replication_slot(''outbox'', ''wal2json'')';
        END IF;
    END \$\$;"
)

# Connect to the database and run migrations
for query in "${QUERIES[@]}"; do
    psql -c "$query"
done