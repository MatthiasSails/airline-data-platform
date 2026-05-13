# Airline API Market Overview

Status as of 2026-05-13. Written to onboard a new session quickly.

---

## Current Status

| API | Status | Integration |
|---|---|---|
| **Lufthansa Public API** | ⚠️ No token — registration broken | Mock mode only |
| **OpenSky Network** | ✅ Active — OAuth2 working | Real data in PostgreSQL |
| **AviationStack** | 🔍 Evaluated — not used | Too limited for dev use |

---

## Lufthansa Public API

- **Docs:** https://developer.lufthansa.com
- **Swagger spec:** `02-api-docs/LH_public_API_swagger_2_0.json` (in git)
- **Auth:** OAuth2 Client Credentials
- **Cost:** Free (registration required)
- **Status:** Registration attempted twice with different email addresses — no confirmation email arrives. Known issue on LH Developer Portal side. Mentor (NicoTheDataSherpa) informed via Slack.

**Available endpoints (from Swagger spec):**
```
/references/airports/{airportCode}
/references/airports/nearest/{latitude},{longitude}
/references/airlines/{airlineCode}
/references/cities/{cityCode}
/references/countries/{countryCode}
/references/aircraft/{aircraftCode}
/operations/flightstatus/{flightNumber}/{date}
/operations/flightstatus/arrivals/{airportCode}/{fromDateTime}
/operations/flightstatus/departures/{airportCode}/{fromDateTime}
/operations/flightstatus/route/{origin}/{destination}/{date}
/operations/schedules/{origin}/{destination}/{fromDateTime}
```

**Code format:** IATA (3 chars — `BER`, `LH`)

**Client:** `03-data-collection/lufthansa_api/client.py`
- `use_mock=True` (default) — no token needed, uses `mock_data.py`
- `use_mock=False` — requires `LH_CLIENT_ID` + `LH_CLIENT_SECRET` in `.env`

---

## OpenSky Network API

- **Docs:** https://opensky-network.org/apidoc
- **Our API doc:** `02-api-docs/opensky_api_doc.md` (in git)
- **No Swagger spec available**
- **Auth:** OAuth2 Client Credentials (separate from website login)
- **Cost:** Free — 4,000 credits/day for registered users
- **Account:** registered as `delius` — credentials in `.env`

**Available endpoints (used):**
```
POST https://auth.opensky-network.org/.../token   → get Bearer token
GET  /api/flights/departure?airport=EDDB&begin=...&end=...
GET  /api/flights/arrival?airport=EDDB&begin=...&end=...
GET  /api/flights/aircraft?icao24=...&begin=...&end=...
GET  /api/states/all                               → live positions
```

**Code format:** ICAO (4 chars — `EDDB`, `EDDM`)

**⚠️ Important — IATA vs ICAO mismatch:**
- LH API → airports table uses **IATA** codes (`BER`)
- OpenSky → flights table uses **ICAO** codes (`EDDB`)
- No foreign key possible between the two tables currently
- Solution planned for Phase 2: IATA↔ICAO mapping table
- Documented in: `01-requirements/c-architecture/architecture_m.md` (ERD section)

**Client:** `03-data-collection/opensky_api/client.py`
- `use_mock=True` — uses `mock_data.py` (no API calls, no credits)
- `use_mock=False` — requires `OPENSKY_CLIENT_ID` + `OPENSKY_CLIENT_SECRET` in `.env`

---

## AviationStack (evaluated, not used)

- **Docs:** https://aviationstack.com/documentation
- **No Swagger/OpenAPI spec**
- **Auth:** API Key as query parameter
- **Cost:**
  - Free: 100 requests/month, HTTP only (no HTTPS)
  - Paid: from ~$50/month
- **Decision:** Not integrated — 100 requests/month too limiting for development, no HTTPS on free plan is a security concern.
- **Advantage over OpenSky:** delivers both IATA and ICAO codes — would solve the mapping problem. Worth revisiting if LH token stays unavailable.

**Endpoints available:**
```
GET /v1/flights     → live status + historical
GET /v1/airports    → IATA + ICAO codes
GET /v1/airlines
GET /v1/routes
GET /v1/airplanes
```

---

## Other APIs (not evaluated)

| API | Notes | Cost |
|---|---|---|
| **FlightAware** | Professional, reliable | from ~$150/month |
| **FlightRadar24** | No public API | Business only |
| **Aviation Edge** | Schedules, status | from ~$50/month |
| **AeroDataBox** | Flight status, airport info | 100 req/month free |
| **Airlabs** | Schedules, status | 500 req/month free |
| **ADS-B Exchange** | Raw ADS-B live data, no filter | Free, no account |
| **Kaggle datasets** | Historical CSVs (e.g. Bureau of Transportation) | Free, one-time |

---

## Architecture Decision

See `01-requirements/c-architecture/adr_001_postgresql_first_mongodb_phase2.md`

The project uses a **mock-first approach**:
1. Build pipeline with mock data → validate structure
2. Switch to real API when token available (`use_mock=False`)
3. No code changes needed — only `.env` credentials

---

## Next Steps (API related)

- [ ] Retry LH API registration or ask mentor for a shared token
- [ ] Build IATA↔ICAO mapping table (Phase 2)
- [ ] Evaluate Airlabs as fallback if LH token stays unavailable
- [ ] Add more mock flight data for `lufthansa_api/mock_data.py`
