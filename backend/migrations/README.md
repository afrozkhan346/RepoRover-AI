# Backend Migrations

This directory stores database migrations for the Python backend.

Current status:
- `0001_initial_schema.sql` captures the current domain schema as a starting point.
- Alembic environment is now configured in `backend/alembic.ini` and `backend/migrations/env.py`.
- Alembic baseline revision: `backend/migrations/versions/0001_sqlalchemy_baseline.py`.
- SQLite is the first migration target.
- PostgreSQL compatibility will be added after the backend services stabilize.

## Alembic Usage

From `backend/`:

```bash
alembic current
alembic upgrade head
alembic downgrade -1
```

To create a new revision:

```bash
alembic revision -m "describe change"
```

For autogenerate after model changes:

```bash
alembic revision --autogenerate -m "autogen: model updates"
```
