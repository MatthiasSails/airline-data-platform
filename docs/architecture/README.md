# Architecture

The platform follows a **medallion** structure: Bronze (raw landing zone, MongoDB Atlas) → Silver
(Supabase Postgres — currently the flat `map1` MVP table; curated star schema is the target) → Gold
(consumption layer: two independent dashboards). This page describes the system **as it currently
runs**; planned/future work is tracked as draft issues in the
[GitHub Project](https://github.com/users/MatthiasSails/projects/1), not here. The pipeline code
lives in the top-level code modules, each with its own README.

**Related:**
- [silver-layer-er.md](silver-layer-er.md) — Silver-layer ER diagram (relational model)
- [../adr/](../adr/) — Architecture Decision Records (why)

---

## Bronze — Raw Landing Zone

Ingest every source **raw, untransformed** into the MongoDB Atlas landing zone. *Ingestion ≠
modeling* (ADR 004): Bronze keeps the original payloads; the Silver model promotes only what it
needs. Two live feeds run every Bronze cycle (`etl/bronze.py`): OpenSky `/states/all` (the
preferred, richer source) and adsb.lol (no-auth secondary source, same geo coverage as the OpenSky
BBOX). Static reference feeds (AircraftDB, OpenFlights, OurAirports) are still planned.

```mermaid
graph LR
    OS["OpenSky States API<br/>/states/all<br/>OAuth2 — live"]
    REF["Static reference feeds<br/>AircraftDB · OpenFlights · OurAirports<br/>(planned)"]
    ADSB["adsb.lol API<br/>public REST, no auth<br/>same geo coverage as OpenSky BBOX"]

    OS -->|state vectors| COL["Collectors<br/>(etl/bronze.py)"]
    REF -->|raw rows| COL
    ADSB -->|raw snapshots| COL

    COL -->|insert| CON["Mongo connector"]
    CON --> MDB["MongoDB Atlas<br/>airlines db<br/>states_all + adsb_raw"]

    style OS fill:#4CAF50,color:#fff
    style REF fill:#4CAF50,color:#fff,stroke-dasharray:5 5
    style ADSB fill:#4CAF50,color:#fff
    style COL fill:#0066CC,color:#fff
    style CON fill:#0066CC,color:#fff
    style MDB fill:#FF6B35,color:#fff
```

> adsb.lol started Bronze-only for data-quality reasons ([ADR 009](../adr/009-states-api-silver-model.md))
> but is now also used as a Silver fallback — see Silver below and [ADR 014](../adr/014-adsb-lol-silver-fallback.md).
> The retrospective OpenSky `/flights/*` model was dropped in favour of the live States feed.

---

## Silver — Normalized Layer

ETL from the Bronze landing zone into the **Silver** layer on Supabase Postgres
(`etl/silver.py`). **Current state is a lean MVP:** the ETL flattens the latest raw snapshot into a
single table **`map1`** (raw values, no dimensions) that backs both Gold dashboards. The curated
**star schema** (`fact_states` + dims) is the *target* model
([silver-layer-er.md](silver-layer-er.md)) — not yet built; tracked as a draft issue in the
[GitHub Project](https://github.com/users/MatthiasSails/projects/1).

**OpenSky is the preferred source; adsb.lol is a fallback** ([ADR 014](../adr/014-adsb-lol-silver-fallback.md)).
`silver.py` picks whichever Bronze snapshot is freshest by `fetched_at`. In normal operation
that's OpenSky; on the production VM, OpenSky's egress is blocked by `opensky-network.org` and its
snapshot goes stale, so adsb.lol takes over automatically — no environment-specific branching, no
manual failover. This fallback applies to the `map1` MVP only; the target `fact_states` model is
still OpenSky-States-centric per ADR 009 and will need revisiting once that model is built.

```mermaid
graph LR
    MDB1["MongoDB Atlas<br/>states_all (OpenSky)"]
    MDB2["MongoDB Atlas<br/>adsb_raw (adsb.lol)"]
    MDB1 -->|freshest wins| ETL["Python ETL<br/>(psycopg2 direct)"]
    MDB2 -->|freshest wins| ETL
    ETL -->|write| PG["Supabase Postgres (Silver)<br/>map1 — flat live-map table ✅"]
    PG -.->|planned| STAR["Star schema (target)<br/>fact_states + dim_aircraft<br/>dim_airlines · dim_airports"]

    style MDB1 fill:#FF6B35,color:#fff
    style MDB2 fill:#FF6B35,color:#fff
    style ETL fill:#FFA500,color:#fff
    style PG fill:#0066CC,color:#fff
    style STAR fill:#0066CC,color:#fff,stroke-dasharray:5 5
```

> **Target Silver tables** (see [silver-layer-er.md](silver-layer-er.md), [ADR 008](../adr/008-airline-attribution-star-schema.md), [ADR 009](../adr/009-states-api-silver-model.md)):
> `fact_states` (OpenSky `/states/all`), `dim_aircraft` (OpenSky AircraftDB, join on `icao24`),
> `dim_airlines` (OpenFlights, join on resolved `airline_icao`), `dim_airports` (OurAirports,
> **standalone reference, unjoined**). No `fact_flights` / `fact_delays`: the live States feed has no
> origin/destination and no scheduled-vs-actual times, so route from/to and delay analytics are out
> of scope for Silver.

---

## Gold — Consumption (API & Dashboards)

**Two independent Gold-layer implementations run side by side**, each its own Cloudflare Tunnel
subdomain — not a planned/built split, but two parallel, fully working stacks, both reading the
same `map1` table:

```mermaid
graph LR
    PG["Supabase Postgres (Silver)<br/>map1"]
    PG -->|psycopg2| ST["Streamlit dashboard ✅<br/>03-gold/dashboard<br/>airline-dashboard.matthiaskoehler.com"]
    PG -->|asyncpg, read-only| API["FastAPI ✅<br/>03-gold-dash/api<br/>/states · /aircraft (planned endpoints)"]
    API -->|polls every 45s| DASH["Dash map ✅<br/>03-gold-dash/dashboard"]
    DASH -->|Nginx reverse proxy| TUN["airlive.matthiaskoehler.com"]

    style PG fill:#0066CC,color:#fff
    style ST fill:#9933CC,color:#fff
    style API fill:#9933CC,color:#fff
    style DASH fill:#9933CC,color:#fff
    style TUN fill:#475569,color:#fff
```

> **`03-gold/dashboard`** — Streamlit, queries `map1` directly via psycopg2, deployed via
> `deployment/dashboard.yml` (Portainer GitOps), exposed at `airline-dashboard.matthiaskoehler.com`.
> **`03-gold-dash/`** — read-only FastAPI service (`api/`, asyncpg/Supavisor session pooler) +
> Dash frontend (`dashboard/`, polls the API every 45s) behind an Nginx reverse proxy on the same
> VM, exposed at `airlive.matthiaskoehler.com`. Endpoint scope for both: positions/aircraft/airline
> only — no route or delay analytics, since the live States feed has no origin/destination or
> scheduled times.

---

## Deployment

Data stores are **managed cloud services** (MongoDB Atlas, Supabase Postgres); the application
services run as **Docker containers** on a dedicated VM, via **two different deployment paths** —
not by original design, just how each stack was actually rolled out. Automated ingestion
scheduling and CI/CD are still planned.

```mermaid
graph TB
    subgraph MANAGED["Managed cloud (data stores)"]
        M1["MongoDB Atlas — Bronze"]
        M2["Supabase Postgres — Silver"]
    end
    subgraph GITOPS["Portainer GitOps (deployment/*.yml, auto-pulls main)"]
        D1["adsb_dashboard (Streamlit) ✅"]
        D2["landing_page ✅"]
        D3["etl_app2 (ETL pipeline) ✅"]
        D6["scheduler — planned"]
    end
    subgraph MANUAL["Manually deployed (03-gold-dash/, plain docker compose)"]
        D4["api (FastAPI) ✅"]
        D5["dashboard (Dash) ✅"]
    end
    subgraph CICD["CI/CD — GitHub Actions (planned)"]
        CI["lint · test · build · push"]
    end

    D6 -.-> M1
    D6 -.-> M2
    CI -.-> GITOPS
    CI -.-> MANUAL

    style MANAGED fill:#FF6B35,color:#fff
    style GITOPS fill:#0066CC,color:#fff
    style MANUAL fill:#9933CC,color:#fff
    style CICD fill:#FFA500,color:#fff
```

- **Portainer GitOps** (`deployment/*.yml`) — `adsb_dashboard`, `landing_page`, `etl_app2`. Each is
  its own Portainer stack, auto-pulled from `main` (see
  [`deployment/README.md`](../../deployment/README.md)). Portainer here is purely a management
  view over the containers (equivalent to running `docker ps`/`docker compose` by hand on the VM)
  — it isn't part of the infrastructure itself, just how updates get rolled out.
- **`03-gold-dash`** (FastAPI + Dash) is **not** Portainer-managed — it's a plain `docker compose
  up` from `03-gold-dash/docker-compose.yml`, run manually on the VM, both containers bound to
  `127.0.0.1` only (see [Infrastructure](#infrastructure) for how it's exposed).

---

## Infrastructure

The actual resources — data stores, compute, network — and how they connect. Independent of which
deployment path put a given container there (see [Deployment](#deployment) above). Split into two
diagrams on purpose: one combined graph of data-store connections *and* network exposure becomes an
unreadable tangle of crossing lines, so **data connectivity** and **network exposure** are shown
separately.

### Data connectivity

```mermaid
graph LR
    BRONZE["etl_app2<br/>bronze.py"]
    SILVER["etl_app2<br/>silver.py"]
    DASH1["Streamlit Dashboard<br/>adsb_dashboard"]
    API["FastAPI<br/>03-gold-dash api"]
    MONGO["MongoDB Atlas<br/>Bronze"]
    SUPA["Supabase Postgres<br/>Silver — map1"]

    BRONZE -->|write| MONGO
    MONGO -->|read| SILVER
    SILVER -->|write| SUPA
    DASH1 -->|read| SUPA
    API -->|read| SUPA

    style MONGO fill:#FF6B35,color:#fff
    style SUPA fill:#FF6B35,color:#fff
    style BRONZE fill:#0066CC,color:#fff
    style SILVER fill:#0066CC,color:#fff
    style DASH1 fill:#0066CC,color:#fff
    style API fill:#0066CC,color:#fff
```

- **MongoDB Atlas** (Bronze) — written only by `etl_app2`, via SRV connection string (no IPv6
  dependency). Nothing currently reads it back out (the notebooks that used to are gone, #16).
- **Supabase Postgres** (Silver, `map1`) — three readers/writers, **two different connection
  strategies**, both confirmed working despite `docker-compose.yml` (`etl_app2`) not setting
  `network_mode: host` the way `dashboard.yml` does:
  - `adsb_dashboard` (host networking, by design — see `dashboard.yml`'s comment block) and
    `etl_app2` (plain bridge network) both reach the Direct Connection (port 5432) successfully;
    `etl_app2`'s logs confirm repeated successful `map1` writes from its bridge-networked
    container, so the IPv6-bridge concern documented for the dashboard doesn't block it in
    practice.
  - `03-gold-dash api` instead uses the **Supavisor session pooler** (IPv4-compatible) — see
    `03-gold-dash/README.md`.
- **`etl_app2` reliability** — it had no restart policy and an unhandled-exception path that could
  kill the whole pipeline loop on a single transient error (e.g. a Postgres `statement_timeout` on
  the old `TRUNCATE TABLE map1`, since replaced with `DELETE`). Confirmed in production: the
  container sat `Exited (1)` for 3 days (2026-06-27 → 2026-06-30), `map1` silently stale the whole
  time. Fixed in #18 (`restart: unless-stopped`, resilient `run_pipeline.sh`, `DELETE` instead of
  `TRUNCATE`).

### Network exposure

```mermaid
graph LR
    subgraph PUBLISHED["Published ports"]
        DASH1["Streamlit Dashboard<br/>adsb_dashboard"]
        LAND["landing_page"]
    end
    subgraph LOCALONLY["127.0.0.1-only"]
        DASH2["Dash Dashboard<br/>03-gold-dash dashboard"]
    end
    NGINX["Nginx<br/>native systemd, not a container"]
    CF["cloudflared"]
    EDGE["Cloudflare edge<br/>*.matthiaskoehler.com"]

    DASH2 --> NGINX --> CF
    DASH1 --> CF
    LAND --> CF
    CF -->|outbound-only tunnel,<br/>no inbound ports open| EDGE

    style PUBLISHED fill:#0066CC,color:#fff
    style LOCALONLY fill:#9933CC,color:#fff
    style NGINX fill:#475569,color:#fff
    style CF fill:#475569,color:#fff
    style EDGE fill:#475569,color:#fff
```

- **Nginx runs natively on the VM** (systemd service, not a container) and is the only entry point
  for `03-gold-dash` — reverse-proxies `127.0.0.1:8050` out to `airlive.matthiaskoehler.com`.
  Installed manually per `03-gold-dash/README.md`, not pulled by GitOps.
- **Cloudflare Tunnel** (`cloudflared`) makes an outbound-only connection to the Cloudflare edge;
  no inbound ports are open on the VM. The edge maps each subdomain (`airline-dashboard.`,
  `airlive.`, `airline.`) to the matching local service.

