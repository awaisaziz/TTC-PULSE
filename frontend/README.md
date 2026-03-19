# Frontend

## Purpose
The `frontend/` folder contains the Next.js dashboard UI for visualizing TTC delay analytics from the backend API.

## What is in this folder
- `app/page.tsx` — landing page.
- `app/dashboard/page.tsx` — main analytics dashboard page.
- `app/route/[id]/page.tsx` — route-level details page.
- `app/layout.tsx` — app shell and metadata.
- `app/globals.css` — global styles.
- `components/` — reusable UI components/charts (`Filters`, `DelayTrendChart`, `RouteRankingChart`, `DelayHeatmap`).
- `lib/api.ts` — typed API calls to FastAPI endpoints.
- `lib/types.ts` — shared frontend data types.
- `package.json` — Node dependencies and scripts.
- `next.config.ts`, `tsconfig.json`, `next-env.d.ts` — framework/tooling config.

## Core frontend files and why they matter
1. `app/dashboard/page.tsx` — orchestrates filters + chart data loading.
2. `lib/api.ts` — single integration point with backend REST API.
3. `components/DelayTrendChart.tsx`, `components/RouteRankingChart.tsx`, `components/DelayHeatmap.tsx` — core visual analytics components.

## Run only the frontend
From repo root:

```bash
./scripts/start_frontend.sh
```

Manual alternative:

```bash
cd frontend
npm install
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev -- --hostname 0.0.0.0 --port 3000
```

Open `http://localhost:3000` after startup.
