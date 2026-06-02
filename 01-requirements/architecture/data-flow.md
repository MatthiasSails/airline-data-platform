# Airline Data Flow Architecture

# High-Level Goal

Build a pragmatic and understandable Data Engineering platform for airline data.

Main design goals:
- simple
- reproducible
- dockerized
- explainable
- extensible

---

# High-Level Data Flow

External Airline APIs
        ↓
Data Collector Services
        ↓
Raw JSON Storage (MongoDB)
        ↓
ETL / Transformation
        ↓
Curated Warehouse (PostgreSQL)
        ↓
FastAPI
        ↓
Dashboards / Analytics / ML

---

# MongoDB Role

MongoDB acts as:
- raw landing zone
- ingestion buffer
- schema-flexible storage

Why MongoDB:
- APIs return nested JSON
- minimal preprocessing needed
- preserves original payloads
- easier debugging
- supports schema evolution

Typical stored data:
- flights
- schedules
- airports
- airline metadata
- delay data

---

# PostgreSQL Role

PostgreSQL acts as:
- curated warehouse
- analytics layer
- relational reporting database

Why PostgreSQL:
- SQL analytics
- joins
- aggregations
- stable schema
- BI-friendly

Typical tables:
- fact_states   (live position/state events — central fact)
- dim_aircraft
- dim_airports
- dim_airlines

(Note: `fact_delays` / `fact_flights` dropped — the live States/adsb.lol streams carry no
scheduled vs. actual times, so delay analytics is out of scope. See silver-layer-er.md gotchas.)

---

# ETL Layer

Responsibilities:
- normalize JSON
- validate data
- deduplicate records
- transform timestamps
- create dimensions/facts
- aggregate metrics

Possible technologies:
- Python
- Pandas
- SQLAlchemy

---

# API Layer

Technology:
- FastAPI

Responsibilities:
- expose analytics
- provide REST endpoints
- support dashboard frontend
- serve ML predictions

Possible endpoints:
- /flights
- /routes
- /airports
- /delays
- /predictions

---

# Dashboard Layer

Possible technologies:
- Dash
- Plotly
- Streamlit

Potential features:
- route maps
- delay analytics
- airline KPIs
- airport statistics

---

# Optional Future Extensions

## Kafka

Possible use:
- streaming ingestion
- event pipelines
- real-time updates

Not required initially.

---

## Spark

Possible use:
- distributed processing
- larger datasets

Likely overkill for MVP.

---

## Neo4j

Possible use:
- route network analysis
- airport graph exploration

Example:
Airport → Route → Airport relationships

Optional extension.

---

# Deployment Strategy

Primary target:
Docker Compose

Services:
- mongodb
- postgres
- fastapi
- dashboard
- scheduler

Goal:
Simple local reproducible setup.

---

# Engineering Philosophy

Prefer:
- understandable systems
- reproducible pipelines
- small deployable services
- simple operations

Avoid:
- premature distributed systems
- unnecessary cloud complexity
- Kubernetes too early