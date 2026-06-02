# ADR 006 — MongoDB Migration: Self-hosted on Liora VM → MongoDB Atlas

**Status:** Accepted
**Date:** 2026-05-27
**Supersedes:** Infrastructure aspect of ADR 004 (MongoDB hosted on Liora VM)
**Builds on:** ADR 004 (multi-source landing zone), ADR 005 (OpenSky → MongoDB)

---

## Context

ADR 004 established MongoDB as the central landing zone for all raw ingestion. The
initial deployment ran `mongo:7-jammy` as a Docker container (`my_mongo`) on the
Liora VM (AWS EC2 Ubuntu), reachable via `liora-vm.matthiaskoehler.com:27017`.

Several pain points emerged during Phase 2 / early Phase 3 work:

- **VM IP volatility** — every reboot changes the public IP. Cloudflare DDNS handles
  the DNS name, but operational friction remains (SSH host-key resets, IP-whitelist
  drift in any external service).
- **Backup story** — no point-in-time recovery, only manual `mongodump`. A wrong
  command or volume corruption would lose all landing-zone data.
- **Credential management** — single shared `airline_admin` user, no fine-grained
  roles, no audit trail.
- **Single point of failure** — VM downtime stops both the database and the
  dashboard. For the Final Defense demo (2026-07-20), this is a real risk.
- **DataScientest evaluation criteria** — managed cloud services demonstrate
  awareness of modern data engineering tradeoffs (build vs. buy).

MongoDB Atlas Free Tier (M0, 512 MB) covers the project's data volume comfortably
(~0.3 MB after Step 1, expected < 100 MB by Final Defense).

---

## Decision

Migrate the `airline_landing` database from the self-hosted MongoDB on Liora VM
to **MongoDB Atlas** (cluster `mongo-mk1`, region eu-central-1 Frankfurt).

`MONGO_URI` in all `.env` files points to the Atlas SRV connection string:

```
mongodb+srv://<user>:<pass>@mongo-mk1.ptb1k2b.mongodb.net/?appName=mongo-mk1
```

The application code (`db/mongo/connector.py`) is **unchanged** — it already
reads `MONGO_URI` and `MONGO_DB` as separate env vars, so swapping the URI is
sufficient.

---

## Migration steps (executed 2026-05-27)

1. Atlas cluster `mongo-mk1` created (M0 Free Tier).
2. Database user `matthiaskoehler_db_user` provisioned with `readWrite` on
   `airline_landing`.
3. Network Access list seeded with the local Mac IP and the current Liora VM
   public IP (`52.214.227.99/32`).
4. Connectivity verified from Mac and from Liora VM (pymongo ping + TLS handshake).
5. Data transferred via streamed `mongodump | mongorestore` inside the `my_mongo`
   container — 123 documents across 3 collections (`adsb_raw`, `opensky_raw`,
   `flight_tracker_raw`), 0 failures.
6. `.env` updated in three locations:
   - `airline-data-platform/.env` (local Mac)
   - `airline-data-platform/03-data-collection/.env` (VM)
   - `airline-data-platform/04-dashboard/adsb-dashboard/.env` (VM)
   Old VM URI kept commented for rollback.
7. `adsb_dashboard` container recreated via `docker compose up -d --force-recreate`
   to pick up the new `MONGO_URI` from `.env`.
8. End-to-end smoke test: ADS-B collector run on Mac writes to Atlas; dashboard
   on VM reads from Atlas.

---

## Operational implications

| Aspect | Before (VM Mongo) | After (Atlas) |
|---|---|---|
| Host | `liora-vm.matthiaskoehler.com:27017` | `mongo-mk1.ptb1k2b.mongodb.net` (SRV) |
| TLS | None | Required (Atlas-managed certs) |
| Auth | `authSource=admin` user/pass | SCRAM-SHA user/pass via SRV |
| Backups | Manual `mongodump` | Atlas continuous backup (Free Tier: snapshot-based) |
| Network ACL | None (firewall only) | Atlas Network Access IP allow-list |
| Cost | EC2 RAM/disk share | $0 (M0 Free Tier, 512 MB) |
| Outbound from VM | n/a (loopback) | Requires VM outbound HTTPS — confirmed working |

---

## Open issues

- **VM IP rotation** — every reboot, the new public IP must be added to the
  Atlas Network Access list. Options to address later:
  1. Pin AWS Elastic IP to the EC2 instance (~$3/month if not attached, free if attached).
  2. Allow `0.0.0.0/0` and rely on DB user/password auth (Atlas warns; acceptable
     for a learning project but documented as a tradeoff).
  3. Manual IP update after each reboot (documented procedure).
- **VM Mongo container `my_mongo`** — left running for now as fallback / rollback
  target. Will be stopped (not removed) once Atlas is verified stable for ≥ 1 week.
- **Future collectors** — anyone (including a Phase 5 Airflow DAG) that needs to
  write to MongoDB must read `MONGO_URI` from env, never hardcode the host.

---

## Consequences

**Positive:**
- Dashboard and DB now decoupled from VM uptime.
- Free managed backups, monitoring, and connection pooling.
- Migration was zero-friction at the code layer (env var swap only).
- Demonstrates awareness of managed-service tradeoffs for the Final Defense.

**Negative / tradeoffs:**
- Network Access management adds an extra step at VM-reboot time (until Elastic IP).
- All ingestion now depends on outbound internet from the executing host. If
  Atlas or its DNS becomes unreachable, collectors fail (mitigated by collectors
  being idempotent batch jobs — re-run later).
- Free Tier has hard limits (512 MB storage, 100 max connections) — sufficient
  for the project scope but not for production-scale flight data over months.
