# MongoDB Atlas Access — Team Onboarding

The Bronze landing zone runs on **MongoDB Atlas** (managed, `eu-central-1`, M0 Free Tier). Two ways
in: the **browser console** (shared team account) and **database users** (connection-string URI for
code). All real values — account, passwords, full SRV URI — live in **Proton Pass** (vault
"Airlines"); ask the project owner. Nothing secret is committed to this repo.

---

## Access

| What | Role / use | Secret |
|---|---|---|
| Atlas console (`cloud.mongodb.com`) | shared team account — `Project Data Access Admin`, MFA on | Proton Pass |
| DB user `airline-reader-ro` | `read` — notebooks, exploration | Proton Pass |
| DB user `airline-collector-rw` | write — collectors / ETL | Proton Pass |

From the console: manage DB users, the IP allowlist, browse collections, view metrics.

---

## Connecting from code

Put the connection string in `.env` at the project root (gitignored) — full SRV URI from Proton Pass:

```bash
MONGO_URI=mongodb+srv://airline-reader-ro:<PASSWORD>@<cluster>.mongodb.net/...      # read-only
MONGO_URI_RW=mongodb+srv://airline-collector-rw:<PASSWORD>@<cluster>.mongodb.net/... # write
```

- **The `etl/` pipeline** (`bronze.py` / `silver.py`) connects directly via `pymongo.MongoClient`
  and reads **`MONGO_URL`** (not `MONGO_URI`).

> ⚠️ **Naming drift to reconcile:** the live pipeline uses Mongo db `airlines`, collections
> `states_all` (OpenSky) and `adsb_raw` (adsb.lol); older docs reference `airline_landing` with
> `opensky_raw` / `adsb_raw`. Until the convention is settled, treat the console's "Browse
> Collections" as the source of truth.

---

## Notes

- **IP allowlist:** Atlas is open to `0.0.0.0/0` — security relies on SCRAM auth. Tighten to specific
  IPs or a Private Endpoint for production.
- **`ServerSelectionTimeoutError` / `SSL handshake failed`** usually means your IP isn't allowlisted
  (or a VPN is interrupting TLS) — add your IP under Network Access in the console.
