# MongoDB Atlas Access — Team Onboarding

## What is MongoDB Atlas?

**MongoDB** is the document database engine. **Atlas** is MongoDB's managed
cloud service: it handles infrastructure, backups, scaling, and access control.
You never touch a server directly.

---

## Atlas hierarchy

```
Organization  (Matthias Koehler Co.)
└── Project: airline
    └── Cluster: mongo-mk1  (M0 Free Tier, eu-central-1 Frankfurt)
        ├── airline_landing     ← Bronze landing zone (active)
        │   ├── flight_tracker_raw
        │   ├── opensky_raw
        │   └── adsb_raw
        └── airlines            ← legacy experiment, not in active use
            └── states_all
```

`mongodbVSCodePlaygroundDB` is a VS Code Playground leftover — ignore it.

---

## Access layers

Atlas has three completely independent access layers — do not confuse them:

### 1. Organization Members

Browser login to `cloud.mongodb.com` at the **organization** level. Grants
visibility across all projects in the org. Managed under
*Access Manager → Members* at the org level.

### 2. Project Members

Browser login to `cloud.mongodb.com` scoped to the **airline** project.
Grants access to cluster metrics, database user management, IP allowlist,
and collection browsing. Managed under *Access Manager → Project Access*.

We use a shared team account:

| | |
|---|---|
| **Account** | `SECRET@protonmail.com` |
| **Project Role** | `Project Data Access Admin` |
| **Can** | View metrics, manage DB users, manage IP allowlist, browse collections |
| **Cannot** | Create/scale clusters, touch billing |
| **MFA** | Mandatory — codes go to the Protonmail inbox |

Credentials are stored in **Proton Pass** → Vault "Airlines". Ask Pavel or
Matthias for access.

### 3. Database Users

MongoDB credentials embedded in a connection string (URI). No browser login —
used exclusively for programmatic access (application code, notebooks, tooling).

| DB User | Role | When to use |
|---|---|---|
| `airline-reader-ro` | `read` (all databases) | Notebooks, exploration, any read-only query |
| `airline-collector-rw` | `atlasAdmin` | Collectors, ETL, anything that writes data |

Passwords are stored in **Proton Pass** (`SECRET@protonmail.com`).

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

Get the passwords from Proton Pass (`SECRET@protonmail.com`).

### Step 2 — Use the connector

The project provides `data_connectors/mongo.py` (repo root must be on `sys.path`):

```python
from data_connectors.mongo import from_env

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

**VS Code MongoDB Extension:** `Cmd+Shift+P` → `MongoDB: Connect` → `Connect with Connection String`. Use the read-only SRV URI from Proton Pass.

**MongoDB Compass:** paste the SRV URI into the connection dialog.

---

## Secret management

| Environment | How secrets are provided |
|---|---|
| Local Mac | `.env` in project root, filled manually from Proton Pass |
| aws-airline-1 (Lightsail) | `.env` deployed manually to project root |

**Future:** replace the manually deployed `.env` on the VM with AWS SSM
Parameter Store — the Lightsail instance gets an IAM role that allows
`ssm:GetParameter`, so the URI is fetched at runtime and never written to disk.

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `ServerSelectionTimeoutError` | IP not in Atlas allowlist | Send your IP (`curl -s ifconfig.me`) to Matthias |
| `Authentication failed` | Wrong password | Re-copy the URI from Proton Pass |
| `SSL handshake failed` | VPN interrupting TLS | Split-tunnel or disable VPN for the Atlas domain |
| `MONGO_URI not set` | `.env` missing or wrong directory | Check `pwd` — must be the project root |

**IP Allowlist:** Atlas is configured with `0.0.0.0/0` (all IPs allowed).
Security relies on SCRAM authentication. For production: switch to individual
IP entries or an Atlas Private Endpoint.

---

## Atlas console (browser)

URL: `https://cloud.mongodb.com` → Organization *Matthias Koehler Co.* → Project `airline` → Cluster `mongo-mk1`

Log in with the shared team account (`SECRET@protonmail.com`). Key sections:

- **Database Access** — manage database users, rotate passwords
- **Network Access** — IP allowlist
- **Browse Collections** — inspect data directly in the browser
- **Metrics** — connections, storage, operations
- **Access Manager** — manage project members and their roles
