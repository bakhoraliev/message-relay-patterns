#!/bin/bash

# Get the PostgreSQL version for installing the wal2json extension
PG_VERSION=$(psql -V | awk '{print $3}' | cut -d '.' -f 1)

# Install the wal2json extension
apt-get update && apt-get install -y postgresql-${PG_VERSION}-wal2json

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
    # Query to create a logical replication slot for the outbox table
    "SELECT * FROM pg_create_logical_replication_slot('general.outbox', 'wal2json');"
)

# Connect to the database and run migrations
for query in "${QUERIES[@]}"; do
    psql -c "$query"
done