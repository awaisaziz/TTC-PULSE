# CHANGELOG

## 2026-03-17 - Step 2 (Silver Canonical Model)

- Added Silver normalization modules for bus, subway, and GTFS-RT entities.
- Built canonical facts: `fact_delay_events_norm`, `fact_gtfsrt_alerts_norm`.
- Built GTFS dimensions: `dim_route_gtfs`, `dim_stop_gtfs`, `dim_service_gtfs`.
- Built bridge table: `bridge_route_direction_stop`.
- Built alias dimensions: `dim_route_alias`, `dim_station_alias`, `dim_incident_code`.
- Built review QA tables: `route_alias_review`, `station_alias_review`, `incident_code_review`.
- Exported Step 2 outputs to local Parquet and registered all tables in DuckDB.
- Added Step 2 technical docs, caveats, layer contracts, and agent run log.

## 2026-03-17 - Step 3 (Gold Marts + GTFS-RT Side-car)

- Added Gold mart builders for core delay analytics, linkage quality, route/station/time reliability metrics, rankings, and alert validation.
- Added reliability scoring framework (`src/ttc_pulse/marts/scoring.py`) implementing weighted composite score with exposed components.
- Added deferred scaffold for `gold_spatial_hotspot` with confidence-gated status.
- Added GTFS-RT side-car scripts: polling and parsing (`src/ttc_pulse/alerts/*`).
- Added Airflow DAG `airflow/dags/poll_gtfsrt_alerts.py` scheduled every 30 minutes for live alerts chain.
- Exported Gold outputs to local Parquet and registered in DuckDB.
- Added Step 3 docs: gold layer, design decisions, confidence gating, airflow pipeline notes, linkage quality QA, agent run log, and summary artifacts.

## 2026-03-17 - Step 4 (Dashboard + Deployment + Final Docs)

- Built modular Streamlit dashboard with ordered stakeholder pages (1-9 locked panel order).
- Added dashboard utility modules for DuckDB loaders, reusable charts, and formatting helpers.
- Added deployment artifacts: `requirements.txt` and optional `.streamlit/config.toml`.
- Added dashboard documentation (`panel_descriptions`, `ux_decisions`) and architecture/pipeline narratives.
- Added final delivery documentation: `docs/architecture.md`, `docs/data_dictionary.md`, `docs/runbook.md`, and `reports/final_project_summary.md`.
- Recorded Step 4 execution log in `docs/changelog/agent_run_logs/step4_run.md`.

