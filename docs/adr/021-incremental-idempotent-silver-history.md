# ADR 021 — Incremental, Idempotent, Watermarked Silver-History Loader

**Status:** Proposed
**Date:** 2026-07-15
**Builds on:** ADR 020 (Redshift warehouse), ADR 004 (Mongo landing-zone hub), ADR 015 (Docker-loop scheduling)

---

## Context

`etl/silver.py` loads `map1` by **full refresh** (`DELETE` + reload of the freshest Bronze
snapshot). That is correct for a live map — it is rerun-safe *by replacement* and holds only
the current state — but it keeps **no history**: yesterday's rows are gone.

The Redshift warehouse (ADR 020) needs the opposite: **accumulate** every observation over
time. A full refresh cannot do that, and a naive append would create **duplicates** on every
rerun (the same aircraft/poll seen twice) and reprocess the entire Bronze collection each run.
We need a loader that (a) processes only *new* Bronze data, and (b) is safe to rerun or resume
after a crash.

## Decision

`etl/silver_history.py` loads Redshift with three mechanisms working together:

1. **Deterministic key.** Every observation gets `obs_id = md5(icao24 | time_position)` — the
   same natural key as `map1`'s `(icao24, time_position)` unique constraint.
2. **Idempotent load.** Positions are **insert-if-new** (`WHERE NOT EXISTS`), the aircraft
   dimension is a key-matched **UPDATE-then-INSERT** upsert, and flight legs are
   **delete+insert** of recomputed keys (`etl/sql/load_incremental.sql`). Re-running the same
   batch changes nothing.
3. **Watermark.** `meta.etl_watermark.last_watermark` stores the **max Bronze `fetched_at`**
   already processed (ISO 8601 string, copied from Bronze so it compares directly to Mongo's
   `fetched_at`). Each run reads it, queries `fetched_at > watermark`, and **advances it only
   after a successful commit**. `updated_at` is a wall-clock audit column, never used for
   filtering.

```mermaid
sequenceDiagram
    participant Loop as Docker loop (15 min)
    participant SH as silver_history.py
    participant MG as MongoDB (adsb_raw)
    participant WM as meta.etl_watermark
    participant RS as Redshift (silver + gold)

    Loop->>SH: run
    SH->>WM: SELECT last_watermark
    WM-->>SH: watermark (fetched_at)
    SH->>MG: find adsb_raw WHERE fetched_at > watermark
    MG-->>SH: new Bronze docs
    Note over SH: map_adsb_doc -> rows<br/>obs_id = md5(icao24 | time_position)
    SH->>RS: load TEMP stg_position
    SH->>RS: insert-if-new -> silver.aircraft_position
    SH->>RS: upsert -> dim_aircraft + fact_aircraft_position
    SH->>RS: sessionize -> silver.flight + fact_flight_summary
    Note over RS: re-run = no-op (deterministic keys)
    SH->>WM: UPDATE last_watermark = MAX(fetched_at)
    Note over SH,WM: advanced only after commit -> crash-safe
```

## Rationale

- **Crash-safety.** If the run dies after loading but before advancing the watermark, the
  watermark still points at the old boundary → the next run replays the same window → the
  idempotent MERGE absorbs it → no duplicates, no gap. The whole load runs in one transaction;
  the watermark advance is inside the same commit.
- **Why `fetched_at`, not a wall-clock.** Storing the actual Bronze `fetched_at` we processed
  (not `now()`) means the resume point matches Mongo's own field exactly — no drift-induced
  skips or overlaps between the collector and the loader.
- **Why insert-if-new rather than blind append.** Bronze can contain duplicate polls; the
  deterministic `obs_id` + `WHERE NOT EXISTS` makes the load converge to one row per
  observation regardless.
- **Redshift over BigQuery `MERGE`.** Plain Redshift `INSERT ... WHERE NOT EXISTS` and
  `UPDATE`/`INSERT` upserts are portable across Redshift versions and need no special table
  format; the deterministic key gives the same idempotency guarantee.

## Consequences

- Loader connects with **psycopg2** (Redshift wire-compatible; ADR 002/020) and bulk-loads a
  session `TEMP` table with `execute_values`, then runs `etl/sql/load_incremental.sql`.
- Scheduled by `etl/run_silver_history.sh` on a **15-minute** Docker loop (ADR 015, ADR 020),
  independent of `run_silver.sh`.
- The loader can **backfill** the whole warehouse from Bronze by resetting the watermark to the
  epoch — the history is all in Mongo.
- `meta.etl_watermark` is a control-plane table (`etl/sql/watermark.sql`), kept in its own
  `meta` schema, separate from the `silver`/`gold` data tables.

## Related

- [ADR 020](020-redshift-serverless-warehouse.md), [ADR 022](022-flight-leg-fact-revisits-adr009.md), [ADR 004](004-mongo-as-multisource-hub.md), [ADR 015](015-etl-scheduling-docker-loop.md)
