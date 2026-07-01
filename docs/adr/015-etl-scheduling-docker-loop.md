# ADR 015 — ETL Scheduling Stays a Docker Loop, Not systemd

**Status:** Accepted
**Date:** 2026-07-01
**Related:** PR #21 (closed, not merged), PR #26 (carries the Docker-loop approach forward into
separate bronze/silver containers)

---

## Context

PR #21 proposed replacing `etl/run_pipeline.sh`'s `while true; sleep 45` loop with a systemd timer
(`OnUnitActiveSec=5s`) plus a `deploy.sh` script, running the pipeline as a one-shot script directly
on the VM host instead of inside the long-lived `etl_app2` Docker container.

Two problems surfaced on review:

1. **Loses Portainer/GitOps visibility.** The current setup is fully GitOps-managed: Portainer polls
   `main` and redeploys the container automatically, with centralized logs/status in the Portainer
   UI. Moving to systemd would mean deploying via manual SSH + `deploy.sh`, and reading logs via
   `journalctl` instead of `docker logs` / Portainer — a regression in operational consistency with
   the rest of the stack (`airline-dashboard`, `airline-landing`).
2. **5s doesn't fit either upstream API's limits.** OpenSky's BBOX query costs 2 credits/call
   (`etl/bronze.py`); the account is on the Registered tier (4,000 credits/day, confirmed in
   `docs/data-sources/airline_api_market_overview.md`). At 5s intervals: 17,280 calls/day × 2 =
   34,560 credits/day — 8.6x over even the Data-feeder tier (8,000/day). The daily budget would be
   exhausted in ~5-6h, after which the pipeline would be rate-limited for the rest of the day —
   worse than the 45s status quo. adsb.lol's maintainers also explicitly recommend 30-60s intervals
   for periodic requests (`docs/data-sources/adsb_lol_api_doc.md`) and call faster polling "hammering
   the endpoint."

## Decision

Keep ETL scheduling as a Docker container running a Bash loop (`while true; ... ; sleep N; done`),
managed by Portainer GitOps — not systemd, not a host-native process. PR #21 was closed without
merging (see PR #21 review comment for the full comparison).

The interval was tightened from 45s to a split cadence as part of #23/PR #26: bronze (rate-limited,
external fetch) runs every 50s; silver (local Mongo → Postgres refresh, no external rate limit) runs
independently every 10s. See ADR 016 for the container-split rationale.

## Rationale

- Sub-minute scheduling doesn't need systemd or cron (cron's floor is 1 minute) — a plain Bash loop
  inside a long-lived container already provides arbitrary-precision scheduling with Docker/Portainer
  handling restarts (`restart: unless-stopped`) and GitOps deploys for free.
- 50s for bronze leaves comfortable OpenSky credit headroom (1,440 calls/day × 2 = 2,880/4,000 =
  72%, vs. 96% at 45s) and lands at the upper end of adsb.lol's recommended 30-60s window.

## Consequences

- No systemd units, no `deploy.sh`, no native host processes for the ETL — everything stays
  containerized and Portainer-managed.
- Scheduling logic lives in `etl/run_bronze.sh` / `etl/run_silver.sh`, not in a separate
  orchestration layer.

## Related

- [ADR 012](012-github-flow-branch-merge.md) (branch/PR workflow — PR #21 went through the closed-without-merge path)
- [docs/data-sources/opensky_api_doc.md](../data-sources/opensky_api_doc.md), [docs/data-sources/adsb_lol_api_doc.md](../data-sources/adsb_lol_api_doc.md)
