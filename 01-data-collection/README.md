# 01 — Data Collection

Ingestion layer of the Airline Data Platform. Python collectors and notebooks that write raw data from active sources into the MongoDB landing zone `airline_landing`.

## Data flow

```
adsb.lol (local or cloud VM)       ──►  MongoDB Atlas airline_landing.adsb_raw     ┐
OpenSky /states/all (local only)   ──►  MongoDB Atlas airline_landing.opensky_raw  ├─► ETL → Supabase map1 (Silver)
OurAirports CSV (planned)          ──►  MongoDB Atlas airline_landing.airports_ref ┘
```

ETL lives in [`../02-data-modeling/etl/opensky_to_supabase.py`](../02-data-modeling/etl/opensky_to_supabase.py).
Background: [ADR 003](../docs/adr/003-dual-stream-adsb.md), [ADR 004](../docs/adr/004-mongo-as-multisource-hub.md), [ADR 009](../docs/adr/009-states-api-silver-model.md).

## Index

| Path | Source | Role | Status |
|---|---|---|---|
| `opensky_api/client.py` | OpenSky | OAuth2 API client (live + mock) | active |
| `opensky_api/mock_data.py` | OpenSky | Mock responses for `--mock` runs | active |
| `collectors/opensky_states_collector.py` | OpenSky | `/states/all` → `opensky_raw` (local Mac only) | **active** |
| `collectors/opensky_collector.py` | OpenSky | `/flights/*` → `opensky_raw` (local only) | legacy — retired per ADR 009 |
| `collect_opensky.ipynb` | OpenSky | Step-by-step collector walkthrough | active |
| `explore_opensky_api.ipynb` | OpenSky | Ad-hoc API exploration | active |
| `collectors/adsb_collector.py` | adsb.lol | `/v2` → `adsb_raw` (local or cloud VM) | active |
| `collect_adsb.ipynb` | adsb.lol | Step-by-step collector walkthrough | active |
| `explore_adsb_lol.ipynb` | adsb.lol | Ad-hoc API exploration | active |
| `explore_mongo_atlas.ipynb` | MongoDB Atlas | Landing zone inspection, all collections + cross-join | active |
| `db/mongo/` | MongoDB | Connector + landing zone docs | active |

> The PostgreSQL connector + schema (Silver) are in [`../02-data-modeling/warehouse/`](../02-data-modeling/warehouse/).

Convention: `collect_*.ipynb` = production walkthrough with MongoDB writes; `explore_*.ipynb` = ad-hoc inspection without side effects.

## Quickstart

### OpenSky (local Mac only)

```bash
cd 01-data-collection

# Active collector — /states/all (live flight positions, Europe bounding box):
python collectors/opensky_states_collector.py
python collectors/opensky_states_collector.py --interval 60  # continuous
```

> OpenSky OAuth2 (`auth.opensky-network.org`) is blocked from external VMs — collector must run locally (see ADR 004, ADR 009).

### adsb.lol (local or cloud VM)

```bash
cd 01-data-collection
python collectors/adsb_collector.py
python collectors/adsb_collector.py --interval 60  # continuous
```

### Inspect the landing zone

```bash
# Via local JupyterLab:
jupyter lab 01-data-collection/explore_mongo_atlas.ipynb

# Via the JupyterLab container on aws-airline-1:
# http://airline.matthiaskoehler.com:8888  (token in .env → JUPYTER_TOKEN)
```

## Environment

`.env` at **project root** `airline-data-platform/.env` (local, gitignored):

```
OPENSKY_CLIENT_ID=...
OPENSKY_CLIENT_SECRET=...
MONGO_URI=mongodb+srv://airline-reader-ro:<password>@mongo-mk1.ptb1k2b.mongodb.net/airline_landing
MONGO_URI_RW=mongodb+srv://airline-collector-rw:<password>@mongo-mk1.ptb1k2b.mongodb.net/airline_landing
MONGO_DB=airline_landing
JUPYTER_TOKEN=...         # used by the JupyterLab Docker container
```

## API documentation

See [`../docs/data-sources/`](../docs/data-sources/) — OpenSky, adsb.lol, and market overview.
