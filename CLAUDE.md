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
- **Silver / Analytics Warehouse**: **Supabase Postgres** — project `leanMVP` (`civmkvcgbklejootrkks`), eu-central-1, Free/NANO. Decided 2026-06-09 (see ADR 007 addendum). MVP table: `map1` (flat, live-map). Star schema (`fact_states` + dims) planned for Step 3.
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
│   ├── adr/                  # Architecture Decision Records (001–011)
│   ├── architecture/         # data-flow.md, silver-layer-er.md, diagrams
│   ├── data-sources/         # external API references (OpenSky, adsb.lol, market overview)
│   ├── report/               # DataScientest final project report
│   ├── setup.md              # local setup runbook
│   └── mongodb-access.md     # Atlas access / DB users
├── 01-bronze/                # Collectors → BRONZE (MongoDB)  (+ own README)
│   └── collectors/           # adsb_collector, opensky_states_collector
├── 02-silver/                # BRONZE → SILVER
│   ├── etl/                  # Bronze → Silver transform (opensky_to_supabase.py)
│   └── warehouse/            # star-schema DDL: schema.sql
├── 03-gold/                  # consumption: api/ (FastAPI) + dashboard/ (Streamlit); warehouse/ (Gold aggregates) planned
├── deployment/               # docker-compose, scheduler, orchestration (un-numbered, cross-cutting)
├── data_connectors/          # provider-abstracted DB access: mongo.py, supabase.py (ADR 011)
├── notebooks/                # exploration + collector walkthroughs (explore_*, collect_*)
├── requirements.txt          # Pinned Python dependencies
└── CLAUDE.md                 # This file
```

### Documentation layout

Two axes — keep them separate (this is the whole point of the layout):

- **`docs/` = knowledge layer** — everything *about the whole project*: requirements, ADRs, architecture, data-source references, the report. Project-wide, un-numbered. Has its own index `docs/README.md`. (Mirrors the global rule "Git = knowledge layer, Projects V2 = workflow layer".)
- **Numbered folders (`01-`–`03-`) = data-pipeline layers (code)** — `01-bronze` → `02-silver` → `03-gold`. The medallion is readable from the tree (ADR 011). Cross-cutting code is **un-numbered**: `data_connectors/`, `deployment/`, `notebooks/`.
- **Module `README.md`** — "how to run *this* module", co-located in each code dir (e.g. `01-bronze/README.md`).

Rule of thumb: about the whole project → `docs/`; a pipeline stage's code → its numbered folder; how to run one module → that module's README. **Project progress/tracking is GitHub Projects V2, not a repo file.** Learning artefacts (bootcamp theory, not project docs) do **not** belong in this repo — they go to `knowledgebase/methodology/`.

---

## Data Pipeline Architecture

```
Phase 2 — Ingestion (current, see ADR 004 + ADR 006):

  adsb.lol (live ADS-B)           →  MongoDB Atlas airline_landing.adsb_raw      ┐
  OpenSky /states/all (Mac only)  →  MongoDB Atlas airline_landing.opensky_raw   ├→ ETL → Supabase map1 (Silver MVP)
  Kaggle / reference data         →  MongoDB Atlas airline_landing.kaggle_* / airports_ref ┘

Phase 3 — Transformation (planned, see ADR 007 + ADR 008/009):
  ETL reads from MongoDB Atlas → normalises → loads Silver Postgres Star Schema
  (Supabase confirmed; Star Schema fact_states + dims planned alongside map1)

Phase 4 — Serving (planned):
  FastAPI endpoints + Streamlit/Dash dashboards read from Silver Postgres

Phase 5 — Orchestration (planned):
  Cron / Airflow / Lambda — exact tooling TBD; sub-minute streaming as a stretch goal
```

**Key Principle:** MongoDB Atlas is the raw landing zone (schema-on-read, one document per API call).
The Silver layer is **Supabase Postgres** (managed serverless, eu-central-1). MVP table: `map1`.
Star schema (`fact_states` + dims per ADR 008/009) will be added alongside `map1` in Step 3.

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
- **Silver (Warehouse):** **Supabase Postgres** — project `leanMVP` (`civmkvcgbklejootrkks`), eu-central-1, Free/NANO. Credentials in Proton Pass (`bde.airline.0426@protonmail.com`). `SUPABASE_DB_PASSWORD` in `.env`.
  - **Local dev connection** (Mac has no global IPv6 — Direct Connection is IPv6-only on Free Tier):
    ```bash
    ssh -i ~/.ssh/airline_vm -f -N \
        -L 5432:db.civmkvcgbklejootrkks.supabase.co:5432 \
        ubuntu@63.185.229.117
    # ETL load() reads SUPABASE_DB_HOST/PORT (default localhost:5432). Keep SUPABASE_DB_HOST
    # unset on the Mac so it targets the tunnel; user=postgres dbname=postgres.
    ```
  - **On aws-airline-1:** use port **5432** (Direct Connection on `db.<ref>.supabase.co`, IPv6) — verified working from the VM 2026-06-11 (387 rows in `map1`). `app.py` defaults to 5432.
  - **Docker containers on aws-airline-1 do NOT inherit IPv6 automatically.** Docker bridge networks are created without IPv6 even when the host is dual-stack. Any container that needs to reach Supabase must use `network_mode: host`. Do not add `ports:` when using host networking (silently ignored).
  - **Supabase port history (2026-06-11):** port **6543** on the direct host (legacy pgBouncer) now **refuses connections** — Supabase removed it. The Supavisor pooler (`aws-0-eu-central-1.pooler.supabase.com`) returns *tenant/user not found* for this project. **Use direct port 5432** with `user=postgres`, `dbname=postgres`. Mac has no global IPv6, so local dev needs the SSH tunnel above; the VM has IPv6 and connects directly.
  - **PostgREST / supabase-py:** currently broken (PGRST002 after Supabase API-key migration). Use psycopg2 direct. If using supabase-py later, use legacy JWT key (`eyJ…`) not new `sb_secret_` format.
- **Compute (dedicated VM with fixed IP):** **AWS Lightsail `aws-airline-1`** (provisioned 2026-06-05). Static IP `63.185.229.117`, eu-central-1a. Docker 29.1 + Compose 2.40. SSH: `ssh -i ~/.ssh/airline_vm ubuntu@63.185.229.117`. Compose lives under `deployment/`, **one file per stack** (`dashboard.yml`, `jupyter.yml`, `landing.yml`) — see [`deployment/README.md`](deployment/README.md).
  - **Portainer CE 2.42.0 (STS)** — deployed 2026-06-09, upgraded from 2.39.3 the same day. URL: https://airline-portainer.matthiaskoehler.com. Container pinned to `portainer/portainer-ce:2.42.0`, port `9443:9443`, volume `portainer_data`. CE serves HTTPS only on 9443, no HTTP on 9000. **Do not pin the `latest` tag** — it tracks the LTS line, not STS; the 2.42 GitOps Sources/Workflows views require an explicit STS version. Pre-upgrade DB backup on the VM: `/home/ubuntu/portainer_data_backup_2.39.3_20260609.tar.gz` (plus Portainer's own `/data/backups/portainer.db.bak`).
    - **One stack per independently deployable service (since 2026-06-11 reorg).** A stack is a lifecycle boundary; the old `airline-services` bundle (dashboard + jupyter) and `airline-platform` were split. Env vars are set directly in the Portainer stack env store per stack (never a `.env` on the VM).
      - **`airline-dashboard`** → GitOps `deployment/dashboard.yml`. Container `adsb_dashboard`, Streamlit Supabase live map, **`network_mode: host`** (IPv6 → Supabase). Env: `SUPABASE_DB_HOST`, `SUPABASE_DB_PASSWORD`.
      - **`airline-jupyter`** → GitOps `deployment/jupyter.yml`. Container `jupyter` (port 8888, JupyterLab, repo mounted). Env: `JUPYTER_TOKEN`, `MONGO_URI`.
      - **`airline-landing`** → GitOps `deployment/landing.yml`. Container `landing_page` (port 80, `nginx:1.27-alpine`, static HTML from `deployment/landing-page/index.html`).
      - Reserved: **`airline-etl`** → `deployment/etl.yml` once the Bronze→Silver ETL is containerized (also host-net for IPv6).
  - **ADR 011 repoint done 2026-06-10:** the `04-deployment/` → `deployment/` move made the old git Compose path 404. Since the path is **immutable on existing git stacks**, both stacks were **deleted + recreated** via the Portainer API on the new `deployment/...` path (old IDs 6/8 → new **10/9**). Env vars re-applied from Proton Pass. Verified: all three containers running, `https://airline.matthiaskoehler.com` → 200. A Portainer API key is in macOS Keychain as `portainer_api_mk` (revoke if no longer needed).
  - **Deployment Pattern — `environment: - VAR=${VAR}` (since commit 4e44817):** `docker-compose.yml` uses `environment: - VAR=${VAR}` instead of `env_file:`. Portainer GitOps pulls the Compose file from git but injects secrets via its own environment store, so there is no `.env` on the VM. This is the required pattern for any service whose secrets are managed in Portainer.
  - **GitOps build rule — a `build:` service must NOT carry an `image:` tag (since commit 53f314d):** Portainer runs `compose pull` before every deploy. A service that has both `build:` and an explicit `image: <name>` makes Portainer try to pull `<name>` from a registry; for a locally-built image this fails the whole stack with `pull access denied`. Use `build:` **without** `image:` — Portainer then builds locally on every git push (rebuild verified 2026-06-09) and Compose auto-names the image `<stack>-<service>` (e.g. `airline-platform-landing-page`). The landing stack carried this bug until 53f314d.
  - **Cloudflare Tunnel** — all services exposed via `cloudflared` container (`--network host`, `restart: always`), no ports need to be open in Lightsail firewall. Token in Keychain: `cloudflare_airline_tunnel_token`.
  - **Service URLs** (via Cloudflare Tunnel, valid HTTPS):
    - https://airline-portainer.matthiaskoehler.com — Portainer
    - https://airline-jupyter.matthiaskoehler.com — JupyterLab
    - https://airline-dashboard.matthiaskoehler.com — ADS-B Dashboard
    - https://airline.matthiaskoehler.com — Landing Page (nginx:1.27-alpine, static HTML)
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

Naming convention: `explore_<source>.ipynb` in `notebooks/`.

| Notebook | Source |
|---|---|
| `explore_adsb_lol.ipynb` | adsb.lol API |
| `explore_mongo_atlas.ipynb` | MongoDB Atlas landing zone — `adsb_raw` + `opensky_raw`, incl. cross-collection join (sec. 9–11) |

### Active Collectors (Phase 2)

```bash
cd 01-bronze

# ADS-B — single run (or --interval 60 for continuous):
python collectors/adsb_collector.py

# OpenSky /states/all — active Silver-layer source (local Mac only, see ADR 009):
# Bounding box: Frankfurt ~150x150 km (centre 50.11°N 8.68°E). Agreed scope for MVP
# with Pavel/Chaithra. BBOX constants in collectors/opensky_states_collector.py line ~48.
python collectors/opensky_states_collector.py
python collectors/opensky_states_collector.py --interval 60  # continuous polling

# Educational step-by-step notebook:
# collect_adsb.ipynb
```

> The legacy OpenSky `/flights/*` client (`opensky_api/`, `opensky_collector.py`) was **removed**
> 2026-06-10 — retired per ADR 009; the live source is `/states/all`.

### Bronze → Silver ETL

```bash
# load() reads SUPABASE_DB_HOST/PORT (default localhost:5432) since commit bdf363b — this is
# what makes the VM-direct path actually work. Mac → tunnel (SUPABASE_DB_HOST unset → localhost);
# VM → direct (SUPABASE_DB_HOST set in the VM .env, IPv6, no tunnel).

# --- On aws-airline-1 (no tunnel; VM has its own venv) ---
ssh -i ~/.ssh/airline_vm ubuntu@63.185.229.117
cd ~/airline-data-platform && .venv/bin/python 02-silver/etl/opensky_to_supabase.py

# --- Local Mac dev (start tunnel first, SUPABASE_DB_HOST stays unset) ---
ssh -i ~/.ssh/airline_vm -f -N -L 5432:db.civmkvcgbklejootrkks.supabase.co:5432 ubuntu@63.185.229.117
python 02-silver/etl/opensky_to_supabase.py
```

> **PostgREST / supabase-py:** still returning `PGRST002` (Supabase API-key migration, June 2026). Use psycopg2 direct. Do not rely on PostgREST until resolved upstream.

**ETL known limitations:**

- **No deduplication key in `map1`:** The table uses a Supabase auto-generated `id` as PK, so `ON CONFLICT DO NOTHING` is a no-op — it never fires. Running the ETL twice produces duplicate rows. Current workaround: `TRUNCATE map1` before each ETL run. Long-term fix: add `UNIQUE (icao24, time_position)` constraint when migrating to `fact_states` (Step 3).
- **ETL reads all historical Bronze documents:** `opensky_to_supabase.py` reads every document from `opensky_raw` and `adsb_raw` without a date filter. If `map1` is truncated but old Bronze documents remain, they re-populate `map1` with stale data on the next ETL run. When resetting Silver, also clean Bronze: delete `opensky_raw` docs whose `query_params` don't match the current BBOX, and clear `adsb_raw` if stale.

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
| `01-bronze/collectors/adsb_collector.py` | ADS-B collector → MongoDB adsb_raw |
| `01-bronze/collectors/opensky_states_collector.py` | OpenSky /states/all collector → MongoDB opensky_raw (active, local Mac only; OAuth2/basic-auth inline) |
| `data_connectors/mongo.py` | MongoDB connector (insert_raw, insert_adsb_snapshot) |
| `02-silver/etl/opensky_to_supabase.py` | Bronze → Silver ETL: Atlas adsb_raw + opensky_raw → Supabase map1 |
| `02-silver/warehouse/schema.sql` | PostgreSQL schema (airports, airlines, flights) |

---

## Architectural Decisions (ADRs)

ADRs are tracked in `docs/adr/`:

- **ADR 001** — PostgreSQL first, MongoDB deferred to Phase 2.
- **ADR 002** — `psycopg2-binary` as PostgreSQL driver. Raw SQL over ORM for transparency.
- **ADR 003** — Dual-stream ADS-B: adsb.lol (free, ODbL) + OpenSky into MongoDB landing zone.
- **ADR 004** — MongoDB as multi-source landing zone hub. OpenSky runs locally only (VM blocked); adsb.lol is the only VM-side live source.
- **ADR 005** — OpenSky pipeline migration: Phase-1 PostgreSQL schema-at-ingest → Phase-2 raw JSON per API call into MongoDB opensky_raw.
- **ADR 006** — MongoDB Atlas Free Tier as Bronze landing zone (migrated from self-hosted VM 2026-05-27).
- **ADR 007** — Decouple from Liora VM; dedicated cloud VM (AWS Lightsail `aws-airline-1`). Includes addenda: dual-stack networking (2026-05-28), Lightsail over EC2 (2026-06-05), Supabase as Silver provider (2026-06-09).
- **ADR 008** — Airline attribution star schema (Silver analytics layer).
- **ADR 009** — States API (`/states/all`) as Silver source; `/flights/*` retired.
- **ADR 010** — Repo layout: `docs/` (knowledge) vs. numbered pipeline folders (code).

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
