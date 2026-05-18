# Airline API Market Overview

*Last updated: 2026-05-13 — onboarding doc for new sessions*

---

## Current Integration Status

| API | Status | Notes |
|---|---|---|
| **Lufthansa Public API** | ⚠️ Mock only | Registration broken, no token |
| **OpenSky Network** | ✅ Active | OAuth2, real data in PostgreSQL |
| **AviationStack** | ❌ Not used | 100 req/month, no HTTPS on free plan |

---

## Lufthansa Public API

- Swagger spec: `02-api-docs/LH_public_API_swagger_2_0.json`
- Auth: OAuth2 Client Credentials (`LH_CLIENT_ID`, `LH_CLIENT_SECRET` in `.env`)
- Code format: **IATA** (3 chars — `BER`, `LH`)
- Client: `03-data-collection/lufthansa_api/client.py`
- **Problem:** Registration at developer.lufthansa.com fails — no confirmation email. Tried twice. Mentor informed.

Key endpoints: `/references/airports`, `/references/airlines`, `/operations/flightstatus`, `/operations/schedules`

---

## OpenSky Network API

- Docs: `02-api-docs/opensky_api_doc.md`
- Auth: OAuth2 Client Credentials (`OPENSKY_CLIENT_ID`, `OPENSKY_CLIENT_SECRET` in `.env`)
- Code format: **ICAO** (4 chars — `EDDB`, `EDDM`)
- Client: `03-data-collection/opensky_api/client.py`
- Credits: 4,000/day (registered user)

Key endpoints: `/flights/departure`, `/flights/arrival`, `/flights/aircraft`

**⚠️ IATA vs ICAO mismatch:** LH airports use IATA, OpenSky flights use ICAO — no FK possible. IATA↔ICAO mapping table planned for Phase 2. See ERD in `architecture_m.md`.

---

## AviationStack (evaluated, rejected)

- Auth: API key as query parameter
- Free plan: 100 req/month, HTTP only
- Advantage: delivers both IATA + ICAO — would solve the mapping problem
- Worth revisiting if LH token stays unavailable

---

## ADS-B Exchange & Alternatives (Evaluated 2026-05-13)

### ADS-B Exchange via RapidAPI (⚠️ Not Recommended)

- **Cost:** $10/month (Community Tier)
- **Rate Limit:** 10,000 requests/month (~330/day)
- **Auth:** API key via HTTP header
- **Data:** Raw ADS-B (500ms update frequency, ICAO24 hex)
- **Status:** Commercial, restriction: "non-commercial use only" in ToS
- **Blocker:** Non-commercial restriction incompatible with DataScientest project context

### adsb.lol API (⭐ Recommended)

- **Cost:** $0 (Free, open-source, community-driven)
- **Rate Limit:** Dynamic based on load (very generous; no published hard limit)
- **Auth:** Currently none (future: API key for feeders; currently public)
- **Data:** Live ADS-B from global receiver network (ICAO24 hex, near-real-time)
- **Status:** ✅ Active, open-source, drop-in replacement for ADSBexchange.com
- **Advantage:** No licensing restrictions; compatible with existing ADSBExchange client code
- **Docs:** https://api.adsb.lol/docs (interactive OpenAPI)
- **Technical:** Python/asyncio/aiohttp, Kubernetes-hosted

**See also:** `adsb_lol_api_doc.md` for detailed API specification.

---

## Comparison: OpenSky vs adsb.lol vs ADSBExchange

| Dimension | OpenSky | adsb.lol | ADSBExchange RapidAPI |
|-----------|---------|----------|----------------------|
| **Cost** | Free | Free | $10/month |
| **Auth** | OAuth2 (required) | None (public) | API key |
| **Rate Limit** | 4,000 req/day (registered) | Dynamic/unlimited | 10,000 req/month |
| **Data Type** | Structured (flights, departures, arrivals) | Raw ADS-B (streaming) | Raw ADS-B (REST) |
| **Update Frequency** | Periodic | Near-real-time (500ms) | Per-request |
| **Code Format** | ICAO | ICAO24 hex | ICAO24 hex |
| **Historical Data** | 1 hour lookback | Limited | Per-request |
| **Licensing** | Academic-friendly, free non-commercial | Open-source (ODbL) | Non-commercial only ⚠️ |
| **Stability** | Academic (established) | Community (mature) | Commercial (volatile) |

**Phase 2 Hybrid Strategy (Recommended):**
- Primary: OpenSky (structured flight legs, status)
- Secondary: adsb.lol (raw position tracking, live updates, dashboard visualization)

See ADR 003 for detailed rationale.

---

## Static Reference Data

| Source | Cost | Content | Relevance |
|---|---|---|---|
| **OurAirports.com** | Free, CSV download | ~28k airports, IATA + ICAO + coordinates + country | ⭐ Solves the IATA↔ICAO mapping problem (ADR 003) |
| **OpenFlights.org** | Free, CSV | Airlines, airports, routes | Outdated but usable as fallback |
| **Kaggle (airline datasets)** | Free | Historical CSVs (e.g. BTS On-Time Performance) | Useful for backfill / testing |

**OurAirports import plan (Phase 2):** One-time CSV download from `ourairports.com/data/airports.csv` → load into `iata_icao_codes` table in PostgreSQL. Gives a stable join key between Lufthansa API (IATA) and OpenSky/adsb.lol (ICAO/ICAO24). No API calls needed, no rate limits.

---

## Other Providers (not evaluated)

| API | Cost | Notes |
|---|---|---|
| Airlabs | 500 req/month free | Schedules, status |
| AeroDataBox | 100 req/month free | Flight status, airport info |
| FlightAware | from ~$150/month | Professional grade |

---

## Next Steps

- [ ] Implement adsb.lol collector (Phase 2 start) — parallel to OpenSky
- [x] Evaluated ADS-B Exchange alternatives (completed 2026-05-13)
- [ ] Design IATA↔ICAO mapping table (Phase 2) — needed to join airports (IATA) ↔ flights (ICAO)
- [ ] Build MongoDB landing zone schema for raw ADS-B JSON (Phase 2)
- [ ] Retry LH API registration or get shared token via mentor (Phase 1, ongoing)
