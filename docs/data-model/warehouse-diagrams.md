# Redshift Warehouse — Diagram Reference

Scope: adsb.lol only · Redshift Serverless · pure star (no `dim_aircraft_type`) ·
`fact_flight_summary` included (Option A).

> Temporary reference on `feature/redshift-silver-history` — to be folded into the ADRs
> (020/021/022) and `docs/architecture/` once the warehouse lands. GitHub renders the
> Mermaid below inline.

---

## 1. Medallion data flow (movement between stores)

```mermaid
flowchart TD
    SRC[adsb.lol API] --> BRP[bronze.py]
    BRP -->|append raw| MG[(MongoDB Atlas<br/>Bronze: adsb_raw)]

    MG -->|full-refresh · UNCHANGED| SVP[silver.py]
    SVP --> PG[(Supabase Postgres<br/>Silver: map1 live map)]
    PG --> DLIVE[Dash — live airmap]

    MG -->|incremental · watermark| SHP[silver_history.py]
    SHP --> RS[(Redshift Serverless<br/>silver · gold · meta)]
    RS --> DANA[Dash — analytics]

    WM[(meta.etl_watermark)] <--> SHP
```

---

## 2. Gold star-schema build (how dims + facts are assembled)

```mermaid
flowchart TD
    subgraph SRC["Sources"]
        SAP[silver.aircraft_position]
        SFL[silver.flight]
        GEN[dim_date generator<br/>one-time seed]
    end
    subgraph DIMS["Dimensions"]
        DAC[dim_aircraft]
        DDATE[dim_date]
    end
    subgraph FACTS["Facts"]
        GFP[fact_aircraft_position]
        GFS[fact_flight_summary]
    end
    SAP --> DAC
    GEN --> DDATE
    SAP --> GFP
    SFL --> GFS
    DAC --> GFP
    DAC --> GFS
    DDATE --> GFP
    DDATE --> GFS
```

---

## 3. Gold star schema — field-level (MLD, Redshift types)

```mermaid
erDiagram
    fact_aircraft_position }o--|| dim_aircraft : aircraft_key
    fact_aircraft_position }o--|| dim_date : date_key
    fact_flight_summary    }o--|| dim_aircraft : aircraft_key
    fact_flight_summary    }o--|| dim_date : date_key

    dim_aircraft {
        VARCHAR aircraft_key PK
        VARCHAR registration
        VARCHAR type_code
        TIMESTAMPTZ updated_at
    }
    dim_date {
        INTEGER date_key PK
        DATE full_date
        SMALLINT year
        SMALLINT quarter
        SMALLINT month
        SMALLINT day
        SMALLINT day_of_week
        VARCHAR weekday_name
        BOOLEAN is_weekend
    }
    fact_aircraft_position {
        VARCHAR obs_id PK
        VARCHAR aircraft_key FK
        INTEGER date_key FK
        BIGINT time_position
        DATE event_date
        VARCHAR callsign
        DOUBLE longitude
        DOUBLE latitude
        BOOLEAN on_ground
        DOUBLE true_track
        DOUBLE vertical_rate
        INTEGER alt_baro
        DOUBLE ground_speed
    }
    fact_flight_summary {
        VARCHAR flight_key PK
        VARCHAR aircraft_key FK
        INTEGER date_key FK
        DATE event_date
        TIMESTAMPTZ window_start
        TIMESTAMPTZ window_end
        INTEGER duration_min
        INTEGER num_positions
        INTEGER max_alt_baro
        DOUBLE avg_ground_speed
        DOUBLE max_ground_speed
    }
```

`DOUBLE` = `DOUBLE PRECISION` in the actual DDL (shortened so Mermaid parses cleanly).

---

## 4. Silver layer — field-level

```mermaid
erDiagram
    silver_flight ||--o{ silver_aircraft_position : "derived (group by icao24, callsign)"

    silver_aircraft_position {
        VARCHAR obs_id PK
        VARCHAR icao24
        VARCHAR callsign
        BIGINT time_position
        DATE event_date
        DOUBLE longitude
        DOUBLE latitude
        BOOLEAN on_ground
        DOUBLE true_track
        DOUBLE vertical_rate
        INTEGER alt_baro
        DOUBLE ground_speed
        VARCHAR registration
        VARCHAR type_code
        VARCHAR source
        TIMESTAMPTZ loaded_at
    }
    silver_flight {
        VARCHAR flight_bk PK
        VARCHAR icao24
        VARCHAR callsign
        TIMESTAMPTZ window_start
        TIMESTAMPTZ window_end
        DATE event_date
        INTEGER num_positions
        INTEGER max_alt_baro
        DOUBLE avg_ground_speed
        DOUBLE max_ground_speed
        TIMESTAMPTZ loaded_at
    }
```

The `silver_flight → silver_aircraft_position` link is a **logical derivation** (sessionization),
not a stored foreign key — `aircraft_position` carries no `flight_bk`.

---

## 5. Control table — `meta.etl_watermark`

```mermaid
erDiagram
    etl_watermark {
        VARCHAR table_name PK
        VARCHAR last_watermark
        TIMESTAMPTZ updated_at
    }
```

`last_watermark` = max Bronze `fetched_at` (ISO 8601) processed — copied from Bronze so it
compares directly to Mongo's `fetched_at`. `updated_at` = loader wall-clock (audit only).

---

## 6. Idempotent incremental load (sequence)

```mermaid
sequenceDiagram
    participant Loop as Docker loop
    participant SH as silver_history.py
    participant MG as MongoDB (adsb_raw)
    participant WM as meta.etl_watermark
    participant RS as Redshift (silver + gold)

    Loop->>SH: run
    SH->>WM: SELECT last_watermark
    WM-->>SH: watermark (fetched_at)
    SH->>MG: find adsb_raw WHERE fetched_at > watermark
    MG-->>SH: new Bronze docs
    Note over SH: map_adsb_doc → rows<br/>obs_id = md5(icao24 | time_position)
    SH->>RS: load staging (temp table)
    SH->>RS: insert-if-new → silver.aircraft_position
    SH->>RS: upsert → dim_aircraft + fact_aircraft_position
    SH->>RS: sessionize → silver.flight + fact_flight_summary
    Note over RS: re-run = no-op (deterministic keys)
    SH->>WM: UPDATE last_watermark = MAX(fetched_at)
    Note over SH,WM: advanced only after success → crash-safe
```
