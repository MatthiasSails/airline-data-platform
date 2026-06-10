# 01 — Requirements & Architecture

Documentation entry point for the **Airline Data Engineering Platform** — DataScientest / Liora Data Engineer Bootcamp project.

---

## What this project is

A multi-source data platform that ingests airline / flight data into a MongoDB landing zone, transforms it into a curated PostgreSQL warehouse, and exposes it through a FastAPI backend and a Streamlit dashboard. Built as the capstone project of a Data Engineering bootcamp.

**Why it exists:** to demonstrate end-to-end Data Engineering — API ingestion, multi-database architecture, ETL, automation, containerization, and CI/CD — under realistic constraints (no premium API access, partially blocked network, evolving requirements).

**Live:** ADS-B and OpenSky collectors write to MongoDB Atlas landing zone.

---

## Status (as of 2026-05-18)

| Phase | Deadline | Status |
|---|---|---|
| Step 0 — Scoping & Kickoff | 07.05.2026 | ✅ done |
| Step 1 — Data Discovery & Organization | 20.05.2026 | 🚧 in progress |
| Step 2 — Data Consumption & API | 10.06.2026 | ⏳ pending |
| Step 3 — Automation & Pipelines | 16.06.2026 | ⏳ pending |
| Step 4 — Deployment & Frontend | 02.07.2026 | ⏳ pending |
| Final Defense | 20.07.2026 | ⏳ pending |

**Currently live:**
- ADS-B and OpenSky collectors writing to MongoDB Atlas landing zone ✅
- PostgreSQL connector + schema (airports, airlines, flights) ✅

**Next up:** UML / ERD documentation, ETL pipeline (MongoDB → PostgreSQL).

---

## Team & Context

**Team:** Matthias Köhler, Pavel, Chaithra (3 people)
**Mentor:** Nicolas ("NicoTheDataSherpa")
**Program:** DataScientest Data Engineer Bootcamp, cohort `apr26_bde_airlines`

**Constraints worth knowing as a reader:**
- OpenSky API blocked on external VMs (outbound HTTPS) — local-only collector (see ADR 005)
- ML is explicitly de-prioritized (mentor approved)
- Strategic pivot: MongoDB positioned as multi-source hub, not single-feed buffer ([ADR 004](../adr/004-mongo-as-multisource-hub.md))

For the full original assignment see [source/](source/).

---

## How to navigate this folder

| Path | What's inside |
|---|---|
| **[scope.md](scope.md)** | What we deliver per phase, what's out of scope, non-goals |
| **[timeline.md](timeline.md)** | Mermaid Gantt chart of milestones |
| **[architecture/](../architecture/)** | Phase diagrams, data flow, ERD |
| **[adr/](../adr/)** | Architecture Decision Records — *why* the design looks like it does |
| **[source/](source/)** | Original Liora assignment + mentor messages (immutable) |

**New to the repo?** Read in this order: this file → [scope.md](scope.md) → [architecture/README.md](../architecture/README.md) → [adr/](../adr/).

---

## Repository structure beyond this folder

```
airline-data-platform/
├── docs/                   ← knowledge layer (you are in docs/requirements/)
│   ├── requirements/       ← scope, timeline, source assignment
│   ├── adr/                ← Architecture Decision Records
│   ├── architecture/       ← data flow, Silver ER model
│   ├── data-sources/       ← external API references (OpenSky, adsb.lol, market overview)
│   └── report/             ← final project report
├── 01-bronze/              ← collectors → Bronze (MongoDB)
├── 02-silver/              ← Bronze → Silver: etl/ + warehouse/ (Postgres star schema)
├── 03-gold/               ← consumption: api/ (FastAPI) + dashboard/ (Streamlit)
├── deployment/            ← docker-compose, scheduler, orchestration (un-numbered)
├── data-connectors/        ← provider-abstracted DB access (mongo.py, supabase.py)
└── notebooks/              ← exploration + collector walkthroughs
```
