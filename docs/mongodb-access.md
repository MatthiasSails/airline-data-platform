# MongoDB Atlas Access — Team Onboarding

**Cluster:** `mongo-mk1` (M0 Free Tier, eu-central-1 Frankfurt)
**Database:** `airline_landing`

**How the connection works:**
- **SRV string** (`mongodb+srv://`) — PyMongo resolves the cluster hosts automatically via DNS. No port or individual hostname needed; Atlas can replace nodes without changing your URI.
- **TLS** — all traffic is encrypted in transit. Atlas enforces this; plain connections are rejected. PyMongo enables it automatically for `mongodb+srv://` URIs.
- **SCRAM-SHA** — the authentication mechanism. Your password is never sent in plain text; Atlas and the client do a cryptographic challenge-response handshake. Visible as "SCRAM" in the Atlas UI under Database Access.

None of this requires any configuration — it is all handled automatically by PyMongo and Atlas when you set `MONGO_URI` in your `.env`.

---

## Roles Overview

| DB User | Atlas Role | Used by |
|---|---|---|
| `airline-collector-rw` | `readWriteAnyDatabase` | OpenSky collector (Mac), ADS-B collector (Liora VM) |
| `airline-reader-ro` | `read` (all databases) | Notebooks, ETL jobs (Bronze → Silver), FastAPI, Dashboard |
| `matthiaskoehler_db_user` | `atlasAdmin` (personal admin) | Matthias — Atlas console + direct DB work |

**Note:** FastAPI and dashboards that read from the Silver layer (Neon Postgres) will use a
separate read-only credential on Neon — not this Atlas credential.

The SRV URI contains the password in plain text — it is a secret and must
**never be committed to Git**. Share exclusively via an encrypted channel
(Bitwarden Shared Vault or Signal).

---

## Setting Up a Connection (all platforms)

### Step 1 — Create a `.env` file

In the project root `airline-data-platform/` (already gitignored):

```bash
# For collector machines (write access):
MONGO_URI=mongodb+srv://airline-collector-rw:<PASSWORD>@mongo-mk1.ptb1k2b.mongodb.net/?appName=mongo-mk1
MONGO_DB=airline_landing

# For notebooks and ETL jobs (read Bronze layer only):
MONGO_URI=mongodb+srv://airline-reader-ro:<PASSWORD>@mongo-mk1.ptb1k2b.mongodb.net/?appName=mongo-mk1
MONGO_DB=airline_landing
```

Passwords are distributed by Matthias via Bitwarden (`airline-data-platform` vault)
or Signal — never via Slack, email, or chat.

### Step 2 — Test the connection

```bash
python - <<'EOF'
from dotenv import load_dotenv; load_dotenv()
import os
from pymongo import MongoClient

uri = os.getenv("MONGO_URI")
if not uri:
    raise RuntimeError("MONGO_URI not set — is .env present?")

c = MongoClient(uri, serverSelectionTimeoutMS=5000)
print(c.admin.command("ping"))   # expected: {'ok': 1.0}
c.close()
EOF
```

### Step 3 — List collections (airline-reader-ro)

```bash
python - <<'EOF'
from dotenv import load_dotenv; load_dotenv()
import os
from pymongo import MongoClient

c = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
db = c[os.getenv("MONGO_DB", "airline_landing")]
for name in db.list_collection_names():
    print(f"{name}: {db[name].count_documents({})} docs")
c.close()
EOF
```

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `ServerSelectionTimeoutError` | IP not in Atlas allowlist | Contact Matthias with your IP: `curl -s ifconfig.me` |
| `Authentication failed` | Wrong password in URI | Re-copy URI from vault |
| `SSL handshake failed` | VPN interrupting TLS | Split-tunnel or disable VPN for the Atlas domain |
| `MONGO_URI not set` | `.env` missing or wrong working directory | Check `pwd` — must be the project root |

---

## IP Allowlist Note

Atlas is configured with `0.0.0.0/0` (all IPs allowed). The actual security
boundary is SCRAM authentication — without a valid credential, no access is
possible. This setting is deliberate for the project duration (learning
environment, M0 Free Tier) to avoid friction from changing IPs (home, office,
café, Liora VM after reboot).

For production use: switch to individual IP entries or an Atlas Private Endpoint.

---

## Collector Deployments

All collector scripts read `MONGO_URI` and `MONGO_DB` from the environment
(`.env` in the working directory). No code changes needed — only the `.env`
must be present.

**Liora VM (ADS-B collector):** `.env` lives at
`~/airline-data-platform/03-data-collection/.env`.

**Local (OpenSky collector):** `.env` in the project root.

---

## Atlas Console (Matthias / Project Admin only)

URL: https://cloud.mongodb.com → Project `airline-data-platform` → Cluster `mongo-mk1`

Key sections:
- **Database Access** — manage DB users, rotate passwords
- **Network Access** — IP allowlist
- **Browse Collections** — inspect data directly
- **Metrics** — connections, storage, operations
