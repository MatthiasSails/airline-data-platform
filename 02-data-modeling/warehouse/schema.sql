-- ============================================================
-- Airline Data Engineering — PostgreSQL Schema (Silver layer)
-- Star schema: central fact `fact_states` (live "aircraft in the air")
-- + dimensions. See architecture/erd.md and architecture/warehouse-er.md.
--
-- Sources (all verified):
--   fact_states   ← OpenSky /states/all          (live state vectors)
--   dim_aircraft  ← OpenSky aircraftDatabase.csv  (icao24 → registration/type/operator)
--   dim_airlines  ← OpenFlights airlines.dat      (⚠ snapshot last updated 2017)
--   dim_airports  ← OurAirports airports.csv      (standalone reference, NOT joined)
--
-- adsb.lol stays in the Bronze landing zone only (not promoted here).
--
-- Load order (referential integrity + outer-join semantics):
--   1. Load dim_airlines, dim_airports.
--   2. Upsert dim_aircraft: enrich from AircraftDB; for any observed icao24 not
--      in the DB, insert a STUB row (icao24 only, rest NULL) so the fact FK holds.
--   3. Insert fact_states. Missing dimension detail surfaces as NULL on LEFT joins
--      — a fact observation never depends on dimension completeness.
-- ============================================================

-- ── Dimension: airlines (OpenFlights) ────────────────────
CREATE TABLE IF NOT EXISTS dim_airlines (
    icao_code  VARCHAR(3)   PRIMARY KEY,     -- e.g. "DLH"
    iata_code  VARCHAR(2),                   -- e.g. "LH"
    name       VARCHAR(255),                 -- e.g. "Lufthansa"
    country    VARCHAR(255)
);

-- ── Dimension: aircraft (OpenSky AircraftDB) ─────────────
-- Keyed by ICAO24 transponder hex. operator_icao is a plain attribute
-- (the airframe's registered operator) — an input to fact_states.airline_icao,
-- NOT a foreign key here.
CREATE TABLE IF NOT EXISTS dim_aircraft (
    icao24            VARCHAR(8)  PRIMARY KEY, -- transponder hex, e.g. "3c6758"
    registration      VARCHAR(10),             -- tail number, e.g. "D-AIUB"
    manufacturer_name VARCHAR(255),            -- e.g. "Airbus"
    model             VARCHAR(255),            -- e.g. "A320 214"
    type_code         VARCHAR(4),              -- ICAO type, e.g. "A320"
    operator_icao     VARCHAR(3),              -- registered operator (e.g. "DLH")
    built             DATE,                    -- build date/year
    origin_country    VARCHAR(255),            -- inferred from icao24 (OpenSky)
    first_seen_at     TIMESTAMPTZ,             -- first observation on the platform
    last_seen_at      TIMESTAMPTZ
);

-- ── Dimension: airports (OurAirports) — STANDALONE ───────
-- Reference table only; NOT joined to the fact. States data carries no
-- origin/destination, so "from/to" is unknown in this Silver model
-- (a future Bronze-layer concern). Kept for ad-hoc geo / reporting lookups.
-- Loader filters OurAirports to rows WITH an icao_code (PK is NOT NULL),
-- e.g. WHERE icao_code IS NOT NULL [AND type IN ('large_airport','medium_airport')].
CREATE TABLE IF NOT EXISTS dim_airports (
    icao_code    VARCHAR(4)  PRIMARY KEY,     -- OurAirports icao_code, e.g. "EDDB"
    iata_code    VARCHAR(3)  UNIQUE,          -- OurAirports iata_code, e.g. "BER"
    name         VARCHAR(255),                -- OurAirports name
    municipality VARCHAR(255),                -- OurAirports municipality
    country_code VARCHAR(2),                  -- OurAirports iso_country (ISO alpha-2)
    latitude     DOUBLE PRECISION,            -- OurAirports latitude_deg
    longitude    DOUBLE PRECISION             -- OurAirports longitude_deg
);

-- ── Fact: states (OpenSky /states/all) ───────────────────
-- One row per aircraft per observation timestamp ("aircraft in the air").
-- OpenSky reports SI (m, m/s); stored as aviation units (ft, kt, fpm) via ETL.
-- airline_icao is resolved at ETL: COALESCE(dim_aircraft.operator_icao,
--   callsign_prefix(callsign)); NULL when neither resolves to a known airline.
CREATE TABLE IF NOT EXISTS fact_states (
    icao24            VARCHAR(8)   NOT NULL REFERENCES dim_aircraft(icao24),
    observed_at       TIMESTAMPTZ  NOT NULL,            -- from time_position (unix → ts)
    airline_icao      VARCHAR(3)   REFERENCES dim_airlines(icao_code),  -- resolved, nullable
    callsign          VARCHAR(10),
    latitude          DOUBLE PRECISION,
    longitude         DOUBLE PRECISION,
    altitude_baro_ft  INT,                              -- baro_altitude (m → ft)
    altitude_geom_ft  INT,                              -- geo_altitude (m → ft)
    on_ground         BOOLEAN      NOT NULL DEFAULT FALSE,
    ground_speed_kts  REAL,                             -- velocity (m/s → kt)
    track_deg         REAL,                             -- true_track
    vertical_rate_fpm INT,                              -- vertical_rate (m/s → fpm)
    squawk            VARCHAR(4),
    category          SMALLINT,                         -- OpenSky category enum 0-20
    position_source   SMALLINT,                         -- 0=ADS-B,1=ASTERIX,2=MLAT,3=FLARM
    spi               BOOLEAN,
    PRIMARY KEY (icao24, observed_at)
);

-- ── Indexes for typical queries ──────────────────────────
-- (PK already covers icao24 → time-range lookups per aircraft.)
CREATE INDEX IF NOT EXISTS idx_fact_states_observed_at ON fact_states (observed_at);
CREATE INDEX IF NOT EXISTS idx_fact_states_airline     ON fact_states (airline_icao);

-- Scaling note: fact_states is high-volume / append-only. When it grows,
-- range-partition by observed_at (e.g. monthly). "Latest position per aircraft"
-- for dashboards is best served by a separate materialized view, not this table.
