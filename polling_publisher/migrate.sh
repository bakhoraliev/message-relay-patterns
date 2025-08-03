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
)

# Connect to the database and run migrations
for query in "${QUERIES[@]}"; do
    psql -c "$query"
done