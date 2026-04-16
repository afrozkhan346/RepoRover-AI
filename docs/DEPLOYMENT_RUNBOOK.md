# Deployment Runbook

## 1. Pre-deploy checks

- Frontend:
  - `npm ci`
  - `npm run lint`
  - `npm run build`
- Backend:
  - `cd backend`
  - `pip install -r requirements.txt`
  - `pytest -q tests`

## 2. Environment and secrets

- Do not commit `.env` files.
- Use only:
  - `.env.example`
  - `backend/.env.example`
- Rotate provider keys before go-live if any were exposed:
  - Groq
  - Upstash Redis
  - Database credentials

## 3. Database migrations

- Run migrations before serving traffic:
  - `cd backend`
  - `alembic upgrade head`
- App startup warns if required tables are missing, but does not auto-migrate PostgreSQL.

## 4. Deploy configuration

- Render backend:
  - `rootDir: backend`
  - `buildCommand: pip install -r requirements.txt`
  - `startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Vercel frontend:
  - Set `VITE_BACKEND_URL` to backend API base ending in `/api`.

## 5. Post-deploy smoke tests

- Backend:
  - `GET /`
  - `GET /api/health/llm`
  - `GET /api/project/analyze/<project_name>` (with a known project)
- Frontend:
  - Load app shell
  - Login/Register
  - Project upload/clone
  - AI summary flow

## 6. Rollback plan

- Keep previous Render and Vercel deploy artifacts available.
- Roll back immediately if:
  - health endpoints fail
  - migration errors appear
  - login or analysis routes return 5xx at significant rate
- Rollback order:
  1. Frontend (Vercel) to previous stable deployment
  2. Backend (Render) to previous stable deployment
  3. If needed, DB rollback with Alembic only when schema downgrade is verified safe
