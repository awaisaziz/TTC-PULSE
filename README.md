# TTC Delay Analytics (Local Scaffold)

Production-oriented project scaffold for a local TTC delay analytics system.

## Tech Stack

- **Backend:** FastAPI (Python)
- **Data layer:** DuckDB + Parquet
- **Data processing:** pandas + pyarrow
- **Frontend:** Next.js (React + TypeScript)

## Project Structure

```text
project-root/
├── data/
│   ├── raw/
│   ├── processed/
│   └── parquet/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── db/
│   │   └── models/
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   └── package.json
├── pipeline/
│   ├── ingest/
│   ├── transform/
│   └── utils/
├── scripts/
├── .gitignore
└── README.md
```

## Local Setup

### 1) Prerequisites

- Python 3.10+
- Node.js 20+
- npm 10+

### 2) Python virtual environment + backend dependencies

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3) Run backend (FastAPI + Uvicorn)

From the `backend/` directory:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check endpoint:

- `GET http://localhost:8000/health`

### 4) Frontend dependencies + run Next.js

```bash
cd frontend
npm install
npm run dev
```

Open:

- `http://localhost:3000`

## Notes

- This is a **scaffold only** (no business logic implemented yet).
- `data/raw/` is intended for source CSV drops.
- `data/processed/` and `data/parquet/` are local artifacts and currently ignored by git.
- The folder layout is designed for messy multi-schema ingestion, large small-file workloads, and fast analytical querying once implementation is added.
