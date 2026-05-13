# CLAUDE.md — Airline Data Engineering Project

Project-level instructions for Claude Code when working in this repository.

> Cross-cutting policies (no worktrees, no Co-Authored-By, secrets handling, etc.) live in the **global** CLAUDE.md. This file covers only what's specific to the airline-data-platform project.

---

## Project Overview

**Airline Data Engineering Platform** — A modern, cloud-style data pipeline that ingests flight and airline data from the Lufthansa API, transforms it, and serves it via analytics dashboards and REST APIs.

**Main Stack:**
- **Source**: Lufthansa API (OAuth2)
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
│   └── c-architecture/       # Architecture diagrams, data flows, ERD
├── 02-api-docs/              # Lufthansa Swagger spec, API documentation
├── 03-data-collection/       # Python tools for data ingestion
│   ├── lufthansa_api/        # API client, schemas, mock data
│   ├── collectors/           # airports_collector.py, airlines_collector.py
│   ├── explore_lh_api.ipynb  # Interactive exploration notebook
│   └── demo.py               # Demo script (no credentials needed)
├── requirements.txt          # Pinned Python dependencies
└── CLAUDE.md                 # This file
```

---

## Data Pipeline Architecture

```
Step 1: Collection (Phase 1 — current)
  ↓
Lufthansa API (OAuth2, /references/airports, /references/airlines)
  ↓
PostgreSQL directly (ADR 001: MongoDB deferred to Phase 2)

Step 1b: Collection (Phase 2 — planned)
  ↓
Lufthansa API → MongoDB (raw landing zone) → ETL → PostgreSQL

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

## Quick Start

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

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
| `02-api-docs/LH_public_API_swagger_2_0.json` | Full Lufthansa API specification |
| `03-data-collection/lufthansa_api/client.py` | Main API client (OAuth2, mock/real modes) |
| `03-data-collection/collectors/airports_collector.py` | Airports data ingestion |
| `03-data-collection/collectors/airlines_collector.py` | Airlines data ingestion |
| `03-data-collection/lufthansa_api/schemas.py` | Pydantic models for data validation |
| `03-data-collection/demo.py` | Mock data collector for testing |

---

## Architectural Decisions (ADRs)

ADRs are tracked in `01-requirements/c-architecture/`:

- **ADR 001** — PostgreSQL first, MongoDB deferred to Phase 2. Direct DB write for Phase 1; two-layer raw/curated architecture comes later.
- **ADR 002** — `psycopg2-binary` as PostgreSQL driver. Raw SQL over ORM for transparency and learning value.

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
