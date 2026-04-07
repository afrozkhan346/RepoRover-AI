# Part 8 - SQLite-First SQLAlchemy + Alembic Baseline

Date: 2026-04-06
Status: Completed

## Goal

Implement a SQLite-first migration-ready database layer with SQLAlchemy models and an Alembic baseline, while preparing for PostgreSQL migration in later parts.

## Implemented Changes

### 1) Alembic Scaffold Added

Created Alembic configuration and environment under backend:

- `backend/alembic.ini`
- `backend/migrations/env.py`
- `backend/migrations/script.py.mako`
- `backend/migrations/versions/`

Behavior:

- `env.py` uses `app.core.config.settings.database_url` as source of truth.
- Alembic metadata target is `Base.metadata` from app models.
- Online/offline migrations are enabled.
- Type/default comparison is enabled (`compare_type`, `compare_server_default`).

### 2) Baseline Revision Created (SQLite-First)

Created baseline revision:

- `backend/migrations/versions/0001_sqlalchemy_baseline.py`

This revision creates the canonical SQLAlchemy model tables currently used by backend runtime:

- `user`
- `session`
- `account`
- `verification`
- `user_progress`
- `learning_paths`
- `lessons`
- `lesson_progress`
- `achievements`
- `user_achievements`
- `quizzes`
- `quiz_attempts`
- `repositories`

It also includes a full downgrade path in reverse dependency order.

### 3) DB Session Pattern Standardization

Updated `backend/app/db/session.py`:

- Added reusable dependency helper `get_db_session()` returning a managed SQLAlchemy session generator.

This allows route modules to stop duplicating local session boilerplate and converge on one pattern.

### 4) Packaging Dependency Alignment

Updated `backend/pyproject.toml` dependencies to include DB/migration stack required for SQLAlchemy + Alembic workflows:

- `SQLAlchemy`
- `alembic`
- `psycopg[binary]`
- `aiosqlite`
- `python-multipart`
- `pydantic` (explicit)

This aligns project metadata with runtime requirements already declared in `backend/requirements.txt`.

### 5) Migration Workflow Documentation

Updated migration instructions in:

- `backend/migrations/README.md`

Now includes Alembic commands for current/upgrade/downgrade/revision/autogenerate.

## Notes

- Existing SQL migration file `backend/migrations/0001_initial_schema.sql` is retained as a historical/manual reference.
- Alembic baseline is now the canonical migration path going forward.
- SQLite remains the primary migration target for this part; PostgreSQL-specific migration behavior is reserved for Part 9.

## Outcome

Part 8 deliverables are met:

- Canonical SQLAlchemy model set is migration-ready.
- Alembic baseline revision and runtime migration scaffold are present.
- DB session usage now has a standardized reusable helper for upcoming route unification.
