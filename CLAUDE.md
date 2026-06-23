# CLAUDE.md — Airline Data Engineering Project

Project-level instructions for Claude Code in this repository. Cross-cutting policy (worktrees,
commit trailers, secrets handling) lives in the **global** `~/.claude/CLAUDE.md`; this file is only
what's specific to airline-data-platform. Private infra pointers (VM, hosts, keys) live in
`CLAUDE.local.md` (gitignored), never here.

---

## Git workflow

See [ADR 012](docs/adr/012-github-flow-cicd-pipeline.md) for the full decision (feature branches + squash-merge).

- **Feature branch + Pull Request required — never push directly to `main`.** Every change goes
  through a PR, reviewed by a second team member.
- **Squash and merge** is the team's default merge strategy (one commit per PR, linear history).
- `main` is always deployable. Use `feature/` · `fix/` · `chore/` branches; delete after merge.

---

## What Claude may and may not do

**Secrets:**
- Never commit secrets. `.env` lives at the project root and is gitignored.
- No real credentials, IPs, hostnames, or other private infra in tracked files — pointers go in
  `CLAUDE.local.md`.

**Coding standards:**
- Python 3.12+, type hints, `pathlib`, logging instead of `print()`.
- **Raw SQL via psycopg2, not an ORM** ([ADR 002](docs/adr/002-psycopg2.md)) — transparency over abstraction.
- Keep it simple: no Kubernetes, no microservices, no premature optimization (it's a learning project).
- New diagrams in Markdown + Mermaid.

---

## The project (orientation)

**Airline Data Engineering Platform** — a cloud-style data pipeline that ingests live flight data,
transforms it, and serves it via a dashboard and (planned) REST API. Capstone of the DataScientest
Data Engineer bootcamp; evaluation is on **Data Engineering mastery, not ML** (mentor de-prioritized
ML — see [docs/requirements/](docs/requirements/README.md)).

**Pipeline (medallion):**

```
OpenSky /states/all (+ adsb.lol)  →  MongoDB Atlas (Bronze, raw)  →  ETL
   →  Supabase Postgres (Silver: map1 live-map table)  →  Streamlit dashboard + (planned) FastAPI
```

Full design and the *why* live in [docs/architecture/](docs/architecture/README.md) and the ADRs.

**Repository layout:**

```
airline-data-platform/
├── docs/             # knowledge layer — requirements, ADRs, architecture, data-sources, report
├── etl/              # the pipeline: bronze.py (ingest) + silver.py (transform) + run_pipeline.sh
├── 03-gold/          # consumption: api/ (FastAPI, planned) + dashboard/ (Streamlit)
├── data_connectors/  # provider-abstracted DB access (mongo.py, supabase.py)
├── deployment/       # Docker Compose stacks (Portainer GitOps)
├── notebooks/        # exploration + walkthroughs
└── requirements.txt
```

> Bronze + Silver used to be numbered folders (`01-bronze/`, `02-silver/`); they were merged into
> `etl/` (PR #13). The numbered-folder convention of [ADR 010](docs/adr/010-repo-layout-knowledge-vs-pipeline.md) /
> [011](docs/adr/011-layer-named-folders-connector-abstraction-ml.md) is therefore partly superseded —
> those ADRs still hold the original rationale.

**Where to look:**

| Need | File |
|---|---|
| Docs index | [docs/README.md](docs/README.md) |
| Why the design is what it is | [docs/adr/](docs/adr/README.md) |
| Scope, deadlines, mentor context | [docs/requirements/](docs/requirements/README.md) |
| DB access (MongoDB / Postgres) | [docs/mongodb-access.md](docs/mongodb-access.md) |
| VM / SSH / running services | [docs/vm-access.md](docs/vm-access.md) |
| Private infra pointers (local, gitignored) | `CLAUDE.local.md` |
