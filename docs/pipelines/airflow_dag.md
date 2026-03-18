# Airflow DAG

Generated: 2026-03-17 (America/New_York)

## DAG File

- `airflow/dags/poll_gtfsrt_alerts.py`

## Schedule

- Every 30 minutes (`*/30 * * * *`)

## Side-car Scope

Only GTFS-RT service alerts are handled in this DAG.

## Task Chain

1. `poll_service_alerts`
2. `register_raw_gtfsrt_snapshots`
3. `parse_gtfsrt_alerts_to_bronze`
4. `normalize_gtfsrt_entities`
5. `build_fact_gtfsrt_alerts_norm`
6. `build_gold_alert_validation`

## Runtime Config

- `TTC_PULSE_HOME`: repo root override.
- `TTC_PULSE_PYTHON`: python executable for script tasks.
- `GTFSRT_ALERTS_URL`: live feed URL (optional; if absent, poll task writes a stub snapshot).
