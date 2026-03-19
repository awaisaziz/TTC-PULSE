# Scripts

## Purpose
The `scripts/` folder provides helpers to run pipeline, backend, frontend, and DuckDB setup/verification tasks.

## What is in this folder
- `run_pipeline.py`: runs ingestion and initializes DuckDB SQL objects.
- `start_backend.sh` / `start_backend.ps1`: starts FastAPI backend with dependency bootstrap.
- `start_frontend.sh` / `start_frontend.ps1`: starts Next.js frontend with dependency bootstrap.
- `setup_duckdb.sh`: initializes DuckDB objects from SQL files.
- `verify_duckdb.sh`: runs DuckDB sanity/performance checks.

## Core scripts
1. `run_pipeline.py`: prepares data and DB in one step.
2. `start_backend.ps1` (`start_backend.sh` on Linux/macOS): starts backend.
3. `start_frontend.ps1` (`start_frontend.sh` on Linux/macOS): starts frontend.

## Run individual parts

Windows (PowerShell):

```powershell
py -3 scripts/run_pipeline.py
powershell -ExecutionPolicy Bypass -File .\scripts\start_backend.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\start_frontend.ps1
```

macOS/Linux:

```bash
python3 scripts/run_pipeline.py
./scripts/start_backend.sh
./scripts/start_frontend.sh
./scripts/setup_duckdb.sh
./scripts/verify_duckdb.sh
```
