# API Documentation

Reference docs for the data sources used by the airline data platform. All raw responses land in MongoDB (`airline_landing.*`); see [ADR 004](../01-requirements/adr/004-mongo-as-multisource-hub.md).

| File | Source | Status |
|---|---|---|
| [`airline_api_market_overview.md`](airline_api_market_overview.md) | Cross-source comparison, integration status, rejected APIs | ✅ Current |
| [`opensky_api_doc.md`](opensky_api_doc.md) | OpenSky Network — endpoints, auth, known gotchas | ✅ Current |
| [`adsb_lol_api_doc.md`](adsb_lol_api_doc.md) | adsb.lol — endpoints, schema, ETL notes | ✅ Current |

## Not documented here

- **Lufthansa Public API** — closed, no token. Decision in [ADR 004](../01-requirements/adr/004-mongo-as-multisource-hub.md). The Swagger spec and LH-specific docs were removed on 2026-05-18.
