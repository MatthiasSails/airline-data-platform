# ADR 004 — MongoDB as Multi-Source Landing Zone Hub

**Status:** Accepted
**Date:** 2026-05-18
**Context:** Team meetup 2026-05-18

---

## Context

After Step 0 and Step 1 progress, the team is at a turning point on data sources:

1. **Lufthansa API:** No API key available. Pavel asked Liora/Vincent — no response indicating a key will be provided. Working assumption: no LH key will materialize.
2. **OpenSky Network API:** Reachable from local Macs (OAuth2 works), but **not from the Liora VM** — outbound HTTPS to `auth.opensky-network.org` (194.209.200.34) times out. Confirmed: AWS Security Group `de_terminal` is managed by DataScientest and cannot be opened by participants.
3. **adsb.lol:** Free, public, no auth, reliable. Currently the only fully-working live data source on the VM.
4. **Team size:** Reduced from 4 to 3 (Lukas leaving — focusing on remaining bootcamp courses).
5. **Mentor guidance (Nicolas):** ML can be skipped if data is insufficient; Kaggle dataset acceptable as fallback.

The team explicitly decided **against switching to the CryptoBot project** (Vincent offered the switch; team confirmed staying on Airlines).

---

## Decision

Position **MongoDB as the central landing zone hub** integrating multiple heterogeneous data sources, rather than treating it as a buffer for a single feed.

Concretely:

| Source | Where collector runs | Lands in |
|---|---|---|
| adsb.lol (live ADS-B over Berlin) | Liora VM (on the same network as MongoDB) or local | `airline_landing.adsb_raw` |
| OpenSky Network (structured flights) | Local Mac (VM blocked) | `airline_landing.opensky_raw` |
| Kaggle / static datasets (historical / reference) | Local one-shot loaders | `airline_landing.kaggle_*` |
| OurAirports.com (IATA↔ICAO mapping) | Local one-shot loader | `airline_landing.airports_ref` |

The ETL layer reads from any of these collections and produces the curated PostgreSQL warehouse.

---

## Rationale

### Why position MongoDB as the **hub**, not a single-source buffer?

- **Honest reflection of reality:** The team has multiple data sources of mixed shape and origin. A landing zone that handles all of them is more realistic than pretending it serves one.
- **Stronger defense story:** "We built a multi-source landing zone that decouples ingestion from transformation" is a real Data Engineering pattern — and it's exactly what we are doing.
- **Resilient to source loss:** If a source goes away, ETL still has the historical snapshots in MongoDB.
- **Schema-on-read pays off:** Each source has its own JSON shape; storing raw and normalizing at ETL time avoids brittle ingestion code.

### Why not stick with PostgreSQL-only (as in Phase 1)?

- Direct API → PostgreSQL only works if the source has a stable schema. With three+ sources of different shapes, the upfront flattening becomes a maintenance burden.
- We lose the ability to replay or re-transform.

### Rejected alternatives

| Option | Why rejected |
|---|---|
| Switch to CryptoBot project | Team chose to stick with Airlines despite data source friction |
| Wait for Lufthansa API key | No timeline from Liora; blocks Step 1 deadline (20.05.2026) |
| Drop OpenSky entirely | Provides structured flight legs that complement raw ADS-B |
| Move OpenSky collector to VM | Outbound HTTPS to OpenSky auth is blocked by Liora-controlled Security Group |
| Run all collectors on the VM | OpenSky impossible (see above); keeping mixed local + VM is unavoidable |

---

## Consequences

**Architecture:**
- `architecture/README.md` Phase 2 diagram updated to show multi-source convergence into MongoDB
- ETL layer becomes per-source, not per-table
- Collectors can be local or remote; MongoDB is the rendezvous point

**Workflow:**
- ADS-B collector runs on VM (cron, every 5 min) → `adsb_raw`
- OpenSky collector runs locally as CLI script (`python collectors/opensky_collector.py`) → `opensky_raw`
- Kaggle / reference loaders are one-shot scripts

**Team:**
- 3 people: Matthias Köhler, Pavel, Chaithra
- Lukas departing — no further code contributions expected

**Defense narrative:**
The multi-source landing zone is the demonstrable Data Engineering achievement of the project. Step 4 deck must lead with this.

---

## Related

- [ADR 001](001-postgres-first.md) — postponed MongoDB to Phase 2 (this ADR activates it)
- [ADR 003](003-dual-stream.md) — established OpenSky + adsb.lol parallel streams (this ADR generalizes to N sources)
- [source/mentor_update_nicolas.md](../source/mentor_update_nicolas.md) — mentor's ML-can-be-skipped guidance
