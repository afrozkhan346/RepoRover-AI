# PostgreSQL Migration Path

Date: 2026-04-03

This document describes how the backend will move from the initial SQLite target to PostgreSQL.

## Current Runtime

- SQLite is the default development database.
- Tables are created automatically on backend startup in development.
- The SQLAlchemy connection layer already accepts PostgreSQL URLs, but PostgreSQL should be migration-driven rather than startup-auto-created.

## Planned PostgreSQL Path

1. Populate PostgreSQL settings in the backend environment.
2. Point `DATABASE_URL` to a PostgreSQL DSN.
3. Keep the SQLAlchemy models unchanged where possible.
4. Generate and run PostgreSQL-compatible migrations from the shared schema.
5. Validate feature parity against SQLite before switching deployment defaults.

## Connection Strategy

- Use the shared connection layer in `app.db.connection`.
- Keep the engine/session factory creation centralized.
- Use `build_postgres_url()` for local development or deployment scripts when needed.

## Migration Rule

SQLite remains the development-first runtime. PostgreSQL should be introduced as a compatible deployment target, not as a forked data model.
