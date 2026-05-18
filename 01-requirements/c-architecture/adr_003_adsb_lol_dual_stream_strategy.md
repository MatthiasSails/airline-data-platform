# ADR 003 — Dual-Stream ADS-B Strategy: OpenSky + adsb.lol

**Status:** Proposed  
**Date:** 2026-05-13  
**Author:** Session consolidation (2026-05-13)

---

## Context

Phase 2 calls for a two-layer data architecture:

```
APIs → MongoDB (raw landing zone) → ETL → PostgreSQL (curated warehouse)
```

The current Phase 1 uses **OpenSky Network API** for live flight data (OAuth2, structured response format, ICAO codes, 4,000–8,000 req/day free).

In parallel, we need a data source for **raw ADS-B signals** to enable:
- Live aircraft position tracking (for dashboard visualization)
- Higher temporal granularity than OpenSky provides
- Global coverage without subscription costs

Previously, **ADS-B Exchange (RapidAPI, $10/mo)** was the only known commercial provider. However, evaluation (2026-05-13) identified two problems:

1. **Licensing Restriction:** ADS-B Exchange ToS states "non-commercial use only," which conflicts with DataScientest project context (educational, but commercial platform)
2. **Cost & Availability:** $10/month not required if viable free alternative exists

---

## Decision

Adopt a **dual-stream data collection strategy** for Phase 2:

1. **OpenSky Network** — Primary structured source
   - Flight departures, arrivals, aircraft tracking
   - Curated for accuracy and detail
   - Target: PostgreSQL directly

2. **adsb.lol** — Secondary raw ADS-B source
   - Unfiltered global aircraft positions
   - Real-time updates from community receiver network
   - Target: MongoDB landing zone (raw JSON)

Both streams flow into the same PostgreSQL warehouse via ETL (Phase 2). OpenSky provides structure; adsb.lol provides granularity.

---

## Rationale

### Why adsb.lol (not ADSBExchange RapidAPI)?

- **Cost:** Free (vs. $10/month)
- **Licensing:** Open-source (ODbL), no "non-commercial only" restriction
- **Compatibility:** Drop-in replacement API for existing ADSBExchange integrations
- **Stability:** Community-driven (mature) vs. commercial (volatile)
- **Rate Limits:** Dynamic and generous (no published hard cap, vs. 10k req/month)

### Why keep OpenSky?

- **Complementary data:** Structured flight legs (callsign, airport pair, timestamps) vs. raw positions
- **Reliability:** Established academic network (17+ years)
- **Learning value:** Two contrasting architectures (structured API + raw stream)
- **Coverage:** Different receiver networks → merged view improves global visibility

### Why MongoDB for raw ADS-B?

- Raw ADS-B responses are large, nested JSON — schema-on-read better than schema-on-write
- Replay raw → ETL → PostgreSQL is the core data engineering pattern here
- Demonstrates flexible NoSQL landing zone (key Phase 1 learning objective per mentor)

---

## Implementation Notes

### IATA ↔ ICAO Mapping

- **OpenSky:** Airports use ICAO codes (4 chars: `EDDB`, `EDDM`)
- **Lufthansa API:** Airports use IATA codes (3 chars: `BER`, `MUC`)
- **adsb.lol:** Aircraft use ICAO24 hex (8 hex digits: `780338`); no airport code

**Solution:** Phase 2 must include a mapping table `iata_icao_codes` to join:
- Lufthansa airports (IATA) ↔ OpenSky airports (ICAO)
- Not needed for adsb.lol (no airport codes in response)

See `architecture_m.md` ERD section for foreign key design.

### Data Flow (Phase 2)

```
Lufthansa API (IATA)    →  Skipped if token unavailable
OpenSky API (ICAO)       →  PostgreSQL directly
adsb.lol API (ICAO24)    →  MongoDB raw landing zone
                             ↓
                             ETL (Python + Pandas)
                             ↓
                             PostgreSQL (enriched)
```

---

## Consequences

**Phase 2 Deliverables (updated):**
- adsb.lol collector module (`collectors/adsb_collector.py`)
- MongoDB schema and connector (`db/mongo/connector.py`)
- ETL pipeline for raw ADS-B flattening
- IATA ↔ ICAO mapping table

**Tech Stack Addition:**
- No new external dependency (adsb.lol is HTTP REST, same as OpenSky)
- MongoDB Python driver: `pymongo` (Phase 2)

**Rollback Plan:**
If adsb.lol service degrades, revert to ADSBExchange RapidAPI ($10/mo) or Airlabs free tier (500 req/month, lower precision).

---

## Related

- ADR 001: PostgreSQL first (Phase 1), MongoDB phase 2
- `02-api-docs/airline_api_market_overview.md` — API comparison matrix
- `02-api-docs/adsb_lol_api_doc.md` — adsb.lol API specification
- `architecture_m.md` (Phase 2 diagram) — two-layer MongoDB → PostgreSQL
