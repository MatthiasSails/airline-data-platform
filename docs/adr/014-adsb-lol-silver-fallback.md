# ADR 014 — adsb.lol Promoted to Silver as an Operational Fallback

**Status:** Accepted
**Date:** 2026-06-30
**Partially supersedes:** ADR 009 (lifts the "adsb.lol not promoted to Silver" decision; the rest of
ADR 009 — States as the central fact, dimensions, no `fact_flights`/`fact_delays` — still holds.)
**Builds on:** ADR 003 (dual-stream), ADR 004 (Mongo landing-zone hub), ADR 009.

---

## Context

ADR 009 rejected promoting adsb.lol into Silver, on **data-quality** grounds: adsb.lol's content is
a subset of OpenSky States once registration/type come from the AircraftDB, so promoting it added
dedup/normalization cost for no informational gain.

That reasoning still holds — but a separate, operational problem has since appeared and was not
contemplated in ADR 009: **OpenSky blocks the production VM's AWS egress IP** (no TCP/ICMP to
`opensky-network.org` from the VM's static IP — confirmed 2026-06-23, whole AWS range filtered, not
an Elastic IP / NAT-gateway-fixable issue). On the VM, `etl/bronze.py`'s OpenSky call now fails on
every run; `states_all` in MongoDB goes stale indefinitely while adsb.lol (no auth, not
IP-filtered) keeps updating normally.

Without a fallback, `map1` (and the live-map dashboard reading it) would silently freeze on the VM
the moment OpenSky stopped responding, with no automatic recovery path.

## Decision

1. `etl/bronze.py` fetches **both** sources every run: OpenSky `/states/all` (existing BBOX) and
   adsb.lol via `lat/lon/dist`, using a center + radius approximating the same Germany-wide BBOX
   coverage (adsb.lol has no native bounding-box query). adsb.lol needs no auth, so it is
   unaffected by the OpenSky token/egress problem.
2. `etl/silver.py` picks **whichever snapshot is freshest** by `fetched_at` — `states_all` or
   `adsb_raw` — and maps it into the same `map1` row shape. OpenSky stays the default in practice
   (it free-runs locally and wherever the VM's IP isn't blocked); adsb.lol only wins when OpenSky's
   snapshot has gone stale (the VM case).
3. `map1`'s schema is **unchanged** — no new columns, no constraint changes. The fallback is
   transparent to anything reading `map1`.
4. adsb.lol's `alt_baro == "ground"` and `seen_pos`-derived `time_position` quirks are handled in
   `map_adsb_doc()`; see inline comments in `etl/silver.py`.

## Rationale

- This is **not** a reversal of ADR 009's data-quality argument — OpenSky States is still the
  richer, preferred source. adsb.lol is promoted only as a **last-resort substitute**, not a
  parallel/competing fact.
- "Freshest wins" needs no environment-specific branching (no `if running_on_vm` flag) — it
  degrades automatically wherever OpenSky becomes unreachable, and recovers automatically once it
  isn't.
- Alternative considered and rejected: run OpenSky from a non-AWS host and push into the same
  Mongo collection (the fix originally planned in the known-issue note). Still a good idea for
  data quality, but doesn't remove the need for *some* fallback during the gap, and adds new
  infrastructure (a second always-on host) for a problem the existing adsb.lol Bronze collector
  already solves with zero new infra.

## Consequences

- `docs/architecture/README.md`: adsb.lol is no longer "planned, Bronze-only" — it is implemented
  and conditionally promoted to Silver. Diagram and prose updated accordingly.
- ADR 009 remains correct on everything except the one "not promoted to Silver" clause, which this
  ADR lifts for the fallback case only.
- `map1` rows can now originate from either source on a given refresh; `source`/`pipeline_run_id`
  audit fields in the Bronze documents (`states_all` vs `adsb_raw`) remain the way to tell which
  snapshot fed a given load, if ever needed for debugging.

## Related

- [ADR 009](009-states-api-silver-model.md), [ADR 003](003-dual-stream.md), [ADR 004](004-mongo-as-multisource-hub.md)
- [`architecture/README.md`](../architecture/README.md)
