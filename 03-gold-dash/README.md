# Frankfurt Airport Live Traffic Dashboard

Read-only FastAPI service + Dash dashboard for live Frankfurt-area aircraft positions, sourced from
a `map1` table already populated by an external OpenSky poller in Supabase Postgres.

## Repository structure

```
api/                  FastAPI service (read-only, queries map1)
dashboard/            Dash app (polls API every 45s, renders dl.Map)
docker-compose.local.yml    Local development compose file
.env.example          Template for the Supabase connection string
```

Production deployment config lives in [`../deployment/gold-dash.yml`](../deployment/gold-dash.yml)
(Portainer GitOps stack), not in this directory — see [Deployment](#2-deployment) below.

## 1. Local setup

1. Copy `.env.example` to `.env` and fill in your real Supabase connection string:

   ```bash
   cp .env.example .env
   ```

   Use the **Supavisor session pooler** connection string from Supabase (Project Settings ->
   Database -> Connection string -> "Session" mode), in SQLAlchemy async form:

   ```
   DATABASE_URL=postgresql+asyncpg://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
   ```

   Do **not** use the direct `db.<project-ref>.supabase.co` host — it's IPv6-only since early
   2024, and most Docker hosts (including Docker Desktop) have no outbound IPv6 route, which
   surfaces as `OSError: [Errno 101] Network is unreachable` from inside the `api` container.
   The session pooler is IPv4-compatible and, unlike the transaction pooler, supports the
   persistent long-lived connections this app uses.

2. Build and run both services:

   ```bash
   docker compose -f docker-compose.local.yml up --build
   ```

3. Verify:
   - FastAPI Swagger UI: http://localhost:8000/docs
   - Health check: http://localhost:8000/health
   - Dashboard: http://localhost:8050

4. Stop with `docker compose -f docker-compose.local.yml down`.

### Running without Docker (optional, for fast iteration)

```bash
# Terminal 1 — API
cd api
pip install -r requirements.txt
set DATABASE_URL=postgresql+asyncpg://...   # PowerShell: $env:DATABASE_URL = "..."
uvicorn main:app --reload --port 8000

# Terminal 2 — Dashboard
cd dashboard
pip install -r requirements.txt
python app.py
```

The dashboard defaults `API_BASE_URL` to `http://127.0.0.1:8000` when not running in Docker.

## 2. Deployment

Both containers are a Portainer GitOps stack (`airline-gold-dash`,
[`../deployment/gold-dash.yml`](../deployment/gold-dash.yml)) — same mechanism as every other
service, see [`deployment/README.md`](../deployment/README.md) for the shared conventions. Nothing
manual runs on the VM for this service.

- **Images** are built and pushed to GHCR by
  [`../.github/workflows/build-push.yml`](../.github/workflows/build-push.yml) on every push to
  `main` that touches `api/` or `dashboard/` — Portainer only pulls (`pull_policy: always`), it
  never builds from source on the VM.
- **`DATABASE_URL`** is set in Portainer's stack environment variables, not from a `.env` file —
  same Supavisor session pooler connection string as local dev (see above). The Direct Connection
  host still doesn't work here (IPv6-only); this stack stays on the default bridge network for
  that reason, unlike `dashboard.yml`/`silver.yml` which need `network_mode: host`.
- **Both `api` and `dashboard` publish only to `127.0.0.1`** — not reachable from outside the VM
  directly. Public access goes through the Cloudflare Tunnel (`cloudflared`, its own stack,
  running with `network_mode: host`), whose ingress routes `airlive.<domain>` straight to
  `http://localhost:8050`. No reverse proxy runs on the VM for this service.
- **Updating**: push to `main` — CI rebuilds the changed image(s), Portainer picks up the new
  compose file and image on its next poll (or "Pull and redeploy").

## 3. Notes

- The API is read-only; it never writes to `map1`.
- No altitude/velocity fields exist in `map1` and are not displayed anywhere.
- `vertical_rate` NULL or within ±1.0 m/s is treated as level flight (no arrow badge).
- `on_ground` NULL defaults to airborne (blue marker); `true_track` NULL defaults to heading 0°
  (north).
