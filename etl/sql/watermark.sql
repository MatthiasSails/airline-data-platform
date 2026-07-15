-- watermark.sql — Incremental-load watermark store (Amazon Redshift, schema `meta`)
--
-- One row per incremental target. `last_watermark` holds the max Bronze `fetched_at`
-- (ISO 8601 string) already processed by etl/silver_history.py, so it compares directly
-- to MongoDB's `fetched_at` field (both are the same ISO string, same clock).
-- `updated_at` is the loader's wall-clock at advance time — audit only, never used for the
-- incremental filter. See ADR 021.
--
--   \i etl/sql/watermark.sql

CREATE SCHEMA IF NOT EXISTS meta;

CREATE TABLE IF NOT EXISTS meta.etl_watermark (
    table_name     VARCHAR(64) NOT NULL,   -- e.g. 'silver.aircraft_position'
    last_watermark VARCHAR(40) NOT NULL,   -- max Bronze fetched_at (ISO 8601) processed
    updated_at     TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (table_name)
)
DISTSTYLE ALL;
