# Frankfurt Airport Live Traffic Dashboard

Read-only FastAPI service + Dash dashboard for live Frankfurt-area aircraft positions, sourced from
a `map1` table already populated by an external OpenSky poller in Supabase Postgres.

## Repository structure

```
api/                  FastAPI service (read-only, queries map1)
dashboard/            Dash app (polls API every 45s, renders dl.Map)
deploy/nginx.conf     Nginx reverse proxy config (used on the Lightsail VM)
docker-compose.yml          Production compose file (Lightsail VM)
docker-compose.local.yml    Local development compose file
.env.example          Template for the Supabase connection string
```

## 1. Local setup

1. Copy `.env.example` to `.env` and fill in your real Supabase connection string:

   ```bash
   cp .env.example .env
   ```

   Use the **session/direct** Postgres connection string from Supabase (not the transaction
   pooler), in SQLAlchemy async form:

   ```
   DATABASE_URL=postgresql+asyncpg://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres
   ```

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

## 2. Deploying to AWS Lightsail

On a fresh Ubuntu Lightsail instance (2 GB RAM / 2 vCPU / 60 GB SSD):

1. **Install Docker Engine** (one-time):

   ```bash
   curl -fsSL https://get.docker.com | sudo sh
   sudo usermod -aG docker $USER
   newgrp docker
   docker --version && docker compose version
   ```

2. **Get the repo onto the VM** (e.g. `git clone` or `scp`), then create `.env` from
   `.env.example` with the real Supabase connection string.

3. **Build and start the app containers:**

   ```bash
   docker compose build
   docker compose up -d
   docker compose ps    # confirm both services are healthy
   ```

   Both `api` and `dashboard` publish only to `127.0.0.1` — they are not reachable from outside
   the VM directly; Nginx is the single public entry point.

4. **Install and configure Nginx** (native host package, not containerized):

   ```bash
   sudo apt update && sudo apt install -y nginx
   sudo cp deploy/nginx.conf /etc/nginx/sites-available/opensky-frankfurt
   sudo ln -s /etc/nginx/sites-available/opensky-frankfurt /etc/nginx/sites-enabled/
   sudo rm -f /etc/nginx/sites-enabled/default
   sudo nginx -t && sudo systemctl reload nginx
   ```

5. **(Optional) TLS via Certbot**, once a domain points at the VM:

   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.example.com
   ```

6. **Lightsail firewall**: open only ports 22, 80, and 443 (443 only if TLS is configured) in the
   Lightsail networking tab.

7. **Verify end-to-end**: visit `http://<vm-ip-or-domain>/` and confirm live aircraft markers
   appear, sourced from the existing poller writing into `map1`.

### Updating a deployment

```bash
git pull
docker compose build
docker compose up -d
docker image prune -f   # periodic cleanup of old image layers
```

## 3. Notes

- The API is read-only; it never writes to `map1`.
- No altitude/velocity fields exist in `map1` and are not displayed anywhere.
- `vertical_rate` NULL or within ±1.0 m/s is treated as level flight (no arrow badge).
- `on_ground` NULL defaults to airborne (blue marker); `true_track` NULL defaults to heading 0°
  (north).
