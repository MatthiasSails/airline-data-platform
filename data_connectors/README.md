# Data Connectors

Provider-abstracted database access for the Airline Data Platform (see
[`docs/adr/011-layer-named-folders-connector-abstraction-ml.md`](../docs/adr/011-layer-named-folders-connector-abstraction-ml.md)).
Connectors are shared by multiple layers (Silver ETL writes, Gold apps read), so they live here —
in no single numbered layer.

| File | Store | Used by |
|---|---|---|
| `mongo.py` | MongoDB Atlas — **Bronze** raw landing zone (`airline_landing`) | collectors (`01-bronze/`) |
| `supabase.py` | Supabase/PostgreSQL — **Silver** (and later Gold) | ETL (`02-silver/etl/`) |

This is an **importable Python package** (underscore name, with `__init__.py`). Consumers add the
repo root to `sys.path` and import e.g. `from data_connectors.mongo import from_env` (see the
collectors in `01-bronze/collectors/`).

> **ADR 011 follow-up (not yet done):** introduce the Ports & Adapters split — an abstract
> `base.py` (`SourceStore`, `WarehouseStore`) plus a `factory.py` selecting the adapter from env, so
> the ETL depends on the interface instead of `psycopg2`/`pymongo` directly. The current
> `mongo.py` / `supabase.py` are the existing concrete connectors, moved here unchanged
> (`02-silver/etl/opensky_to_supabase.py` still calls `psycopg2`/`pymongo` directly).

---

## Bronze — `mongo.py` (MongoDB landing zone)

Multi-source raw landing zone. Database: **`airline_landing`**.

See ADRs:
- [`adr/001-postgres-first.md`](../docs/adr/001-postgres-first.md) — original phase plan
- [`adr/004-mongo-as-multisource-hub.md`](../docs/adr/004-mongo-as-multisource-hub.md) — Mongo as multi-source hub
- [`adr/005-opensky-mongo-migration.md`](../docs/adr/005-opensky-mongo-migration.md) — OpenSky local → Mongo

### Collections

| Collection | Source | Status | Description |
|---|---|---|---|
| `opensky_raw` | OpenSky API (OAuth2) | active | Departures/arrivals for EDDB, 1 document per API call. Runs locally (Mac) — auth blocked on external VMs |
| `adsb_raw` | adsb.lol (no auth) | active | Live ADS-B snapshots, cron on cloud VM |
| `airports_ref` | OurAirports CSV | planned | Static ICAO ↔ IATA mapping |
| `kaggle_*` | Kaggle reference sets | planned | Historical reference data |

### Connector

`MongoConnector` with `from_env()` factory.

- `from_env()` reads `MONGO_URI` — the `airline-reader-ro` user (read-only). Use for exploration.
- `from_env(write=True)` reads `MONGO_URI_RW` — the `airline-collector-rw` user (write access). Use in collectors.

## Environment

`.env` at project root (`airline-data-platform/.env`):

```
MONGO_URI=mongodb+srv://airline-reader-ro:<PASSWORD>@mongo-mk1.ptb1k2b.mongodb.net/?appName=mongo-mk1
MONGO_URI_RW=mongodb+srv://airline-collector-rw:<PASSWORD>@mongo-mk1.ptb1k2b.mongodb.net/?appName=mongo-mk1
MONGO_DB=airline_landing
```

Full access setup: [`docs/mongodb-access.md`](../docs/mongodb-access.md).
