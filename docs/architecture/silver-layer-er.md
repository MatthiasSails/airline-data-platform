# Silver-Layer ER Diagram — Relational Model

PostgreSQL warehouse — **Silver layer** (curated / relational).

Two stages:

| Stage | Table(s) | Status |
|---|---|---|
| **MVP** | `map1` | ✅ deployed (Supabase, 2026-06-09) |
| **Step 3 — Star Schema** | `fact_states`, `dim_aircraft`, `dim_airlines`, `dim_airports` | planned |

> **Bronze vs. Silver:** the raw landing zone (MongoDB Atlas, Bronze) keeps *all* sources —
> including **adsb.lol** — collected for optionality and a later OpenSky-vs-adsb.lol data-quality
> comparison. This Silver model promotes **only OpenSky** (States + AircraftDB). adsb.lol is
> intentionally *not* in this diagram. Ingestion ≠ modeling (ADR 004).

---

## Stage 1 — MVP: `map1` (deployed)

Flat table. One row per aircraft observation. No joins, no unit conversion, no deduplication key —
Supabase auto-generates `id`. ETL appends on every run (`ON CONFLICT DO NOTHING` is a no-op since
the only unique constraint is `id`).

**Source of every field is shown inline.**

```mermaid
erDiagram
    map1 {
        bigint      id              PK  "Supabase auto-generated"
        timestamptz created_at          "Supabase auto-generated"
        varchar     icao24              "OpenSky States · icao24 (ICAO24 transponder hex)"
        integer     time_position       "OpenSky States · time_position (unix seconds, raw)"
        varchar     callsign            "OpenSky States · callsign"
        real        longitude           "OpenSky States · longitude (degrees)"
        real        latitude            "OpenSky States · latitude (degrees)"
        boolean     on_ground           "OpenSky States · on_ground"
        double      true_track          "OpenSky States · true_track (degrees)"
        double      vertical_rate       "OpenSky States · vertical_rate (m/s raw — SI, not converted)"
        timestamptz updated_at          "ETL run timestamp"
    }
```

**Known gaps vs. Step 3 target** (fields available in OpenSky States but not yet stored):

| Missing field | OpenSky States index | Target column in `fact_states` |
|---|---|---|
| Barometric altitude | `s[7]` (m) | `altitude_baro_ft` (converted m→ft) |
| Geometric altitude | `s[13]` (m) | `altitude_geom_ft` (converted m→ft) |
| Ground speed | `s[9]` (m/s) | `ground_speed_kts` (converted m/s→kt) |
| Squawk | `s[14]` | `squawk` |
| Category | `s[16]` | `category` |
| Position source | `s[15]` | `position_source` |
| SPI | `s[17]` | `spi` |

Unit note: `vertical_rate` is stored as raw m/s (OpenSky SI). Step 3 converts to fpm (×196.85).

---

## Stage 2 — Star Schema: `fact_states` + dims (Step 3, planned)

**The source of every field is shown inline** in each attribute's comment. See legend.

**Modeling terminology & naming:**

| Layer | Tables | Classification | Why |
|---|---|---|---|
| **Fact / event** | `fact_states` | transactional / *Bewegungsdaten*, high-volume, append-only | live observations, timestamped |
| **Dimensions** | `dim_aircraft`, `dim_airlines` (joined to fact); `dim_airports` (standalone reference, unjoined) | **reference data** (not master data) | externally standardized, slowly changing, *imported* not *authored* |

> Names carry a `fact_` / `dim_` prefix (Kimball convention) so the modeling role is visible
> at a glance. **Live vs. historical is *not* encoded in names** — recency lives in the
> `observed_at` column (`WHERE observed_at > now() - interval '5 min'`), volume is handled by
> time-partitioning. A "latest position per aircraft" optimization would be a separate
> materialized view (e.g. `aircraft_current_state`), not part of this core model.

**Data sources:**

| Tag in diagram | Source | Type | Notes |
|---|---|---|---|
| **OpenSky States** | OpenSky `/states/all` | live (OAuth2) | state vectors → `fact_states` |
| **OpenSky AircraftDB** | OpenSky `aircraftDatabase.csv` (free download) | static reference | `dim_aircraft` — icao24→registration/type/operator; community-maintained; terms: research/non-commercial |
| **OurAirports** | OurAirports `airports.csv` (~12 MB, public domain) | static reference | `dim_airports` — icao_code/iata_code/coords; ~85k rows, filtered to those with icao_code (ADR 004) |
| **OpenFlights** | OpenFlights `airlines.dat` (GitHub raw, ODbL, free) | static reference | airlines — ⚠ snapshot **last updated 2017**, post-2017 airlines stale/missing |
| **derived** | computed in ETL | — | not a raw API field (conversion / lookup) |
| *(Bronze only)* | *adsb.lol API* | *live (public)* | *raw landing zone only — not promoted to this Silver model* |

> **Canonical units = aviation (ft, kt, ft/min).** OpenSky States is the only feed and reports SI;
> values are converted in ETL (m → ft ×3.281, m/s → kt ×1.944, m/s → fpm ×196.85).

```mermaid
erDiagram
    dim_aircraft ||--o{ fact_states : "emits (icao24)"
    dim_airlines ||--o{ fact_states : "operates (airline_icao, resolved)"

    fact_states {
        varchar_8   icao24       PK,FK "OpenSky States · icao24"
        timestamptz observed_at  PK "OpenSky States · time_position (derived: unix to ts)"
        varchar_3   airline_icao FK "derived · COALESCE(aircraft.operator_icao, callsign prefix)"
        varchar_10  callsign        "OpenSky States · callsign"
        double      latitude        "OpenSky States · latitude"
        double      longitude       "OpenSky States · longitude"
        int         altitude_baro_ft "OpenSky States · baro_altitude (derived: m to ft)"
        int         altitude_geom_ft "OpenSky States · geo_altitude (derived: m to ft)"
        boolean     on_ground        "OpenSky States · on_ground"
        real        ground_speed_kts "OpenSky States · velocity (derived: m/s to kt)"
        real        track_deg        "OpenSky States · true_track"
        int         vertical_rate_fpm "OpenSky States · vertical_rate (derived: m/s to fpm)"
        varchar_4   squawk           "OpenSky States · squawk"
        smallint    category         "OpenSky States · category (int 0-20)"
        smallint    position_source  "OpenSky States · position_source (0=ADS-B,2=MLAT,...)"
        boolean     spi              "OpenSky States · spi"
    }

    dim_aircraft {
        varchar_8   icao24       PK "OpenSky AircraftDB · transponder hex"
        varchar_10  registration    "OpenSky AircraftDB · registration (D-AIUB)"
        varchar     manufacturer_name "OpenSky AircraftDB · manufacturername (Airbus)"
        varchar     model            "OpenSky AircraftDB · model (A320 214)"
        varchar_4   type_code        "OpenSky AircraftDB · typecode (A320)"
        varchar_3   operator_icao    "OpenSky AircraftDB · operatoricao (registered operator; input to airline_icao)"
        date        built            "OpenSky AircraftDB · built (date/year)"
        varchar     origin_country   "OpenSky States origin_country / derived from icao24"
        timestamptz first_seen_at    "derived · first seen on platform"
        timestamptz last_seen_at     "derived · last seen on platform"
    }

    dim_airlines {
        varchar_3   icao_code    PK "OpenFlights · DLH"
        varchar_2   iata_code       "OpenFlights · LH"
        varchar     name            "OpenFlights · Lufthansa"
        varchar     country         "OpenFlights"
    }

    dim_airports {
        varchar_4   icao_code    PK "OurAirports · icao_code (EDDB) — filter NOT NULL"
        varchar_3   iata_code    UK "OurAirports · iata_code (BER)"
        varchar     name            "OurAirports · name"
        varchar     municipality    "OurAirports · municipality"
        varchar_2   country_code    "OurAirports · iso_country (ISO alpha-2)"
        double      latitude        "OurAirports · latitude_deg"
        double      longitude       "OurAirports · longitude_deg"
    }
```

---

## Diagram legend (ER notation)

How to read the diagram — key markers and crow's-foot cardinality:

| Marker | Meaning |
|---|---|
| **PK** | Primary key (uniquely identifies a row) |
| **FK** | Foreign key (references another table's PK) |
| **UK** | Unique key (unique, but not the primary key) |
| **PK,FK** | Column is part of the primary key *and* a foreign key |
| `"..."` | Inline comment — here: **the data source** of each field |

| Connector | Cardinality | Used for |
|---|---|---|
| `||--o{` | one **→** zero-or-many, *solid* (identifying) | reliable FK join, e.g. `dim_aircraft → fact_states` |
| `||..o{` | one **→** zero-or-many, *dashed* (non-identifying) | derived / soft link (not currently used — `dim_airports` is unjoined) |

Crow's-foot symbols read left-to-right: `||` = exactly one, `o{` = zero or many.
A **solid** line is an enforced/reliable relationship; a **dashed** line is derived or heuristic
(not enforced by a DB constraint).

### Attribute row layout (the unlabeled "columns")

Each row inside an entity box has **no header** — its meaning is fixed by position. The diagram
follows **Mermaid's attribute grammar** (a Crow's-Foot / Information-Engineering style box), which
is *not* part of the original Chen ER standard:

| Position | Content | Example | Note |
|---|---|---|---|
| 1 | **data type** | `varchar_8`, `timestamptz`, `int`, `double`, `boolean`, `real` | physical SQL type |
| 2 | **column name** | `icao24`, `observed_at` | — |
| 3 | **key constraint** | `PK`, `FK`, `UK`, `PK,FK` | optional |
| 4 | **comment** | `"OpenSky icao24 / adsb.lol hex"` | optional; here = **data source** (Mermaid extension) |

> **Type notation:** Mermaid types may not contain spaces or parentheses, so `varchar_8` means
> `VARCHAR(8)`, `varchar_3` means `VARCHAR(3)`, etc. The real SQL types live in `schema.sql`.

---

## Relationship notes (Star Schema)

All dimension joins are **LEFT/outer** — a `fact_states` observation must survive even when a
dimension lookup misses (unknown aircraft, unresolved airline). Fact integrity does not depend on
dimension completeness.

- **`dim_aircraft` → `fact_states`** (solid): join on `icao24`. The shared, reliable key.
- **`dim_airlines` → `fact_states`** (solid, **star** — decided, see [ADR 008](../adr/008-airline-attribution-star-schema.md)):
  the fact carries a resolved `airline_icao` (single-hop FK), so airline analytics reflect the
  **operating airline of the flight**, not just the airframe's registered operator.
  - **Resolution rule (ETL):** `airline_icao = COALESCE(dim_aircraft.operator_icao, callsign_prefix(fact_states.callsign))`
    — registered operator first, ICAO callsign prefix (`DLH123`→`DLH`) as fallback.
  - `dim_aircraft.operator_icao` remains a *plain attribute* (the airframe's registered operator),
    an input to the resolution — no longer the fact's airline path.
- **`dim_airports`** — **standalone reference table, not joined to the fact.** States data carries
  **no origin/destination**; a "nearest airport" would be a geometric guess (the airport under a
  cruising aircraft says nothing about its route). So *from/to is unknown* in this Silver model.
  Capturing real source/destination airports is a **future Bronze-layer concern** (needs a
  scheduled-flight or flight-leg source). `dim_airports` stays available for ad-hoc geo/reporting.

## Field gotchas

- **Units** — OpenSky States reports SI (m, m/s); `map1` stores raw SI. `fact_states` converts to aviation units (ft, kt, fpm) in ETL.
- **No departure/arrival airports (from/to unknown)** — the States API model dropped OpenSky's
  retrospective `/flights/*` endpoints (not live; see ADR 003). Only live position/state is captured,
  so `dim_airports` stays unjoined; real origin/destination is deferred to the Bronze layer.
- **adsb.lol is Bronze-only** — collected raw into the landing zone for optionality and a later
  OpenSky-vs-adsb.lol data-quality comparison, but **not promoted** into this Silver model.
  Aircraft metadata comes solely from the OpenSky AircraftDB.
- **`dim_airports` load filter** — OurAirports has ~85k rows but most (small fields, heliports,
  `closed`) carry **no `icao_code`**. Since `icao_code` is the PK (NOT NULL), the loader filters
  `WHERE icao_code IS NOT NULL` (optionally also `type IN ('large_airport','medium_airport')`).

DDL: [`02-data-modeling/warehouse/schema.sql`](../../02-data-modeling/warehouse/schema.sql) — in sync with this model (Star Schema target; `map1` was created via Supabase UI).
