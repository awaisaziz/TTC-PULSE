# Scripts

## Purpose
The `scripts/` folder provides executable helpers to run isolated parts of the project (pipeline, backend, frontend, and DuckDB setup/verification).

## What is in this folder
- `run_pipeline.py` — runs ingestion and initializes DuckDB analytical objects from SQL.
- `start_backend.sh` — creates/uses backend virtualenv, installs requirements, starts FastAPI.
- `start_frontend.sh` — installs frontend deps, starts Next.js dev server.
- `setup_duckdb.sh` — runs DuckDB SQL initialization scripts.
- `verify_duckdb.sh` — runs post-setup validation and performance sanity checks.

## Core scripts and why they matter
1. `run_pipeline.py` — best single command to prepare data + DB.
2. `start_backend.sh` — fastest backend startup path.
3. `start_frontend.sh` — fastest frontend startup path.

## Run only one part of the project
From repo root:

```bash
# Pipeline/data only
python3 scripts/run_pipeline.py

# Backend only
./scripts/start_backend.sh

# Frontend only
./scripts/start_frontend.sh

# DuckDB setup only
./scripts/setup_duckdb.sh

# DuckDB verification only
./scripts/verify_duckdb.sh
```
