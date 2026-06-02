# docs/ — Knowledge Layer

Everything *about the whole project* lives here (project-wide, un-numbered). The **numbered folders**
(`01-data-collection/` … `04-deployment/`) are the **pipeline phases (code)**; module-specific "how to
run this" docs live in each code module's own README (e.g. `01-data-collection/README.md`).

| Path | Purpose |
|---|---|
| [requirements/](requirements/) | Scope, timeline, original assignment (`source/`) |
| [adr/](adr/) | Architecture Decision Records — *why* the design looks like it does |
| [architecture/](architecture/) | Data flow, Silver ER model, diagrams |
| [data-sources/](data-sources/) | External API references (OpenSky, adsb.lol, market overview) |
| [report/](report/) | DataScientest final project report |
| [setup.md](setup.md) | Local development setup (venv, kernel, environment) |
| [mongodb-access.md](mongodb-access.md) | MongoDB Atlas team access — users, roles, connection, secrets |

`images/` holds shared assets referenced from the project README and these docs.

> Project **progress/tracking** is not here — it lives in GitHub Projects V2 (the workflow layer).
