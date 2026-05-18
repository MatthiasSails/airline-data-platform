# MongoDB — Raw Landing Zone (Phase 2)

Multi-Source Raw Landing Zone der Airline Data Platform. Database: **`airline_landing`**.

Siehe ADRs:
- [`adr/001-postgres-first.md`](../../../01-requirements/adr/001-postgres-first.md) — ursprünglicher Phasen-Plan
- [`adr/004-mongo-as-multisource-hub.md`](../../../01-requirements/adr/004-mongo-as-multisource-hub.md) — Mongo als Multi-Source Hub
- [`adr/005-opensky-mongo-migration.md`](../../../01-requirements/adr/005-opensky-mongo-migration.md) — OpenSky lokal → Mongo

## Collections

| Collection | Quelle | Status | Beschreibung |
|---|---|---|---|
| `opensky_raw` | OpenSky API (OAuth2) | aktiv | Departures/Arrivals für EDDB, 1 Dokument pro API-Call. Läuft lokal (Mac) — Auth von Liora VM blockiert |
| `adsb_raw` | adsb.lol (no auth) | aktiv | Live ADS-B Snapshots, Cron auf Liora VM |
| `airports_ref` | OurAirports CSV | geplant | Statisches ICAO ↔ IATA Mapping (Ersatz für nie erhaltenen LH API Key) |
| `kaggle_*` | Kaggle Reference Sets | geplant | Historische Referenzdaten |

## Connector

`connector.py` — `MongoConnector` mit `from_env()` Factory. Liest `MONGO_URI` und `MONGO_DB` aus `.env`.

```python
from db.mongo.connector import from_env

mongo = from_env().connect()
coll = mongo.collection("opensky_raw")
```

## Environment

```
MONGO_URI=mongodb://localhost:27017         # lokal (OpenSky Collector)
MONGO_URI=mongodb://<liora-vm>:27017        # VM (adsb.lol Collector)
MONGO_DB=airline_landing
```
