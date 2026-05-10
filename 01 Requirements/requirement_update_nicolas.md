# Airlines Project — Data Engineering Bootcamp (Liora / DataScientest)

## Mentor

**Nicolas (“NicoTheDataSherpa”)**  
Role: Mentor / Project Supervisor  
Main communication channel: Slack  
Response time: Usually within 24 hours

---

# Executive Summary

## Project: Airlines

Goal of the project:

Build a complete Data Engineering architecture around airline / flight data.

Focus areas:

- Data collection from APIs and web sources
- Data organization and architecture
- Relational + NoSQL databases
- API development with FastAPI
- Automation pipelines
- Docker containerization
- CI/CD
- Frontend / analytics dashboard
- Final defense presentation

Important note from mentor:

> Machine Learning performance is NOT the main objective.  
> The main evaluation criterion is Data Engineering mastery.

Recommended ML effort:

- Maximum 1–2 days
- Use Kaggle inspiration if needed
- Quickly obtain a functional model and move on

---

# Timeline & Milestones

| Stage | Topic | Deadline |
|---|---|---|
| Step 0 | Scoping / Kickoff Meeting | 07.05.2026 |
| Step 1 | Data Discovery & Organization | 20.05.2026 |
| Step 2 | Data Consumption & API | 10.06.2026 |
| Step 3 | Automation & Pipelines | 16.06.2026 |
| Step 4 | Deployment & Frontend | 02.07.2026 |
| Final Defense | Presentation & Demo | 20.07.2026 |

---

# Step 0 — Scoping

## Deadline
**07.05.2026**

## Goals

- Q&A
- Define project scope
- Initial architectural understanding
- Kickoff discussion with mentor

## Notes

- Meeting recording available if attendance not possible
- Suggested initial Zoom meeting:
  - Thu, May 7
  - 16:00
  - Duration: 15 min

---

# Step 1 — Data Discovery & Organization

## Deadline
**20.05.2026**

## Main Objective

This is described as:

> The most important part of the project.

Core Data Engineering tasks happen here.

## Required Tasks

### Data Discovery

- Explore APIs
- Explore websites
- Understand data structures
- Identify datasets

### Data Architecture

Organize data using:

- Relational databases
- NoSQL databases

Potential examples:

- PostgreSQL
- MongoDB

## Important Design Requirement

You must think about:

- How datasets are linked together
- Data relationships
- Architecture design

---

## Deliverables

### Architecture Documentation

Must include:

- UML diagram
- Explanation of chosen architecture

### Data Source Report

Must include:

- Description of all data sources
- Examples of collected data

---

# Step 2 — Data Consumption & API

## Deadline
**10.06.2026**

## Main Objective

Consume the stored data through services and APIs.

---

## Required Components

### Backend Functions

Create functions to:

- Collect data
- Process data
- Calculate statistics
- Return API-ready data

---

## Machine Learning Path

### Required Components

- Training dataset query scripts
- Notebook for model training
- Saved artifacts
- `predict.py`

### API Endpoint

- `/predict`

---

## Dashboard Path

### Required Components

- Query scripts for raw data
- `analytics.py`

### API Endpoints

- `/stats`
- `/charts`

---

## API Framework

### Required

- FastAPI

---

# Step 3 — New Data Collection & Automation

## Deadline
**16.06.2026**

## Main Objective

Automate the complete system.

---

# Batch Pipeline (Required)

## Purpose

Process data on schedule.

Examples:

- Daily
- Hourly

## Pipeline Tasks

- Read data from storage
- Transform/process data
- Prepare data for analytics/API

## Suggested Technologies

- Airflow
- Jenkins
- CRON jobs

---

# Streaming Pipeline (Optional)

## Goal

Near real-time processing.

## Suggested Architecture

### Kafka-based Streaming

Components:

- Kafka broker
- Producer
- Consumer

### Producer

Connected to:

- External API
- WebSocket
- SSE stream

### Consumer

- Reads streaming events
- Usable by dashboard
- Testable via Python script

---

## Alternative if Real Streaming Is Impossible

Simulate streaming:

- FastAPI sends SQL rows periodically
- Example:
  - one new line every X seconds

---

# Step 4 — Deployment & Frontend

## Deadline
**02.07.2026**

---

# Testing

## Required

- Unit tests for API code

---

# CI/CD

## Required Pipelines

### `ci.yaml`

Runs on:

- All branches

Tasks:

- Linter
- Unit tests
- Docker image build

---

### `release.yaml`

Runs only on:

- `master` branch

Tasks:

- Linter
- Unit tests
- Docker build
- DockerHub deployment

---

# Dockerization

## Required

Create:

- `docker-compose.yml`

## Containers Should Include

- Database
- API
- Streamlit
- Airflow OR Kafka

---

# Frontend

## ML Option

- Streamlit prediction app

## Dashboard Option

- Streamlit analytics pages
- OR Dash analytics pages

---

# Final Defense

## Deadline
**20.07.2026**

---

# Presentation Structure

## 