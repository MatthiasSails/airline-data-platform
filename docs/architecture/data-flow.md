# Airline Data Flow Architecture

# High-Level Goal

Build a pragmatic and understandable Data Engineering platform for airline data.

Main design goals:
- simple
- reproducible
- dockerized
- explainable
- extensible

---

# Medallion Layers (Bronze → Silver → Gold?)

The platform follows a **medallion** structure. *Ingestion ≠ modeling* (ADR 004): the landing zone
keeps every source raw; the curated model promotes only what it needs.

| Layer | Store | Role | Contents |
|---|---|---|---|
| **Bronze** | MongoDB Atlas | raw landing zone — all sources, untransformed | OpenSky States, OpenSky AircraftDB, OpenFlights, OurAirports, **adsb.lol** |
| **Silver** | PostgreSQL (Neon) | curated relational star schema | `fact_states` + `dim_aircraft`, `dim_airlines`, `dim_airports` |
| **Gold?** | (deferred) | aggregates / marts / materialized views | e.g. `aircraft_current_state` — not built yet |

- **adsb.lol lives only in Bronze** — collected for optionality and a later OpenSky-vs-adsb.lol
  data-quality comparison, **not promoted** to Silver (see [ADR 009](../adr/009-states-api-silver-model.md)).
- The Silver model is OpenSky **States-centric**: the central fact is live "aircraft in the air"
  observations from `/states/all`. Source of truth = [`silver-layer-er.md`](silver-layer-er.md),
  [ADR 008](../adr/008-airline-attribution-star-schema.md), [ADR 009](../adr/009-states-api-silver-model.md).
- A "Gold" layer (BI-facing aggregates) is a future option, not part of the MVP.

---

# High-Level Data Flow

External APIs (OpenSky States + static reference feeds)
        ↓
Data Collector Services
        ↓
Bronze — Raw JSON Storage (MongoDB Atlas)
        ↓
ETL / Transformation
        ↓
Silver — Curated Star Schema (PostgreSQL / Neon)
        ↓
FastAPI
        ↓
Dashboards / Analytics / ML

---

# MongoDB Role (Bronze)

MongoDB acts as:
- raw landing zone (Bronze layer)
- ingestion buffer
- schema-flexible storage

Why MongoDB:
- APIs return nested JSON
- minimal preprocessing needed
- preserves original payloads
- easier debugging
- supports schema evolution

Typical stored data (raw, all sources):
- OpenSky States (`/states/all` live state vectors)
- OpenSky AircraftDB (`aircraftDatabase.csv`)
- OpenFlights airlines (`airlines.dat`)
- OurAirports (`airports.csv`)
- adsb.lol raw snapshots (Bronze-only — not promoted to Silver)

---

# PostgreSQL Role (Silver)

PostgreSQL acts as:
- curated warehouse — **Silver layer** star schema
- analytics layer
- relational reporting database

Why PostgreSQL:
- SQL analytics
- joins
- aggregations
- stable schema
- BI-friendly

Typical tables (star schema — see [`silver-layer-er.md`](silver-layer-er.md)):
- fact_states   (live "aircraft in the air" from OpenSky `/states/all` — central fact)
- dim_aircraft  (OpenSky AircraftDB — joined via `icao24`)
- dim_airlines  (OpenFlights — joined via resolved `airline_icao`)
- dim_airports  (OurAirports — **standalone reference, unjoined**: from/to unknown in Silver)

(Note: no `fact_flights` / `fact_delays`. The live States feed carries no scheduled-vs-actual times
and no origin/destination, so delay analytics and route from/to are out of scope for Silver —
deferred as a future Bronze-layer concern. See [ADR 009](../adr/009-states-api-silver-model.md).)

---

# ETL Layer

Responsibilities:
- normalize JSON
- validate data
- deduplicate records
- transform timestamps
- create dimensions/facts
- aggregate metrics

Possible technologies:
- Python
- Pandas
- SQLAlchemy

---

# API Layer

Technology:
- FastAPI

Responsibilities:
- expose analytics
- provide REST endpoints
- support dashboard frontend
- serve ML predictions

Possible endpoints:
- /states      (live aircraft positions/state vectors — backed by `fact_states`)
- /aircraft    (airframe lookup — `dim_aircraft`)
- /airlines    (airline reference — `dim_airlines`)
- /airports    (airport reference — `dim_airports`, standalone)
- /predictions

(Out of scope for Silver: route from/to and delay endpoints — the live States feed has no
origin/destination or scheduled-vs-actual times. A future Bronze-layer scheduled-flight source
would be needed first.)

---

# Dashboard Layer

Possible technologies:
- Dash
- Plotly
- Streamlit

Potential features:
- live position maps (aircraft in the air, from `fact_states`)
- airline KPIs (by resolved `airline_icao`)
- aircraft / fleet breakdowns (by type, operator)
- airport reference lookups

(Out of scope for Silver: route maps and delay analytics — no origin/destination or
scheduled-vs-actual times in the live States feed; deferred to a future Bronze-layer source.)

---

# Optional Future Extensions

## Kafka

Possible use:
- streaming ingestion
- event pipelines
- real-time updates

Not required initially.

---

## Spark

Possible use:
- distributed processing
- larger datasets

Likely overkill for MVP.

---

## Neo4j

Possible use:
- route network analysis
- airport graph exploration

Example:
Airport → Route → Airport relationships

Optional extension.

---

# Deployment Strategy

Primary target:
Docker Compose

Services:
- mongodb
- postgres
- fastapi
- dashboard
- scheduler

Goal:
Simple local reproducible setup.

---

# Engineering Philosophy

Prefer:
- understandable systems
- reproducible pipelines
- small deployable services
- simple operations

Avoid:
- premature distributed systems
- unnecessary cloud complexity
- Kubernetes too early