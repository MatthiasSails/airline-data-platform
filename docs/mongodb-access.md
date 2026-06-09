# MongoDB Atlas Access — Team Onboarding

## What is MongoDB Atlas?

**MongoDB** is the database engine — it stores documents (JSON-like records) in
collections. **Atlas** is MongoDB's managed cloud service: MongoDB runs on Atlas
infrastructure, Atlas handles backups, scaling, networking, and access control.
You never touch a server directly.

In this project Atlas hosts our raw landing zone (Bronze layer):

- **Cluster:** `mongo-mk1` (M0 Free Tier, eu-central-1 Frankfurt)
- **Database:** `airline_landing`
- **Collections:** `adsb_raw`, `opensky_raw`, `flight_tracker_raw`

---

## User types and access

Atlas has two completely independent user layers — do not confuse them:

### 1. Database Users (for code and tooling)

These are MongoDB credentials embedded in a connection string (URI). They have
no browser login — they exist solely to authenticate programmatic access to the
data. All application code, collectors, notebooks, and external tools (e.g. VS
Code MongoDB extension, Compass) connect via a database user.

We have three database users:

| DB User | Role | When to use |
|---|---|---|
| `airline-reader-ro` | `read` (all databases) | Notebooks, exploration, any read-only query |
| `airline-collector-rw` | `atlasAdmin` | Collectors, ETL, anything that writes data |
| `matthiaskoehler_db_user` | `atlasAdmin` | Matthias' personal admin account |

### 2. Atlas UI Members (for browser access to cloud.mongodb.com)

These are accounts that log into the Atlas web console to manage the project —
view metrics, configure database users, manage the IP allowlist. This is a
browser login, not a database connection.

We use a **shared team account** for this:

- **Account:** `SECRET@protonmail.com`
- **Role:** `Project Data Access Admin` — full visibility into the project,
  clusters, metrics, and database user management. Cannot create or scale
  clusters, cannot touch billing.
- **2FA is mandatory:** authentication codes are delivered to the Protonmail
  inbox — you need access to `SECRET@protonmail.com` to log in.

### Where the secrets live

All credentials (Protonmail login, Atlas UI login, database user URIs) are
stored in **Proton Pass** under `SECRET@protonmail.com`. Ask Pavel or
Matthias for access.

---

## Connecting from Python

### Step 1 — Create a `.env` file

In the project root `airline-data-platform/` (already gitignored):

```bash
MONGO_DB=airline_landing

# Read-only — for notebooks and exploration:
MONGO_URI=mongodb+srv://airline-reader-ro:<PASSWORD>@mongo-mk1.ptb1k2b.mongodb.net/?appName=mongo-mk1

# Read-write — for collectors and ETL:
MONGO_URI_RW=mongodb+srv://airline-collector-rw:<PASSWORD>@mongo-mk1.ptb1k2b.mongodb.net/?appName=mongo-mk1
```

Both variables must be present. Get the passwords from Proton Pass
(`SECRET@protonmail.com`).

### Step 2 — Use the connector

The project provides `01-data-collection/db/mongo/connector.py`:

```python
from db.mongo.connector import from_env

# Read-only (default) — notebooks, exploration:
with from_env() as db:
    docs = list(db.collection("adsb_raw").find({}, limit=5))

# Read-write — collectors, ETL:
with from_env(write=True) as db:
    db.insert_raw("adsb_raw", document)
```

`from_env()` reads `MONGO_URI` / `MONGO_URI_RW` and `MONGO_DB` from `.env`
automatically. No credentials appear in code.

### Step 3 — Test the connection

```bash
python - <<'EOF'
from dotenv import load_dotenv; load_dotenv()
import os
from pymongo import MongoClient

c = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
print(c.admin.command("ping"))   # expected: {'ok': 1.0}
for name in c["airline_landing"].list_collection_names():
    print(f"  {name}: {c['airline_landing'][name].count_documents({})} docs")
c.close()
EOF
```

### Connecting from other tools

**VS Code MongoDB Extension:** connect via `Cmd+Shift+P` → `MongoDB: Connect`
→ `Connect with Connection String`. Use the SRV URI from Proton Pass.

**MongoDB Compass:** paste the SRV URI into the connection dialog.

**Other languages / tools:** use the SRV URI directly — the format is the same
regardless of driver or language.

---

## Secret management

### Current setup

| Environment | How secrets are provided |
|---|---|
| Local Mac | `.env` in project root, filled manually from Proton Pass |
| aws-airline-1 (Lightsail) | `.env` deployed manually to project root |

### Future: AWS SSM Parameter Store (aws-airline-1)

Replacing the manually deployed `.env` on the VM with AWS-native secret
management is planned. The Lightsail instance gets an IAM role that allows
`ssm:GetParameter` — the URI is fetched at runtime, never written to disk:

```
Lightsail (IAM role)  →  ssm:GetParameter  →  MONGO_URI in memory only
```

SSM Parameter Store (Standard tier) is free and sufficient for this project.

---

## Rotating a password

If a credential may have leaked, rotate it immediately — this takes ~30 seconds
and instantly invalidates the old password:

1. Atlas → **Database Access** → pick the user → **Edit**
2. **Edit Password** → **Autogenerate Secure Password** → **Copy**
3. **Update User**
4. Update the entry in Proton Pass and notify the team
5. Everyone updates their local `.env`

The old password stops working immediately.

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `ServerSelectionTimeoutError` | IP not in Atlas allowlist | Send your IP (`curl -s ifconfig.me`) to Matthias |
| `Authentication failed` | Wrong password | Re-copy the URI from Proton Pass |
| `SSL handshake failed` | VPN interrupting TLS | Split-tunnel or disable VPN for the Atlas domain |
| `MONGO_URI not set` | `.env` missing or wrong directory | Check `pwd` — must be the project root |

**IP Allowlist:** Atlas is configured with `0.0.0.0/0` (all IPs allowed).
Security relies on SCRAM authentication — without valid credentials, no access
is possible. This is deliberate for the project duration to avoid friction from
changing IPs (home, office, VM reboots). For production: switch to individual IP
entries or an Atlas Private Endpoint.

---

## Atlas console (browser)

URL: https://cloud.mongodb.com → Project `airline` → Cluster `mongo-mk1`

Log in with the shared team account (`SECRET@protonmail.com`). Key sections:

- **Database Access** — manage DB users, rotate passwords
- **Network Access** — IP allowlist
- **Browse Collections** — inspect data directly in the browser
- **Metrics** — connections, storage, operations
- **Access Manager** — manage UI members and their roles
