# CLAUDE.md — Airline Data Engineering Project

Project-level instructions for Claude Code when working in this repository.

> Cross-cutting policies (no worktrees, no Co-Authored-By, secrets handling, etc.) live in the **global** CLAUDE.md. This file covers only what's specific to the airline-data-platform project.

---

## Project Overview

**Airline Data Engineering Platform** — A modern, cloud-style data pipeline that ingests flight and airline data from the Lufthansa API, transforms it, and serves it via analytics dashboards and REST APIs.

**Main Stack:**
- **Sources**:
  - Lufthansa API (OAuth2, IATA codes) — ⚠️ Mock only, registration blocked
  - OpenSky Network (OAuth2, ICAO codes) — ✅ Active in Phase 1
  - adsb.lol (no auth, ICAO24 hex) — ✅ Active (Phase 2, see ADR 003)
- **Ingestion**: Python collectors
- **Raw Storage**: PostgreSQL direct (Phase 1) → MongoDB landing zone (Phase 2, see ADR 001)
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
│   ├── lufthansa_api/        # LH API client (mock + real mode)
│   ├── opensky_api/          # OpenSky API client (OAuth2)
│   ├── collectors/           # airports_collector, airlines_collector, flights_collector
│   ├── db/                   # postgres/, mongo/ (Phase 2)
│   ├── explore_lh_api.ipynb  # LH interactive exploration
│   ├── explore_opensky_api.ipynb  # OpenSky interactive exploration
│   └── demo.py               # Demo script (no credentials needed)
├── requirements.txt          # Pinned Python dependencies
└── CLAUDE.md                 # This file
```

---

## Data Pipeline Architecture

```
Step 1: Collection (Phase 1 — current)
  ↓
Lufthansa API (IATA) + OpenSky (ICAO)
  ↓
PostgreSQL directly (ADR 001: MongoDB deferred to Phase 2)

Step 1b: Collection (Phase 2 — planned, see ADR 003)
  ↓
Lufthansa API (IATA)    → MongoDB (raw)  ┐
OpenSky API (ICAO)      → PostgreSQL     ├→ ETL → PostgreSQL (curated)
adsb.lol API (ICAO24)   → MongoDB (raw)  ┘
  ↓
IATA↔ICAO mapping table joins airports (LH) with flights (OpenSky/adsb.lol)

Step 2: Transformation (Python ETL)
  ↓
Extract nested JSON → Normalize → Validate → PostgreSQL

Step 3: Storage (Analytical Warehouse)
  ↓
PostgreSQL (airports table, airlines table, Star Schema)

Step 4: Serving
  ↓
FastAPI endpoints (/api/airports, /api/airlines, etc.)
Streamlit/Dash dashboards (analytics, KPIs)

Step 5: Orchestration (future)
  ↓
Airflow DAGs or Cron jobs (scheduled ingestion & transformation)
Optional: Kafka for real-time event streams
```

**Key Principle:** Separation of OLTP (operational) from OLAP (analytical) storage.
PostgreSQL = curated warehouse (schema-on-write). MongoDB as landing zone deferred to Phase 2 (see ADR 001).

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

### Real Data Collection (with credentials)

```bash
export LH_CLIENT_ID="your_id"
export LH_CLIENT_SECRET="your_secret"
python collectors/airports_collector.py
python collectors/airlines_collector.py
```

Credentials are read from environment, never committed to git.

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
| `03-data-collection/lufthansa_api/client.py` | LH API client (OAuth2, mock/real modes) |
| `03-data-collection/opensky_api/client.py` | OpenSky API client (OAuth2) |
| `03-data-collection/collectors/airports_collector.py` | Airports data ingestion (LH → PG) |
| `03-data-collection/collectors/airlines_collector.py` | Airlines data ingestion (LH → PG) |
| `03-data-collection/db/postgres/schema.sql` | PostgreSQL schema (airports, airlines, flights) |
| `03-data-collection/demo.py` | Mock data collector for testing |

---

## Architectural Decisions (ADRs)

ADRs are tracked in `01-requirements/c-architecture/`:

- **ADR 001** — PostgreSQL first, MongoDB deferred to Phase 2. Direct DB write for Phase 1; two-layer raw/curated architecture comes later.
- **ADR 002** — `psycopg2-binary` as PostgreSQL driver. Raw SQL over ORM for transparency and learning value.
- **ADR 003** — Dual-stream ADS-B strategy (Phase 2). Use **adsb.lol** (free, open-source, ODbL) instead of ADSBExchange RapidAPI ($10/mo, non-commercial only). Combines OpenSky (structured flight legs) + adsb.lol (raw live positions) into MongoDB landing zone.

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
