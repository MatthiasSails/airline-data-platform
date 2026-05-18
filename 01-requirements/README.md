# Airline Data Engineering Project

## Repository Structure

```
Airline/
├── 01-requirements/              ← Projektdokumentation (dieses Verzeichnis)
│   ├── a-source/               ← Originaldokumente (unverändert, von extern)
│   │   ├── liora_airlines_original.pdf   ← Aufgabenstellung von Liora/DataScientest
│   │   └── mentor_update_nicolas.md      ← Klärungen & Updates vom Mentor Nicolas
│   ├── b-requirements/         ← Ausgearbeitete Projektanforderungen
│   │   ├── project_description_doc.md    ← Executive Summary, Ziele, Deliverables
│   │   ├── project_context_doc.md        ← Technischer Projektkontext
│   │   └── timeline_m.md                 ← Meilenstein-Timeline (Mermaid Gantt)
│   └── c-architecture/         ← Architekturentscheidungen & Diagramme
│       ├── architecture_m.md             ← Systemarchitektur (Mermaid)
│       └── dataflow_doc.md               ← Dataflow-Beschreibung (Prosa)
│
├── 02-api-docs/                  ← Lufthansa Public API Dokumentation
│   ├── LH_public_API_swagger_2_0.json    ← Vollständige Swagger/OpenAPI Spec
│   └── README.md                         ← API Übersicht & Auth-Hinweise
│
├── 03-data-collection/           ← Step 1: Datenbeschaffung (Python)
│   ├── lufthansa_api/            ← API-Client Package
│   │   ├── client.py             ← Haupt-Client (mock + real mode)
│   │   ├── mock_data.py          ← Sample-Daten für Entwicklung ohne Credentials
│   │   └── schemas.py            ← Datenmodelle
│   ├── opensky_api/              ← OpenSky Network Client (OAuth2)
│   │   ├── client.py
│   │   ├── mock_data.py
│   │   └── schemas.py
│   ├── collectors/               ← Standalone Collector-Scripts
│   │   ├── airports_collector.py ← Flughäfen → PostgreSQL
│   │   ├── airlines_collector.py ← Airlines → PostgreSQL
│   │   └── adsb_collector.py     ← ADS-B Positionen → MongoDB Landing Zone
│   ├── db/
│   │   ├── postgres/             ← PostgreSQL Connector + Schema
│   │   │   ├── connector.py
│   │   │   └── schema.sql
│   │   └── mongo/                ← MongoDB Connector (Landing Zone)
│   │       └── connector.py
│   ├── explore_lh_api.ipynb      ← Lufthansa API Exploration
│   ├── explore_opensky_api.ipynb ← OpenSky API Exploration
│   ├── explore_adsb_lol.ipynb    ← adsb.lol API Exploration
│   ├── explore_mongo_vm.ipynb    ← MongoDB Landing Zone Exploration
│   ├── collect_adsb.ipynb        ← ADS-B Collector: Schritt-für-Schritt Walkthrough
│   └── demo.py                   ← Demo-Script (läuft ohne Credentials)
│
└── 04-dashboard/                 ← Step 1 Deliverable: Landing Zone Visualisierung
    └── adsb-dashboard/           ← Streamlit App (live auf Liora VM, Port 8502)
        ├── app.py
        ├── Dockerfile
        ├── docker-compose.yml
        └── deploy.sh
```

## Geplante Verzeichnisse (noch nicht angelegt)

```
Airline/
├── 05-backend/                   ← FastAPI Service
├── 06-devops/                    ← Docker Compose, CI/CD, GitHub Actions
└── 07-final-defense/             ← Präsentation & Demo
```

---

## File Naming Convention

| Typ | Suffix / Pattern | Beispiel |
|---|---|---|
| Reine Mermaid-Diagramme | `*_m.md` | `architecture_m.md`, `timeline_m.md` |
| Architekturtext / Prosa | `*_doc.md` | `dataflow_doc.md` |
| Architekturentscheidungen | `adr_NNN_*.md` | `adr_001_postgres_vs_mongo.md` |
| Meeting Notes | `meeting_YYYY-MM-DD.md` | `meeting_2026-05-10.md` |
| Quelldokumente (original) | in `a-source/` | `liora_airlines_original.pdf` |
