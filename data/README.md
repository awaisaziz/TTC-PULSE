# Data

## Purpose
The `data/` folder stores project datasets and generated artifacts used by the ingestion pipeline, DuckDB, backend APIs, and frontend dashboard.

## What is in this folder
- `raw/` — source TTC files used as ingestion input.
  - `raw/bus/` — raw bus delay CSV files.
  - `raw/subway/` — raw subway delay CSV files.
  - `raw/gtfs/` — GTFS reference CSVs (routes/stops/etc.).
- `processed/` *(created by pipeline)* — cleaned CSV outputs.
- `parquet/` *(created by pipeline/SQL setup)* — partitioned analytics parquet dataset.
- `ttc.duckdb` *(created by pipeline/SQL setup)* — DuckDB database used by backend queries.

## Core data artifacts and why they matter
1. `raw/` — source of truth for ingestion.
2. `parquet/delays/...` — analytics-ready partitioned data for fast queries.
3. `ttc.duckdb` — live database file consumed by the backend.

## Build or refresh only the data layer
From repo root:

```bash
python3 scripts/run_pipeline.py
```

Alternative (DuckDB CLI route):

```bash
./scripts/setup_duckdb.sh
```

Quick validation:

```bash
./scripts/verify_duckdb.sh
```
