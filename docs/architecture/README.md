# Architecture

The platform follows a **medallion** structure: Bronze (raw landing zone, MongoDB Atlas) → Silver
(Supabase Postgres, flat `map1` table) → Gold (consumption layer: two independent dashboards). This
page describes the system **as it currently runs**; future work is tracked as draft issues in the
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
BBOX).

```mermaid
graph LR
    OS["OpenSky States API<br/>/states/all<br/>OAuth2 — live"]
    ADSB["adsb.lol API<br/>public REST, no auth<br/>same geo coverage as OpenSky BBOX"]

    OS -->|state vectors| COL["Collectors<br/>(etl/bronze.py)"]
    ADSB -->|raw snapshots| COL

    COL -->|insert| CON["Mongo connector"]
    CON --> MDB["MongoDB Atlas<br/>airlines db<br/>states_all + adsb_raw"]

    style OS fill:#4CAF50,color:#fff
    style ADSB fill:#4CAF50,color:#fff
    style COL fill:#0066CC,color:#fff
    style CON fill:#0066CC,color:#fff
    style MDB fill:#FF6B35,color:#fff
```

> adsb.lol started Bronze-only for data-quality reasons ([ADR 009](../adr/009-states-api-silver-model.md))
> but is now also used as a Silver fallback, writing to its own `adsb_raw` collection — see Silver
> below and [ADR 014](../adr/014-adsb-lol-silver-fallback.md).
> The retrospective OpenSky `/flights/*` model was dropped in favour of the live States feed.

---

## Silver — Normalized Layer

ETL from the Bronze landing zone into the **Silver** layer on Supabase Postgres
(`etl/silver.py`). The ETL flattens the latest raw snapshot into a single table **`map1`** (raw
values, no dimensions) that backs both Gold dashboards.

**OpenSky is the preferred source; adsb.lol is a fallback** ([ADR 014](../adr/014-adsb-lol-silver-fallback.md)).
`silver.py` picks whichever Bronze snapshot is freshest by `fetched_at`. In normal operation
that's OpenSky; on the production VM, OpenSky's egress is blocked by `opensky-network.org` and its
snapshot goes stale, so adsb.lol takes over automatically — no environment-specific branching, no
manual failover.

```mermaid
graph LR
    MDB1["MongoDB Atlas<br/>states_all (OpenSky)"]
    MDB2["MongoDB Atlas<br/>adsb_raw (adsb.lol)"]
    MDB1 -->|freshest wins| ETL["Python ETL<br/>(psycopg2 direct)"]
    MDB2 -->|freshest wins| ETL
    ETL -->|write| PG["Supabase Postgres (Silver)<br/>map1 — flat live-map table"]

    style MDB1 fill:#FF6B35,color:#fff
    style MDB2 fill:#FF6B35,color:#fff
    style ETL fill:#FFA500,color:#fff
    style PG fill:#0066CC,color:#fff
```

---

## Gold — Consumption (API & Dashboards)

**Two independent Gold-layer implementations run side by side**, each its own Cloudflare Tunnel
subdomain — two parallel, fully working stacks, both reading the same `map1` table:

```mermaid
graph LR
    PG["Supabase Postgres (Silver)<br/>map1"]
    PG -->|psycopg2| ST["Streamlit dashboard<br/>03-gold/dashboard<br/>airline-dashboard.matthiaskoehler.com"]
    PG -->|asyncpg, read-only| API["FastAPI<br/>03-gold-dash/api<br/>/health · /aircraft/current"]
    API -->|polls every 45s| DASH["Dash map<br/>03-gold-dash/dashboard"]
    DASH -->|Cloudflare Tunnel| TUN["airlive.matthiaskoehler.com"]

    style PG fill:#0066CC,color:#fff
    style ST fill:#9933CC,color:#fff
    style API fill:#9933CC,color:#fff
    style DASH fill:#9933CC,color:#fff
    style TUN fill:#475569,color:#fff
```

> **`03-gold/dashboard`** — Streamlit, queries `map1` directly via psycopg2, deployed via
> `deployment/dashboard.yml` (Portainer GitOps), exposed at `airline-dashboard.matthiaskoehler.com`.
> **`03-gold-dash/`** — read-only FastAPI service (`api/`, asyncpg/Supavisor session pooler) +
> Dash frontend (`dashboard/`, polls the API every 45s), deployed via
> `deployment/gold-dash.yml` (Portainer GitOps), exposed at `airlive.matthiaskoehler.com` directly
> via the Cloudflare Tunnel — no reverse proxy on the VM. Endpoint scope for both:
> positions/aircraft/airline only — no route or delay analytics, since the live States feed has no
> origin/destination or scheduled times.

---

## Deployment

Data stores are **managed cloud services** (MongoDB Atlas, Supabase Postgres); every application
service runs as a **Docker container** on a dedicated VM, deployed the same way: **Portainer
GitOps**, auto-pulling `main`.

```mermaid
graph TB
    subgraph MANAGED["Managed cloud (data stores)"]
        M1["MongoDB Atlas — Bronze"]
        M2["Supabase Postgres — Silver"]
    end
    subgraph GITOPS["Portainer GitOps (deployment/*.yml, auto-pulls main)"]
        D1["adsb_dashboard (Streamlit)"]
        D2["landing_page"]
        D3["etl_bronze"]
        D6["etl_silver"]
        D4["gold_api (FastAPI)"]
        D5["gold_dashboard (Dash)"]
    end

    D3 -.-> M1
    D6 -.-> M1
    D6 -.-> M2

    style MANAGED fill:#FF6B35,color:#fff
    style GITOPS fill:#0066CC,color:#fff
```

- **Portainer GitOps** (`deployment/*.yml`) — every service is its own Portainer stack (`gold_api`/
  `gold_dashboard` share one stack, `gold-dash.yml`, see [`deployment/README.md`](../../deployment/README.md)
  for why), auto-pulled from `main`. Portainer here is purely a management view over the containers
  (equivalent to running `docker ps`/`docker compose` by hand on the VM) — it isn't part of the
  infrastructure itself, just how updates get rolled out.
- **Images**: `adsb_dashboard`, `landing_page`, `gold_api`, `gold_dashboard` are built once by CI
  and pulled from GHCR (see [`deployment/README.md`](../../deployment/README.md)); `etl_bronze`/
  `etl_silver` build in place on the VM from the same Compose file that deploys them.

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
    BRONZE["etl_bronze<br/>bronze.py"]
    SILVER["etl_silver<br/>silver.py"]
    DASH1["Streamlit Dashboard<br/>adsb_dashboard"]
    API["FastAPI<br/>gold_api"]
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

- **MongoDB Atlas** (Bronze) — written only by `etl_bronze`, via SRV connection string, read only by
  `etl_silver`.
- **Supabase Postgres** (Silver, `map1`) — three readers/writers, **two different connection
  strategies** against the Direct Connection (port 5432, IPv6-only): `adsb_dashboard` and
  `etl_silver` connect directly (both via `network_mode: host`); `gold_api` uses the **Supavisor
  session pooler** instead (IPv4-compatible) — see `03-gold-dash/README.md`.

### Network exposure

```mermaid
graph LR
    subgraph PUBLISHED["Published ports"]
        DASH1["Streamlit Dashboard<br/>adsb_dashboard"]
        LAND["landing_page"]
    end
    subgraph LOCALONLY["127.0.0.1-only"]
        DASH2["Dash Dashboard<br/>gold_dashboard"]
    end
    CF["cloudflared<br/>network_mode: host"]
    EDGE["Cloudflare edge<br/>*.matthiaskoehler.com"]

    DASH2 --> CF
    DASH1 --> CF
    LAND --> CF
    CF -->|outbound-only tunnel,<br/>no inbound ports open| EDGE

    style PUBLISHED fill:#0066CC,color:#fff
    style LOCALONLY fill:#9933CC,color:#fff
    style CF fill:#475569,color:#fff
    style EDGE fill:#475569,color:#fff
```

- **No reverse proxy on the VM.** `cloudflared` runs with `network_mode: host`, so it reaches
  `gold_dashboard` directly on `127.0.0.1:8050` — same pattern as the other two services, just
  without a published port.
- **Cloudflare Tunnel** (`cloudflared`) makes an outbound-only connection to the Cloudflare edge;
  no inbound ports are open on the VM. The edge maps each subdomain (`airline-dashboard.`,
  `airlive.`, `airline.`) to the matching local service.

