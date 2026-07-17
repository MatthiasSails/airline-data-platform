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
| `airline-etl-bronze` | [`bronze.yml`](bronze.yml) | fetches OpenSky + adsb.lol into MongoDB, 50s loop ([`../etl/bronze.py`](../etl/bronze.py)) | no published port | `OPENSKY_CLIENT_ID`, `OPENSKY_CLIENT_SECRET`, `MONGO_URL` |
| `airline-etl-silver` | [`silver.yml`](silver.yml) | refreshes `map1` (Postgres) from the latest Mongo snapshot, 10s loop ([`../etl/silver.py`](../etl/silver.py)) | no published port | `MONGO_URL`, `SUPABASE_DB_URL`, `SUPABASE_DB_PASSWORD` |
| `airline-gold-dash` | [`gold-dash.yml`](gold-dash.yml) | read-only FastAPI + Dash over Silver, Supabase session pooler ([`../03-gold-dash/`](../03-gold-dash/)) | bridge, `127.0.0.1:8000`/`:8050` | `DATABASE_URL` |
| `chaitra-cloudflared` | [`chaitra-cloudflared.yml`](chaitra-cloudflared.yml) | second Cloudflare Tunnel connector, routing a collaborator's own-account domain to the same landing page (`localhost:80`) | host net, no published port | `TUNNEL_TOKEN` |

`chaitra-cloudflared.yml` is a *second* tunnel connector alongside the account's main one. A
Cloudflare Tunnel's ingress is account-bound — a hostname can only be routed to a domain whose DNS
zone lives in the same Cloudflare account as the tunnel. A collaborator's domain, managed in *their*
account, therefore cannot be added as an ingress rule on our tunnel; instead they run their own
tunnel in their account and this connector — on our prod VM — dials out to it, pointing at the same
`landing_page` container. Same pattern as [`q-cloudflared.yml`](q-cloudflared.yml), just a different
account/tunnel.

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

## Q environment (PR previews)

A second, smaller VM (`infra/q-vm/`, Terraform-managed) runs the **whole pipeline** as persistent
stacks that PRs deploy into before merge. One Portainer server (on the prod VM) manages both hosts —
the Q VM only runs a Portainer *agent*, registered as a second endpoint.

| Q stack | Compose file | Mirrors |
|---|---|---|
| `q-etl-bronze` | [`bronze.yml`](bronze.yml) | `airline-etl-bronze` |
| `q-etl-silver` | [`silver.yml`](silver.yml) | `airline-etl-silver` |
| `q-dashboard` | [`dashboard.yml`](dashboard.yml) | `airline-dashboard` |
| `q-gold-dash` | [`gold-dash.yml`](gold-dash.yml) | `airline-gold-dash` |
| `q-ml` | [`ml.yml`](ml.yml) | (no prod stack yet — Q-first rollout) |
| `q-cloudflared` | [`q-cloudflared.yml`](q-cloudflared.yml) | (Q's own tunnel connector) |

- **No compose file is duplicated for Q.** Every one is shared with prod and specialised purely by
  env: `${IMAGE_TAG:-latest}` selects the build, `${MAP_TABLE:-map1}` selects the Postgres table.
  Prod leaves both unset and gets `latest`/`map1`; Q's stacks set `pr-<N>`/`q_map1`.
- **Where Q is isolated, and where it isn't:**
  - **Postgres — isolated.** Q writes and reads its own `q_map1` table (created with
    `CREATE TABLE q_map1 (LIKE map1 INCLUDING ALL)`), so `silver.py`'s delete-and-reinsert refresh
    can run in Q without touching prod's `map1`. `MAP_TABLE` is allowlist-validated in code
    (`map1`/`q_map1` only) because a table name is a SQL identifier and cannot be a bind parameter.
  - **MongoDB — shared, deliberately.** Q's bronze writes the same `airlines` database and
    `states_all`/`adsb_raw` collections as prod's. Accepted trade-off: Q's silver therefore reads
    real prod-shaped data with no extra Atlas cost, but a bronze change tested in Q reaches prod's
    silver through that shared collection. **Test bronze changes with that in mind** — the
    `q_map1` isolation protects the Postgres layer only.
  - Because both silvers read the same Mongo snapshot, `q_map1` and `map1` normally hold the same
    rows. Q's value is proving a *code* change, not different data.
- **Tagging (build-once, promote-by-tag):** [`../.github/workflows/build-push.yml`](../.github/workflows/build-push.yml)
  adds an immutable `:sha-<shortsha>` tag to every build. On `main` it also tags `:latest`; on a
  pull request it tags `:pr-<number>` and the `deploy-q` job points every Q stack at that tag via
  the Portainer API ([`scripts/set-q-image-tag.sh`](scripts/set-q-image-tag.sh), which takes a
  stack-id list). No image is ever rebuilt per environment — see Humble/Farley, *Continuous
  Delivery*, "Only Build Your Binaries Once" (p. 113–114).
- **Cleanup:** [`q-reset.yml`](../.github/workflows/q-reset.yml) resets `IMAGE_TAG` to `latest`
  after the **main build completes**, not when the PR closes. Resetting on close races the build:
  until the new `:latest` exists, Q would pull the pre-merge image — and an ETL image built before
  `MAP_TABLE` existed ignores it and writes prod's `map1`. A PR closed without merging resets
  immediately, since `main` never moved.
- **Access:** `https://q-airlive.matthiaskoehler.com`, via its own Cloudflare Tunnel connector
  ([`q-cloudflared.yml`](q-cloudflared.yml)) — a tunnel can't route to `localhost` on two different
  hosts, so Q needed its own, separate from prod's.
- **Known limitations:**
  - The Q stacks' `GitConfig` tracks `main`, so a PR that changes a compose file itself only takes
    effect in Q *after* merging — pre-merge previews cover application code, not the compose file
    or Portainer stack config.
  - Q is one shared stage environment: any merge to `main` resets it to `:latest`, including while
    another PR is being tested there.
