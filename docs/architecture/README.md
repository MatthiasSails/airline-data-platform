# Architecture

The platform follows a **medallion** structure: Bronze (raw landing zone, MongoDB Atlas) → Silver
(Supabase Postgres — currently the flat `map1` MVP table; curated star schema is the target) → Gold
(consumption layer: API + dashboard; dedicated Gold aggregates deferred). The phases below map onto
the repo's folder layout: `01-bronze` (Bronze) → `02-silver` (Silver) → `03-gold` (API + dashboard);
cross-cutting code (`data_connectors/`, `deployment/`, `notebooks/`) is un-numbered (see ADR 011).

**Related:**
- [data-flow.md](data-flow.md) — prose explanation of data flow
- [silver-layer-er.md](silver-layer-er.md) — Silver-layer ER diagram (relational model)
- [../adr/](../adr/) — Architecture Decision Records (why)
- [../requirements/timeline.md](../requirements/timeline.md) — deadlines

---

## Phase 1 — Data Collection (Bronze) 🚧
*Folder: `01-bronze/`*

Ingest every source **raw, untransformed** into the MongoDB Atlas landing zone. *Ingestion ≠
modeling* (ADR 004): Bronze keeps the original payloads; the Silver model promotes only what it needs.
The central live feed is OpenSky **`/states/all`** state vectors; static reference feeds and adsb.lol
land alongside it.

```mermaid
graph LR
    OS["OpenSky States API<br/>/states/all<br/>OAuth2 — live"]
    REF["Static reference feeds<br/>aircraftDatabase.csv<br/>airlines.dat (OpenFlights)<br/>airports.csv (OurAirports)"]
    ADSB["adsb.lol API<br/>public REST<br/>(Bronze-only)"]

    OS -->|state vectors| COL["Collectors<br/>opensky_states_collector.py<br/>adsb_collector.py"]
    REF -->|raw rows| COL
    ADSB -->|raw snapshots| COL

    COL -->|insert| CON["MongoConnector<br/>data_connectors/mongo.py"]
    CON --> MDB["MongoDB Atlas<br/>airline_landing<br/>(opensky_raw, adsb_raw, ...)<br/>mongo-mk1 (eu-central-1)"]

    style OS fill:#4CAF50,color:#fff
    style REF fill:#4CAF50,color:#fff
    style ADSB fill:#4CAF50,color:#fff
    style COL fill:#0066CC,color:#fff
    style CON fill:#0066CC,color:#fff
    style MDB fill:#FF6B35,color:#fff
```

**What exists now:**
- `01-bronze/collectors/opensky_states_collector.py` — OpenSky `/states/all` collector (OAuth2/basic-auth inline) ✅
- `01-bronze/collectors/adsb_collector.py` — adsb.lol collector (Bronze-only) ✅
- `data_connectors/mongo.py` — MongoDB Atlas connector ✅
- `airline_landing` collections live on Atlas ✅

> **adsb.lol is Bronze-only** — collected raw for optionality and a later OpenSky-vs-adsb.lol
> data-quality comparison, **not promoted** to Silver (see [ADR 009](../adr/009-states-api-silver-model.md)).
> The retrospective OpenSky `/flights/*` model was dropped in favour of the live States feed.

---

## Phase 2 — Data Modeling (Silver) 🚧
*Folder: `02-silver/`*

ETL from the Bronze landing zone into the **Silver** layer on Supabase Postgres. **Current state is a
lean MVP:** [`opensky_to_supabase.py`](../../02-silver/etl/opensky_to_supabase.py) flattens
`adsb_raw` + `opensky_raw` into a single table **`map1`** (raw values, no dimensions) that backs the
live-map dashboard. The curated **star schema** (`fact_states` + dims) is the *target* model
([silver-layer-er.md](silver-layer-er.md), [`schema.sql`](../../02-silver/warehouse/schema.sql)), not
yet built. Only **OpenSky** (States + AircraftDB) is promoted; adsb.lol stays in Bronze.

```mermaid
graph LR
    MDB["MongoDB Atlas<br/>(Bronze raw)"]

    MDB -->|read raw| ETL["Python ETL<br/>02-silver/etl/<br/>opensky_to_supabase.py"]

    ETL -->|UPSERT| CON["supabase.py<br/>(psycopg2 direct)"]
    CON --> PG["Supabase Postgres (Silver)<br/>map1 — flat live-map table ✅"]
    PG -.->|planned| STAR["Star schema (target)<br/>fact_states + dim_aircraft<br/>dim_airlines · dim_airports"]

    style MDB fill:#FF6B35,color:#fff
    style ETL fill:#FFA500,color:#fff
    style CON fill:#0066CC,color:#fff
    style PG fill:#0066CC,color:#fff
    style STAR fill:#0066CC,color:#fff,stroke-dasharray:5 5
```

**What exists now:**
- `02-silver/etl/opensky_to_supabase.py` — ETL: Atlas `adsb_raw` + `opensky_raw` → Supabase `map1` ✅
- `data_connectors/supabase.py` — Postgres connector ✅
- `02-silver/warehouse/schema.sql` — star-schema DDL (target model; `map1` itself was created via the Supabase UI and is *not* in this DDL) ✅

**What is pending — promote the `map1` MVP to the star schema:**
- unit conversion (m→ft, m/s→kt, m/s→fpm), `airline_icao` resolution, dimension loaders
  (`01-bronze/reference/` → `dim_*`), and `fact_states` instead of `map1`

> **Silver tables** (see [silver-layer-er.md](silver-layer-er.md), [ADR 008](../adr/008-airline-attribution-star-schema.md), [ADR 009](../adr/009-states-api-silver-model.md)):
> `fact_states` (OpenSky `/states/all`), `dim_aircraft` (OpenSky AircraftDB, join on `icao24`),
> `dim_airlines` (OpenFlights, join on resolved `airline_icao`), `dim_airports` (OurAirports,
> **standalone reference, unjoined**). No `fact_flights` / `fact_delays`: the live States feed has no
> origin/destination and no scheduled-vs-actual times, so route from/to and delay analytics are out
> of scope for Silver.

---

## Phase 3 — Data Consumption (API & Dashboard)
*Folder: `03-gold/`*

Expose the Silver star schema via FastAPI and visualize it. Endpoints and dashboard views are
position/aircraft/airline-centric — there is no route or delay analytics in this model.

```mermaid
graph LR
    PG["PostgreSQL (Silver star schema)"]

    PG -->|SQL queries| API["FastAPI<br/>GET /states<br/>GET /aircraft<br/>GET /airlines<br/>GET /airports<br/>03-gold/api/"]
    PG -->|analytics| DASH["Streamlit / Dash<br/>live position maps<br/>airline KPIs<br/>fleet breakdowns<br/>03-gold/dashboard/"]

    style PG fill:#0066CC,color:#fff
    style API fill:#9933CC,color:#fff
    style DASH fill:#9933CC,color:#fff
```

**What exists now:**
- `03-gold/dashboard/` — Streamlit dashboard ✅

**What will be added:**
- `03-gold/api/` — FastAPI service (`/states`, `/aircraft`, `/airlines`, `/airports`)

> **Endpoint scope** (see [data-flow.md](data-flow.md)): `/states` (live positions, backed by
> `fact_states`), `/aircraft` (`dim_aircraft`), `/airlines` (`dim_airlines`), `/airports`
> (`dim_airports`, standalone). Route from/to and delay endpoints are out of scope — the live States
> feed has no origin/destination or scheduled times.

---

## Phase 4 — Deployment & Automation
*Folder: `deployment/`*

Containerize everything. Automate ingestion. Add CI/CD.

```mermaid
graph TB
    subgraph CICD["CI/CD — GitHub Actions"]
        CI["ci.yaml<br/>lint + test + build"]
        REL["release.yaml<br/>lint + test + build + push DockerHub"]
    end

    subgraph COMPOSE["Docker Compose"]
        C1["postgres"]
        C2["mongodb"]
        C3["fastapi"]
        C4["dashboard"]
        C5["scheduler"]
    end

    subgraph SCHED["Scheduler — ingestion DAGs"]
        D1["collect_states"]
        D2["refresh_reference_feeds"]
        D3["etl_transform"]
    end

    CI --> COMPOSE
    REL --> COMPOSE
    SCHED --> C1
    SCHED --> C2

    style CICD fill:#FF6B35,color:#fff
    style COMPOSE fill:#0066CC,color:#fff
    style SCHED fill:#FFA500,color:#fff
```

**What will be added:**
- `deployment/` — Dockerfiles, docker-compose.yml, GitHub Actions, scheduler

---

## Technical Details

### Entity Relationship Diagram

Moved to [silver-layer-er.md](silver-layer-er.md).

---

### File Dependencies

```mermaid
graph TD
    OS["collectors/opensky_states_collector.py"]
    ADSB["adsb.lol API"]

    OS --> COL["01-bronze/collectors/"]
    ADSB --> COL

    COL --> CONN["data_connectors/mongo.py"]
    CONN --> MDB["MongoDB Atlas (Bronze)"]
    MDB --> ETL["02-silver/etl/"]
    ETL --> WCON["data_connectors/supabase.py"]
    WCON --> PG["PostgreSQL (Silver)"]
    PG --> API["03-gold/api/ (FastAPI)"]
    PG --> DASH["03-gold/dashboard/"]

    style OS fill:#4CAF50,color:#fff
    style ADSB fill:#4CAF50,color:#fff
    style COL fill:#0066CC,color:#fff
    style CONN fill:#0066CC,color:#fff
    style MDB fill:#FF6B35,color:#fff
    style ETL fill:#FFA500,color:#fff
    style WCON fill:#0066CC,color:#fff
    style PG fill:#0066CC,color:#fff
    style API fill:#9933CC,color:#fff
    style DASH fill:#9933CC,color:#fff
```

---

### Bronze → Silver Transformation (`fact_states`) — *target*

The core ETL step **of the target star schema** (not the current `map1` MVP, which stores raw values
without conversion): a raw OpenSky `/states/all` state vector (Bronze) becomes a `fact_states` row
(Silver), with SI → aviation unit conversion and a resolved `airline_icao` (see [ADR 008](../adr/008-airline-attribution-star-schema.md)).

```mermaid
graph LR
    subgraph MONGO["MongoDB Document (Bronze, raw state vector)"]
        M["icao24: 3c6750<br/>callsign: DLH123<br/>baro_altitude: 11277.6 (m)<br/>velocity: 231.5 (m/s)<br/>vertical_rate: 0.0 (m/s)<br/>on_ground: false"]
    end

    subgraph ETL["Python ETL"]
        T["normalize · convert units<br/>resolve airline_icao"]
    end

    subgraph PGSQL["PostgreSQL Row (Silver, fact_states)"]
        P["icao24: 3c6750<br/>callsign: DLH123<br/>airline_icao: DLH (resolved)<br/>altitude_baro_ft: 37000<br/>ground_speed_kts: 450<br/>vertical_rate_fpm: 0<br/>on_ground: false"]
    end

    M --> T --> P

    style MONGO fill:#FF6B35,color:#fff
    style ETL fill:#FFA500,color:#fff
    style PGSQL fill:#0066CC,color:#fff
```

> Unit conversions: m → ft (×3.281), m/s → kt (×1.944), m/s → fpm (×196.85).
> `airline_icao = COALESCE(dim_aircraft.operator_icao, callsign_prefix(callsign))`.
