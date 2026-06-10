# Airline API Market Overview

*Last updated: 2026-06-02*

> **Lufthansa Public API: closed.** No token was provided to the project; see [ADR 004](../adr/004-mongo-as-multisource-hub.md). The project proceeds without it.
>
> **Silver-model pivot (ADR 009, 2026-06-02):** the Silver warehouse is now built on OpenSky's
> **live `/states/all`** (not the retrospective `/flights/*`). **adsb.lol stays Bronze-only.** The
> aircraft dimension is sourced from the **OpenSky AircraftDB** and airlines from **OpenFlights**.

---

## Current Integration Status

| API | Status | Landing collection |
|---|---|---|
| **OpenSky `/states/all`** | ✅ Silver fact source (OAuth2) — live state vectors | `fact_states` (via Bronze) |
| **OpenSky AircraftDB** | ✅ `dim_aircraft` reference (free CSV) | one-shot loader |
| **adsb.lol** | ✅ Active, **Bronze-only** (no auth) — not promoted to Silver | `airline_landing.adsb_raw` |
| **OpenSky `/flights/*`** | ⏸ Dropped from Silver (retrospective, not live — ADR 009) | `airline_landing.opensky_raw` (Bronze) |
| **AviationStack** | ❌ Rejected (100 req/month, HTTP-only free plan) | — |
| **ADS-B Exchange (RapidAPI)** | ❌ Rejected (paid, non-commercial ToS) | — |

See [ADR 003](../adr/003-dual-stream.md) for the dual-stream rationale and [ADR 005](../adr/005-opensky-mongo-migration.md) for the OpenSky → MongoDB migration.

---

## OpenSky Network API

- Docs: `opensky_api_doc.md`
- Auth: OAuth2 Client Credentials (`OPENSKY_CLIENT_ID`, `OPENSKY_CLIENT_SECRET` in `.env`)
- Code format: **ICAO** (4 chars — `EDDB`, `EDDM`)
- Live access: `01-bronze/collectors/opensky_states_collector.py` (`/states/all`)
- Credits: 4,000/day (registered user)
- Key endpoints: `/flights/departure`, `/flights/arrival`, `/flights/aircraft`

**VM constraint:** Outbound HTTPS to `auth.opensky-network.org` is blocked by the DataScientest-managed Security Group on the Liora VM. OpenSky collection therefore runs on the local Mac only.

---

## adsb.lol API

- Docs: `adsb_lol_api_doc.md`
- Auth: none (public)
- Code format: **ICAO24 hex** (8 hex digits — aircraft identifier, not airport)
- Client: see `01-bronze/collectors/` and `explore_adsb_lol.ipynb`
- Rate limit: dynamic, generous; recommended 30–60 s polling interval
- Runs on the Liora VM (no auth, no SG restrictions)

---

## IATA ↔ ICAO Mapping

OpenSky uses ICAO airport codes, adsb.lol uses ICAO24 aircraft hex codes, downstream reporting often expects IATA. The mapping is solved by a one-shot import from **OurAirports.com** (`ourairports.com/data/airports.csv`) into `airline_landing.airports_ref` (MongoDB). No API calls, no rate limits. See [ADR 004](../adr/004-mongo-as-multisource-hub.md).

---

## Comparison: OpenSky vs adsb.lol

| Dimension | OpenSky | adsb.lol |
|-----------|---------|----------|
| **Cost** | Free | Free |
| **Auth** | OAuth2 (required) | None (public) |
| **Rate Limit** | 4,000 req/day (registered) | Dynamic/generous |
| **Data Type** | Structured (flights, departures, arrivals) | Raw ADS-B positions |
| **Update Frequency** | Periodic (request-based) | Near-real-time (500 ms from network) |
| **Code Format** | ICAO airport (4 chars) | ICAO24 aircraft hex (8 digits) |
| **Historical Lookback** | 1 hour | None (live only) |
| **Licensing** | Academic-friendly | Open-source (ODbL) |
| **VM reachable** | ❌ (SG blocks auth host) | ✅ |

---

## Rejected / Not Evaluated

| API | Cost | Reason |
|---|---|---|
| AviationStack | 100 req/month free, HTTP-only | Too restrictive, no HTTPS on free tier |
| ADS-B Exchange (RapidAPI) | $10/month | Non-commercial ToS incompatible with project |
| Airlabs Schedules | 500 req/month free | ❌ Evaluated & rejected (2026-06-02): free tier paywalls the useful fields (ICAO codes, actual/estimated times, delay, status), caps results at 50/query, and looks only ~10 h ahead. Revisit only if a paid tier is justified. |
| AeroDataBox | 100 req/month free | Not evaluated |
| FlightAware | from ~$150/month | Out of budget |

---

## Static Reference Data

| Source | Cost | Content | Use |
|---|---|---|---|
| **OurAirports.com** | Public-domain CSV (~12 MB, ~85k rows) | airports: IATA + ICAO + coords; most rows have **no** icao_code | `dim_airports` — load filtered to `icao_code IS NOT NULL` (ADR 004/009) |
| **OpenSky AircraftDB** | Free CSV (`aircraftDatabase.csv`) | icao24 → registration, type, manufacturer, model, built, **operator** | `dim_aircraft` (ADR 008/009); terms: research/non-commercial |
| **OpenFlights.org** | Free CSV (`airlines.dat`, ODbL) | airline ICAO/IATA/name/country | `dim_airlines` (ADR 009) — ⚠ **snapshot stale since 2017** |
| **Kaggle (airline datasets)** | Free | Historical CSVs (e.g. BTS On-Time) | Backfill / testing |
