# Airline Data Engineering Project

Data pipeline for Lufthansa flight data — from API to database.

## Project Structure

```
airline/
├── 01-requirements/       # Project specs and architecture docs
├── 02-api-docs/           # Lufthansa API Swagger spec
├── 03-data-collection/    # API client, collectors, notebooks
├── requirements.txt       # Python dependencies (all pinned)
└── README.md              # This file
```

## Development Setup

### 1. Clone and enter the project
```bash
git clone <repo>
cd airline
```

### 2. Create virtual environment
```bash
python3 -m venv .venv
```

A `.venv` folder is created locally. It is excluded from git (see `.gitignore`).

### 3. Activate virtual environment
```bash
source .venv/bin/activate   # Mac / Linux
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

All packages are pinned to exact versions to guarantee reproducible environments across machines and CI. The file lists both the libraries we use directly (e.g. `requests`, `psycopg2-binary`) and the transitive dependencies they pull in — generated via `pip freeze` so every install produces the same versions.

### 5. Start exploring
Open VS Code, select the `.venv` kernel in Jupyter, and open:
```
03-data-collection/explore_lh_api.ipynb
```

---

## Dependency Management

Direct dependencies we actually use:

| Package | Why |
|---|---|
| `jupyter` | Interactive notebooks |
| `requests` | HTTP calls to LH API |
| `psycopg2-binary` | PostgreSQL connector |

All other packages in `requirements.txt` are installed automatically as transitive dependencies.

### Adding a new package

```bash
# 1. Add to requirements.txt (without version first)
echo "pandas" >> requirements.txt

# 2. Install
pip install -r requirements.txt

# 3. Pin the exact version
pip freeze | grep pandas >> requirements.txt   # then clean up duplicates

# 4. Commit
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

## Database

PostgreSQL 16 runs on the training server via Docker.

Connection settings are stored in `.env` (not in git):

```
DB_HOST=<server-ip>    # changes on every VM restart
DB_PORT=5432
DB_NAME=dst_db
DB_USER=...
DB_PASSWORD=...
```

> **Note:** The training server (AWS) gets a new public IP on every restart.
> Update `DB_HOST` in your `.env` after each restart.
