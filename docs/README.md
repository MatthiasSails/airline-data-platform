# docs/ — Knowledge Layer

Everything *about the whole project* lives here — concepts, decisions, requirements (project-wide).
The **pipeline code** lives in the top-level code modules; module-specific "how to run this" docs live
next to the code, in each module's own README.

| Path | Purpose |
|---|---|
| [requirements/](requirements/) | Scope, timeline, original assignment (`source/`) |
| [adr/](adr/) | Architecture Decision Records — *why* the design looks like it does |
| [architecture/](architecture/) | Data flow, Silver ER model, diagrams |
| [data-sources/](data-sources/) | External API references (OpenSky, adsb.lol, market overview) |
| [report/](report/) | DataScientest final project report |
| [mongodb-access.md](mongodb-access.md) | MongoDB Atlas team access — users, roles, connection, secrets |
| [vm-access.md](vm-access.md) | AWS Lightsail VM — SSH access, running services, team keys |

`images/` holds shared assets referenced from the project README and these docs.

> Project **progress/tracking** is not here — it lives in GitHub Projects V2 (the workflow layer).
