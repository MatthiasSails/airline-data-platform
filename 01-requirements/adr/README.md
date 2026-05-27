# Architecture Decision Records (ADRs)

Each ADR documents one significant decision: the context, the choice, the alternatives we considered, and the consequences. They are the single source of truth for **why** the architecture looks the way it does.

## Index

| # | Title | Status | Date |
|---|---|---|---|
| [001](001-postgres-first.md) | PostgreSQL First, MongoDB in Phase 2 | Accepted | 2026-05-12 |
| [002](002-psycopg2.md) | psycopg2 as PostgreSQL Driver | Accepted | 2026-05-12 |
| [003](003-dual-stream.md) | Dual-Stream ADS-B Strategy (OpenSky + adsb.lol) | Accepted | 2026-05-13 |
| [004](004-mongo-as-multisource-hub.md) | MongoDB as Multi-Source Landing Zone Hub | Accepted | 2026-05-18 |
| [005](005-opensky-mongo-migration.md) | OpenSky Pipeline Migration: PostgreSQL → MongoDB | Accepted | 2026-05-18 |
| [006](006-mongo-atlas-migration.md) | MongoDB Migration: Self-hosted on VM → MongoDB Atlas | Accepted | 2026-05-27 |
| [007](007-decouple-from-liora-vm.md) | Decouple from Liora VM; Dedicated Cloud Compute + Neon Postgres | Accepted | 2026-05-27 |

## Format

Each ADR follows this structure:

- **Context** — what situation required a decision
- **Decision** — what we chose
- **Rationale** — why, including rejected alternatives
- **Consequences** — what changes because of this decision

## When to write a new ADR

Write one when:
- A choice is hard to reverse (technology, architecture pattern, vendor)
- Multiple reasonable alternatives existed
- A future team member would ask "why did they do it that way?"

Do **not** write ADRs for:
- Reversible coding decisions (variable names, function signatures)
- Routine library upgrades
- Implementation details that are obvious from the code
