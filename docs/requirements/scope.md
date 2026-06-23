# Scope — What We Will Deliver

Concrete deliverables per phase, with explicit non-goals.

> Timeline and milestones: see [timeline.md](timeline.md).
> Architecture and decisions: see [architecture/](../architecture/) and [adr/](../adr/).

---

## Step 1 — Data Discovery & Organization
**Deadline:** 20.05.2026

**In scope:**
- Live flight data collection into a MongoDB Atlas landing zone (Bronze): OpenSky `/states/all`
  (Frankfurt bounding box, ~150×150 km) and adsb.lol ADS-B
- OpenSky collected via a local script — external VMs block OpenSky egress (see [ADR 005](../adr/005-opensky-mongo-migration.md))
- Cross-collection join exploration: ADS-B ↔ OpenSky via ICAO24 transponder address
- PostgreSQL warehouse schema design (later revised to the States-centric star schema — [ADR 008](../adr/008-airline-attribution-star-schema.md) / [ADR 009](../adr/009-states-api-silver-model.md))
- Streamlit dashboard (live)
- UML / ERD and data-source documentation

**Out of scope:**
- Lufthansa API integration (no key available — see [ADR 004](../adr/004-mongo-as-multisource-hub.md))
- OpenSky from the deployment VM (OpenSky blocks the VM's egress — local-only collector, see [ADR 005](../adr/005-opensky-mongo-migration.md))

---

## Step 2 — Data Consumption & API
**Deadline:** 10.06.2026

**In scope:**
- FastAPI backend with `/states`, `/aircraft`, `/airlines`, `/airports` endpoints (no route/delay endpoints — see [ADR 009](../adr/009-states-api-silver-model.md))
- ETL pipeline: MongoDB raw → PostgreSQL curated
- IATA ↔ ICAO mapping table (from OurAirports.com)
- Dashboard reads from FastAPI (not directly from DBs)

**Out of scope:**
- Production-grade ML model — mentor approved skipping or using Kaggle dataset

---

## Step 3 — Automation & Pipelines
**Deadline:** 16.06.2026

**In scope:**
- Scheduled ADS-B collection (cron or Airflow)
- Batch ETL pipeline scheduled
- Documentation of pipeline operations

**Out of scope (unless time permits):**
- Kafka streaming (only if MVP is stable)

---

## Step 4 — Deployment & Frontend
**Deadline:** 02.07.2026

**In scope:**
- Docker Compose stacks for the app services (dashboard, ETL, API, landing) via Portainer GitOps — MongoDB Atlas and Supabase Postgres are managed, not containerized
- CI pipeline: lint + unit tests + Docker build (`ci.yaml`)
- Release pipeline: + DockerHub push on `main` (`release.yaml`)
- Unit tests for API code

---

## Final Defense
**Deadline:** 20.07.2026

**In scope:**
- Architecture presentation (why MongoDB + PostgreSQL, ETL strategy, automation)
- Live demo of dashboard + API
- Defense of design decisions (see [adr/](../adr/))

---

## Project-Wide Non-Goals

These were considered and explicitly excluded:

| Non-goal | Why | Reference |
|---|---|---|
| Machine learning as a core feature | Mentor: ML performance not evaluated | [source/mentor_update_nicolas.md](source/mentor_update_nicolas.md) |
| Lufthansa API as data source | No API key available; Liora cannot provide | [ADR 004](../adr/004-mongo-as-multisource-hub.md) |
| Kubernetes deployment | Docker Compose sufficient for MVP | — |
| Real-time Kafka streaming | Only if MVP is stable and time permits | — |
| Neo4j route graph | Out of scope; mentioned as future extension | — |
