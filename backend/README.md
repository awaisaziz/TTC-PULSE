# Backend

FastAPI service for TTC delay analytics.

## Run locally (Windows)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python dev_server.py
```

Backend URL: `http://localhost:8000`

Health check:

```bash
curl "http://localhost:8000/health"
```

## Notes

- `dev_server.py` loads `.env` from repo root automatically.
- Default DuckDB path is `data/ttc.duckdb` (resolved from repo root).
