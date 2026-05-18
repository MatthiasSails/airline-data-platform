# ADR 002 — psycopg2 as PostgreSQL Driver

**Status:** Accepted  
**Date:** 2026-05-12  

---

## Context

To write data from the LH API into PostgreSQL we need a Python driver. The main candidates are:

| Package | Type | Notes |
|---|---|---|
| `psycopg2-binary` | Low-level adapter, raw SQL | Industry standard since 2001 |
| `psycopg3` | Low-level adapter, raw SQL | Modern successor, less documentation |
| `SQLAlchemy` | ORM, hides SQL behind Python objects | Large projects, many tables |
| `asyncpg` | Async adapter | Only relevant with async frameworks |

---

## Decision

We use **`psycopg2-binary`**.

---

## Reasons

**psycopg2 over psycopg3:**
- Vastly more documentation, Stack Overflow answers, tutorials
- API syntax is nearly identical — migration to psycopg3 takes minutes
- No async needed in our batch ingestion pipeline

**psycopg2 over SQLAlchemy:**
- We write raw SQL — the learner sees and understands every query
- SQLAlchemy hides SQL behind Python objects (counterproductive for learning)
- Our schema is simple (2 tables in Phase 1), ORM overhead is not justified

**psycopg2 over asyncpg:**
- Our pipeline is synchronous: fetch → transform → insert
- No concurrent connections, no async framework (FastAPI comes in Phase 2)

---

## Consequences

- All DB access goes through `psycopg2-binary==2.9.12` (pinned in `requirements.txt`)
- SQL is written explicitly — no ORM magic
- If FastAPI is introduced in Phase 2, SQLAlchemy or async drivers can be evaluated then
- `psycopg2-binary` bundles the C library — no system-level `libpq` installation needed
