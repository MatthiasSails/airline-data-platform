# Airline Data Engineering Project

## Repository Structure

```
Airline/
├── 01 Requirements/              ← Projektdokumentation (dieses Verzeichnis)
│   ├── A - source/               ← Originaldokumente (unverändert, von extern)
│   │   ├── liora_airlines_original.pdf   ← Aufgabenstellung von Liora/DataScientest
│   │   └── mentor_update_nicolas.md      ← Klärungen & Updates vom Mentor Nicolas
│   ├── B - requirements/         ← Ausgearbeitete Projektanforderungen
│   │   ├── project_description_doc.md    ← Executive Summary, Ziele, Deliverables
│   │   ├── project_context_doc.md        ← Technischer Projektkontext
│   │   └── timeline_m.md                 ← Meilenstein-Timeline (Mermaid Gantt)
│   └── C - architecture/         ← Architekturentscheidungen & Diagramme
│       ├── architecture_m.md             ← Systemarchitektur (Mermaid)
│       └── dataflow_doc.md               ← Dataflow-Beschreibung (Prosa)
│
├── 02 API docs/                  ← Lufthansa Public API Dokumentation
│   ├── LH_public_API_swagger_2_0.json    ← Vollständige Swagger/OpenAPI Spec
│   └── README.md                         ← API Übersicht & Auth-Hinweise
│
└── 03 Data Collection/           ← Step 1: Datenbeschaffung (Python)
    ├── lufthansa_api/            ← API-Client Package
    │   ├── client.py             ← Haupt-Client (mock + real mode)
    │   ├── mock_data.py          ← Sample-Daten für Entwicklung ohne Credentials
    │   └── schemas.py            ← Datenmodelle
    ├── collectors/               ← Standalone Collector-Scripts
    │   ├── airports_collector.py ← Flughäfen abrufen & speichern
    │   └── airlines_collector.py ← Airlines abrufen & speichern
    ├── data/                     ← Output-Verzeichnis (JSON → MongoDB landing zone)
    ├── demo.py                   ← Demo-Script (läuft ohne Credentials)
    └── requirements.txt
```

## Geplante Verzeichnisse (noch nicht angelegt)

```
Airline/
├── 04 Data Engineering/          ← ETL, PostgreSQL Warehouse, Airflow DAGs
├── 05 Backend/                   ← FastAPI Service
├── 06 Dashboard/                 ← Streamlit / Dash Frontend
├── 07 DevOps/                    ← Docker Compose, CI/CD, GitHub Actions
└── 08 Final Defense/             ← Präsentation & Demo
```

---

## File Naming Convention

| Typ | Suffix / Pattern | Beispiel |
|---|---|---|
| Reine Mermaid-Diagramme | `*_m.md` | `architecture_m.md`, `timeline_m.md` |
| Architekturtext / Prosa | `*_doc.md` | `dataflow_doc.md` |
| Architekturentscheidungen | `adr_NNN_*.md` | `adr_001_postgres_vs_mongo.md` |
| Meeting Notes | `meeting_YYYY-MM-DD.md` | `meeting_2026-05-10.md` |
| Quelldokumente (original) | in `A - source/` | `liora_airlines_original.pdf` |
