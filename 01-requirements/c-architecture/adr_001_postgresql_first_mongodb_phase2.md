# ADR 001 — PostgreSQL First, MongoDB in Phase 2

**Status:** Accepted  
**Date:** 2026-05-12  

---

## Context

The original architecture defines a two-layer storage strategy:

```
LH API → MongoDB (raw landing zone) → ETL → PostgreSQL (warehouse)
```

MongoDB was chosen as the raw landing zone because:
- The LH API returns nested JSON
- Schema-on-read allows storing data without upfront modeling
- Preserves original payloads for replay and re-transformation

However, at the start of Phase 1 (Data Collection):
- A PostgreSQL 16 instance is already running on the training server (Docker)
- No MongoDB instance is installed or configured
- The team is focused on learning the data pipeline end-to-end
- Adding MongoDB now would introduce setup overhead without immediate learning value

---

## Decision

We start Phase 1 by writing LH API data **directly into PostgreSQL**, skipping MongoDB.

The two-layer architecture (MongoDB + PostgreSQL) remains the **target architecture** and will be implemented in Phase 2.

---

## Consequences

**Short term (Phase 1):**
- Simpler setup: one database, one connection
- Data goes directly from API → PostgreSQL
- JSON flattening happens in Python before insert (no schema-on-read)
- Less flexibility if the API response structure changes

**Phase 2:**
- Introduce MongoDB as raw landing zone
- Replay raw data through ETL into PostgreSQL
- At that point: write ADR 002 documenting the full two-layer transition

---

## What stays unchanged

The overall architecture document (`dataflow_doc.md`, `architecture_m.md`) remains valid as the **target state**. It does not need to be updated — this ADR documents the deviation for Phase 1.
