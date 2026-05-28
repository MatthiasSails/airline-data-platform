# 03 — Data Collection

Ingestion layer of the Airline Data Platform. Python collectors and notebooks that write raw data from active sources into the MongoDB landing zone `airline_landing`.

## Data flow

```
adsb.lol (local or cloud VM)  ──►  MongoDB Atlas airline_landing.adsb_raw      ┐
OpenSky API (local Mac only)  ──►  MongoDB Atlas airline_landing.opensky_raw   ├─► (Phase 3) ETL → PostgreSQL Star Schema
OurAirports CSV (planned)     ──►  MongoDB Atlas airline_landing.airports_ref  ┘
```

Background: [ADR 004](../01-requirements/adr/004-mongo-as-multisource-hub.md), [ADR 005](../01-requirements/adr/005-opensky-mongo-migration.md).

## Index

| Path | Source | Role | Status |
|---|---|---|---|
| `opensky_api/client.py` | OpenSky | OAuth2 API client (live + mock) | active |
| `opensky_api/mock_data.py` | OpenSky | Mock responses for `--mock` runs | active |
| `collectors/opensky_collector.py` | OpenSky | Collector → `opensky_raw`, local only | active |
| `collect_opensky.ipynb` | OpenSky | Step-by-step collector walkthrough | active |
| `explore_opensky_api.ipynb` | OpenSky | Ad-hoc API exploration | active |
| `collectors/adsb_collector.py` | adsb.lol | Collector → `adsb_raw` (local or cloud VM) | active |
| `collect_adsb.ipynb` | adsb.lol | Step-by-step collector walkthrough | active |
| `explore_adsb_lol.ipynb` | adsb.lol | Ad-hoc API exploration | active |
| `explore_mongo_atlas.ipynb` | MongoDB Atlas | Landing zone inspection of all 3 collections incl. cross-join | active |
| `db/mongo/` | MongoDB | Connector + landing zone docs | active |
| `db/postgres/` | PostgreSQL | Connector + Phase-1 schema (for Phase 3 ETL) | active |

Convention: `collect_*.ipynb` = production walkthrough with MongoDB writes; `explore_*.ipynb` = ad-hoc inspection without side effects.

## Quickstart

### OpenSky (local only)

```bash
cd 03-data-collection

# Mock run — no credentials needed
python collectors/opensky_collector.py --mock

# Live, with credentials in .env (OPENSKY_CLIENT_ID / OPENSKY_CLIENT_SECRET):
python collectors/opensky_collector.py --hours 24
```

OpenSky auth (`auth.opensky-network.org`) is blocked from external VMs — collector must run locally (see ADR 005).

### adsb.lol (local or cloud VM)

```bash
cd 03-data-collection
python collectors/adsb_collector.py
# or continuous:
python collectors/adsb_collector.py --interval 60
```

### Inspect the landing zone

```bash
jupyter lab 03-data-collection/explore_mongo_atlas.ipynb
```

## Environment

`.env` at **project root** `airline-data-platform/.env` (local, gitignored):

```
OPENSKY_CLIENT_ID=...
OPENSKY_CLIENT_SECRET=...
MONGO_URI=mongodb+srv://airline-reader-ro:<password>@mongo-mk1.ptb1k2b.mongodb.net/airline_landing
MONGO_URI_RW=mongodb+srv://airline-collector-rw:<password>@mongo-mk1.ptb1k2b.mongodb.net/airline_landing
MONGO_DB=airline_landing
```

## API documentation

See [`../02-api-docs/`](../02-api-docs/) — OpenSky, adsb.lol, and market overview.

## Next steps

1. `airports_ref` loader (OurAirports CSV → MongoDB)
2. Phase 3 ETL: Mongo raw → PostgreSQL Star Schema (see `04-transform/` when created)
