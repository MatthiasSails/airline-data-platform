# ADR 010 — Repo Layout: `docs/` Knowledge Layer + Numbered Pipeline Phases

**Status:** Accepted
**Date:** 2026-06-02
**Supersedes:** the original `01-requirements / 02-api-docs / 03-data-collection / 04-dashboard` layout.

---

## Context

The repo started with numbered top-level folders that mirrored the project's *narrative* phases.
That sequence encoded **two axes at once**: `01-requirements` and `02-api-docs` were
documentation-only, while `03-data-collection` and `04-dashboard` were code-only. Two problems
followed:

1. **The pipeline middle had no home.** ETL (Bronze→Silver), the warehouse schema, and the FastAPI
   service were neither "requirements" nor "dashboard" — they fell between the numbered slots.
2. **A number had no single meaning** — sometimes docs, sometimes code — so the layout could not grow
   without renumbering.

The trigger was the OpenSky-States Silver pivot (ADR 009) plus the realisation that the layout was an
attempt to make the *repo* read like the *project report* (a narrative document). Repo and report
optimise for different things: a report is a linear story; a repo is code organised by component.

## Decision

Split the repo into **two separate axes**:

1. **`docs/` = knowledge layer** (project-wide, un-numbered): `requirements/`, `adr/`,
   `architecture/`, `data-sources/`, `report/`. Mirrors the global rule "Git = knowledge layer,
   Projects V2 = workflow layer".
2. **Numbered folders = pipeline phases (code)**, where each number means exactly one pipeline stage:
   - `01-data-collection/` → Bronze ingestion
   - `02-data-modeling/` → Bronze → Silver (`etl/` + `warehouse/`)
   - `03-data-consumption/` → `api/` (FastAPI) + `dashboard/` (Streamlit)
   - `04-deployment/` → docker-compose, scheduler, orchestration

Phase-specific docs live inside their phase; project-wide knowledge lives in `docs/`. Project progress
tracking stays in GitHub Projects V2, never as a repo file.

## Rationale

- The medallion is now readable from the tree: `01` = Bronze in, `02` = Silver out.
- Every number means one thing → the layout survives inserting stages without renumbering.
- PostgreSQL (Silver) moved out of the old collection folder into `02-data-modeling/warehouse/`,
  giving the warehouse and ETL a real home.

**Rejected:** keeping the report-mirroring numbered docs (would perpetuate the two-axis confusion);
a single flat `src/` package (loses the readable per-phase / per-service split the project wants).

## Consequences

- Executed in one commit (`git mv` rename-detected by Git; history not a concern — solo repo).
- All cross-references in `README.md`, `CLAUDE.md`, and module docs updated; relative Markdown links
  verified. ADR prose left as historical point-in-time records.
- Generalised as reusable methodology in `knowledgebase/methodology/repo-layout-knowledge-vs-pipeline.md`.
