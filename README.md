# TTC Delay Analytics

Local-only analytics app with:
- Pipeline (`scripts/run_pipeline.py`)
- FastAPI backend (`backend/`)
- Next.js frontend (`frontend/`)

## Run locally (no deployment)

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

### If you saw the multiprocessing bootstrap error on Windows

If you previously got this error while starting the backend:

`An attempt has been made to start a new process before the current process has finished its bootstrapping phase`

the backend entrypoint has now been fixed with a proper `if __name__ == "__main__":` guard and `freeze_support()`.
Use the same command below to start the server:

```bash
python dev_server.py
```

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

## 3) Run backend + frontend together (local development)

Use two terminals:

- Terminal 1 (backend): run the backend steps above.
- Terminal 2 (frontend): run the frontend steps above.

Then open:
- App home: `http://localhost:3000`
- Dashboard: `http://localhost:3000/dashboard`
- API docs: `http://localhost:8000/docs`

## 4) Data pipeline (if you need to rebuild DB)

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
