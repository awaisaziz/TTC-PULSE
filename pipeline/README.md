# Pipeline

## Purpose
The `pipeline/` folder contains ingestion and transformation utilities that normalize raw TTC data into cleaned outputs and analytics-ready formats.

## What is in this folder
- `ingest/` — ingestion pipeline implementation.
  - `ingest_pipeline.py` — main multi-agent ingestion logic (scan, classify, transform, verify, quality summary).
  - `run_ingestion.py` — module entrypoint for ingestion.
  - `README.md` — detailed ingest notes.
- `transform/` — transformed-data validation helpers.
  - `verify_parquet.py` — checks parquet outputs.
  - `README.md` — transform notes.
- `utils/` — shared utilities namespace (currently placeholder).
- `__init__.py` files — package markers.

## Core pipeline files and why they matter
1. `ingest/ingest_pipeline.py` — central normalization and output-writing workflow.
2. `ingest/run_ingestion.py` — quick way to run ingestion only.
3. `transform/verify_parquet.py` — verification utility for generated parquet data.

## Run only the pipeline
From repo root:

```bash
python3 -m pipeline.ingest.run_ingestion
```

Or run ingestion + DuckDB initialization in one command:

```bash
python3 scripts/run_pipeline.py
```

Validate transformed parquet output:

```bash
python3 -m pipeline.transform.verify_parquet
```
