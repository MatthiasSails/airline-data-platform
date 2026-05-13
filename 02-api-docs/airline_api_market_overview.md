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

## Other Providers (not evaluated)

| API | Cost | Notes |
|---|---|---|
| Airlabs | 500 req/month free | Schedules, status |
| AeroDataBox | 100 req/month free | Flight status, airport info |
| FlightAware | from ~$150/month | Professional grade |
| ADS-B Exchange | Free | Raw ADS-B, no filtering |
| Kaggle datasets | Free | Historical CSVs only |

---

## Next Steps

- [ ] Retry LH API registration or get shared token via mentor
- [ ] Build IATA↔ICAO mapping table (Phase 2)
- [ ] Evaluate Airlabs as fallback if LH token stays unavailable
