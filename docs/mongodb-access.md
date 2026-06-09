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

Two access levels are available. Pick whichever fits your task — you decide.

| DB User | Atlas Role | What it gives you |
|---|---|---|
| `airline-collector-rw` | `atlasAdmin` | **Full access** — read, write, delete, manage collections/indexes, plus user and cluster administration. Shared team account; also used by the collectors. |
| `airline-reader-ro` | `read` (all databases) | **Read-only** across all databases. Use this when you only need to query data and want zero risk of changing anything. |
| `matthiaskoehler_db_user` | `atlasAdmin` | Matthias' personal admin account. |

The SRV URI contains the password in plain text — it is a secret and must
**never be committed to Git**.

All credentials (DB-user URIs, Atlas UI login) are stored in **Proton Pass**
under the shared team account `SECRET@protonmail.com` —
ask Matthias for access. See "Rotating a password" below if a credential needs
to be changed.

---

## Setting Up a Connection (all platforms)

### Step 1 — Create a `.env` file

In the project root `airline-data-platform/` (already gitignored):

```bash
MONGO_DB=airline_landing

# Read-only — for notebooks and exploration:
MONGO_URI=mongodb+srv://airline-reader-ro:<PASSWORD>@mongo-mk1.ptb1k2b.mongodb.net/?appName=mongo-mk1

# Read-write — for collectors and ETL (write=True in connector):
MONGO_URI_RW=mongodb+srv://airline-collector-rw:<PASSWORD>@mongo-mk1.ptb1k2b.mongodb.net/?appName=mongo-mk1
```

Both variables must be present. `from_env()` uses `MONGO_URI` (read-only) by default;
`from_env(write=True)` uses `MONGO_URI_RW`. Get the passwords from Proton Pass
(`SECRET@protonmail.com`).

Credentials are stored in **Proton Pass** — ask Matthias for access. Never share
passwords via email, Slack, or unencrypted chat.

### Step 2 — Test the connection

```bash
python - <<'EOF'
# load_dotenv() reads the .env file and injects its keys into the process
# environment. The secret (the connection URI with the password) therefore
# never appears in this source code — only in .env, which is gitignored.
# This is why the script itself is safe to commit, share, or paste.
from dotenv import load_dotenv; load_dotenv()
import os
from pymongo import MongoClient

# os.getenv() reads the secret from the environment at runtime — never hardcoded.
# Best practice (12-factor app config): configuration and credentials live in the
# environment, the code stays free of secrets. Same pattern as db/mongo/connector.py.
uri = os.getenv("MONGO_URI")
if not uri:
    raise RuntimeError("MONGO_URI not set — is .env present?")

c = MongoClient(uri, serverSelectionTimeoutMS=5000)
print(c.admin.command("ping"))   # expected: {'ok': 1.0}
c.close()
EOF
```

**Why secret management is done this way:**
- A hardcoded password ends up in Git history forever — even if deleted later, it stays in old commits. Environment variables avoid this entirely.
- `.env` is in `.gitignore`, so the secret lives only on each machine, never in the repo.
- The code reads `MONGO_URI` the same way everywhere (local Mac, aws-airline-1, CI), so the *same* code runs in any environment — only the `.env` differs.
- This mirrors the production-grade pattern: secrets injected at runtime (here via `.env`; in cloud setups via a secrets manager), never baked into the artifact.

### Future: secret management on aws-airline-1

The collectors and dashboard run on **AWS Lightsail `aws-airline-1`** (provisioned
2026-06-05). Currently `.env` is deployed manually to the VM. A future improvement
is to replace it with an AWS-native secret store:

| Service | Use | Cost |
|---|---|---|
| **SSM Parameter Store** (`SecureString`) | Config + secrets, KMS-encrypted. No auto-rotation. | Standard tier free |
| **AWS Secrets Manager** | Dedicated secret store with automatic rotation, RDS integration. | ~$0.40/secret/month |

For this project, **Parameter Store is sufficient and free**. The Lightsail instance
gets an **IAM role** (instance profile) that allows `ssm:GetParameter` — `MONGO_URI`
is fetched from the AWS API at runtime, decrypted via KMS, and lives only in memory.
No plain-text secret on disk and every access is audited via CloudTrail.

```
Lightsail instance (IAM role)  →  ssm:GetParameter / secretsmanager:GetSecretValue
                               →  MONGO_URI in memory only, never written to disk
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
| `Authentication failed` | Wrong password in URI | Re-copy the URI from the channel it was shared on |
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

All collector scripts read `MONGO_URI`, `MONGO_URI_RW`, and `MONGO_DB` from the
environment (`.env` in the working directory). No code changes needed — only the
`.env` must be present.

**aws-airline-1 (ADS-B collector, dashboard):** `.env` lives at the project root
(`~/airline-data-platform/.env`). Deployed manually; SSM migration planned (see above).

**Local Mac (OpenSky collector):** `.env` in the project root (`airline-data-platform/.env`).

---

## Rotating a password

If a credential may have leaked (sent over an insecure channel, committed by
accident, shared too widely), rotate it — this takes ~30 seconds and instantly
invalidates the old password:

1. Atlas → **Database Access** → pick the user → **Edit**
2. **Edit Password** → **Autogenerate Secure Password** → **Copy**
3. **Update User**
4. Store the new password in Proton Pass and notify the team
5. Everyone updates `MONGO_URI` in their local `.env`

The old password stops working immediately — anyone still holding it (e.g. in an
old email) is locked out.

---

## Atlas UI Access (cloud.mongodb.com)

### How Atlas access actually works — two separate concepts

Atlas has two completely independent user layers:

**1. Atlas UI Members** — real people (or a shared account) who log into
`cloud.mongodb.com` to manage the project, view metrics, and handle database
user configuration. This is a browser login, not a database connection.

**2. Database Users** — these are not humans. They are MongoDB credentials
embedded in connection strings. They have no UI login. We have two of them set
up for the project (`airline-reader-ro` and `airline-collector-rw`, see Roles
Overview above).

→ Use the database user credentials / URIs for all application connections,
scripts, and tooling. **Do not** use the shared Atlas UI account for connecting
to the database.

### Shared team account

A shared Atlas UI account was set up on 2026-06-09 to give the full team access
to the Atlas console without sharing Matthias' personal account:

- **Account:** `SECRET@protonmail.com`
- **Access role:** `Project Data Access Admin` — full visibility into the
  project, clusters, metrics, and database user management. Cannot create or
  scale clusters, cannot touch billing.
- **2FA is mandatory:** the account uses two-factor authentication via the
  Protonmail inbox itself — you need access to `SECRET@protonmail.com`
  to receive the 2FA code each time you log in.
- **All credentials** (Protonmail login, Atlas login, database user URIs) are
  stored in **Proton Pass** (`SECRET@protonmail.com`) — ask Matthias
  for access.

### Atlas console sections

URL: https://cloud.mongodb.com → Project `airline` → Cluster `mongo-mk1`

- **Database Access** — manage DB users, rotate passwords
- **Network Access** — IP allowlist
- **Browse Collections** — inspect data directly
- **Metrics** — connections, storage, operations
- **Access Manager** — manage UI members (project-level invite/role changes)
