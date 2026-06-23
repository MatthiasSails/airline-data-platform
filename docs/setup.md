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

Create `.env` at the project root with the MongoDB and OpenSky credentials (never commit it — it is
gitignored). The connection strings, read-only vs. read-write users, and Atlas network-access setup
all live in one place: **[mongodb-access.md](mongodb-access.md)**.

Variables you need:
- `MONGO_URI`, `MONGO_DB` — MongoDB Atlas landing zone (read-only `airline-reader-ro` for notebooks,
  read-write `airline-collector-rw` for collectors / ETL)
- `OPENSKY_CLIENT_ID`, `OPENSKY_CLIENT_SECRET` — OpenSky OAuth2 (local only; external VMs block
  outbound auth)

## 5. Start exploring

Register the venv-internal Jupyter kernel once per venv, then open any notebook:

```bash
python -m ipykernel install --sys-prefix --name python3 --display-name ".venv"
```

In VS Code / JupyterLab always select the **`.venv`** kernel (`display_name: .venv`). Do not install
a separate `--user` kernel — a second entry causes "kernel not found". If `.venv` breaks after a
project rename (`bad interpreter`): `rm -rf .venv` and redo steps 2–3.

```
notebooks/collect_adsb.ipynb          ← ADS-B collector walkthrough
notebooks/explore_mongo_atlas.ipynb   ← MongoDB landing zone exploration (all 3 collections)
notebooks/explore_adsb_lol.ipynb      ← adsb.lol API exploration
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

- **MongoDB Atlas** (Bronze landing zone) — connection string, read/write users, and Atlas network
  access: **[mongodb-access.md](mongodb-access.md)**.
- **Supabase Postgres** (Silver store) — managed Postgres; current connection details live in the
  project **[CLAUDE.md](../CLAUDE.md)**.
