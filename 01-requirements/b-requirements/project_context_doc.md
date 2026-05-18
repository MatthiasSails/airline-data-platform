# Liora Airline Project Context

## <span style="color:red">Project Overview</span>

Project: Airlines  
Context: Liora / DataScientest Data Engineering Project

Main objective:
Build a practical Data Engineering architecture around airline and flight data.

Important:
The project evaluation focuses primarily on Data Engineering skills, not on machine learning performance.

---

# Mentor

Nicolas ("NicoTheDataSherpa")

Role:
- Mentor
- Project advisor
- Timeline coordination
- Technical guidance

---

# Main Technical Topics

## Data Collection

Possible sources:
- Lufthansa API
- Other airline APIs
- External aviation datasets

Topics:
- API ingestion
- Authentication
- Scheduling
- Incremental loading

---

## Data Storage

Expected technologies mentioned in project material:
- PostgreSQL
- MongoDB
- Neo4j
- Elasticsearch

Current preferred architecture:
- MongoDB as raw landing zone
- PostgreSQL as curated warehouse

Neo4j optional:
Useful for route/network analysis.

---

## Backend/API Layer

Expected:
- FastAPI
- REST API
- JSON responses

Potential functionality:
- Flight lookup
- Route analytics
- Delay statistics
- Airline KPIs

---

## Dashboard / Visualization

Possible stack:
- Dash
- Plotly
- Streamlit

Goal:
Interactive exploration of airline data.

---

## Containerization

Expected:
- Docker
- docker-compose

Possible later extension:
- CI/CD
- GitHub Actions

---

## Automation / Orchestration

Expected:
- Cron
- Airflow (optional)

Goal:
Automated ingestion and pipeline execution.

---

# Recommended Architecture

External APIs
    ↓
Raw JSON → MongoDB
    ↓ ETL
Curated tables → PostgreSQL
    ↓
FastAPI
    ↓
Dashboard / Analytics

---

# Important Project Advice From Mentor

Main message:
Do NOT spend excessive time on ML model optimization.

Recommendation:
- Build a simple functional model quickly
- Focus on Data Engineering architecture
- Prefer working end-to-end pipeline over ML tuning

Suggested ML effort:
Maximum approximately 1–2 days.

---

# Suggested Engineering Priorities

1. Data ingestion works reliably
2. Storage architecture is understandable
3. ETL pipeline is reproducible
4. APIs are documented
5. Docker environment works cleanly
6. Demo is stable and explainable

---

# Expected Deliverables

Potential deliverables:
- Git repository
- Dockerized setup
- API service
- Data pipeline
- Database schema
- Dashboard
- Documentation
- Final defense/presentation

---

# Key Evaluation Areas

Most likely evaluation focus:
- Data architecture
- Data modeling
- ETL quality
- API handling
- Automation
- Containerization
- Documentation
- Engineering reasoning

Less important:
- SOTA machine learning accuracy