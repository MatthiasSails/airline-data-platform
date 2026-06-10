# ETL — Bronze → Silver

Transformation layer: reads raw payloads from the **Bronze** landing zone (MongoDB Atlas) and
loads the curated **Silver** star schema in PostgreSQL (Neon).

- **Target model:** [`docs/architecture/silver-layer-er.md`](../../docs/architecture/silver-layer-er.md)
  — `fact_states` + `dim_aircraft`, `dim_airlines`, `dim_airports`.
- **DDL:** [`../warehouse/schema.sql`](../warehouse/schema.sql).

_Status: to be implemented (no transformation code yet — exploration lives in
[`01-bronze`](../../01-bronze) notebooks)._
