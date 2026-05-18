# Entity Relationship Diagram

PostgreSQL warehouse schema (Phase 1).

> **Note on airport codes:** `airports` uses IATA codes (3 chars, e.g. `BER`) from the LH API.
> `flights` uses ICAO codes (4 chars, e.g. `EDDB`) from OpenSky.
> No foreign key between the two — a IATA ↔ ICAO mapping table will be added in Phase 2
> (see [ADR 003](../adr/003-dual-stream.md)).

```mermaid
erDiagram
    AIRPORTS {
        varchar_3 code PK
        varchar name
        varchar city_code
        varchar country_code
        float latitude
        float longitude
    }

    AIRLINES {
        varchar_2 code PK
        varchar name
    }

    FLIGHTS {
        varchar_10 icao24 PK
        bigint first_seen PK
        varchar callsign
        bigint last_seen
        varchar_4 departure_airport
        varchar_4 arrival_airport
        int departure_horiz_distance
        int arrival_horiz_distance
    }
```

---

## Phase 2 addition (planned)

```mermaid
erDiagram
    IATA_ICAO_MAPPING {
        varchar_4 icao PK
        varchar_3 iata
        varchar name
        float latitude
        float longitude
        varchar country
    }
```

Source: [OurAirports.com](https://ourairports.com/data/) CSV (~28k airports, one-time import).
