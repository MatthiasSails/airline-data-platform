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

Create `.env` at the project root and fill in real values (credentials via secure channel — never commit):

```env
# MongoDB Atlas (Landing Zone — Bronze)
MONGO_URI=mongodb+srv://airline-collector-rw:<PASSWORD>@mongo-mk1.ptb1k2b.mongodb.net/?appName=mongo-mk1
MONGO_DB=airline_landing

# OpenSky Network (OAuth2 — local only, external VMs block outbound auth)
OPENSKY_CLIENT_ID=...
OPENSKY_CLIENT_SECRET=...
```

For read-only access (exploration notebooks) use the `airline-reader-ro` credentials instead:

```env
MONGO_URI=mongodb+srv://airline-reader-ro:<PASSWORD>@mongo-mk1.ptb1k2b.mongodb.net/?appName=mongo-mk1
```

Full credential reference and Atlas access setup: [docs/mongodb-access.md](mongodb-access.md).

## 5. Atlas Network Access

Your current IP must be whitelisted in the Atlas project's Network Access list.
If you see `SSL handshake failed` or `ServerSelectionTimeoutError`, the IP is missing.
Add it via the Atlas web console → Network Access → Add IP Address.

## 6. Start exploring

Open VS Code, select the `.venv` kernel in Jupyter, then open any notebook:

```
03-data-collection/collect_adsb.ipynb         ← ADS-B collector walkthrough
03-data-collection/collect_opensky.ipynb       ← OpenSky collector walkthrough
03-data-collection/explore_mongo_atlas.ipynb   ← MongoDB landing zone exploration (all 3 collections)
03-data-collection/explore_adsb_lol.ipynb      ← adsb.lol API exploration
03-data-collection/explore_opensky_api.ipynb   ← OpenSky API exploration
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

## Database endpoints

| Service | Host | Note |
|---|---|---|
| MongoDB Atlas | `mongo-mk1.ptb1k2b.mongodb.net` (SRV) | Bronze landing zone — Atlas Free Tier, eu-central-1 |
| PostgreSQL | TBD — Neon (leading candidate, Pavel evaluating) | Silver warehouse, see ADR 007 |
