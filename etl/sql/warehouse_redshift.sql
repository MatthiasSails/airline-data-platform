-- warehouse_redshift.sql — Historical analytical warehouse (Amazon Redshift Serverless)
--
-- Companion to etl/sql/map1.sql. Where map1 is the full-refresh live-map Silver table on
-- Supabase Postgres (loader: etl/silver.py, left untouched), this file defines the *historical*
-- star schema on Redshift: adsb.lol positions accumulate over time.
--
-- Source: adsb.lol only (no OpenSky). registration/type come straight from adsb's `r`/`t`,
-- so there is NO reference-data dependency (no AircraftDB, no S3, no dim_aircraft_type).
--
-- Loader:    etl/silver_history.py  (incremental, idempotent, watermarked — ADR 021)
-- Watermark: etl/sql/watermark.sql  (meta.etl_watermark)
-- Upserts:   etl/sql/load_incremental.sql
--
-- Redshift notes:
--   * PK/FK are declared for the planner but NOT enforced — the loader guarantees uniqueness
--     via a deterministic obs_id = md5(icao24 | time_position), same key as map1's
--     (icao24, time_position) unique constraint.
--   * No PARTITION BY (that's BigQuery); Redshift prunes via SORTKEY and co-locates via DISTKEY.
--   * Small dimensions use DISTSTYLE ALL (replicated to every node) so fact joins stay local.
--
-- Provision once (psql / Redshift wire-compatible client, or the Redshift query editor):
--   \i etl/sql/warehouse_redshift.sql

CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS meta;

-- =============================================================================
-- SILVER — cleaned, append-only history of aircraft position observations.
-- Mirrors the map1 column shape, plus alt_baro/ground_speed (adsb provides both;
-- needed for the flight-leg rollup measures).
-- =============================================================================
CREATE TABLE IF NOT EXISTS silver.aircraft_position (
    obs_id        VARCHAR(32) NOT NULL,   -- md5(icao24 | time_position)
    icao24        VARCHAR(10) NOT NULL,
    callsign      VARCHAR(12),
    time_position BIGINT,                 -- unix seconds (UTC)
    event_date    DATE        NOT NULL,   -- derived from time_position
    longitude     DOUBLE PRECISION,
    latitude      DOUBLE PRECISION,
    on_ground     BOOLEAN,
    true_track    DOUBLE PRECISION,
    vertical_rate DOUBLE PRECISION,
    alt_baro      INTEGER,                -- NULL when on ground (adsb sends "ground")
    ground_speed  DOUBLE PRECISION,       -- adsb `gs`
    registration  VARCHAR(12),            -- adsb `r`
    type_code     VARCHAR(8),             -- adsb `t`
    source        VARCHAR(16),            -- 'adsb_raw'
    loaded_at     TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (obs_id)
)
DISTKEY (icao24)
SORTKEY (event_date, icao24);

-- =============================================================================
-- SILVER — flight legs, derived from aircraft_position by sessionization
-- (group by icao24 + callsign, split on a >30 min gap). Accumulating: an open
-- leg's window_end/measures keep updating until the gap closes.
-- =============================================================================
CREATE TABLE IF NOT EXISTS silver.flight (
    flight_bk        VARCHAR(32) NOT NULL,  -- md5(icao24 | callsign | window_start)
    icao24           VARCHAR(10) NOT NULL,
    callsign         VARCHAR(12),
    window_start     TIMESTAMPTZ,
    window_end       TIMESTAMPTZ,
    event_date       DATE,
    num_positions    INTEGER,
    max_alt_baro     INTEGER,
    avg_ground_speed DOUBLE PRECISION,
    max_ground_speed DOUBLE PRECISION,
    loaded_at        TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (flight_bk)
)
DISTKEY (icao24)
SORTKEY (event_date);

-- =============================================================================
-- GOLD — conformed aircraft dimension. Current attributes only (no SCD here).
-- registration/type_code come from adsb; late/NULL values are backfilled by the
-- loader's UPDATE step (late-arriving dimension).
-- =============================================================================
CREATE TABLE IF NOT EXISTS gold.dim_aircraft (
    aircraft_key VARCHAR(10) NOT NULL,   -- = icao24
    registration VARCHAR(12),
    type_code    VARCHAR(8),
    updated_at   TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (aircraft_key)
)
DISTSTYLE ALL;

-- =============================================================================
-- GOLD — generated calendar dimension (seeded below, not from the feed).
-- =============================================================================
CREATE TABLE IF NOT EXISTS gold.dim_date (
    date_key     INTEGER  NOT NULL,      -- YYYYMMDD
    full_date    DATE     NOT NULL,
    year         SMALLINT,
    quarter      SMALLINT,
    month        SMALLINT,
    day          SMALLINT,
    day_of_week  SMALLINT,               -- 1=Mon .. 7=Sun
    weekday_name VARCHAR(9),
    is_weekend   BOOLEAN,
    PRIMARY KEY (date_key)
)
DISTSTYLE ALL;

-- =============================================================================
-- GOLD — position fact. Grain = one aircraft observation. Skinny: FKs + measures.
-- =============================================================================
CREATE TABLE IF NOT EXISTS gold.fact_aircraft_position (
    obs_id        VARCHAR(32) NOT NULL,
    aircraft_key  VARCHAR(10) NOT NULL,   -- FK -> gold.dim_aircraft
    date_key      INTEGER     NOT NULL,   -- FK -> gold.dim_date
    time_position BIGINT,
    event_date    DATE        NOT NULL,
    callsign      VARCHAR(12),
    longitude     DOUBLE PRECISION,
    latitude      DOUBLE PRECISION,
    on_ground     BOOLEAN,
    true_track    DOUBLE PRECISION,
    vertical_rate DOUBLE PRECISION,
    alt_baro      INTEGER,
    ground_speed  DOUBLE PRECISION,
    PRIMARY KEY (obs_id),
    FOREIGN KEY (aircraft_key) REFERENCES gold.dim_aircraft (aircraft_key),
    FOREIGN KEY (date_key)     REFERENCES gold.dim_date (date_key)
)
DISTKEY (aircraft_key)
SORTKEY (event_date, aircraft_key);

-- =============================================================================
-- GOLD — flight-leg fact (accumulating snapshot). Grain = one flight leg.
-- Revisits ADR 009's "no fact_flights" clause — see ADR 022.
-- =============================================================================
CREATE TABLE IF NOT EXISTS gold.fact_flight_summary (
    flight_key       VARCHAR(32) NOT NULL,  -- = silver.flight.flight_bk
    aircraft_key     VARCHAR(10) NOT NULL,  -- FK -> gold.dim_aircraft
    date_key         INTEGER     NOT NULL,  -- FK -> gold.dim_date
    event_date       DATE,
    window_start     TIMESTAMPTZ,
    window_end       TIMESTAMPTZ,
    duration_min     INTEGER,
    num_positions    INTEGER,
    max_alt_baro     INTEGER,
    avg_ground_speed DOUBLE PRECISION,
    max_ground_speed DOUBLE PRECISION,
    PRIMARY KEY (flight_key),
    FOREIGN KEY (aircraft_key) REFERENCES gold.dim_aircraft (aircraft_key),
    FOREIGN KEY (date_key)     REFERENCES gold.dim_date (date_key)
)
DISTKEY (aircraft_key)
SORTKEY (event_date);

-- =============================================================================
-- SEED — gold.dim_date, 2026-01-01 .. 2030-12-31 (idempotent: only inserts
-- date_keys not already present, so re-running this file is safe). Extend the
-- upper bound and re-run to add more years.
-- =============================================================================
INSERT INTO gold.dim_date (date_key, full_date, year, quarter, month, day,
                           day_of_week, weekday_name, is_weekend)
WITH RECURSIVE calendar (d) AS (
    SELECT DATE '2026-01-01'
    UNION ALL
    SELECT DATEADD(day, 1, d) FROM calendar WHERE d < DATE '2030-12-31'
)
SELECT
    CAST(TO_CHAR(d, 'YYYYMMDD') AS INTEGER),
    d,
    EXTRACT(year    FROM d),
    EXTRACT(quarter FROM d),
    EXTRACT(month   FROM d),
    EXTRACT(day     FROM d),
    ((EXTRACT(dow FROM d)::INT + 6) % 7) + 1,     -- 0=Sun..6=Sat  ->  1=Mon..7=Sun
    TRIM(TO_CHAR(d, 'Day')),
    EXTRACT(dow FROM d) IN (0, 6)
FROM calendar c
WHERE NOT EXISTS (
    SELECT 1 FROM gold.dim_date x
    WHERE x.date_key = CAST(TO_CHAR(c.d, 'YYYYMMDD') AS INTEGER)
);
