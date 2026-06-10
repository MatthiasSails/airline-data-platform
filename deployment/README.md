# Deployment

Orchestration of the whole platform: top-level `docker-compose`, the collection scheduler, and any
infra glue. Per-service Dockerfiles live with their service (e.g.
[`../03-gold/dashboard/`](../03-gold/dashboard/)).

_Status: to be consolidated (the dashboard currently ships its own `docker-compose.yml`)._
