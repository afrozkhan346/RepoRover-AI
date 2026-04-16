# Reponium Backend

FastAPI backend for the final React + FastAPI architecture.

## Run locally

```bash
uvicorn app.main:app --reload --app-dir backend
```

## Database Modes

The backend is designed for PostgreSQL (Supabase) as the default and recommended database for all deployments. Drizzle ORM is used for migrations and queries.

### Local Development

By default, the backend will use PostgreSQL if you provide a valid `DATABASE_URL` (Supabase or self-hosted). If no PostgreSQL configuration is found, it will fall back to SQLite for local development only. This fallback is for quick prototyping and should not be used in production.

**Recommended:**

```bash
DATABASE_BACKEND=postgresql
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/Reponium?sslmode=prefer
```

**Fallback (not for production):**

```bash
DATABASE_BACKEND=sqlite
DATABASE_URL=sqlite:///./Reponium.db
```

`DATABASE_URL` is always the single runtime source and is resolved from the above policy. For production, always use Supabase or another PostgreSQL instance.

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
PROJECTS_MAX_FILE_COUNT=20000
PROJECTS_MAX_TOTAL_SIZE_BYTES=268435456
PROJECTS_MAX_ZIP_ENTRY_COUNT=50000
PROJECTS_MAX_ZIP_UNCOMPRESSED_BYTES=536870912
PROJECTS_ALLOWED_EXTENSIONS=
PROJECTS_DISALLOW_SYMLINKS=true
```

Ingestion responses now include metadata describing operation mode and workspace policy applied.

Local and ZIP ingestion now enforce the same safety policy:

- traversal-safe extraction only
- optional extension allowlist
- file count and total size limits
- symlink rejection by default
- ZIP entry count and uncompressed size limits

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

## LLM Providers

The backend can use different LLM providers for repo summarization and code explanations.

### Ollama

In `.env`:

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
OLLAMA_TIMEOUT_SECONDS=120
```

Use `LLM_PROVIDER=gemini` or `LLM_PROVIDER=openai` to keep the existing remote providers.

### Quick Smoke Test (Repo Summaries)

From `backend/`, run the smoke script against a local repository path:

```bash
python -m scripts.ollama_repo_summary_smoke ..\
```

Or target a specific folder and model:

```bash
python -m scripts.ollama_repo_summary_smoke D:\path\to\repo --model llama3.1 --base-url http://localhost:11434
```

The script prints:

- `project_summary`
- `architecture_summary`
- `execution_flow_summary`
- summary metrics payload

## Project Scanner Response

`GET /api/project/analyze/{project_name}` returns language summary plus scanned files.

Each file row includes:

- `name`
- `path`
- `extension`
- `category`

`category` values currently emitted by the scanner:

- `source`
- `test`
- `config`

Example:

```json
{
  "language": "Python",
  "total_files": 3,
  "total_files_scanned": 3,
  "files": [
    {
      "name": "main.py",
      "path": "src/main.py",
      "extension": "py",
      "category": "source"
    },
    {
      "name": "test_main.py",
      "path": "tests/test_main.py",
      "extension": "py",
      "category": "test"
    },
    {
      "name": "settings.json",
      "path": "config/settings.json",
      "extension": "json",
      "category": "config"
    }
  ]
}
```

## Code Analysis Response

`GET /api/project/code-analysis/{project_name}` now returns a diagnostics-aware payload:

- `project_path`
- `files_scanned`
- `files_parsed`
- `files_failed`
- `files` (successful parse outputs)
- `errors` (per-file failure details)

Each parsed file includes `data.parse_mode`:

- `python_ast`: native Python `ast` semantic parsing
- `tree_sitter`: Tree-sitter parser path
- `fallback`: regex/generic fallback path when Tree-sitter parser is unavailable

Example:

```json
{
  "project_path": "D:/Reponium/RepoRover-AI/projects/demo",
  "files_scanned": 3,
  "files_parsed": 2,
  "files_failed": 1,
  "files": [
    {
      "file": "src/main.py",
      "language": "python",
      "data": {
        "parse_mode": "python_ast"
      }
    },
    {
      "file": "src/util.js",
      "language": "javascript",
      "data": {
        "parse_mode": "fallback"
      }
    }
  ],
  "errors": [
    {
      "file": "src/problem.ts",
      "language": "typescript",
      "error_type": "parse_error",
      "error": "Unable to parse ..."
    }
  ]
}
```

## Parsing Troubleshooting

If multi-language Tree-sitter parsers are not available (for example due to restricted network access), project parsing continues in degraded mode:

- Python files still parse through native `ast` (`parse_mode=python_ast`)
- JS/TS files switch to fallback extraction (`parse_mode=fallback`)
- parse failures are reported in `errors` instead of being silently dropped

Quick health check:

1. Call `GET /api/project/code-analysis/{project_name}`
2. Inspect `files_failed` and `errors`
3. Inspect `files[*].data.parse_mode`
