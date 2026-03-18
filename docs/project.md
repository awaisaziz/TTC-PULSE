# TTC Pulse Project Map (Toronto Transit Reliability Observatory)

Generated: 2026-03-17 (America/New_York)

This document explains the project code files, what each file does, where datasets are read from, which files clean/normalize/process data, and how the Streamlit dashboard is organized.

## Scope and Data Sources

Geographic/domain scope: Toronto Transit Commission (TTC), Toronto, Ontario, Canada.

Primary source directories:
- `data/bus/` -> historical TTC bus delay CSV files
- `data/subway/` -> historical TTC subway delay CSV files
- `data/gtfs/` -> static GTFS reference CSV files
- `alerts/raw_snapshots/` -> GTFS-RT service alert snapshots (`.json` / `.pb`)

Core storage targets:
- DuckDB: `data/ttc_pulse.duckdb`
- Layered Parquet outputs: `raw/`, `bronze/`, `silver/`, `dimensions/`, `bridge/`, `reviews/`, `gold/`

## Pipeline Role by Step

- Step 1: raw registries + bronze row-preserving ingestion
- Step 2: silver canonical model + facts + dimensions + bridge + review queues
- Step 3: gold marts + scoring + GTFS-RT side-car DAG
- Step 4: Streamlit dashboard + deployment package + final docs

## Code File Catalog

Note: `__init__.py` files are package markers and contain no processing logic.

### A) Setup, Ingestion, and Bronze

| File | Purpose | Reads | Writes / Registers |
|---|---|---|---|
| `src/ttc_pulse/utils/project_setup.py` | Shared utilities: path constants, project scaffolding, DuckDB connection, logging, registry helpers | N/A (utility module) | `logs/ingestion_log.csv`, DuckDB connection helpers |
| `src/ttc_pulse/ingestion/ingest_bus.py` | Build immutable raw registry for TTC bus historical files | `data/bus/*.csv` | `raw/bus/raw_bus_delay_events_registry.csv`, `raw/bus/raw_bus_delay_events_registry.parquet`, table `raw_bus_delay_events_registry` |
| `src/ttc_pulse/ingestion/ingest_subway.py` | Build immutable raw registry for TTC subway historical files | `data/subway/*.csv` | `raw/subway/raw_subway_delay_events_registry.csv`, `raw/subway/raw_subway_delay_events_registry.parquet`, table `raw_subway_delay_events_registry` |
| `src/ttc_pulse/ingestion/ingest_gtfs.py` | Build immutable raw registry for static GTFS files | `data/gtfs/*.csv` | `raw/gtfs/raw_gtfs_static_files_registry.csv`, `raw/gtfs/raw_gtfs_static_files_registry.parquet`, table `raw_gtfs_static_files_registry` |
| `src/ttc_pulse/ingestion/register_gtfsrt_snapshots.py` | Build immutable raw registry for GTFS-RT alert snapshots | `alerts/raw_snapshots/*` | `raw/gtfsrt/raw_gtfsrt_alert_snapshots_registry.csv`, `raw/gtfsrt/raw_gtfsrt_alert_snapshots_registry.parquet`, table `raw_gtfsrt_alert_snapshots_registry` |
| `src/ttc_pulse/bronze/build_bronze_tables.py` | Build Bronze row-preserving tables with lineage for bus/subway/gtfs and GTFS-RT shell | Raw registries + source CSVs | `bronze/*.parquet`, tables `bronze_*`, docs `docs/source_inventory.md`, `docs/step1_summary.md` |

### B) Silver, Facts, Dimensions, Bridge, and QA Review

| File | Purpose | Reads | Writes / Registers |
|---|---|---|---|
| `src/ttc_pulse/normalization/normalize_bus.py` | Canonical bus normalization (route-first) | `bronze_bus_events` | `silver/silver_bus_events.parquet`, table `silver_bus_events` |
| `src/ttc_pulse/normalization/normalize_subway.py` | Canonical subway normalization (station-first) | `bronze_subway_events` | `silver/silver_subway_events.parquet`, table `silver_subway_events` |
| `src/ttc_pulse/normalization/normalize_gtfsrt_entities.py` | Canonical GTFS-RT entity normalization | `bronze_gtfsrt_alert_entities` | `silver/silver_gtfsrt_alert_entities.parquet`, table `silver_gtfsrt_alert_entities` |
| `src/ttc_pulse/facts/build_fact_delay_events_norm.py` | Unified canonical delay fact (bus+subway), joins aliases and incident dims | `silver_bus_events`, `silver_subway_events`, alias dims, incident dim | `silver/fact_delay_events_norm.parquet`, table `fact_delay_events_norm` |
| `src/ttc_pulse/facts/build_fact_gtfsrt_alerts_norm.py` | Canonical GTFS-RT alert fact with GTFS linkages | `silver_gtfsrt_alert_entities`, GTFS dims/tables | `silver/fact_gtfsrt_alerts_norm.parquet`, table `fact_gtfsrt_alerts_norm` |
| `src/ttc_pulse/gtfs/build_dimensions.py` | Build GTFS reference dimensions (route/stop/service) | `bronze_gtfs_routes`, `bronze_gtfs_stops`, `bronze_gtfs_calendar`, `bronze_gtfs_calendar_dates` | `dimensions/*.parquet`, tables `dim_route_gtfs`, `dim_stop_gtfs`, `dim_service_gtfs` |
| `src/ttc_pulse/gtfs/build_bridge.py` | Build route-direction-stop bridge from GTFS | `bronze_gtfs_trips`, `bronze_gtfs_stop_times`, `bronze_gtfs_stops` | `bridge/bridge_route_direction_stop.parquet`, table `bridge_route_direction_stop` |
| `src/ttc_pulse/aliasing/build_route_alias.py` | Build route alias mappings to GTFS route IDs | `silver_*`, `dim_route_gtfs` | `dimensions/dim_route_alias.parquet`, table `dim_route_alias` |
| `src/ttc_pulse/aliasing/build_station_alias.py` | Build station/location alias mappings to GTFS stop IDs | `silver_*`, `dim_stop_gtfs` | `dimensions/dim_station_alias.parquet`, table `dim_station_alias` |
| `src/ttc_pulse/aliasing/build_incident_code_dim.py` | Canonical incident code dimension from bus/subway events | `silver_bus_events`, `silver_subway_events` | `dimensions/dim_incident_code.parquet`, table `dim_incident_code` |
| `src/ttc_pulse/aliasing/build_review_tables.py` | Build QA review queues for unresolved/low-confidence mappings | alias dims + incident dim | `reviews/*.parquet`, tables `route_alias_review`, `station_alias_review`, `incident_code_review` |

### C) Gold Marts, Scoring, Alerts Side-car, and Airflow

| File | Purpose | Reads | Writes / Registers |
|---|---|---|---|
| `src/ttc_pulse/marts/scoring.py` | Reliability scoring utilities and weighted composite formula | N/A | Used by Gold metric builders |
| `src/ttc_pulse/marts/build_gold_delay_core.py` | Build event-level Gold core + spatial hotspot table (confidence-gated) | `fact_delay_events_norm`, stop dims | `gold/gold_delay_events_core.parquet`, `gold/gold_spatial_hotspot.parquet`, tables `gold_delay_events_core`, `gold_spatial_hotspot` |
| `src/ttc_pulse/marts/build_gold_linkage_quality.py` | Build linkage QA summary mart | `fact_delay_events_norm`, `fact_gtfsrt_alerts_norm` | `gold/gold_linkage_quality.parquet`, table `gold_linkage_quality` |
| `src/ttc_pulse/marts/build_gold_route_metrics.py` | Build route x weekday x hour reliability metrics | `gold_delay_events_core` | `gold/gold_route_time_metrics.parquet`, table `gold_route_time_metrics` |
| `src/ttc_pulse/marts/build_gold_station_metrics.py` | Build station x weekday x hour reliability metrics | `gold_delay_events_core` | `gold/gold_station_time_metrics.parquet`, table `gold_station_time_metrics` |
| `src/ttc_pulse/marts/build_gold_time_metrics.py` | Build mode-level weekday x hour reliability overview | `gold_delay_events_core` | `gold/gold_time_reliability.parquet`, table `gold_time_reliability` |
| `src/ttc_pulse/marts/build_gold_rankings.py` | Build top offender rankings from route/station metrics | `gold_route_time_metrics`, `gold_station_time_metrics` | `gold/gold_top_offender_ranking.parquet`, table `gold_top_offender_ranking` |
| `src/ttc_pulse/marts/build_gold_alert_validation.py` | Build alert validation mart (entity validation + snapshot health coverage) | `fact_gtfsrt_alerts_norm`, `fact_delay_events_norm`, `raw_gtfsrt_alert_snapshots_registry`, `silver_gtfsrt_alert_entities` | `gold/gold_alert_validation.parquet`, table `gold_alert_validation` |
| `src/ttc_pulse/alerts/poll_service_alerts.py` | Poll GTFS-RT service alerts and persist raw snapshots (supports stub mode) | GTFS-RT URL or none | `alerts/raw_snapshots/*.json|*.pb` |
| `src/ttc_pulse/alerts/parse_service_alerts.py` | Parse JSON/PB snapshots into Bronze GTFS-RT alert entities | `alerts/raw_snapshots/*` | `alerts/parsed/gtfsrt_alert_entities_latest.jsonl`, `bronze/bronze_gtfsrt_alert_entities.parquet`, table `bronze_gtfsrt_alert_entities` |
| `airflow/dags/poll_gtfsrt_alerts.py` | 30-minute side-car DAG for live GTFS-RT alert chain | Airflow scheduler + scripts | Orchestrates poll -> raw registry -> bronze parse -> normalize -> fact -> gold validation |

### D) Streamlit App and Pages

| File | Purpose | Reads |
|---|---|---|
| `app/streamlit_app.py` | Dashboard entry page with KPI snapshot and panel navigation guidance | DuckDB via dashboard loaders |
| `src/ttc_pulse/dashboard/loaders.py` | DuckDB data-access layer for Streamlit pages | Gold/review/raw snapshot tables |
| `src/ttc_pulse/dashboard/charts.py` | Reusable Altair chart builders | DataFrames from loaders |
| `src/ttc_pulse/dashboard/formatting.py` | Shared numeric formatting helpers | N/A |

## Streamlit Pages (Count and Purpose)

Total pages: **9** (locked order)

1. `app/pages/01_Linkage_QA_Panel.py`
   - Linkage rates and review backlog visibility.
2. `app/pages/02_Reliability_Overview.py`
   - High-level reliability composite trends and distribution.
3. `app/pages/03_Bus_Route_Ranking.py`
   - Bus route offender rankings.
4. `app/pages/04_Subway_Station_Ranking.py`
   - Subway station offender rankings.
5. `app/pages/05_Weekday_x_Hour_Heatmap.py`
   - Weekday x hour reliability heatmap.
6. `app/pages/06_Monthly_Trends.py`
   - Monthly trend lines for volume and delay metrics.
7. `app/pages/07_Cause_Category_Mix.py`
   - Incident/cause mix by mode.
8. `app/pages/08_Live_Alert_Validation.py`
   - Live alert validation, including pipeline status and snapshot-health rows.
9. `app/pages/09_Spatial_Hotspot_Placeholder.py`
   - Spatial hotspot map page (now mapped and confidence-gated).

## Which Files Clean/Normalize/Process Data?

Cleaning/normalization/transformation roles:
- Cleaning and canonicalization: `normalize_bus.py`, `normalize_subway.py`, `normalize_gtfsrt_entities.py`
- Alias and QA enrichment: `build_route_alias.py`, `build_station_alias.py`, `build_incident_code_dim.py`, `build_review_tables.py`
- Fact processing: `build_fact_delay_events_norm.py`, `build_fact_gtfsrt_alerts_norm.py`
- Aggregation/mart processing: all `src/ttc_pulse/marts/build_gold_*.py`
- GTFS-RT parsing/processing: `parse_service_alerts.py`

## Existing Docs That Already Covered Parts of This

The information requested was partially documented already in:
- `docs/architecture.md`
- `docs/architecture/overview.md`
- `docs/architecture/data_flow.md`
- `docs/data_dictionary.md`
- `docs/runbook.md`
- `docs/dashboard/panel_descriptions.md`
- `docs/pipelines/agent_pipeline.md`
- `docs/step_review.md`

This `docs/project.md` is the consolidated, code-file-level view across all steps.
