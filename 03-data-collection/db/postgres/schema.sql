-- Airline Data Engineering — PostgreSQL Schema
-- Phase 1: Reference data (airports, airlines)
-- See ADR 001: PostgreSQL direct in Phase 1, MongoDB landing zone in Phase 2

CREATE TABLE IF NOT EXISTS airports (
    code         VARCHAR(3)   PRIMARY KEY,  -- IATA code, e.g. "BER"
    name         VARCHAR(255),              -- e.g. "Berlin Brandenburg"
    city_code    VARCHAR(3),               -- e.g. "BER"
    country_code VARCHAR(2),               -- ISO 2-letter, e.g. "DE"
    latitude     FLOAT,
    longitude    FLOAT
);

CREATE TABLE IF NOT EXISTS airlines (
    code  VARCHAR(2)   PRIMARY KEY,        -- IATA code, e.g. "LH"
    name  VARCHAR(255)                     -- e.g. "Lufthansa"
);

CREATE TABLE IF NOT EXISTS flights (
    icao24                          VARCHAR(10)  NOT NULL,   -- Aircraft transponder address
    callsign                        VARCHAR(20),             -- e.g. "EWG1R"
    first_seen                      BIGINT       NOT NULL,   -- Unix timestamp departure
    last_seen                       BIGINT       NOT NULL,   -- Unix timestamp arrival
    departure_airport               VARCHAR(4),              -- ICAO code, e.g. "EDDB"
    arrival_airport                 VARCHAR(4),              -- ICAO code, e.g. "EDDM"
    departure_horiz_distance        INT,                     -- meters to departure airport
    arrival_horiz_distance          INT,                     -- meters to arrival airport
    PRIMARY KEY (icao24, first_seen)
);
