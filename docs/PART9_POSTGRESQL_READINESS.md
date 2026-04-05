# Part 9 - PostgreSQL Readiness Layer

Date: 2026-04-06
Status: Completed

## Goal

Implement PostgreSQL-ready configuration, URL policy, and migration-safe runtime behavior while keeping SQLite-first flow intact.

## Implemented Changes

### 1) Database Backend Policy and URL Resolution

Updated backend settings in `backend/app/core/config.py`:

- Added `DATABASE_BACKEND` policy (`sqlite`, `postgresql`, `auto`)
- Added PostgreSQL readiness options:
  - `POSTGRES_SSLMODE`
  - `DB_POOL_SIZE`
  - `DB_MAX_OVERFLOW`
- Added resolved properties:
  - `resolved_database_backend`
  - `resolved_database_url`

Resolution behavior:

- If backend is `sqlite`, use `DATABASE_URL` (default SQLite file).
- If backend is `postgresql`:
  - Use explicit PostgreSQL `DATABASE_URL` when provided, otherwise
  - Build DSN from `POSTGRES_*` fields with `sslmode`.
- If backend is `auto`, infer from `DATABASE_URL` prefix.

Validation behavior:

- If `DATABASE_BACKEND=postgresql` and `DATABASE_URL` is not PostgreSQL, required `POSTGRES_*` fields must exist.

### 2) Engine and Pooling Readiness

Updated `backend/app/db/connection.py`:

- Engine now uses `settings.resolved_database_url` and `settings.resolved_database_backend`.
- PostgreSQL engine kwargs now include:
  - `pool_pre_ping=True`
  - `pool_recycle=1800`
  - `pool_size` from `DB_POOL_SIZE`
  - `max_overflow` from `DB_MAX_OVERFLOW`

SQLite behavior remains unchanged (`check_same_thread=False`).

### 3) Migration Safety Alignment

Updated Alembic environment in `backend/migrations/env.py`:

- Alembic now resolves URL from `settings.resolved_database_url`, ensuring migration target matches runtime DB policy for both SQLite and PostgreSQL.

This keeps migration execution consistent across local and deployment environments.

### 4) Environment and Operational Guidance

Updated environment template in `backend/.env.example` with PostgreSQL-ready keys:

- `DATABASE_BACKEND`
- `POSTGRES_SSLMODE`
- `DB_POOL_SIZE`
- `DB_MAX_OVERFLOW`

Updated `backend/README.md` with:

- SQLite mode example
- PostgreSQL mode examples (explicit DSN or composed fields)
- Alembic command workflow

## Migration-Safety Notes

- SQLite baseline migration remains canonical first step (`0001_sqlalchemy_baseline`).
- The same Alembic commands can now target either backend depending on resolved DB URL policy.
- No schema mutation was introduced in Part 9; this part is configuration and operational hardening only.

## Outcome

Part 9 deliverables are met:

- PostgreSQL connection settings and URL policy are finalized.
- Runtime and Alembic now share the same resolved DB target behavior.
- Environment and operational guidance for local/prod PostgreSQL rollout is documented.
