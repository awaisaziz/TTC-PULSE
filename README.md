# TTC Delay Analytics

Local-only analytics app with:
- Pipeline (`scripts/run_pipeline.py`)
- FastAPI backend (`backend/`)
- Next.js frontend (`frontend/`)

## What you asked for

Run locally without shell helper scripts:
- Frontend: `npm run dev`
- Backend: `python dev_server.py`

## Prerequisites (Windows)

- Python 3.12+
- Node.js 20+

## 1) Backend setup and run

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python dev_server.py
```

Backend will run at `http://localhost:8000`.

Health check:

```bash
curl "http://localhost:8000/health"
```

## 2) Frontend setup and run

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:3000`, dashboard at `http://localhost:3000/dashboard`.

## 3) Data pipeline (if you need to rebuild DB)

From repo root:

```bash
cd backend
.venv\Scripts\activate
cd ..
python scripts/run_pipeline.py
```

This creates/updates:
- `data/processed/`
- `data/parquet/`
- `data/ttc.duckdb`

## Local testing checklist

- Backend health returns `{"status":"ok"}`.
- `http://localhost:8000/routes` returns JSON data.
- Dashboard loads charts without API errors.

## Notes

- Backend automatically reads `.env` from repo root if present.
- If `.env` is missing, safe local defaults are used (`localhost:8000`, `localhost:3000`, `data/ttc.duckdb`).
