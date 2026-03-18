# Step Review (Steps 1-4) - TTC Pulse / TTC Reliability Observatory

Context: TTC Pulse is focused on TTC public transit reliability analysis for Toronto, Ontario, Canada.
Audit date: 2026-03-17 (America/New_York)

## 1) Files Saved Locally

Below are the key deliverable files confirmed on disk by step.

### Step 1 (Raw + Bronze + DB foundation)
- `src/ttc_pulse/utils/project_setup.py`
- `src/ttc_pulse/ingestion/ingest_bus.py`
- `src/ttc_pulse/ingestion/ingest_subway.py`
- `src/ttc_pulse/ingestion/ingest_gtfs.py`
- `src/ttc_pulse/ingestion/register_gtfsrt_snapshots.py`
- `src/ttc_pulse/bronze/build_bronze_tables.py`
- `configs/schema_bus.yml`
- `configs/schema_subway.yml`
- `docs/source_inventory.md`
- `logs/ingestion_log.csv`
- `docs/step1_summary.md`
- `data/ttc_pulse.duckdb`

### Step 2 (Silver + facts + dims + bridge + review)
- `src/ttc_pulse/normalization/normalize_bus.py`
- `src/ttc_pulse/normalization/normalize_subway.py`
- `src/ttc_pulse/normalization/normalize_gtfsrt_entities.py`
- `src/ttc_pulse/facts/build_fact_delay_events_norm.py`
- `src/ttc_pulse/facts/build_fact_gtfsrt_alerts_norm.py`
- `src/ttc_pulse/gtfs/build_dimensions.py`
- `src/ttc_pulse/gtfs/build_bridge.py`
- `src/ttc_pulse/aliasing/build_route_alias.py`
- `src/ttc_pulse/aliasing/build_station_alias.py`
- `src/ttc_pulse/aliasing/build_incident_code_dim.py`
- `src/ttc_pulse/aliasing/build_review_tables.py`
- `docs/layers/silver_layer.md`
- `docs/architecture/layer_contracts.md`
- `docs/decisions/alias_strategy.md`
- `docs/qa_and_review/review_tables.md`
- `docs/qa_and_review/known_caveats.md`
- `docs/changelog/agent_run_logs/step2_run.md`
- `docs/step2_summary.md`

### Step 3 (Gold marts + GTFS-RT side-car)
- `src/ttc_pulse/marts/build_gold_delay_core.py`
- `src/ttc_pulse/marts/build_gold_linkage_quality.py`
- `src/ttc_pulse/marts/build_gold_route_metrics.py`
- `src/ttc_pulse/marts/build_gold_station_metrics.py`
- `src/ttc_pulse/marts/build_gold_time_metrics.py`
- `src/ttc_pulse/marts/build_gold_rankings.py`
- `src/ttc_pulse/marts/build_gold_alert_validation.py`
- `src/ttc_pulse/marts/scoring.py`
- `src/ttc_pulse/alerts/poll_service_alerts.py`
- `src/ttc_pulse/alerts/parse_service_alerts.py`
- `airflow/dags/poll_gtfsrt_alerts.py`
- `docs/layers/gold_layer.md`
- `docs/decisions/design_decisions.md`
- `docs/decisions/confidence_gating.md`
- `docs/pipelines/airflow_dag.md`
- `docs/qa_and_review/linkage_quality.md`
- `docs/changelog/agent_run_logs/step3_run.md`
- `outputs/final_metrics_summary.md`
- `docs/step3_summary.md`

### Step 4 (Dashboard + deployment + final docs)
- `app/streamlit_app.py`
- `app/pages/01_Linkage_QA_Panel.py`
- `app/pages/02_Reliability_Overview.py`
- `app/pages/03_Bus_Route_Ranking.py`
- `app/pages/04_Subway_Station_Ranking.py`
- `app/pages/05_Weekday_x_Hour_Heatmap.py`
- `app/pages/06_Monthly_Trends.py`
- `app/pages/07_Cause_Category_Mix.py`
- `app/pages/08_Live_Alert_Validation.py`
- `app/pages/09_Spatial_Hotspot_Placeholder.py`
- `src/ttc_pulse/dashboard/loaders.py`
- `src/ttc_pulse/dashboard/charts.py`
- `src/ttc_pulse/dashboard/formatting.py`
- `docs/dashboard/panel_descriptions.md`
- `docs/dashboard/ux_decisions.md`
- `docs/architecture/data_flow.md`
- `docs/pipelines/agent_pipeline.md`
- `docs/architecture/overview.md`
- `docs/changelog/agent_run_logs/step4_run.md`
- `docs/architecture.md`
- `docs/data_dictionary.md`
- `docs/runbook.md`
- `reports/final_project_summary.md`
- `requirements.txt`
- `.streamlit/config.toml`
- `src/RUN_PROJECT.md` (additional run guide in `src/`)

## 2) DuckDB Tables Created

### Step 1 tables (Raw + Bronze)
- `raw_bus_delay_events_registry` (100)
- `raw_subway_delay_events_registry` (61)
- `raw_gtfs_static_files_registry` (8)
- `raw_gtfsrt_alert_snapshots_registry` (1)
- `bronze_bus_events` (776435)
- `bronze_subway_events` (250558)
- `bronze_gtfs_agency` (1)
- `bronze_gtfs_calendar` (8)
- `bronze_gtfs_calendar_dates` (7)
- `bronze_gtfs_routes` (229)
- `bronze_gtfs_shapes` (1025672)
- `bronze_gtfs_stop_times` (4249149)
- `bronze_gtfs_stops` (9417)
- `bronze_gtfs_trips` (133665)
- `bronze_gtfsrt_alert_entities` (0)

### Step 2 tables (Silver + Facts + Dims + Bridge + Review)
- `silver_bus_events` (776435)
- `silver_subway_events` (250558)
- `silver_gtfsrt_alert_entities` (0)
- `fact_delay_events_norm` (1026993)
- `fact_gtfsrt_alerts_norm` (0)
- `dim_route_gtfs` (229)
- `dim_stop_gtfs` (9417)
- `dim_service_gtfs` (8)
- `dim_route_alias` (1306)
- `dim_station_alias` (136273)
- `dim_incident_code` (280)
- `bridge_route_direction_stop` (17824)
- `route_alias_review` (1056)
- `station_alias_review` (135276)
- `incident_code_review` (280)

### Step 3 tables (Gold)
- `gold_delay_events_core` (1026993)
- `gold_linkage_quality` (3)
- `gold_route_time_metrics` (35882)
- `gold_station_time_metrics` (224282)
- `gold_time_reliability` (337)
- `gold_top_offender_ranking` (100618)
- `gold_alert_validation` (0)
- `gold_spatial_hotspot` (1077)

### Step 4 tables
- No new DuckDB tables were created in Step 4 (dashboard/docs/deployment step).

## 3) Parquet Outputs Created

### Step 1
- Raw registry Parquet files:
  - `raw/bus/raw_bus_delay_events_registry.parquet`
  - `raw/subway/raw_subway_delay_events_registry.parquet`
  - `raw/gtfs/raw_gtfs_static_files_registry.parquet`
  - `raw/gtfsrt/raw_gtfsrt_alert_snapshots_registry.parquet`
- Bronze Parquet files:
  - `bronze/bronze_bus_events.parquet`
  - `bronze/bronze_subway_events.parquet`
  - `bronze/bronze_gtfs_*.parquet`
  - `bronze/bronze_gtfsrt_alert_entities.parquet`

### Step 2
- `silver/silver_bus_events.parquet`
- `silver/silver_subway_events.parquet`
- `silver/silver_gtfsrt_alert_entities.parquet`
- `silver/fact_delay_events_norm.parquet`
- `silver/fact_gtfsrt_alerts_norm.parquet`
- `dimensions/dim_route_gtfs.parquet`
- `dimensions/dim_stop_gtfs.parquet`
- `dimensions/dim_service_gtfs.parquet`
- `dimensions/dim_route_alias.parquet`
- `dimensions/dim_station_alias.parquet`
- `dimensions/dim_incident_code.parquet`
- `bridge/bridge_route_direction_stop.parquet`
- `reviews/route_alias_review.parquet`
- `reviews/station_alias_review.parquet`
- `reviews/incident_code_review.parquet`

### Step 3
- `gold/gold_delay_events_core.parquet`
- `gold/gold_linkage_quality.parquet`
- `gold/gold_route_time_metrics.parquet`
- `gold/gold_station_time_metrics.parquet`
- `gold/gold_time_reliability.parquet`
- `gold/gold_top_offender_ranking.parquet`
- `gold/gold_alert_validation.parquet`
- `gold/gold_spatial_hotspot.parquet`

### Step 4
- No new Parquet outputs were created in Step 4.

## 4) What Remains Incomplete

- Spatial hotspot mapping is now runnable and materialized in `gold_spatial_hotspot` with confidence gating (`confidence_gate_passed`, `confidence_gate_reason`).
- GTFS-RT alert validation is now runnable and produces snapshot-health validation rows even when parsed alert entities are zero; full alert-to-delay validation depth still depends on sustained live Toronto TTC GTFS-RT snapshots.
- Subway station linkage quality is still comparatively weak and relies on review-table remediation.
- Local runtime dependencies may still need installation in the active environment (`pip install -r requirements.txt`) before launching Streamlit.

## 5) Ready for Next Step?

Yes. The project is structurally ready for the next step.

Readiness confirmation:
- Steps 1-4 required code and docs are present locally.
- Core Raw/Bronze/Silver/Facts/Dimensions/Bridge/Review/Gold tables exist in DuckDB.
- Required Parquet exports exist for data layers.
- Streamlit app and ordered dashboard pages are implemented.
- Deployment/runtime configs and run guides are present (`docs/runbook.md`, `src/RUN_PROJECT.md`).

Primary next-step focus should be data quality hardening (subway linkage and live alert volume) rather than missing architecture deliverables.


