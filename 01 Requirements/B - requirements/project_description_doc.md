# Airlines Project — Executive Summary & Timeline

## Project

**Airlines — Data Engineering Project**  
Provider: Liora / DataScientest  
Track: Data Engineer  
Difficulty: 8.5 / 10  

Mentor: Nicolas (“NicoTheDataSherpa”)

Sources: :contentReference[oaicite:0]{index=0} :contentReference[oaicite:1]{index=1}

---

# Executive Summary

The goal of the project is to build a complete modern Data Engineering platform around airline and flight data.

Main focus areas:

- API ingestion
- ETL pipelines
- database architecture
- SQL + NoSQL modeling
- FastAPI backend
- dashboard analytics
- automation pipelines
- Docker deployment
- CI/CD
- final architecture defense

Important mentor clarification:

> Machine Learning performance is NOT the main evaluation criterion.  
> The primary objective is demonstrating Data Engineering mastery.

Recommended ML effort:

- maximum 1–2 days
- functional model only
- use Kaggle inspiration if necessary

Source: :contentReference[oaicite:2]{index=2}

---

# Project Timeline & Milestones

| Step | Topic | Deadline | Main Deliverables |
|---|---|---|---|
| Step 0 | Scoping / Kickoff | 07.05.2026 | Scope definition, architecture discussion |
| Step 1 | Data Discovery & Organization | 20.05.2026 | APIs, UML, DB architecture, collected datasets |
| Step 2 | Data Consumption & API | 10.06.2026 | FastAPI, analytics endpoints, ML/dashboard layer |
| Step 3 | Automation & Pipelines | 16.06.2026 | Batch jobs, Airflow, optional Kafka streaming |
| Step 4 | Deployment & Frontend | 02.07.2026 | Docker Compose, CI/CD, Streamlit/Dash |
| Final Defense | Presentation & Demo | 20.07.2026 | Architecture presentation & live demo |

Source: :contentReference[oaicite:3]{index=3}

---

# Recommended Final Architecture

```text
Lufthansa API / External APIs
            ↓
MongoDB (raw JSON landing zone)
            ↓
ETL / Airflow
            ↓
PostgreSQL (analytics warehouse)
            ↓
FastAPI
            ↓
Dashboard (Streamlit / Dash)
```

Optional extensions:

- Kafka
- Spark Streaming
- Neo4j
- Elasticsearch
- MQTT events

---

# Core Architectural Idea

## MongoDB
Used for:

- raw API responses
- flexible JSON storage
- schema evolution
- event snapshots

## PostgreSQL
Used for:

- relational analytics
- SQL joins
- dashboard queries
- OLAP-style reporting

This creates a simplified layered warehouse architecture:

```text
Raw Layer      → MongoDB
Curated Layer  → PostgreSQL
Serving Layer  → FastAPI
Analytics      → Streamlit / Dash
```

---

# Step 0 — Scoping / Kickoff

## Deadline
07.05.2026

## Objectives

- Q&A with mentor
- define project scope
- understand expected architecture
- clarify technologies & deliverables

## Deliverables

- architecture direction
- initial technical planning

Source: :contentReference[oaicite:4]{index=4}

---

# Step 1 — Data Discovery & Organization

## Deadline
20.05.2026

## Main Objective

This is described by the mentor as:

> The most important part of the project.

Core Data Engineering work happens here.

---

## Required Tasks

### Data Collection

Use Lufthansa API to retrieve:

- flight data
- airport data
- airline data
- IATA codes

Possible technologies:

- Python requests
- Postman
- Selenium
- BeautifulSoup

---

## Database Architecture

Use multiple databases because of different data types.

Suggested technologies:

- PostgreSQL
- MongoDB
- Elasticsearch
- Neo4j

Main requirement:

- understand relationships between datasets
- design the architecture carefully

---

## Required Deliverables

### Documentation

- UML diagram
- architecture explanation
- data source documentation

### Data

- collected sample datasets
- SQL creation scripts
- NoSQL collections

Sources: :contentReference[oaicite:5]{index=5} :contentReference[oaicite:6]{index=6}

---

# Step 2 — Data Consumption & API

## Deadline
10.06.2026

## Main Objective

Consume and expose data through APIs and analytics services.

---

## Required Backend Functions

- collect data
- process data
- calculate statistics
- expose APIs

---

## API Requirements

Framework:

- FastAPI

Possible endpoints:

- `/predict`
- `/stats`
- `/charts`

---

## Dashboard Option

Use:

- Streamlit
- OR Dash + Plotly

Dashboard examples:

- flight delays
- airport statistics
- airline KPIs
- route analytics

---

## Deliverables

- operational FastAPI backend
- dashboard frontend
- analytics queries

Sources: :contentReference[oaicite:7]{index=7} :contentReference[oaicite:8]{index=8}

---

# Step 3 — Automation & Pipelines

## Deadline
16.06.2026

## Main Objective

Automate ingestion and processing pipelines.

---

# Required Batch Pipeline

## Tasks

- retrieve API data periodically
- transform datasets
- update warehouse
- prepare dashboard/API data

## Technologies

- Airflow
- Jenkins
- Cronjobs

---

# Optional Streaming Pipeline

## Technologies

- Kafka
- WebSocket
- SSE

## Possible Architecture

```text
External API
      ↓
Kafka Producer
      ↓
Kafka Broker
      ↓
Kafka Consumer
      ↓
Dashboard / API
```

Alternative if no real stream exists:

- simulate streaming via FastAPI
- periodically send SQL rows

---

## Deliverables

- Airflow DAGs
- scheduled jobs
- optional Kafka demo

Source: :contentReference[oaicite:9]{index=9}

---

# Step 4 — Deployment & Frontend

## Deadline
02.07.2026

---

# Dockerization

## Required

Create:

- Dockerfiles
- docker-compose.yml

Containers should include:

- database
- API
- dashboard
- Airflow OR Kafka

---

# CI/CD

## Required Pipelines

### ci.yaml

Runs on all branches.

Tasks:

- linting
- unit tests
- Docker build

---

### release.yaml

Runs on master branch.

Tasks:

- linting
- unit tests
- Docker build
- DockerHub deployment

---

# Testing

## Required

- unit tests for API code

---

# Frontend

## Options

### ML App
- Streamlit prediction interface

### Analytics App
- Streamlit dashboard
- OR Dash dashboard

---

## Deliverables

- complete dockerized platform
- CI/CD pipeline
- frontend application

Source: :contentReference[oaicite:10]{index=10}

---

# Final Defense

## Deadline
20.07.2026

## Objective

Demonstrate and explain the complete architecture.

---

# Expected Defense Topics

- Why MongoDB + PostgreSQL
- ETL architecture
- API design
- warehouse layering
- dashboard architecture
- automation strategy
- Docker deployment
- CI/CD strategy

---

# Expected Final Result

A modern cloud-style airline analytics platform demonstrating:

- API ingestion
- ETL engineering
- OLAP-style warehouse thinking
- automation pipelines
- dashboard analytics
- containerized deployment
- CI/CD workflows
- production-style architecture reasoning

Sources: :contentReference[oaicite:11]{index=11} :contentReference[oaicite:12]{index=12}