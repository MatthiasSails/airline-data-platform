# ADR 005 — OpenSky Pipeline Migration: PostgreSQL → MongoDB Landing Zone

**Status:** Accepted  
**Date:** 2026-05-18  
**Supersedes:** Phase-1 OpenSky design implied by ADR 001 and ADR 003

---

## Context

In Phase 1 (ADR 001), OpenSky data was planned to flow through a structured pipeline:
OpenSky API → `schemas.py` (dataclasses) → PostgreSQL (typed rows).

ADR 004 established MongoDB as the multi-source landing zone for all ingestion. This ADR
records the specific migration of the OpenSky path from Phase 1 to Phase 2, and why the
original PostgreSQL-first design is not extended.

---

## Decision

The OpenSky collector writes raw API responses to `airline_landing.opensky_raw` in MongoDB.
Schema normalization (flattening `flights[]` arrays into relational rows) happens in the
ETL layer (Phase 3), not at ingestion time.

---

## Changes from Phase 1

| Aspect | Phase 1 (original) | Phase 2 (this ADR) |
|---|---|---|
| Target store | PostgreSQL | MongoDB `opensky_raw` |
| Schema enforcement | `schemas.py` dataclasses at ingest | None at ingest; ETL-time |
| Collector entry point | Ad-hoc notebook / `client.py` direct | `collectors/opensky_collector.py` |
| Document granularity | Per flight record (rows) | Per API call (one document) |
| Execution environment | Any | **Local Mac only** (VM blocks OpenSky auth) |

---

## Document structure (`opensky_raw`)

One document per API call, two calls per run (departures + arrivals):

```json
{
  "collected_at": "2026-05-18T14:00:00+00:00",
  "source": "opensky-network",
  "endpoint": "departures",
  "query_params": { "airport": "EDDB", "begin": 1747526400, "end": 1747612800 },
  "flight_count": 47,
  "flights": [ { "icao24": "3c56f0", "callsign": "EWG1R", ... }, ... ]
}
```

---

## Rationale

**Consistency:** All landing zone sources follow the same raw-JSON-per-call pattern established
in ADR 004 (`adsb_raw`, `opensky_raw`, future `kaggle_*`, `airports_ref`).

**Replay capability:** Raw documents can be re-processed if ETL logic changes, without re-querying
the OpenSky API (rate-limited).

**Operational constraint:** The collector must run locally — outbound HTTPS to
`auth.opensky-network.org` is blocked by the Liora VM's AWS Security Group (ADR 004).
A CLI script (`python collectors/opensky_collector.py`) is easier to run locally than
maintaining a persistent Jupyter session.

**`schemas.py` is not deleted** — it remains as field-name reference documentation.

---

## Consequences

- `collectors/opensky_collector.py` is the canonical ingestion entry point.
- `03-data-collection/opensky_api/client.py` continues as the HTTP client (unchanged).
- `03-data-collection/opensky_api/schemas.py` is documentation only.
- `collectors/airlines_collector.py` and `collectors/airports_collector.py` remain as
  Phase-1 artifacts; the LH API key never materialized, so these are not actively used.
  `airports_collector.py` will be rewritten in a later step to load OurAirports reference
  data into `airline_landing.airports_ref` (see ADR 004 consequence table).
- ETL layer (Phase 3) is responsible for flattening `flights[]` arrays into PostgreSQL rows.

---

## Related

- [ADR 001](001-postgres-first.md) — original PostgreSQL-first decision
- [ADR 003](003-dual-stream.md) — established OpenSky + adsb.lol parallel streams
- [ADR 004](004-mongo-as-multisource-hub.md) — MongoDB as multi-source landing zone (parent decision)
