# Part 20 - Production Hardening

Date: 2026-04-06
Status: Completed

## Goal

Finalize the repo for split deployment, environment hygiene, CI validation, and production-oriented documentation.

## Implemented Changes

### 1) Deployment split documented

Updated the top-level [README.md](../README.md) to describe the current production model:

- React + Vite frontend on Vercel
- FastAPI backend on Render
- backend API accessed directly through `VITE_BACKEND_URL`

### 2) Environment templates refreshed

Replaced the stale environment examples with current-stack templates:

- [`.env.example`](../.env.example)
- [backend/.env.example](../backend/.env.example)

The frontend template now points at the FastAPI backend, and the backend template reflects the current SQLite-first / PostgreSQL-ready settings.

### 3) CI checks aligned to the repo

Replaced the legacy frontend-only workflow with [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

The new workflow validates:

- frontend production build
- frontend linting
- backend Python syntax compilation
- backend config smoke import

### 4) Validation

Ran local validation after the hardening update:

- `npm run build`
- `python -m compileall backend/app`

Observed outcome:

- frontend production build completed successfully
- backend package compiled successfully

## Outcome

Part 20 is complete:

- the repo documents the Vercel + Render deployment split
- env templates match the active frontend/backend stack
- CI checks now match the current repository shape
- final validation passed