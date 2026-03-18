# Runbook

This runbook covers TTC Pulse for TTC transit reliability analysis in Toronto, Ontario.

Generated: 2026-03-17 (America/New_York)

## 1. Environment Setup

1. Install dependencies:
   - `pip install -r requirements.txt`
2. Ensure `data/ttc_pulse.duckdb` exists.

## 2. Rebuild Pipeline Artifacts (if needed)

Run Step modules in sequence:
- Step 1 ingestion/bronze scripts
- Step 2 silver/facts/dimensions/bridge/review scripts
- Step 3 gold mart scripts

## 3. Run Streamlit Dashboard

From project root:
- `streamlit run app/streamlit_app.py`

Optional config file is included at `.streamlit/config.toml`.

## 4. Run GTFS-RT Side-car Manually

1. Poll snapshot:
   - `python src/ttc_pulse/alerts/poll_service_alerts.py --url "<GTFSRT_ALERTS_URL>"`
2. Register snapshot metadata:
   - `python src/ttc_pulse/ingestion/register_gtfsrt_snapshots.py`
3. Parse alerts to Bronze:
   - `python src/ttc_pulse/alerts/parse_service_alerts.py`
4. Normalize/build facts/mart:
   - `python src/ttc_pulse/normalization/normalize_gtfsrt_entities.py`
   - `python src/ttc_pulse/facts/build_fact_gtfsrt_alerts_norm.py`
   - `python src/ttc_pulse/marts/build_gold_alert_validation.py`

## 5. Airflow DAG

- DAG file: `airflow/dags/poll_gtfsrt_alerts.py`
- Schedule: every 30 minutes
- Scope: GTFS-RT service alerts only

## 6. Troubleshooting

- If tables appear empty, check `logs/ingestion_log.csv` and confirm source snapshots exist.
- If dashboard import fails, run from repo root so `src/` path resolution works.
- If GTFS-RT URL is absent, poll script writes a stub snapshot to keep pipeline continuity.

