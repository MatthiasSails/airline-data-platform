# 03 — Data Collection

Ingestion-Layer der Airline Data Platform. Python Collectors + Notebooks, die Rohdaten aus aktiven Quellen in die MongoDB Landing Zone `airline_landing` schreiben.

## Datenfluss

```
adsb.lol (Liora VM, no auth)  ──►  MongoDB airline_landing.adsb_raw     ┐
OpenSky API (lokaler Mac)     ──►  MongoDB airline_landing.opensky_raw  ├─► (Phase 3) ETL → PostgreSQL Star Schema
OurAirports CSV (geplant)     ──►  MongoDB airline_landing.airports_ref ┘
```

Hintergrund: [`adr/004-mongo-as-multisource-hub.md`](../01-requirements/adr/004-mongo-as-multisource-hub.md), [`adr/005-opensky-mongo-migration.md`](../01-requirements/adr/005-opensky-mongo-migration.md).

## Index

| Pfad | Quelle | Rolle | Status |
|---|---|---|---|
| `opensky_api/client.py` | OpenSky | OAuth2 API Client (Live + Mock) | aktiv |
| `opensky_api/mock_data.py` | OpenSky | Mock-Responses für `--mock` Lauf | aktiv |
| `collectors/opensky_collector.py` | OpenSky | Collector → `opensky_raw`, lokal | aktiv |
| `collect_opensky.ipynb` | OpenSky | Produktiver Walkthrough Collector | aktiv |
| `explore_opensky_api.ipynb` | OpenSky | Ad-hoc API Exploration | aktiv |
| `collectors/adsb_collector.py` | adsb.lol | Collector → `adsb_raw`, Cron auf Liora VM | aktiv |
| `collect_adsb.ipynb` | adsb.lol | Produktiver Walkthrough Collector | aktiv |
| `explore_adsb_lol.ipynb` | adsb.lol | Ad-hoc API Exploration | aktiv |
| `explore_mongo_vm.ipynb` | MongoDB | Landing Zone Inspektion (quellen-übergreifend) | aktiv |
| `db/mongo/` | MongoDB | Connector + Doku Landing Zone | aktiv |
| `db/postgres/` | PostgreSQL | Connector + Phase-1-Schema (für Phase 3 ETL) | aktiv |
| Lufthansa API | — | — | **geschlossen** (kein Key, ADR 004) |

Konvention: `collect_*.ipynb` = produktiver Walkthrough mit Mongo-Write; `explore_*.ipynb` = ad-hoc Inspektion ohne Side-Effects.

## Quickstart

### OpenSky (lokal)

```bash
cd 03-data-collection

# Mock-Lauf, keine Credentials nötig
python collectors/opensky_collector.py --mock

# Live, mit Credentials in .env (OPENSKY_CLIENT_ID / OPENSKY_CLIENT_SECRET):
python collectors/opensky_collector.py --hours 24
```

OpenSky-Auth ist von der Liora VM blockiert — Collector muss lokal laufen (siehe ADR 005).

### adsb.lol (Liora VM)

Läuft als Cron auf `Liora_VM`. Manuell:

```bash
ssh Liora_VM
cd /opt/airline-data-platform/03-data-collection
python collectors/adsb_collector.py
```

### Landing Zone inspizieren

```bash
jupyter lab explore_mongo_vm.ipynb
```

## Environment

`.env` in `03-data-collection/` (lokal, gitignored):

```
OPENSKY_CLIENT_ID=...
OPENSKY_CLIENT_SECRET=...
MONGO_URI=mongodb://localhost:27017
MONGO_DB=airline_landing
```

## API-Dokumentation

Siehe [`../02-api-docs/`](../02-api-docs/) — OpenSky, adsb.lol, sowie Markt-Überblick.

## Nächste Schritte

1. `airports_ref` Loader (OurAirports CSV → MongoDB)
2. Phase 3 ETL: Mongo Raw → PostgreSQL Star Schema (siehe `04-transform/` sobald angelegt)
