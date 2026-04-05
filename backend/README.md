# RepoRover Backend

FastAPI backend for the final React + FastAPI architecture.

## Run locally

```bash
uvicorn app.main:app --reload --app-dir backend
```

## Database Modes

The backend supports SQLite-first development and PostgreSQL readiness.

### SQLite (default)

In `.env`:

```bash
DATABASE_BACKEND=sqlite
DATABASE_URL=sqlite:///./repoorover.db
```

### PostgreSQL (ready)

Option A: explicit DSN

```bash
DATABASE_BACKEND=postgresql
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/repoorover?sslmode=prefer
```

Option B: component fields (auto-built DSN)

```bash
DATABASE_BACKEND=postgresql
DATABASE_URL=sqlite:///./repoorover.db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=repoorover
POSTGRES_USERNAME=repoorover
POSTGRES_PASSWORD=change-me
POSTGRES_SSLMODE=prefer
```

`DATABASE_URL` remains the single runtime URL source, and is resolved from the above policy.

## Alembic Migrations

From `backend/`:

```bash
alembic current
alembic upgrade head
alembic downgrade -1
```

Create a revision:

```bash
alembic revision -m "describe change"
```

Autogenerate after model updates:

```bash
alembic revision --autogenerate -m "autogen: model updates"
```

## GitHub Ingestion Workspace Policy

Repository ingestion now uses a shared workspace strategy with GitPython:

- Remote Git URLs:
	- first request: clone into shared workspace
	- subsequent requests: fetch + best-effort fast-forward pull (update in place)
- Local folder ingestion:
	- copied into managed workspace for consistent analysis lifecycle
- ZIP ingestion:
	- extracted into managed upload workspace

Workspace policy env knobs:

```bash
PROJECTS_WORKSPACE_PATH=./projects
PROJECTS_RETENTION_DAYS=14
PROJECTS_MAX_ENTRIES=200
PROJECTS_CLEANUP_ENABLED=true
```

Ingestion responses now include metadata describing operation mode and workspace policy applied.

## Idempotent CSV Seeding (SQLAlchemy)

A canonical SQLAlchemy seed loader is available at `app/db/seed.py`.
It is rerunnable and idempotent via conflict-safe upserts on natural keys:

- `learning_paths.title`
- `lessons(learning_path_id, title)`
- `achievements.title`
- `quizzes(lesson_id, question)`

Expected CSV files under `backend/data/seed/`:

- `learning_paths.csv`
- `lessons.csv`
- `achievements.csv`
- `quizzes.csv`

Run from `backend/`:

```bash
python -m app.db.seed
```

Dry-run validation (no writes):

```bash
python -m app.db.seed --dry-run
```

Optional flags:

- `--data-dir <path>`: custom CSV directory
- `--chunk-size <n>`: bulk upsert chunk size (default `1000`)
