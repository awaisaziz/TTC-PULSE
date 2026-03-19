# Frontend

Next.js dashboard for TTC delay analytics.

## Run locally

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:3000`  
Dashboard: `http://localhost:3000/dashboard`

## Backend API target

Default API base URL is `http://localhost:8000`.

If needed, create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```
