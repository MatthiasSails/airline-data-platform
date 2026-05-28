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

`connector.py` — `MongoConnector` with `from_env()` factory.

- `from_env()` reads `MONGO_URI` — the `airline-reader-ro` user (read-only). Use for exploration.
- `from_env(write=True)` reads `MONGO_URI_RW` — the `airline-collector-rw` user (write access). Use in collectors.

```python
from db.mongo.connector import from_env

# read-only exploration
mongo = from_env().connect()
coll = mongo.collection("opensky_raw")

# collector (writes documents)
mongo = from_env(write=True).connect()
```

## Environment

`.env` at project root (`airline-data-platform/.env`):

```
MONGO_URI=mongodb+srv://airline-reader-ro:<PASSWORD>@mongo-mk1.ptb1k2b.mongodb.net/?appName=mongo-mk1
MONGO_URI_RW=mongodb+srv://airline-collector-rw:<PASSWORD>@mongo-mk1.ptb1k2b.mongodb.net/?appName=mongo-mk1
MONGO_DB=airline_landing
```

Full access setup: [`docs/mongodb-access.md`](../../../docs/mongodb-access.md).
