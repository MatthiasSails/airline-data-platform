-- load_incremental.sql — Idempotent upsert from staging into silver + gold (Redshift).
--
-- Run by etl/silver_history.py AFTER it has, in the same session/transaction:
--   1. created a TEMP table `stg_position` with the silver.aircraft_position columns, and
--   2. bulk-inserted the current batch of mapped adsb rows into it.
--
-- Idempotency: deterministic obs_id = md5(icao24 | time_position). Every step is
-- insert-if-new or a key-matched replace, so re-running the same batch is a no-op.
-- See ADR 021.

-- =============================================================================
-- 1. SILVER positions — insert only rows we haven't seen (immutable history).
-- =============================================================================
INSERT INTO silver.aircraft_position (
    obs_id, icao24, callsign, time_position, event_date, longitude, latitude,
    on_ground, true_track, vertical_rate, alt_baro, ground_speed,
    registration, type_code, source, loaded_at
)
SELECT s.obs_id, s.icao24, s.callsign, s.time_position, s.event_date, s.longitude, s.latitude,
       s.on_ground, s.true_track, s.vertical_rate, s.alt_baro, s.ground_speed,
       s.registration, s.type_code, s.source, s.loaded_at
FROM stg_position s
WHERE NOT EXISTS (
    SELECT 1 FROM silver.aircraft_position t WHERE t.obs_id = s.obs_id
);

-- =============================================================================
-- 2. GOLD dim_aircraft — backfill changed/late attributes, then insert new keys.
--    (Classic Redshift upsert: UPDATE existing, then INSERT missing.)
-- =============================================================================
UPDATE gold.dim_aircraft
SET registration = s.registration,
    type_code    = s.type_code,
    updated_at   = SYSDATE
FROM (
    SELECT icao24, MAX(registration) AS registration, MAX(type_code) AS type_code
    FROM stg_position
    WHERE icao24 IS NOT NULL
    GROUP BY icao24
) s
WHERE gold.dim_aircraft.aircraft_key = s.icao24
  AND ( NVL(gold.dim_aircraft.registration, '') <> NVL(s.registration, '')
     OR NVL(gold.dim_aircraft.type_code,    '') <> NVL(s.type_code,    '') );

INSERT INTO gold.dim_aircraft (aircraft_key, registration, type_code, updated_at)
SELECT s.icao24, MAX(s.registration), MAX(s.type_code), SYSDATE
FROM stg_position s
WHERE s.icao24 IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM gold.dim_aircraft t WHERE t.aircraft_key = s.icao24)
GROUP BY s.icao24;

-- =============================================================================
-- 3. GOLD fact_aircraft_position — insert-if-new; date_key derived from event_date.
-- =============================================================================
INSERT INTO gold.fact_aircraft_position (
    obs_id, aircraft_key, date_key, time_position, event_date, callsign,
    longitude, latitude, on_ground, true_track, vertical_rate, alt_baro, ground_speed
)
SELECT s.obs_id, s.icao24,
       CAST(TO_CHAR(s.event_date, 'YYYYMMDD') AS INTEGER),
       s.time_position, s.event_date, s.callsign,
       s.longitude, s.latitude, s.on_ground, s.true_track, s.vertical_rate,
       s.alt_baro, s.ground_speed
FROM stg_position s
WHERE NOT EXISTS (
    SELECT 1 FROM gold.fact_aircraft_position t WHERE t.obs_id = s.obs_id
);

-- =============================================================================
-- 4. SILVER flight legs + GOLD fact_flight_summary.
--    Sessionize recent positions (gap > 30 min = new leg), then delete+insert the
--    recomputed legs so still-open legs pick up their latest window_end/measures.
--    Recompute window: last 2 days of positions (covers any leg that may still be open).
-- =============================================================================

-- 4a. Recompute legs into a staging temp table.
DROP TABLE IF EXISTS stg_flight;
CREATE TEMP TABLE stg_flight AS
WITH ordered AS (
    SELECT icao24, callsign, time_position, alt_baro, ground_speed,
           TIMESTAMP 'epoch' + time_position * INTERVAL '1 second' AS ts,
           time_position - LAG(time_position) OVER (
               PARTITION BY icao24, callsign ORDER BY time_position
           ) AS gap_sec
    FROM silver.aircraft_position
    WHERE event_date >= DATEADD(day, -2, CURRENT_DATE)
      AND callsign IS NOT NULL
),
flagged AS (
    SELECT *,
           SUM(CASE WHEN gap_sec IS NULL OR gap_sec > 1800 THEN 1 ELSE 0 END)
               OVER (PARTITION BY icao24, callsign ORDER BY time_position
                     ROWS UNBOUNDED PRECEDING) AS leg_id
    FROM ordered
)
SELECT
    MD5(icao24 || '|' || NVL(callsign, '') || '|' || CAST(MIN(ts) AS VARCHAR)) AS flight_bk,
    icao24,
    callsign,
    MIN(ts)          AS window_start,
    MAX(ts)          AS window_end,
    CAST(MIN(ts) AS DATE) AS event_date,
    COUNT(*)         AS num_positions,
    MAX(alt_baro)    AS max_alt_baro,
    AVG(ground_speed) AS avg_ground_speed,
    MAX(ground_speed) AS max_ground_speed
FROM flagged
GROUP BY icao24, callsign, leg_id;

-- 4b. Replace the recomputed legs in silver.flight (delete + insert = idempotent upsert).
DELETE FROM silver.flight WHERE flight_bk IN (SELECT flight_bk FROM stg_flight);

INSERT INTO silver.flight (
    flight_bk, icao24, callsign, window_start, window_end, event_date,
    num_positions, max_alt_baro, avg_ground_speed, max_ground_speed, loaded_at
)
SELECT flight_bk, icao24, callsign, window_start, window_end, event_date,
       num_positions, max_alt_baro, avg_ground_speed, max_ground_speed, SYSDATE
FROM stg_flight;

-- 4c. Replace the same legs in gold.fact_flight_summary.
DELETE FROM gold.fact_flight_summary WHERE flight_key IN (SELECT flight_bk FROM stg_flight);

INSERT INTO gold.fact_flight_summary (
    flight_key, aircraft_key, date_key, event_date, window_start, window_end,
    duration_min, num_positions, max_alt_baro, avg_ground_speed, max_ground_speed
)
SELECT f.flight_bk, f.icao24,
       CAST(TO_CHAR(f.event_date, 'YYYYMMDD') AS INTEGER),
       f.event_date, f.window_start, f.window_end,
       DATEDIFF(minute, f.window_start, f.window_end),
       f.num_positions, f.max_alt_baro, f.avg_ground_speed, f.max_ground_speed
FROM stg_flight f;
