# MongoDB — Raw Landing Zone (Phase 2)

Multi-source raw landing zone of the Airline Data Platform. Database: **`airline_landing`**.

See ADRs:
- [`adr/001-postgres-first.md`](../../../01-requirements/adr/001-postgres-first.md) — original phase plan
- [`adr/004-mongo-as-multisource-hub.md`](../../../01-requirements/adr/004-mongo-as-multisource-hub.md) — Mongo as multi-source hub
- [`adr/005-opensky-mongo-migration.md`](../../../01-requirements/adr/005-opensky-mongo-migration.md) — OpenSky local → Mongo

## Collections

| Collection | Source | Status | Description |
|---|---|---|---|
| `opensky_raw` | OpenSky API (OAuth2) | active | Departures/arrivals for EDDB, 1 document per API call. Runs locally (Mac) — auth blocked on external VMs |
| `adsb_raw` | adsb.lol (no auth) | active | Live ADS-B snapshots, cron on cloud VM |
| `airports_ref` | OurAirports CSV | planned | Static ICAO ↔ IATA mapping |
| `kaggle_*` | Kaggle reference sets | planned | Historical reference data |

## Connector

`connector.py` — `MongoConnector` with `from_env()` factory. Reads `MONGO_URI` and `MONGO_DB` from `.env`.

```python
from db.mongo.connector import from_env

mongo = from_env().connect()
coll = mongo.collection("opensky_raw")
```

## Environment

`.env` at project root (`airline-data-platform/.env`):

```
MONGO_URI=mongodb+srv://airline-collector-rw:<PASSWORD>@mongo-mk1.ptb1k2b.mongodb.net/?appName=mongo-mk1
MONGO_DB=airline_landing
```

For read-only notebooks: use `airline-reader-ro` credentials.
Full access setup: [`docs/mongodb-access.md`](../../../docs/mongodb-access.md).
