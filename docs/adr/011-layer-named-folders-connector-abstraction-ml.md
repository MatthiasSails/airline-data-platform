# ADR 011 — Layer-Named Folders, Data-Connector Abstraction, and ML Placement

**Status:** Accepted
**Date:** 2026-06-10
**Refines:** ADR 010 (numbered pipeline phases) — renames phases to medallion-layer names and
adds the rules for code that is *not* a data layer (connectors, serving apps, ML).
**Builds on:** ADR 008 (star schema), ADR 009 (States-centric Silver model).
**Scope note:** this layout governs *our* repo (`MatthiasSails/airline-data-platform`). Whether the
DataScientest course expects the Cookiecutter template is being clarified separately with the tutors
and is treated as **non-binding** — the template is course guidance, not a hard submission spec (see
*Rationale*). The §6 mapping table is the bridge if a template-shaped submission is ever needed.

---

## Context

ADR 010 split the repo into a `docs/` knowledge layer plus numbered pipeline phases, where each
number means exactly one pipeline stage (`01-data-collection` … `04-deployment`). Two things have
since become clear and motivate a refinement:

1. **The phase names describe the *activity* ("data-collection", "data-modeling"), not the
   *medallion layer* the activity produces.** The medallion (Bronze/Silver/Gold) is the project's
   actual organizing concept (ADR 009), so naming the folders after the layers makes the tree
   self-documenting and removes a translation step.
2. **The repo will accumulate code that is not itself a data layer** — database connectors, the
   serving apps (FastAPI, dashboard), and possibly machine learning. ADR 010 had no rule for where
   non-data-layer code lives, which invites the same "two axes in one numbering" confusion ADR 010
   set out to kill.

A separate trigger: the official course template
([`DataScientest-Studio/apr26_bde_airlines`](https://github.com/DataScientest-Studio/apr26_bde_airlines))
is a **Cookiecutter Data Science** scaffold — a flat `src/{data,features,models,visualization}`
package organized by *ML-workflow function*, not by data layer. ADR 010 explicitly **rejected** a
flat `src/` package. The two structures encode different axes (ML-workflow-function vs.
data-veredelung), so a deliberate mapping decision is required rather than a silent drift.

## Decision

### 1. Numbered folders are named after the medallion data layer

```
01-bronze/     # raw ingestion → MongoDB Atlas landing zone   (was 01-data-collection)
02-silver/     # ETL + warehouse → curated star schema          (was 02-data-modeling)
03-gold/       # consumption-ready business layer               (was 03-data-consumption)
```

- Folder names use **hyphens** (`01-bronze`), consistent with the existing repo convention; no
  `_layer` suffix (the folder *is* the layer).
- A number still means exactly one pipeline stage (preserves ADR 010's "every number means one
  thing" invariant).

### 2. Gold is the "consumption-ready business layer" — it holds Gold *data* **and** the serving apps

The medallion strictly classifies *data*; API and dashboard are *applications* that read Gold. We
nonetheless co-locate them under `03-gold/` (the consumption side), but keep data and apps
**visibly separate** inside it so a reader looking for Gold *tables* does not trip over FastAPI code:

```
03-gold/
├── warehouse/    # Gold DATA: aggregate DDL, KPI tables, materialized views
├── api/          # FastAPI service (reads Gold/Silver)
└── dashboard/    # Streamlit
```

> Current reality: there is no Gold layer yet — the dashboard reads Silver (`map1`) directly. That
> is acceptable for the MVP but must be stated in the architecture docs, not hidden.

### 3. Non-data-layer code lives in un-numbered top-level folders

The rule that resolves every "where does X go?" question: **data flows → numbered layers; code and
workloads → un-numbered folders.**

```
data-connectors/   # provider-abstracted data access (see §4)
ml/                # machine-learning workload (see §5)
deployment/        # Docker, compose, GitHub Actions, scheduler, Portainer GitOps
docs/              # knowledge layer (ADR 010)
notebooks/         # exploration
requirements.txt   # dev tooling lives at repo root, not inside a layer
```

### 4. Database access goes through a provider-abstracted `data-connectors/` (Ports & Adapters)

Connectors are shared by multiple layers (the warehouse store is written by Silver ETL and read by
the Gold serving apps), so they belong to *no single layer*. They are abstracted so that the
technology and vendor are swappable:

```
data-connectors/
├── base.py       # Ports: abstract SourceStore, WarehouseStore (domain operations)
├── mongo.py      # MongoSource(SourceStore)          — Bronze landing zone
├── supabase.py   # SupabaseWarehouse(WarehouseStore) — Silver / Gold
└── factory.py    # selects the adapter from env (e.g. PROVIDER=supabase|neon)
```

The interface speaks in **domain terms** (`read_raw_states()`, `upsert_fact_states(rows)`), never in
DB terms (`execute(sql)`), so provider/SQL knowledge cannot leak into ETL or apps. Swapping
Supabase → Neon, or Mongo → another store, becomes a new adapter with **zero ETL changes**.

### 5. Machine learning is a *workload*, not a data layer

If ML is added later, it does **not** become "the Gold folder". It splits across two homes:

- **ML data** follows the medallion: ML *reads* features primarily from **Silver** (granular signal,
  not pre-aggregated Gold) and *writes* predictions/scores back as **Gold tables**
  (`gold_*_forecast`, `gold_*_score`) — business-ready enriched data.
- **ML code** lives in an un-numbered `ml/` folder with its own lifecycle:

  ```
  ml/
  ├── features/    # feature engineering (reads Silver via data-connectors)
  ├── training/
  ├── models/      # artifacts / registry references
  └── inference/   # scoring → writes Gold
  ```

ML is **out of scope** for the current DE track and is recorded here only to reserve the structure.

### 5b. Resolved target layout (canonical reference)

```
airline-data-platform/
├── 01-bronze/
│   ├── collectors/        # opensky_states_collector.py, adsb_collector.py (→ Mongo)
│   ├── opensky_api/       # OpenSky OAuth2 client
│   └── reference/         # raw fetch of OpenFlights / OurAirports / OpenSky AircraftDB → Mongo
├── 02-silver/
│   ├── etl/               # extract.py · transform.py · load.py · dimensions.py
│   └── warehouse/         # schema.sql (fact_states + dims)
├── 03-gold/
│   ├── warehouse/         # Gold aggregates / materialized views (DDL)
│   ├── api/               # FastAPI
│   └── dashboard/         # Streamlit
├── data-connectors/       # base.py · mongo.py · supabase.py · factory.py
├── deployment/            # docker/ · scheduler/  (CI lives in .github/workflows/ at root)
├── docs/                  # adr/ · architecture/ · data-sources/ · requirements/ · report/
├── notebooks/             # exploration (moved out of 01-)
├── tests/                 # mirrors layers (test_bronze/ · test_silver/ · …)
├── .env.example           # template; real .env gitignored
├── requirements.txt
└── README.md
```

**Reference-data routing:** the static reference feeds (OpenFlights `airlines.dat`, OurAirports
`airports.csv`, OpenSky `aircraftDatabase.csv`) land **raw in Bronze** (`01-bronze/reference/` →
Mongo snapshot) and are promoted to dims in Silver (`02-silver/etl/dimensions.py`). Chosen over a
direct Silver seed-load to preserve the *raw-immutable* principle and reproducible snapshots
(consistent with ADR 004 landing-zone hub and ADR 009). There is deliberately **no `data/` directory
in the repo** — all data lives in MongoDB Atlas (Bronze) and Supabase (Silver).

### 6. Relationship to the DataScientest Cookiecutter template

We keep the **medallion structure internally** and document a **mapping** from the course template to
ours (in `README.md` / `docs/architecture/`), rather than adopting the flat `src/` layout (which
ADR 010 already rejected on architectural grounds).

| Course template (`apr26_bde_airlines`)         | → This repo                                  |
|------------------------------------------------|----------------------------------------------|
| `src/data/make_dataset.py`                     | `01-bronze/` + `02-silver/` (ingestion ≠ modeling, split across two layers) |
| `src/features/build_features.py`               | `ml/features/`                               |
| `src/models/train_model.py` / `predict_model.py` | `ml/training/` / `ml/inference/`           |
| `src/visualization/visualize.py`               | `03-gold/dashboard/`                         |
| `models/`                                      | `ml/models/`                                 |
| `notebooks/`                                   | `notebooks/`                                 |
| `references/`                                  | `docs/data-sources/`                         |
| `reports/figures/`                             | `docs/report/`                               |
| `.github/workflows/`                           | `deployment/` (CI/CD)                        |
| `requirements.txt`                             | repo root                                    |
| *(none)*                                       | `data-connectors/`, `03-gold/{warehouse,api}` (no medallion / API / connector abstraction in the template) |

## Rationale

- **Layer-named folders** make the medallion readable directly from the tree without translating
  "data-modeling" → "Silver" — sharpening ADR 010's stated goal.
- **The data-vs-code rule** ("data → numbered, code → un-numbered") gives every future component an
  unambiguous home and stops the two-axes confusion ADR 010 fought from creeping back.
- **Connector abstraction** matches the user's explicit goal of abstracting technology + vendor; it
  also removes the current direct `psycopg2.connect(...)` coupling inside the ETL
  (`02-silver/etl/opensky_to_supabase.py`), making the pipeline provider-agnostic.
- **ML-as-workload** keeps the medallion honest: predictions are Gold *data*, but training code has a
  different lifecycle and does not belong in a data-layer folder — the same data-vs-code line as the
  serving apps.
- **Internal medallion + mapping doc** preserves the stronger data architecture while staying legible
  to graders familiar with the Cookiecutter template.

- **Cookiecutter is recognized but genre-bound.** Cookiecutter Data Science is a genuine de-facto
  standard (8+ years, ~7.6k GitHub stars) — *for exploratory data-science / ML-analysis projects*.
  Its stated philosophy ("data analysis as a DAG", model-centric `src/models/`) targets a single
  analyst/researcher, not a data *platform*. Its V2 release explicitly leaves seven platform concerns
  unsolved (DAG runners, data management, cloud infra, experiment tracking, env management). It is a
  scaffold to fork, not a complete platform architecture — so following it here would be using a
  notebook-driven-DS template for a pipeline-and-serving project.
- **Data does not belong in the repo.** Cookiecutter places `data/{raw,interim,processed,external}`
  in the tree. Our data lives in MongoDB Atlas (Bronze) and Supabase (Silver) — proper stores. A
  `data/` directory under version control is an anti-pattern for this project; we deliberately have
  no such folder.

**Rejected:**
- *Adopting the flat Cookiecutter `src/` layout* — already rejected in ADR 010; it is ML-first and
  has no medallion, no API, no connector abstraction; Bronze and Silver collapse into one
  `make_dataset.py`; and it carries an in-repo `data/` tree (see above).
- *Putting API/dashboard in a dedicated `04-serving/` layer* — cleaner data/app separation, but the
  user prefers Gold as the single consumption layer; mitigated by the `warehouse/` vs `api/` split.
- *Co-locating each connector with its layer* (Mongo in Bronze, Supabase in Silver) — forces
  `03-gold/` apps to import from `02-silver/`, an ugly cross-layer dependency.

## Consequences

- **Submission structure decoupled:** our repo follows this medallion layout regardless. The course
  template question is handled separately with the tutors and assessed as non-binding; if a
  template-shaped submission is ever required, §6's mapping table is the bridge (and the medallion
  could live *inside* a `src/` package as a follow-up). This does not block our repo.
- When executed:
  - `git mv` the three phase folders (`01-data-collection` → `01-bronze`, etc.); `04-deployment` →
    un-numbered `deployment/`; collapse `03-data-consumption` into `03-gold/`.
  - Extract `data-connectors/`; refactor `02-silver/etl/opensky_to_supabase.py` to depend on the
    `WarehouseStore` port instead of calling `psycopg2` directly.
  - Update all cross-references in `README.md`, `CLAUDE.md`, `docs/architecture/*`, and module docs;
    verify relative Markdown links.
  - Reconcile the stale architecture docs (which still say "ETL pending / Neon" and describe a star
    schema while the live Silver is the flat `map1` table) with the executed reality.
- ADR prose left as a historical point-in-time record per repo convention.
