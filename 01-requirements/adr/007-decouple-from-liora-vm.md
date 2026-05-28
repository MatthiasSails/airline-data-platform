# ADR 007 — Decouple Airline Project from Liora VM; Dedicated Cloud Compute + Neon Postgres

**Status:** Accepted
**Date:** 2026-05-27
**Supersedes:** Infrastructure assumptions in pre-Phase-2 ADRs that placed everything on Liora VM.
**Builds on:** ADR 004 (MongoDB as landing zone), ADR 006 (Atlas migration).

---

## Context

ADR 006 moved the MongoDB landing zone from the Liora VM to MongoDB Atlas. That left
the Liora VM hosting only the Streamlit dashboard container and the (now unused)
`pg_container` for Postgres. Three further pressures arrived in parallel:

1. **Operational friction with Liora VM** — public IP rotates on every reboot, the
   VM is shared with `Liora_Learn_Github`, and project work creates noise on a
   machine that is primarily a learning sandbox for someone else.
2. **Pavel's research (Perplexity, May 2026)** sketched a fully serverless AWS
   architecture: Lambda + EventBridge for ETL, S3 as data lake, **Neon Postgres**
   as the analytics warehouse, FastAPI on Lambda via Mangum, frontend on
   Vercel/Netlify. The Neon idea is the strongest candidate for the Silver
   layer but is **not yet committed** — Pavel will evaluate it; the rest
   trades VM operability for AWS-specific lock-in and complexity.
3. **AWS SAA learning goal** (Matthias) — the project should be a vehicle for
   practicing AWS primitives (EC2, Elastic IP, IAM, Security Groups) rather
   than avoiding them.

A decision was needed: how much of Pavel's serverless vision to adopt, and where
the project's compute lives going forward.

---

## Decision

1. **Liora VM is removed from the airline project scope.** The dashboard and any
   future ingestion/API workloads move to a dedicated cloud VM. Liora VM remains
   the deployment target for `Liora_Learn_Github` only.

2. **A dedicated cloud VM with a stable IP becomes the project's compute home.**
   Concrete choice between **AWS EC2 Free Tier (`t2.micro` / `t3.micro` + Elastic IP)** and
   **Hetzner Cloud (CX11 / CAX11)** is deferred but **AWS is favoured** because of
   the SAA learning goal and ecosystem synergy (S3, IAM, optional later Lambda).

3. **MongoDB Atlas stays as the Bronze / raw landing zone** (per ADR 006). May
   be re-evaluated later (e.g. S3 raw lake as Pavel suggested), but is stable
   for Step 2.

4. **The Silver / analytical warehouse will be a managed serverless Postgres**
   — exact provider **not yet decided**. **Neon is the leading candidate** and
   Pavel will evaluate it (this replaces the original "Postgres on Liora VM"
   plan). Supabase from issue #3 is unlikely (too much beyond just the DB).
   Self-hosted Postgres is rejected for the same reasons as MongoDB in ADR 006.
   Final commit on Neon (or an alternative) is deferred until Pavel reports
   back from the evaluation.

5. **Pavel's full serverless vision (Lambda / EventBridge / Mangum / Vercel) is
   parked for now.** Reasons: end-to-end working system first, then optimise.
   The dedicated VM choice does not preclude moving individual workloads to
   Lambda later if it makes sense.

6. **Streaming / sub-minute updates** remain an aspirational goal. Concrete
   tooling (polling loop, Kinesis, Kafka, ADSB.one direct-to-frontend) is not
   chosen here. For Step 2, ingestion stays at the current cadence into Atlas.

---

## Rationale

**Why a VM, not Lambda?**
- Faster path to a working end-to-end demo.
- Matthias is preparing for AWS SAA, where EC2 + VPC + Elastic IP + Security
  Groups are core exam topics; hands-on practice now is directly useful.
- Lambda's cold starts, 15-min execution limit, and packaging constraints add
  complexity that is not needed at the project's data volume.
- Migrating from a VM to Lambda later is well-trodden ground; the reverse is not.

**Why Neon is the leading candidate (still under evaluation):**
- Managed, serverless, generous free tier — same arguments as Atlas for MongoDB.
- Pavel already started investigating it; concentrating his contribution there
  makes coordination easy.
- Supabase ships Postgres + Auth + Storage + Realtime; we only want the database.
  Neon is the leaner choice.

Final commit on Neon is held until Pavel reports back. The ADR is accepted on
the **principle** (managed serverless Postgres, evaluated by Pavel) — not on
the specific vendor.

**Why decouple from Liora VM at all?**
- Liora VM is primarily Liora's learning environment. Airline workloads share
  CPU/RAM/disk with corolla-run; an issue in one project can take down the
  other.
- The Liora VM's IP-on-reboot pattern (and the Cloudflare DDNS workaround) is
  a wart we would otherwise carry forever.

**Rejected alternatives:**

| Alternative | Why not |
|---|---|
| Stay on Liora VM | Already moved off Mongo (ADR 006); finishing the job is cleaner. |
| Full serverless (Pavel's vision) | Too many new moving parts before end-to-end works. Revisit post-Defense. |
| Hetzner-first | No AWS-ecosystem synergy and weaker SAA learning value. Still on the table if EC2 free-tier limits bite. |
| DynamoDB instead of Mongo Atlas | 400 KB per-document limit forces ADS-B snapshot redesign. Not worth the savings. |
| Supabase | Heavier than needed; Neon is the right scope. |

---

## Consequences

**Positive:**
- Airline project no longer carries Liora-VM-specific quirks (DDNS, host-key
  resets, shared resources).
- A stable IP becomes a known thing on AWS, paired with concrete SAA practice.
- Bronze (Atlas) and Silver (Neon) are both managed — no DB ops burden.
- Pavel has a clearly scoped contribution (Neon setup) that fits his
  architectural interests.

**Negative / tradeoffs:**
- AWS Free Tier expires after 12 months — at ~$8/month after that for t2.micro.
  Re-evaluate Hetzner at that point.
- Atlas + Neon both depend on outbound internet from the compute VM — but the
  same was true once we left the all-on-one-VM setup with ADR 006.
- Pavel's Perplexity-derived vision is partially declined. Action item:
  comment on issues #1/#2/#3 with this decision so Pavel can align.

**Action items (not for this ADR but follow-on):**
- Provision new compute VM (AWS or Hetzner).
- Whitelist its IP in Atlas Network Access; remove old Liora IP.
- Migrate `adsb_dashboard` container off Liora VM.
- **Pavel: evaluate Neon for the Silver warehouse role.** Report back with
  a recommendation (Neon vs. alternative, plus tooling thoughts for the
  Star Schema layer). Once decided, provision and share the connection
  string into the team channel.
- Update `01-requirements/c-architecture/architecture_m.md` to reflect this.
- Reply to GitHub issues #1/#2/#3 with the chosen direction.

---

## Addendum 2026-05-28 — Addressing: dual-stack, not IPv6-only

While scoping the new compute VM, IPv6-only was considered as a cost lever
(AWS bills every public IPv4 at ~$0.005/h ≈ $3.60/mo since Feb 2024; IPv6 is
free). Investigation showed **IPv6-only does not work for this project**:

1. **MongoDB Atlas is reached outbound over IPv4** (Atlas is IPv4 in practice).
   An IPv6-only instance cannot reach an IPv4-only target without NAT64 via a
   NAT Gateway (~$32/mo) — which wipes out any IPv4 savings.
2. **The dev machine has no global IPv6** (only ULA addresses; `curl -6` to the
   internet returns empty). SSH to an IPv6-only instance would be impossible
   from our side.

**Decision:** run the instance **dual-stack (IPv4 + IPv6)**:
- Web ingress → Cloudflare **orange** proxy (may use the IPv6 AAAA record;
  Cloudflare bridges IPv4 clients to an IPv6 origin).
- Atlas outbound + SSH → over **IPv4**.

This **refines, not reverses** the Elastic-IP/IPv4 plan in decision #2 above —
IPv6 is added as an AAAA record for the web path rather than going IPv6-only.

**Cost:** public IPv4 is included in the 12-month Free Tier → **$0 in year one**.
After that, ~$3.60/mo for the IPv4. Optional later optimisation: **SSM Session
Manager** for shell access without a public IP — but Atlas outbound remains the
real IPv4 anchor, so SSH alone doesn't remove the IPv4 dependency.

Documented in issue #1 comments. Background reference:
`knowledgebase/tools/aws-networking-notes.md`.
