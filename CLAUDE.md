# CLAUDE.md — Airline Data Engineering Project

Project-level instructions for Claude Code when working in this repository.

> Cross-cutting policies (no worktrees, no Co-Authored-By, secrets handling, etc.) live in the **global** CLAUDE.md. This file covers only what's specific to the airline-data-platform project.

---

## Project Overview

**Airline Data Engineering Platform** — A modern, cloud-style data pipeline that ingests flight and airline data from the Lufthansa API, transforms it, and serves it via analytics dashboards and REST APIs.

**Main Stack:**
- **Sources**:
  - Lufthansa API (OAuth2, IATA codes) — ⚠️ Mock only, no API key available (see ADR 004)
  - OpenSky Network (OAuth2, ICAO codes) — ✅ Active locally (VM blocked, see ADR 004/005)
  - adsb.lol (no auth, ICAO24 hex) — ✅ Active on VM (see ADR 003)
- **Ingestion**: Python collectors
- **Raw Storage**: MongoDB landing zone (`airline_landing`) — multi-source hub (see ADR 004)
- **Transformation**: Python ETL + Pandas
- **Analytics Storage**: PostgreSQL (Star Schema)
- **API Layer**: FastAPI
- **Dashboards**: Streamlit / Dash
- **Orchestration**: Airflow / Cron (optional)
- **Streaming**: Kafka (optional)

**Project Status**: Step 1 (Data Discovery & Organization) — deadline 20.05.2026

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
├── 03-data-collection/       # Python tools for data ingestion
│   ├── lufthansa_api/        # LH API client (mock only — no key)
│   ├── opensky_api/          # OpenSky API client (OAuth2)
│   ├── collectors/           # adsb_collector, opensky_collector (active); airports/airlines (deprecated)
│   ├── db/                   # postgres/, mongo/
│   ├── collect_adsb.ipynb    # ADS-B collector walkthrough
│   ├── collect_opensky.ipynb # OpenSky collector walkthrough
│   ├── explore_*.ipynb       # Exploration notebooks per source
│   └── demo.py               # Demo script (no credentials needed)
├── requirements.txt          # Pinned Python dependencies
└── CLAUDE.md                 # This file
```

---

## Data Pipeline Architecture

```
Phase 2 — Ingestion (current, see ADR 004):

  adsb.lol (live ADS-B, VM cron)  →  MongoDB airline_landing.adsb_raw      ┐
  OpenSky API (local Mac only)    →  MongoDB airline_landing.opensky_raw   ├→ ETL → PostgreSQL (curated)
  Kaggle / reference data         →  MongoDB airline_landing.kaggle_* / airports_ref ┘

Phase 3 — Transformation (planned):
  ETL reads from MongoDB collections → normalises → loads PostgreSQL Star Schema

Phase 4 — Serving (planned):
  FastAPI endpoints + Streamlit/Dash dashboards read from PostgreSQL

Phase 5 — Orchestration (planned):
  Airflow DAGs or cron jobs; optional Kafka for real-time streams
```

**Key Principle:** MongoDB is the raw landing zone (schema-on-read, one document per API call).
PostgreSQL is the curated analytical warehouse (schema-on-write, Star Schema).

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

## Liora VM — Infrastruktur

Die Liora VM ist eine AWS EC2-Instanz (Ubuntu). SSH-Zugang via:

```bash
ssh Liora_VM
# Config: ~/.ssh/config → Host Liora_VM, User ubuntu, IdentityFile ~/.ssh/data_enginering_machine.pem
```

Claude kann selbst `ssh Liora_VM <befehl>` ausführen — der Key liegt lokal und der Alias ist in `~/.ssh/config` eingetragen.

**Laufende Docker Container:**
- `pg_container` — `postgres:16-alpine`, Port `5432`
- `pgadmin4_container` — pgAdmin 4, Port `5050`
- `mongo_container` — `mongo:7-jammy`, Port `27017`, Volume `mongo_data`, gestartet mit `--auth`

`dpkg -l | grep postgres` findet nichts — immer `docker ps` zur Prüfung verwenden.

**MongoDB-Verbindung** (Phase 2 Landing Zone):
```
MONGO_URI=mongodb://<user>:<pass>@liora-vm.matthiaskoehler.com:27017/<db>?authSource=admin
MONGO_DB=airline_landing
```
`authSource=admin` ist zwingend — der User ist in der `admin`-DB angelegt, ohne diesen Parameter schlägt die Auth fehl. Credentials in `.env` (lokal, nicht committed).

### VM Neustart — IP-Update-Prozedur

Die VM bekommt bei jedem Neustart eine neue öffentliche IP. Ein Cloudflare-DDNS-Updater auf der VM trägt die neue IP automatisch ein.

**`DB_HOST` und `~/.ssh/config` müssen nicht manuell angepasst werden** — beide nutzen den Hostnamen `liora-vm.matthiaskoehler.com`.

Nach einem Neustart ~1–2 Minuten warten, bis Cloudflare aktualisiert ist, dann normal verbinden:

```bash
ssh Liora_VM "docker ps"
```

Wenn SSH sich mit "Host key verification failed" beschwert (alter Host-Key gecacht): `ssh-keygen -R liora-vm.matthiaskoehler.com` → neu verbinden.

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

### Exploration Notebooks

Naming convention: `explore_<quelle>.ipynb` in `03-data-collection/`.

| Notebook | Quelle |
|---|---|
| `explore_lh_api.ipynb` | Lufthansa API (Mock) |
| `explore_opensky_api.ipynb` | OpenSky Network |
| `explore_adsb_lol.ipynb` | adsb.lol API |
| `explore_mongo_vm.ipynb` | MongoDB Landing Zone (Liora VM) |

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

# OpenSky — local Mac only (VM blocked); last 24h by default:
python collectors/opensky_collector.py
python collectors/opensky_collector.py --mock   # no credentials needed
python collectors/opensky_collector.py --hours 6

# Educational step-by-step notebooks:
# collect_adsb.ipynb, collect_opensky.ipynb
```

`airports_collector.py` and `airlines_collector.py` are **deprecated** (LH API key never obtained).
Credentials (OPENSKY_CLIENT_ID/SECRET, MONGO_URI) are read from `.env`, never committed.

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
