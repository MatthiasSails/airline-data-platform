# Architecture Diagrams

Architecture evolves per project phase. Each phase diagram shows the complete system at that point in time.

See `timeline_m.md` for deadlines. See `adr_*.md` for decisions behind each change.

---

## Phase 1 — Data Collection ✅
*Deadline: 20.05.2026 — current phase*

Direct ingestion from two APIs into PostgreSQL. MongoDB deferred (see ADR 001).

```mermaid
graph LR
    LH["Lufthansa API<br/>Mock mode<br/>(no token yet)"]
    OS["OpenSky Network API<br/>OAuth2"]

    LH -->|airports, airlines| COL["Collectors<br/>airports_collector.py<br/>airlines_collector.py<br/>flights_collector.py"]
    OS -->|flights| COL

    COL -->|UPSERT| CON["PostgresConnector<br/>db/postgres/connector.py"]
    CON -->|schema.sql| PG["PostgreSQL 16<br/>airports<br/>airlines<br/>flights"]

    style LH fill:#4CAF50,color:#fff
    style OS fill:#4CAF50,color:#fff
    style COL fill:#0066CC,color:#fff
    style CON fill:#0066CC,color:#fff
    style PG fill:#0066CC,color:#fff
```

**What exists now:**
- `lufthansa_api/` — LH client (mock + real mode)
- `opensky_api/` — OpenSky client (OAuth2)
- `db/postgres/` — connector + schema

---

## Phase 2 — Two-Layer Storage
*Deadline: within Step 2 — 10.06.2026*

Introduce MongoDB as raw landing zone (original target architecture). See ADR 001.

```mermaid
graph LR
    LH["Lufthansa API<br/>OAuth2"]
    OS["OpenSky Network API<br/>OAuth2"]

    LH -->|raw JSON| MDB["MongoDB<br/>landing zone<br/>db.airports<br/>db.airlines<br/>db.flights"]
    OS -->|raw JSON| MDB

    MDB -->|extract| ETL["Python ETL<br/>Pandas<br/>normalize + validate"]

    ETL -->|UPSERT| PG["PostgreSQL 16<br/>airports<br/>airlines<br/>flights"]

    style LH fill:#4CAF50,color:#fff
    style OS fill:#4CAF50,color:#fff
    style MDB fill:#FF6B35,color:#fff
    style ETL fill:#FFA500,color:#fff
    style PG fill:#0066CC,color:#fff
```

**What will be added:**
- `db/mongo/` — MongoDB connector
- `etl/` — transformers, validators

---

## Phase 3 — API & Dashboard
*Deadline: Step 2+3 — 10.06.2026 → 16.06.2026*

Expose data via FastAPI. Visualize via Streamlit or Dash.

```mermaid
graph LR
    PG["PostgreSQL 16"]
    MDB["MongoDB"]

    PG -->|SQL queries| API["FastAPI<br/>GET /api/airports<br/>GET /api/airlines<br/>GET /api/flights<br/>GET /api/stats"]
    PG -->|analytics| DASH["Streamlit / Dash<br/>flight maps<br/>delay analytics<br/>airport KPIs"]
    MDB -->|raw replay| ETL["ETL"]

    style PG fill:#0066CC,color:#fff
    style MDB fill:#FF6B35,color:#fff
    style ETL fill:#FFA500,color:#fff
    style API fill:#9933CC,color:#fff
    style DASH fill:#9933CC,color:#fff
```

**What will be added:**
- `05-backend/` — FastAPI service
- `06-dashboard/` — Streamlit or Dash app

---

## Phase 4 — Deployment & Automation
*Deadline: Step 4 — 02.07.2026*

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
        C5["airflow"]
    end

    subgraph SCHED["Airflow DAGs"]
        D1["ingest_airports"]
        D2["ingest_flights"]
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
- `07-devops/` — Dockerfiles, docker-compose.yml, GitHub Actions

---

## Technical Details

### Entity Relationship Diagram

```mermaid
erDiagram
    AIRPORTS {
        varchar code PK
        varchar name
        varchar city_code
        varchar country_code
        float latitude
        float longitude
    }

    AIRLINES {
        varchar code PK
        varchar name
    }

    FLIGHTS {
        varchar icao24 PK
        bigint first_seen PK
        varchar callsign
        bigint last_seen
        varchar departure_airport
        varchar arrival_airport
        int departure_horiz_distance
        int arrival_horiz_distance
    }

    FLIGHTS }o--|| AIRPORTS : "departs from"
    FLIGHTS }o--|| AIRPORTS : "arrives at"
```

---

### File Dependencies (Phase 1)

```mermaid
graph TD
    LH["lufthansa_api/client.py"]
    OS["opensky_api/client.py"]

    LH --> COL["collectors/"]
    OS --> COL

    COL --> CONN["db/postgres/connector.py"]
    CONN --> SCHEMA["db/postgres/schema.sql"]
    CONN --> PG["PostgreSQL DB"]
    PG --> API["FastAPI (Phase 3)"]

    style LH fill:#4CAF50,color:#fff
    style OS fill:#4CAF50,color:#fff
    style COL fill:#0066CC,color:#fff
    style CONN fill:#0066CC,color:#fff
    style SCHEMA fill:#0066CC,color:#fff
    style PG fill:#0066CC,color:#fff
    style API fill:#9933CC,color:#fff
```

---

### MongoDB → PostgreSQL Transformation (Phase 2 reference)

```mermaid
graph LR
    subgraph MONGO["MongoDB Document"]
        M["AirportCode: TXL<br/>Names.Name[0].$: Berlin Tegel<br/>Position.Coordinate.Latitude: 52.562<br/>CityCode: BER<br/>CountryCode: DE"]
    end

    subgraph ETL["Python ETL"]
        T["flatten + normalize"]
    end

    subgraph PGSQL["PostgreSQL Row"]
        P["code: TXL<br/>name: Berlin Tegel<br/>city_code: BER<br/>country_code: DE<br/>latitude: 52.562"]
    end

    M --> T --> P

    style MONGO fill:#FF6B35,color:#fff
    style ETL fill:#FFA500,color:#fff
    style PGSQL fill:#0066CC,color:#fff
```
