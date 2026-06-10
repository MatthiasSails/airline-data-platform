# ETL — Bronze → Silver

Transformation layer: reads raw payloads from the **Bronze** landing zone (MongoDB Atlas) and
loads the **Silver** layer in Supabase Postgres.

## Current state — `map1` MVP

[`opensky_to_supabase.py`](opensky_to_supabase.py) is the working ETL. It reads `adsb_raw` +
`opensky_raw` from Atlas, flattens both into a common row shape, and upserts into a single flat
table **`map1`** (icao24, position, callsign, track, vertical_rate, …) that backs the live-map
dashboard.

This is a deliberate lean MVP, **not** the target star schema yet:

- single flat table `map1` — no `fact_states`, no dimensions
- **no unit conversion** — raw OpenSky SI values are stored as-is (no m→ft / m/s→kt)
- **no `airline_icao` resolution** — operator attribution is not computed
- connects to Supabase directly via `psycopg2` (SSH tunnel for local dev; see the module docstring)

> `map1` does not appear in [`../warehouse/schema.sql`](../warehouse/schema.sql) — it was created via
> the Supabase UI. See the ETL caveats in the project `CLAUDE.md` (no dedup key, reads all history).

## Target model (planned, not built)

The curated Silver model is the star schema in [`../warehouse/schema.sql`](../warehouse/schema.sql),
documented in [`docs/architecture/silver-layer-er.md`](../../docs/architecture/silver-layer-er.md):
`fact_states` + `dim_aircraft`, `dim_airlines`, `dim_airports` (see ADR 008/009). Building it means
adding unit conversion, `airline_icao` resolution, and the dimension loaders
(`01-bronze/reference/` → dims) on top of the current extract/transform.
