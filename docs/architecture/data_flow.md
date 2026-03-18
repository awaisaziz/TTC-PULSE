# Data Flow

Generated: 2026-03-17 (America/New_York)

## End-to-End Path

1. Source files and snapshots enter **Raw** registries.
2. Row-preserving parsing lands in **Bronze** tables.
3. Canonicalization and linkage metadata are built in **Silver** and facts.
4. Stakeholder-oriented aggregations are produced in **Gold** marts.
5. Streamlit reads DuckDB Gold tables (with optional Parquet export parity).

## Live Alert Side-car Flow

`poll_service_alerts` -> `raw_gtfsrt_alert_snapshots_registry` -> `bronze_gtfsrt_alert_entities` -> `silver_gtfsrt_alert_entities` -> `fact_gtfsrt_alerts_norm` -> `gold_alert_validation`

## Runtime Target

- Backend: DuckDB + Parquet.
- Frontend: Streamlit.
- Spark: explicitly excluded from MVP.
