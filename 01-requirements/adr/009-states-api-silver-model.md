# ADR 009 — Silver Model: OpenSky States as the Central Fact; adsb.lol Bronze-only

**Status:** Accepted
**Date:** 2026-06-02
**Refines:** ADR 003 (dual-stream) — changes the OpenSky role and demotes adsb.lol to Bronze.
**Builds on:** ADR 004 (Mongo landing-zone hub), ADR 007 (Neon Silver warehouse).
**Related:** ADR 008 (airline attribution / star schema).

---

## Context

Designing the Silver-layer relational model (`architecture/silver-layer-er.md`) surfaced a problem
with the data the project had been collecting:

1. **OpenSky's `/flights/*` endpoints are not live.** They return *completed* flights, reconstructed
   retrospectively from ADS-B, with significant processing lag (the project's own docs already note
   arrivals need a 24–30 h look-back). Modelling them as a live fact was wrong.
2. **OpenSky has a genuinely live API we were not using: `/states/all`** (state vectors — live
   position/velocity/altitude). Content-wise this overlaps almost entirely with adsb.lol.
3. **adsb.lol's two original justifications had collapsed:** (a) "structured flights vs. raw
   positions" complementarity (ADR 003) disappears once OpenSky = States = positions; (b) "only
   source runnable on the Liora VM" (ADR 004) is moot since ADR 007 removed the Liora VM.
4. The live streams carry **no origin/destination airport** — only current position.

## Decision

1. **The Silver fact is `fact_states`**, fed by OpenSky `/states/all` (live "aircraft in the air").
   The retrospective `/flights/*` model (`fact_flights` / `positions`) is **dropped**.
2. **adsb.lol is demoted to Bronze-only.** Its collector keeps writing raw snapshots to the landing
   zone (MongoDB Atlas) for optionality and a later OpenSky-vs-adsb.lol data-quality comparison, but
   it is **not promoted** into the Silver model. *Ingestion ≠ modeling* (ADR 004).
3. **Dimensions (all verified against the real sources):**
   - `dim_aircraft` ← OpenSky `aircraftDatabase.csv` (free; icao24 → registration/type/operator).
   - `dim_airlines` ← OpenFlights `airlines.dat` (free, ODbL; ⚠ snapshot stale since 2017).
   - `dim_airports` ← OurAirports `airports.csv` (public domain) — **standalone reference, unjoined**.
4. **No `fact_delays` / `fact_flights`.** Delay analytics needs scheduled vs. actual times, which no
   chosen live source provides; origin/destination ("from/to") is therefore **unknown** in Silver
   and parked as a future Bronze-layer concern.

## Rationale

- States API gives **true live positions**; the Flights API does not (lag) and was being misused.
- adsb.lol content is a **subset** of OpenSky States once registration/type come from the AircraftDB
  (ADR 008); its remaining value is operational (no credit limit, redundancy) — a Bronze concern.
- The OpenSky **AircraftDB is far richer** than adsb.lol's `r`/`t` and uniquely provides the
  `operator_icao` that anchors airline attribution (see ADR 008).
- Keeping adsb.lol in Bronze preserves ADR 004's multi-source landing-zone thesis honestly.

**Rejected:** keeping the retrospective Flights model (not live); promoting adsb.lol to Silver
(redundant, adds dedup + unit-normalization cost); AirLabs Schedules as a delay source (free tier
paywalls the useful fields, 10 h look-ahead, 50 results — evaluated and declined, see
`02-api-docs/airline_api_market_overview.md`).

## Consequences

- `silver-layer-er.md` (renamed from `erd.md`) and `schema.sql` rewritten to the States-centric star.
- `data-flow.md` still references `fact_flights` / `fact_delays` / `/delays` in its API & Dashboard
  sections — **to be reworked next session**.
- adsb.lol collector stays as-is (Bronze); no Silver promotion path for it.
- Deprecated LH collectors (`airports_collector.py`, `airlines_collector.py`) remain a separate
  cleanup to-do (per project status notes).

## Related

- [`architecture/silver-layer-er.md`](../architecture/silver-layer-er.md), [ADR 003](003-dual-stream.md), [ADR 004](004-mongo-as-multisource-hub.md), [ADR 007](007-decouple-from-liora-vm.md), [ADR 008](008-airline-attribution-star-schema.md)
