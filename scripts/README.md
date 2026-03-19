# Scripts

- `run_pipeline.py` — Runs ingestion from `data/raw/` and initializes DuckDB analytical objects.
- `start_backend.sh` — Boots backend venv, installs requirements, and starts FastAPI.
- `start_frontend.sh` — Installs Node dependencies and starts Next.js dev server.
- `setup_duckdb.sh` — DuckDB CLI setup path (manual SQL execution).
- `verify_duckdb.sh` — DuckDB validation checks.

## Usage

```bash
python3 scripts/run_pipeline.py
./scripts/start_backend.sh
./scripts/start_frontend.sh
```
