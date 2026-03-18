# Agent Pipeline

Generated: 2026-03-17 (America/New_York)

## Stepwise Build Ownership

- **Ingestion Agent:** Raw registry build and source inventory.
- **Normalization Agent:** Silver/fact canonicalization and linkage metadata.
- **QA/Alias Agent:** alias dimensions + review queues.
- **Analytics Agent:** Gold marts + scoring logic.
- **Live Alerts Agent:** GTFS-RT polling/parsing + Airflow side-car DAG.
- **Dashboard Agent:** Streamlit app/pages + chart/load utilities.
- **Documentation Agent:** architecture, UX, runbook, changelog, final summary.

## Operational Loop

1. Ingest/update raw sources.
2. Rebuild Bronze/Silver/Facts/Gold.
3. Refresh dashboard reads from DuckDB.
4. Airflow side-car continuously updates alert-driven marts every 30 minutes.
