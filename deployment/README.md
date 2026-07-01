# Deployment

GitOps orchestration for the platform. **One Compose file per independently deployable
service**, each deployed as its own Portainer Git-stack from `main`. Rule of thumb: a stack
is a *lifecycle boundary* — services that deploy/version/roll back independently get their
own stack. Per-service Dockerfiles live with their service (e.g. [`../03-gold/dashboard/`](../03-gold/dashboard/)).

## Stacks

| Portainer stack | Compose file | Service | Port / network | Env (set in Portainer) |
|---|---|---|---|---|
| `airline-dashboard` | [`dashboard.yml`](dashboard.yml) | Streamlit live map over Silver (Supabase) | host net, `:8501` | `SUPABASE_DB_HOST`, `SUPABASE_DB_PASSWORD` |
| `airline-landing` | [`landing.yml`](landing.yml) | static landing page | `:80` | — |
| `airline-etl-bronze` | [`bronze.yml`](bronze.yml) | fetches OpenSky + adsb.lol into MongoDB, 50s loop ([`../etl/bronze.py`](../etl/bronze.py)) | no published port | via `../.env` |
| `airline-etl-silver` | [`silver.yml`](silver.yml) | refreshes `map1` (Postgres) from the latest Mongo snapshot, 10s loop ([`../etl/silver.py`](../etl/silver.py)) | no published port | via `../.env` |
| `airline-gold-dash` | [`gold-dash.yml`](gold-dash.yml) | read-only FastAPI + Dash over Silver, Supabase session pooler ([`../03-gold-dash/`](../03-gold-dash/)) | bridge, `127.0.0.1:8000`/`:8050` | `DATABASE_URL` |

`gold-dash.yml` holds two services (`api`, `dashboard`) in one stack, not two separate files —
they share a release cycle and a hard runtime dependency (`dashboard` won't start until `api` is
healthy), so together they're still one *lifecycle boundary* even though they're two containers.

Bronze and silver are split into separate stacks/containers on purpose: bronze is rate-limited by
upstream APIs and can only run every ~50s, while silver just re-reads the latest Mongo snapshot
into Postgres with no external rate limit, so it runs on its own faster cadence. Splitting them
also means a crash in one doesn't take down the other, and each gets its own restart policy and
healthcheck.

## Conventions

- **Every stack references a pre-built image — none of them build on the VM anymore.**
  [`../.github/workflows/build-push.yml`](../.github/workflows/build-push.yml) builds and pushes to
  GHCR (`ghcr.io/matthiassails/airline-{dashboard,landing,gold-api,gold-dashboard,etl}`) on every
  push to `main` that touches the relevant source. Portainer only pulls (`pull_policy: always`,
  since `:latest` is a mutable tag). `bronze.yml` and `silver.yml` both reference the same
  `airline-etl` image — they share an identical Dockerfile/build context and differ only in which
  script `command:` runs, so building two copies of the same image would be wasteful.
- **Env comes from Portainer**, per stack — *not* from the repo `.env` (gitignored, absent in the
  GitOps clone). Enter the variables in each stack's "Environment variables" field.
- **The dashboard must use `network_mode: host`.** It connects to the IPv6-only Supabase host
  (`db.<ref>.supabase.co`); the Docker default bridge has `EnableIPv6=false`, so a bridged
  container cannot reach Supabase. Host networking gives it the VM's global IPv6. Do not
  "simplify" it to bridge + published ports — that silently breaks the DB connection.
- **Do not `docker compose up` manually on the server.** A fixed `container_name` collides with
  the GitOps-managed container and pulls it into a rogue stack. Deploy via Portainer (or
  "Pull and redeploy"). Manual fallback for local testing only:
  `docker compose -f deployment/<service>.yml --env-file ../.env up -d`.
