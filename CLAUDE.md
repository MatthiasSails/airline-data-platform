# CLAUDE.md — Airline Data Engineering Project

Project-level instructions for Claude Code when working in this repository.

> Cross-cutting policies (no worktrees, no Co-Authored-By, secrets handling, etc.) live in the **global** CLAUDE.md. This file covers only what's specific to the airline-data-platform project.

---

## Project Overview

**Airline Data Engineering Platform** — A modern, cloud-style data pipeline that ingests live flight data from ADS-B and OpenSky sources, transforms it, and serves it via analytics dashboards and REST APIs.

**Main Stack:**
- **Sources**:
  - OpenSky Network (OAuth2, ICAO codes) — ✅ Active locally (see ADR 004/005)
  - adsb.lol (no auth, ICAO24 hex) — ✅ Active (see ADR 003)
- **Ingestion**: Python collectors (currently run locally; future: dedicated cloud VM, see ADR 007)
- **Bronze / Raw Landing Zone**: **MongoDB Atlas** `airline_landing` (see ADR 006). May be replaced later by a different bronze store.
- **Silver / Analytics Warehouse**: managed serverless Postgres — **Neon is the leading candidate, Pavel evaluating** (see ADR 007). Decision not yet final.
- **Transformation**: Python ETL + Pandas (Bronze → Silver)
- **API Layer**: FastAPI (Step 2)
- **Dashboards**: Streamlit / Dash
- **Compute**: **AWS Lightsail `aws-airline-1`** (`63.185.229.117`, eu-central-1a) — provisioned 2026-06-05 (see ADR 007). **Liora VM is no longer part of this project.**
- **Orchestration**: Airflow / Cron (optional, Step 3)
- **Streaming**: open — vision is sub-minute updates, exact tooling TBD

**Project Status**: Step 1 complete (Atlas migration 2026-05-27). Step 2 (FastAPI + Analytics Endpoints) — deadline 10.06.2026.

---

## Branching

- `main` = stable, deployable state
- `feature/<topic>` branches for larger changes
- Use Markdown + Mermaid for any new diagrams

---

## Directory Structure

```
airline-data-platform/
├── docs/                     # KNOWLEDGE layer (project-wide, un-numbered)
│   ├── requirements/         # scope.md, timeline.md, source/ (original PDF, mentor updates)
│   ├── adr/                  # Architecture Decision Records (001–009)
│   ├── architecture/         # data-flow.md, silver-layer-er.md, diagrams
│   ├── data-sources/         # external API references (OpenSky, adsb.lol, market overview)
│   ├── report/               # DataScientest final project report
│   ├── setup.md              # local setup runbook
│   └── mongodb-access.md     # Atlas access / DB users
├── 01-data-collection/       # Collectors → BRONZE (MongoDB)  (+ own README)
│   ├── opensky_api/          # OpenSky API client (OAuth2)
│   ├── collectors/           # adsb_collector, opensky_collector, flight_tracker
│   ├── db/mongo/             # MongoDB connector + landing-zone docs
│   ├── collect_*.ipynb       # collector walkthroughs
│   └── explore_*.ipynb       # exploration notebooks per source / Mongo landing zone
├── 02-data-modeling/         # BRONZE → SILVER
│   ├── etl/                  # Bronze → Silver transforms (to be implemented)
│   └── warehouse/            # PostgreSQL star schema: schema.sql, connector.py
├── 03-data-consumption/      # api/ (FastAPI) + dashboard/ (Streamlit)
├── 04-deployment/            # docker-compose, scheduler, orchestration
├── requirements.txt          # Pinned Python dependencies
└── CLAUDE.md                 # This file
```

### Documentation layout

Two axes — keep them separate (this is the whole point of the layout):

- **`docs/` = knowledge layer** — everything *about the whole project*: requirements, ADRs, architecture, data-source references, the report. Project-wide, un-numbered. Has its own index `docs/README.md`. (Mirrors the global rule "Git = knowledge layer, Projects V2 = workflow layer".)
- **Numbered folders (`01-`–`04-`) = pipeline phases (code)** — each number is one stage of the Bronze→Silver→consumption→deployment pipeline. The medallion is readable: `01` = Bronze ingest, `02` = Silver.
- **Module `README.md`** — "how to run *this* module", co-located in each code dir (e.g. `01-data-collection/README.md`).

Rule of thumb: about the whole project → `docs/`; a pipeline stage's code → its numbered folder; how to run one module → that module's README. **Project progress/tracking is GitHub Projects V2, not a repo file.** Learning artefacts (bootcamp theory, not project docs) do **not** belong in this repo — they go to `knowledgebase/methodology/`.

---

## Data Pipeline Architecture

```
Phase 2 — Ingestion (current, see ADR 004 + ADR 006):

  adsb.lol (live ADS-B)           →  MongoDB Atlas airline_landing.adsb_raw      ┐
  OpenSky API (local Mac only)    →  MongoDB Atlas airline_landing.opensky_raw   ├→ ETL → Neon Postgres (Star Schema)
  Kaggle / reference data         →  MongoDB Atlas airline_landing.kaggle_* / airports_ref ┘

Phase 3 — Transformation (planned, see ADR 007):
  ETL reads from MongoDB Atlas → normalises → loads Silver Postgres Star Schema
  (Silver provider TBD — Neon leading candidate, Pavel evaluating)

Phase 4 — Serving (planned):
  FastAPI endpoints + Streamlit/Dash dashboards read from Silver Postgres

Phase 5 — Orchestration (planned):
  Cron / Airflow / Lambda — exact tooling TBD; sub-minute streaming as a stretch goal
```

**Key Principle:** MongoDB Atlas is the raw landing zone (schema-on-read, one document per API call).
The Silver layer is a managed serverless Postgres (curated analytical warehouse, schema-on-write, Star Schema) — provider not yet committed.

---

## Core Engineering Principles

- **Simplicity over complexity** — no overengineering for a learning project
- **Pragmatism over perfection** — focus on end-to-end pipeline first, optimization later
- **Clarity over cleverness** — readable code that others can understand
- **Explicitness** — avoid hidden magic, state assumptions clearly
- **Data quality matters** — garbage in = garbage out

---

## Coding Standards

**Language & Environment:**
- Python 3.12+
- Type hints preferred
- `pathlib` instead of `os.path`
- Environment variables via `.env` (see global CLAUDE.md for secrets policy)
- Logging instead of `print()`

**Preferred Libraries:**
- FastAPI (REST APIs)
- Pydantic (data validation)
- SQLAlchemy (database ORM)
- Pandas (data transformation)
- psycopg2-binary (PostgreSQL access, Phase 1)
- PyMongo (MongoDB access, Phase 2)

**Avoid:**
- Kubernetes (unnecessary at this scale)
- Complex microservices (keep it monolithic)
- Premature optimization
- Magic and implicit behavior

---

## Compute & Hosting

As of 2026-05-27 this project is **no longer** tied to Liora VM (see ADR 007). Planned infrastructure:

- **Bronze (Landing Zone):** MongoDB Atlas cluster `mongo-mk1` (Free Tier, eu-central-1). Connection string in `.env` at project root.
- **Silver (Warehouse):** managed serverless Postgres — Neon is the leading candidate, **Pavel evaluating**. Connection string goes into `.env` after decision.
- **Compute (dedicated VM with fixed IP):** **AWS Lightsail `aws-airline-1`** (provisioned 2026-06-05). DNS: `airline.matthiaskoehler.com`. Plan: $10/Mon (2 GB RAM, 2 vCPU, 60 GB SSD, x86_64), eu-central-1a. Docker 29.1 + Compose 2.40 installed. Dashboard live at http://airline.matthiaskoehler.com:8501 — entry point `04-deployment/docker-compose.yml`. Connection details (IP, SSH key, account) in local notes.
- **Local development:** Mac with `.venv` + `MONGO_URI` from `.env` pointing to Atlas. Collectors run locally, write directly to Atlas.

**Atlas Network Access:** every compute IP (Mac, new VM) must be whitelisted in the Atlas project. Symptom when missing: `pymongo.errors.ServerSelectionTimeoutError: SSL handshake failed: ... TLSV1_ALERT_INTERNAL_ERROR`.

---

## Quick Start

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# venv-internen Jupyter-Kernel registrieren (einmalig pro venv)
python -m ipykernel install --sys-prefix --name python3 --display-name ".venv"
```

**Kernel convention:** All notebooks use the **venv-internal kernel** (`kernelspec name: python3`, `display_name: .venv`, located at `.venv/share/jupyter/kernels/python3`). Always select the **`.venv`** kernel in VS Code / JupyterLab — do not install a separate `--user` kernel, or a second kernel entry will appear and notebooks show "kernel not found".  
If `.venv` is broken after a project rename (symptom: `bad interpreter`): `rm -rf .venv` and repeat the setup steps above.

### VS Code MongoDB Extension

**MongoDB for VS Code** (official MongoDB extension) is installed and connected.
Connect via SRV URI in the Command Palette: `Cmd+Shift+P` → `MongoDB: Connect` → `Connect with Connection String`.
Playground (`Create playground`) enables ad-hoc queries directly against `airline_landing`.
Onboarding details and all DB users: `docs/mongodb-access.md`.

### Exploration Notebooks

Naming convention: `explore_<source>.ipynb` in `01-data-collection/`.

| Notebook | Source |
|---|---|
| `explore_opensky_api.ipynb` | OpenSky Network |
| `explore_adsb_lol.ipynb` | adsb.lol API |
| `explore_mongo_atlas.ipynb` | MongoDB Atlas landing zone — all 3 collections (`adsb_raw`, `opensky_raw`, `flight_tracker_raw`) incl. cross-collection join (sec. 9–11) + flight_tracker exploration (sec. 12–14) |

### Active Collectors (Phase 2)

```bash
cd 01-data-collection

# ADS-B — single run (or --interval 60 for continuous):
python collectors/adsb_collector.py

# OpenSky — local Mac only; last 24h by default:
python collectors/opensky_collector.py
python collectors/opensky_collector.py --mock   # no credentials needed
python collectors/opensky_collector.py --hours 6

# Educational step-by-step notebooks:
# collect_adsb.ipynb, collect_opensky.ipynb
```

Credentials (`OPENSKY_CLIENT_ID/SECRET`, `MONGO_URI`, `MONGO_URI_RW`) are read from `.env` **at the project root** (`airline-data-platform/.env`) — not from a per-module `.env` as it was historically. `python-dotenv` finds the project-root file via parent-directory search. Collectors connect with `from_env(write=True)` (uses `MONGO_URI_RW`, the `airline-collector-rw` write user); read-only exploration uses `from_env()` (uses `MONGO_URI`, the `airline-reader-ro` user).

### Cross-Collection Join: ADS-B ↔ OpenSky

Join-Key: `adsb_raw.ac[].hex` = `opensky_raw.flights[].icao24` (ICAO24 Transponderadresse, identisch)

- **ADS-B** provides: real-time position, altitude, speed, aircraft type (snapshot)
- **OpenSky** adds: departure/destination airport, callsign, departure time (historical window)
- Match rate is naturally low (ADS-B = snapshot, OpenSky = time window) — increases as OpenSky history grows
- Implementiert in `explore_mongo_atlas.ipynb` Sektion 11

---

## Key Files

| File | Purpose |
|---|---|
| `docs/requirements/scope.md` | Deliverables per phase, explicit non-goals |
| `docs/architecture/README.md` | Architecture diagrams, layer descriptions |
| `docs/architecture/silver-layer-er.md` | Silver star-schema ER model (source of truth) |
| `docs/data-sources/airline_api_market_overview.md` | API market comparison & integration status |
| `docs/data-sources/opensky_api_doc.md` | OpenSky API technical reference |
| `docs/data-sources/adsb_lol_api_doc.md` | adsb.lol API technical reference (Phase 2) |
| `01-data-collection/opensky_api/client.py` | OpenSky API client (OAuth2, mock/real) |
| `01-data-collection/collectors/adsb_collector.py` | ADS-B collector → MongoDB adsb_raw |
| `01-data-collection/collectors/opensky_collector.py` | OpenSky collector → MongoDB opensky_raw (local only) |
| `01-data-collection/collectors/flight_tracker.py` | Single-flight tracker → MongoDB flight_tracker_raw |
| `01-data-collection/db/mongo/connector.py` | MongoDB connector (insert_raw, insert_adsb_snapshot) |
| `02-data-modeling/warehouse/schema.sql` | PostgreSQL schema (airports, airlines, flights) |

---

## Architectural Decisions (ADRs)

ADRs are tracked in `docs/adr/`:

- **ADR 001** — PostgreSQL first, MongoDB deferred to Phase 2.
- **ADR 002** — `psycopg2-binary` as PostgreSQL driver. Raw SQL over ORM for transparency.
- **ADR 003** — Dual-stream ADS-B: adsb.lol (free, ODbL) + OpenSky into MongoDB landing zone.
- **ADR 004** — MongoDB as multi-source landing zone hub. OpenSky runs locally only (VM blocked); adsb.lol is the only VM-side live source.
- **ADR 005** — OpenSky pipeline migration: Phase-1 PostgreSQL schema-at-ingest → Phase-2 raw JSON per API call into MongoDB opensky_raw.

---

## Architectural Principles

These are working assumptions, not yet promoted to ADRs:

- **ETL, not ELT (for now)** — transform in Python before loading. May move to ELT (dbt in warehouse) later.
- **PostgreSQL for analytics** — Star Schema, SQL queries, BI-friendly.
- **Batch-first** — periodic ingestion (nightly). Streaming (Kafka) only if needed.
- **API contracts first** — document the API response shape before writing collector code.

---

## Project Phases (Milestones)

| Phase | Deadline | Focus |
|---|---|---|
| **Step 1** | 20.05.2026 | Data Discovery & Organization — UML, DB architecture, sample datasets |
| **Step 2** | 10.06.2026 | Data Consumption & API — FastAPI, analytics endpoints, dashboards |
| **Step 3** | 16.06.2026 | Automation & Pipelines — Airflow, scheduled jobs, optional Kafka |
| **Step 4** | 02.07.2026 | Deployment & Frontend — Docker Compose, CI/CD, Streamlit/Dash |
| **Final Defense** | 20.07.2026 | Architecture presentation & live demo |

Current focus: **Step 1** — data collection and architecture design.

---

## Project Report

The DataScientest final report lives in [`docs/report/`](docs/report/). Guidance:

- **Follow the "Crypto-arc"** — the structure of the gold-standard DE reference report (13-chapter
  narrative: Introduction → Architecture → Data Collection → Data Modeling → Data Consumption → API →
  Containerisation → Orchestration → Results → Limitations → Conclusion), **not** the ML-centric
  Google-Doc methodology template.
- **No ML chapter** — this is a pure data-engineering pipeline (live OpenSky States → Bronze → Silver).
  Replace the modelling chapter with deeper Silver-modeling coverage (mentor confirmed ML is
  de-prioritised; see Mentor Context below).
- **Reference exemplars** (read-only) are stored locally — a gold-standard DE report (13-chapter narrative) and an airlines-domain example (WIP / earlier cohort).

---

## When in Doubt

Ask:
- Is this change moving the project closer to the Step 1 deadline?
- Is this the simplest way to solve the problem?
- Does this change require documentation (ADR/RFC)?
- Can I explain this decision to a non-technical person?

---

## Mentor Context

**Mentor**: Nicolas ("NicoTheDataSherpa")

**Key Guidance**:
- ML performance is NOT the evaluation criterion — Data Engineering mastery is.
- Suggest ML effort: 1–2 days maximum.
- Focus on end-to-end pipeline and architecture reasoning.

**Evaluation Focus**:
- Data architecture quality
- Data modeling (SQL + NoSQL)
- ETL pipeline design
- API design and documentation
- Automation and orchestration
- Docker deployment
- Engineering reasoning and explanations
