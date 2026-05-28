# CLAUDE.md — Airline Data Engineering Project

Project-level instructions for Claude Code when working in this repository.

> Cross-cutting policies (no worktrees, no Co-Authored-By, secrets handling, etc.) live in the **global** CLAUDE.md. This file covers only what's specific to the airline-data-platform project.

---

## Project Overview

**Airline Data Engineering Platform** — A modern, cloud-style data pipeline that ingests flight and airline data from the Lufthansa API, transforms it, and serves it via analytics dashboards and REST APIs.

**Main Stack:**
- **Sources**:
  - Lufthansa API — ❌ closed, no API key obtained (see ADR 004)
  - OpenSky Network (OAuth2, ICAO codes) — ✅ Active locally (see ADR 004/005)
  - adsb.lol (no auth, ICAO24 hex) — ✅ Active (see ADR 003)
- **Ingestion**: Python collectors (currently run locally; future: dedicated cloud VM, see ADR 007)
- **Bronze / Raw Landing Zone**: **MongoDB Atlas** `airline_landing` (see ADR 006). May be replaced later by a different bronze store.
- **Silver / Analytics Warehouse**: managed serverless Postgres — **Neon is the leading candidate, Pavel evaluating** (see ADR 007). Decision not yet final.
- **Transformation**: Python ETL + Pandas (Bronze → Silver)
- **API Layer**: FastAPI (Step 2)
- **Dashboards**: Streamlit / Dash
- **Compute**: dedicated cloud VM with fixed IP — planned, AWS EC2 (Free Tier) or Hetzner Cloud (see ADR 007). **Liora VM is no longer part of this project.**
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
├── 01-requirements/          # Project context, architecture, timeline
│   ├── a-source/            # Original PDF, mentor updates
│   ├── b-requirements/       # Project description, timeline, scope
│   └── c-architecture/       # Architecture diagrams, ADRs, data flows, ERD
├── 02-api-docs/              # API documentation & market overview
│   ├── LH_public_API_swagger_2_0.json  # Lufthansa Swagger spec
│   ├── opensky_api_doc.md              # OpenSky technical spec
│   ├── adsb_lol_api_doc.md             # adsb.lol technical spec (Phase 2)
│   └── airline_api_market_overview.md  # API comparison matrix
├── 03-data-collection/       # Python tools for data ingestion (+ own README)
│   ├── opensky_api/          # OpenSky API client (OAuth2)
│   ├── collectors/           # adsb_collector, opensky_collector
│   ├── db/                   # postgres/, mongo/
│   ├── collect_adsb.ipynb    # ADS-B collector walkthrough
│   ├── collect_opensky.ipynb # OpenSky collector walkthrough
│   └── explore_*.ipynb       # Exploration notebooks per source / Mongo landing zone
├── 04-dashboard/             # Streamlit dashboard (code)
├── docs/                     # Cross-cutting operational/engineering docs (see below)
├── requirements.txt          # Pinned Python dependencies
└── CLAUDE.md                 # This file
```

### Documentation layout

Three homes for docs, by audience and lifespan — keep them separate:

- **Numbered folders (`01-`, `02-`)** — bootcamp **phase deliverables**. Evaluators navigate these; do not reorganize them mid-project.
- **`docs/`** — **cross-cutting operational/engineering docs** that belong to no single phase (setup, access runbooks, infra). Has its own index `docs/README.md`.
- **Module `README.md`** — "how to run *this* module", co-located in each code dir (`03-data-collection/README.md`).

Rule of thumb: phase-specific → numbered folder; operates the running system → `docs/`; describes one code module → that module's README. Learning artefacts (bootcamp theory, not project docs) do **not** belong in this repo — they go to `knowledgebase/methodology/`.

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

Seit 2026-05-27 ist dieses Projekt **nicht mehr** an Liora_VM gebunden (siehe ADR 007). Geplante Infrastruktur:

- **Bronze (Landing Zone):** MongoDB Atlas Cluster `mongo-mk1` (Free Tier, eu-west-1) — `mongodb+srv://...mongo-mk1.ptb1k2b.mongodb.net/...`. Connection-String in `.env` (Projekt-Root).
- **Silver (Warehouse):** managed serverless Postgres — Neon ist führender Kandidat, **Pavel evaluiert noch**. Connection-String kommt nach Entscheidung in `.env`.
- **Compute (dedicated VM mit fester IP):** offen — AWS EC2 Free Tier (favorisiert wegen AWS SAA-Lernziel) oder Hetzner Cloud.
- **Lokale Entwicklung:** Mac mit `.venv` + `MONGO_URI` aus `.env` zeigt auf Atlas. Collectors laufen lokal, schreiben direkt nach Atlas.

**Atlas Network Access:** jede Compute-IP (Mac, neue VM) muss in der Atlas-Whitelist stehen. Symptom bei fehlender Whitelist: `pymongo.errors.ServerSelectionTimeoutError: SSL handshake failed: ... TLSV1_ALERT_INTERNAL_ERROR` (siehe `knowledgebase/troubleshooting.md`).

---

## Quick Start

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Kernel für JupyterLab / VS Code registrieren (einmalig pro Rechner)
python -m ipykernel install --user --name airline-data-platform --display-name "airline-data-platform"
```

In VS Code: Kernel-Dialog → **Python Environments... → airline-data-platform** auswählen.  
Falls `.venv` nach einer Projekt-Umbenennung kaputt ist (Symptom: `bad interpreter`): `rm -rf .venv` und obige Schritte wiederholen.

### VS Code MongoDB Extension

**MongoDB for VS Code** (official MongoDB extension) ist installiert und verbunden.
Verbindung via SRV-URI in Command Palette: `Cmd+Shift+P` → `MongoDB: Connect` → `Connect with Connection String`.
Playground (`Create playground`) ermöglicht Ad-hoc-Queries direkt gegen `airline_landing`.
Onboarding-Details und alle DB-User: `docs/mongodb-access.md`.

### Exploration Notebooks

Naming convention: `explore_<quelle>.ipynb` in `03-data-collection/`.

| Notebook | Quelle |
|---|---|
| `explore_lh_api.ipynb` | Lufthansa API (Mock) |
| `explore_opensky_api.ipynb` | OpenSky Network |
| `explore_adsb_lol.ipynb` | adsb.lol API |
| `explore_mongo_vm.ipynb` | MongoDB Landing Zone — beide Collections (`adsb_raw` + `opensky_raw`) inkl. Cross-Collection Join (Sektionen 9–11) |

### Demo with Mock Data (no credentials needed)

```bash
cd 03-data-collection
python demo.py
```

This runs collectors with mock Lufthansa API responses.

### Active Collectors (Phase 2)

```bash
cd 03-data-collection

# ADS-B — single run (or --interval 60 for continuous):
python collectors/adsb_collector.py

# OpenSky — local Mac only; last 24h by default:
python collectors/opensky_collector.py
python collectors/opensky_collector.py --mock   # no credentials needed
python collectors/opensky_collector.py --hours 6

# Educational step-by-step notebooks:
# collect_adsb.ipynb, collect_opensky.ipynb
```

`airports_collector.py` and `airlines_collector.py` are **deprecated** (LH API key never obtained).
Credentials (`OPENSKY_CLIENT_ID/SECRET`, `MONGO_URI`) are read from `.env` **at the project root** (`airline-data-platform/.env`) — not from `03-data-collection/.env` as it was historically. `python-dotenv` finds the project-root file via parent-directory search.

### Cross-Collection Join: ADS-B ↔ OpenSky

Join-Key: `adsb_raw.ac[].hex` = `opensky_raw.flights[].icao24` (ICAO24 Transponderadresse, identisch)

- **ADS-B** liefert: Echtzeit-Position, Höhe, Geschwindigkeit, Flugzeugtyp (Momentaufnahme)
- **OpenSky** ergänzt: Abflug- / Zielflughafen, Callsign, Abflugzeit (historisches Zeitfenster)
- Match-Rate naturgemäß gering (ADS-B = Snapshot, OpenSky = Zeitfenster) — mit wachsender OpenSky-History steigt die Rate
- Implementiert in `explore_mongo_vm.ipynb` Sektion 11

---

## Key Files

| File | Purpose |
|---|---|
| `01-requirements/b-requirements/project_description_doc.md` | Executive summary, timeline, milestones |
| `01-requirements/c-architecture/architecture_m.md` | Architecture diagrams, layer descriptions |
| `02-api-docs/airline_api_market_overview.md` | API market comparison & integration status |
| `02-api-docs/LH_public_API_swagger_2_0.json` | Full Lufthansa API specification |
| `02-api-docs/opensky_api_doc.md` | OpenSky API technical reference |
| `02-api-docs/adsb_lol_api_doc.md` | adsb.lol API technical reference (Phase 2) |
| `03-data-collection/lufthansa_api/client.py` | LH API client (mock only) |
| `03-data-collection/opensky_api/client.py` | OpenSky API client (OAuth2, mock/real) |
| `03-data-collection/collectors/adsb_collector.py` | ADS-B collector → MongoDB adsb_raw |
| `03-data-collection/collectors/opensky_collector.py` | OpenSky collector → MongoDB opensky_raw (local only) |
| `03-data-collection/collectors/airports_collector.py` | ⚠️ DEPRECATED (LH API) — rewrite planned |
| `03-data-collection/collectors/airlines_collector.py` | ⚠️ DEPRECATED (LH API) — not replaced |
| `03-data-collection/db/mongo/connector.py` | MongoDB connector (insert_raw, insert_adsb_snapshot) |
| `03-data-collection/db/postgres/schema.sql` | PostgreSQL schema (airports, airlines, flights) |
| `03-data-collection/demo.py` | Mock data collector for testing |

---

## Architectural Decisions (ADRs)

ADRs are tracked in `01-requirements/adr/`:

- **ADR 001** — PostgreSQL first, MongoDB deferred to Phase 2.
- **ADR 002** — `psycopg2-binary` as PostgreSQL driver. Raw SQL over ORM for transparency.
- **ADR 003** — Dual-stream ADS-B: adsb.lol (free, ODbL) + OpenSky into MongoDB landing zone.
- **ADR 004** — MongoDB as multi-source landing zone hub. No LH key; OpenSky runs locally only (VM blocked); adsb.lol is the only VM-side live source.
- **ADR 005** — OpenSky pipeline migration: Phase-1 PostgreSQL schema-at-ingest → Phase-2 raw JSON per API call into MongoDB opensky_raw.

---

## Architectural Principles

These are working assumptions, not yet promoted to ADRs:

- **ETL, not ELT (for now)** — transform in Python before loading. May move to ELT (dbt in warehouse) later.
- **PostgreSQL for analytics** — Star Schema, SQL queries, BI-friendly.
- **Batch-first** — periodic ingestion (nightly). Streaming (Kafka) only if needed.
- **API contracts first** — the Lufthansa Swagger spec drives schema design and collector code.

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
