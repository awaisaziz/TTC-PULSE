# Ingest

Robust ingestion pipeline for TTC raw CSV data.

## Run

```bash
python -m pipeline.ingest.run_ingestion
```

## What it does

- Recursively scans `data/raw/**/*.csv`
- Classifies files as `bus`, `subway`, `gtfs` (or skip unknown)
- Normalizes each file into a common schema
- Handles inconsistent column names and missing values
- Fills unknown locations with `unknown`
- Loads subway incident code lookup and maps `incident_code -> incident_desc`
- Writes per-file cleaned CSVs to `data/processed/`
- Writes unified cleaned CSV to `data/processed/all_data_cleaned.csv`
- Writes partitioned parquet dataset to `data/parquet/year=<year>/vehicle_type=<type>/...`
- Logs progress in `pipeline/ingest/ingestion.log`
