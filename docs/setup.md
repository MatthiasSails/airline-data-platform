# Local Development Setup

How to get the project running on a fresh machine.

---

## 1. Clone

```bash
git clone https://github.com/MatthiasSails/airline-data-platform.git
cd airline-data-platform
```

## 2. Virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS / Linux
```

The `.venv/` folder is gitignored.

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

All packages are **pinned to exact versions** (`pip freeze` output) to guarantee reproducible environments across machines and CI. The file lists both direct dependencies and the transitive ones they pull in.

## 4. Configure `.env`

Copy the template and fill in real values:

```bash
cp .env.example .env  # if a template exists; otherwise create from scratch
```

Required variables:

```env
# PostgreSQL (Liora training server)
DB_HOST=liora-vm.matthiaskoehler.com
DB_PORT=5432
DB_NAME=dst_db
DB_USER=...
DB_PASSWORD=...

# MongoDB (Liora VM — landing zone)
MONGO_URI=mongodb://airline_admin:...@liora-vm.matthiaskoehler.com:27017/airline_landing?authSource=admin
MONGO_DB=airline_landing

# OpenSky Network (OAuth2 — local only, VM blocks outbound)
OPENSKY_CLIENT_ID=...
OPENSKY_CLIENT_SECRET=...
```

Credentials are stored in macOS Keychain or shared via secure channel — never commit `.env`.

## 5. Start exploring

Open VS Code, select the `.venv` kernel in Jupyter, then open any notebook:

```
03-data-collection/collect_adsb.ipynb       ← ADS-B collector walkthrough
03-data-collection/explore_mongo_vm.ipynb   ← MongoDB landing zone exploration
03-data-collection/explore_adsb_lol.ipynb   ← adsb.lol API exploration
03-data-collection/explore_opensky_api.ipynb ← OpenSky API exploration
03-data-collection/explore_lh_api.ipynb     ← Lufthansa API (mock, no key available)
```

---

## Dependency Management

### Adding a new package

```bash
# 1. Install the package
pip install pandas

# 2. Regenerate the pinned list
pip freeze > requirements.txt

# 3. Commit
git add requirements.txt
git commit -m "Add pandas"
```

### Recreating the environment from scratch

```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Deploying the dashboard

The Streamlit dashboard lives in `04-dashboard/adsb-dashboard/` and deploys to the Liora VM via:

```bash
bash 04-dashboard/adsb-dashboard/deploy.sh
```

The script reads `MONGO_URI` from local `.env`, SSHes into the VM, pulls the latest `main`, and rebuilds the Docker container. See [04-dashboard/adsb-dashboard/](../04-dashboard/adsb-dashboard/) for details.

---

## Database hosts

PostgreSQL and MongoDB both run on the Liora VM (AWS Ubuntu):

| Service | Host | Port |
|---|---|---|
| PostgreSQL 16 | liora-vm.matthiaskoehler.com | 5432 |
| MongoDB 7 | liora-vm.matthiaskoehler.com | 27017 |
| Streamlit dashboard | liora-vm.matthiaskoehler.com | 8502 |

> The VM hostname is kept stable via Cloudflare DDNS — the actual AWS public IP changes on every VM restart, but the hostname always resolves to the current IP within ~5 minutes.
