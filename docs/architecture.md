# Architecture

Generated: 2026-03-17 (America/New_York)

## TTC Pulse / TTC Reliability Observatory

MVP architecture follows a medallion-style pipeline with Streamlit serving stakeholder marts from DuckDB.

### Layers

- Raw: immutable source registries and snapshot metadata.
- Bronze: row-preserving extracts with lineage.
- Silver: canonical mode-specific normalization.
- Facts: normalized cross-mode analytical facts.
- Gold: stakeholder marts powering dashboard panels.

### Runtime

- Streamlit app deployment target.
- DuckDB + Parquet backend.
- Spark excluded in MVP.

### Side-car Scheduler

One Airflow DAG (`poll_gtfsrt_alerts`) handles GTFS-RT service alerts every 30 minutes and updates the alert validation path.
