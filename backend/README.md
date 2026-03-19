# Backend

## Purpose
The `backend/` folder contains the FastAPI service that exposes TTC delay analytics APIs backed by DuckDB.

## What is in this folder
- `app/main.py` — FastAPI app entrypoint, CORS config, `/health` endpoint, and global error handler.
- `app/api/analytics.py` — analytics endpoints (`/routes`, `/delay`, `/stats`, `/heatmap`, `/top-routes`, `/delay-trend`).
- `app/db/duckdb_client.py` — DuckDB connection management and TTL query caching.
- `app/models/` — reserved package for API/data models.
- `requirements.txt` — Python dependencies for the backend service.
- `app/api/test_queries.http` — local HTTP request collection for quick endpoint testing.

## Core backend files and why they matter
1. `app/main.py` — boots the API server and mounts all routes.
2. `app/api/analytics.py` — contains the core business queries used by the frontend dashboard.
3. `app/db/duckdb_client.py` — central DB access layer used by all analytics endpoints.

## Run only the backend
From repo root:

```bash
./scripts/start_backend.sh
```

Manual alternative:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
DUCKDB_PATH=../data/ttc.duckdb uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> The backend expects `data/ttc.duckdb` to exist. Create it first with `python3 scripts/run_pipeline.py` or `./scripts/setup_duckdb.sh`.
