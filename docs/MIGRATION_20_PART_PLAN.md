# 20-Part Migration Plan (Execution Tracker)

Date: 2026-04-06
Status: Active
Target Stack:
- Frontend: React + Tailwind
- Backend: FastAPI (Python)
- AI/NLP: PyTorch + HuggingFace + spaCy
- Graph: NetworkX
- Database: SQLite -> PostgreSQL
- Parsing: Tree-sitter
- Repo Handling: GitPython
- Visualization: Chart.js + Mermaid
- Deployment: Vercel + Render
- Data Sources: GitHub + Local Projects

## How We Will Execute

- You type: next
- I load and execute exactly one next unfinished part from this file.
- I then mark that part as done and move to the next.
- This guarantees ordered, complete migration without skipping steps.

## Progress Board (20 Equal Parts)

1. [x] Freeze target stack, lock migration scope, create execution tracker.
2. [x] Build frontend migration map (routes, components, API consumers).
3. [x] Build backend migration map (routers, services, schemas, engine modules).
4. [x] Remove Next.js-only backend/runtime assumptions from frontend workspace.
5. [x] Remove Drizzle/libsql/Better Auth legacy data and auth wiring from frontend.
6. [x] Define backend API contract v1 for all migrated frontend features.
7. [x] Standardize FastAPI app structure, config, CORS, health, and error envelope.
8. [x] Implement SQLite-first database layer with SQLAlchemy models and Alembic baseline.
9. [x] Implement PostgreSQL readiness layer (settings, drivers, migration-safe config).
10. [x] Implement GitHub ingestion with GitPython and shared repository workspace policy.
11. [ ] Implement local project and ZIP ingestion with secure extraction and validation.
12. [ ] Integrate Tree-sitter parser pipeline and normalized AST schema outputs.
13. [ ] Implement token-level lexical extraction and AST evidence mapping.
14. [ ] Implement dependency graph generation with NetworkX.
15. [ ] Implement call graph + impact analysis + graph analytics endpoints.
16. [ ] Implement AI/NLP pipeline using PyTorch + HuggingFace + spaCy services.
17. [ ] Implement explanation pipeline tying AI findings to token/AST/graph evidence.
18. [ ] Rewire frontend data layer to FastAPI endpoints and remove Next API route usage.
19. [ ] Finalize visualization layer with Chart.js and Mermaid fed by backend analysis outputs.
20. [ ] Production hardening: deployment split (Vercel frontend, Render backend), envs, CI checks, and final validation.

## Part 1 Completed Work (2026-04-06)

Objective:
- Freeze the stack and establish strict migration execution control.

What was completed:
- Confirmed final stack already documented in docs/FINAL_TECH_STACK.md.
- Confirmed migration boundaries/checklist already documented in docs/MIGRATION_CHECKLIST.md.
- Audited current root frontend dependencies in package.json and identified major legacy stack still present (Next.js, Drizzle, Better Auth, libsql, Firebase, Google Gemini JS path).
- Audited backend dependencies in backend/requirements.txt and confirmed target Python stack foundations already present (FastAPI, SQLAlchemy, Alembic, GitPython, Tree-sitter, NetworkX, torch, transformers, spaCy).
- Created this 20-part ordered tracker as the source of truth for sequential execution.

Exit criteria met:
- A single, deterministic 20-part plan exists.
- Current progress can be resumed by a simple next command.
- Part 2 is clearly defined and ready.

## Part 2 Completed Work (2026-04-06)

Objective:
- Build a frontend migration map covering pages/components/api-consumer usage.

What was completed:
- Created docs/FRONTEND_MIGRATION_MAP.md as the canonical Part 2 artifact.
- Mapped user-facing routes and identified active page-client ownership.
- Mapped reusable UI/analysis components versus router/auth/theme coupling points requiring refactor.
- Mapped frontend API consumers into two groups:
	- already FastAPI-aligned through src/lib/backend.ts
	- still bound to Next API route handlers under src/app/api/*
- Captured an explicit Next.js-only dependency gap list (next/link, next/navigation, App Router layout, next-themes, better-auth route flow).

Exit criteria met:
- Feature-to-route map produced.
- Component reuse/deprecation map produced.
- API-consumer map produced.
- Next.js-only gap list produced.

## Part 3 Completed Work (2026-04-06)

Objective:
- Build backend migration map (routers, services, schemas, engine modules).

What was completed:
- Created docs/BACKEND_MIGRATION_MAP.md as the canonical Part 3 artifact.
- Mapped all active FastAPI endpoints, including /api routers and /project routes.
- Mapped service architecture split between engine-facade routes and direct-service routes.
- Mapped schema contracts for AI, parsing, graph, explainability, auth, learning, and repository analysis.
- Identified migration gaps: endpoint overlap, response model inconsistency, mixed routing patterns, auth transition coupling, and DB migration consistency requirements.

Exit criteria met:
- Endpoint-to-router map produced.
- Service/module map produced.
- Schema contract map produced.
- Backend gap list produced.

## Part 4 Completed Work (2026-04-06)

Objective:
- Remove Next.js-only backend/runtime assumptions from frontend workspace.

What was completed:
- Switched frontend runtime scripts to Vite and added React client entrypoints.
- Added compatibility shims for next/link and next/navigation so existing pages continue to work during migration.
- Updated TypeScript and Vite configuration for React client assumptions.
- Updated frontend env resolution in backend/auth clients to avoid Next-only process env assumptions.
- Removed Next-only runtime files: middleware.ts, next.config.ts, next-env.d.ts.
- Created docs/PART4_NEXT_RUNTIME_REMOVAL.md as the Part 4 artifact.

Exit criteria met:
- Next-only runtime files removed.
- Compatibility shims documented and implemented.
- Frontend scripts/config shifted to React-only runtime assumptions.

## Part 5 Completed Work (2026-04-06)

Part 5 objective:
- Remove Drizzle/libsql/Better Auth legacy data and auth wiring from frontend.

What was completed:
- Replaced `src/lib/auth-client.ts` Better Auth usage with a backend-auth contract client (session, login, register, logout).
- Replaced `src/lib/auth.ts` with a transitional non-Better-Auth helper to break frontend runtime coupling.
- Removed legacy Next auth bridge route by deleting `src/app/api/auth/[...all]/route.ts`.
- Rewired user-facing pages from local Next API calls to backend endpoints:
	- `src/app/achievements/page.tsx`
	- `src/app/profile/page.tsx`
- Updated social auth actions in `src/app/login/page-client.tsx` and `src/app/register/page.tsx` to explicit transitional behavior under FastAPI auth flow.
- Removed legacy frontend dependencies from root `package.json`: `better-auth`, `drizzle-orm`, `drizzle-kit`, `@libsql/client`.
- Synced dependencies and validated production build success with `npm run build`.

Exit criteria met:
- Better Auth coupling removed from active frontend runtime path.
- Drizzle/libsql packages removed from frontend dependency manifest.
- Auth/session and profile/achievements flows now use backend contract paths.

## Part 6 Completed Work (2026-04-06)

Part 6 objective:
- Define backend API contract v1 for all migrated frontend features.

What was completed:
- Created `docs/BACKEND_API_CONTRACT_V1.md` as the canonical Part 6 artifact.
- Documented endpoint contracts for:
	- auth (`/api/auth/*`)
	- repositories and ingestion (`/project/*`, `/api/github/*`)
	- analysis and explainability (`/api/ai/*`, `/api/graph-analysis/*`, parsing/tokens/graphs)
	- learning and user progression (`/api/learning-paths`, `/api/lessons`, `/api/achievements*`)
- Defined v1 standardized error-envelope target and status code policy while capturing current behavior.
- Added frontend-to-backend one-to-one endpoint mapping notes, including remaining normalization item in `src/app/analyze/page-client.tsx` direct code-analysis call.

Exit criteria met:
- Canonical API contract v1 documented for migrated frontend features.
- Request/response and error-format standards explicitly defined.
- Frontend contract mapping recorded for migration continuity.

## Part 7 Completed Work (2026-04-06)

Part 7 objective:
- Standardize FastAPI app structure, config, CORS, health, and error envelope.

What was completed:
- Added centralized exception handling and error-envelope normalization in `backend/app/core/errors.py`.
- Wired exception handlers at app startup in `backend/app/main.py` for consistent HTTP, validation, and unhandled error payloads.
- Normalized root service metadata response in `backend/app/main.py`.
- Standardized health endpoints in `backend/app/api/routes/health.py`:
	- `GET /api/health`
	- `GET /api/health/version`
- Expanded default CORS origin coverage in `backend/app/core/config.py` for localhost and 127.0.0.1 on active frontend dev ports.
- Created `docs/PART7_FASTAPI_STANDARDIZATION.md` as the Part 7 artifact.

Exit criteria met:
- Uniform API error envelope policy implemented centrally.
- App-level exception handling policy added.
- Health/version endpoint contract normalized.
- CORS/config behavior aligned for frontend runtime usage.

## Part 8 Completed Work (2026-04-06)

Part 8 objective:
- Implement SQLite-first database layer with SQLAlchemy models and Alembic baseline.

What was completed:
- Added Alembic scaffold to backend runtime:
	- `backend/alembic.ini`
	- `backend/migrations/env.py`
	- `backend/migrations/script.py.mako`
	- `backend/migrations/versions/`
- Created SQLite-first Alembic baseline revision:
	- `backend/migrations/versions/0001_sqlalchemy_baseline.py`
	- Includes full table create/drop lifecycle for current SQLAlchemy model set.
- Standardized DB session usage pattern in `backend/app/db/session.py` by adding reusable `get_db_session()` dependency helper.
- Aligned backend packaging dependencies in `backend/pyproject.toml` to include SQLAlchemy/Alembic and DB drivers.
- Updated migration workflow documentation in `backend/migrations/README.md` and created `docs/PART8_SQLITE_ALEMBIC_BASELINE.md` artifact.

Exit criteria met:
- SQLAlchemy model set is migration-ready for SQLite-first execution.
- Alembic baseline migration and scaffold are in place.
- DB session usage has a standardized helper for upcoming PostgreSQL readiness work.

## Part 9 Completed Work (2026-04-06)

Part 9 objective:
- Implement PostgreSQL readiness layer (settings, drivers, migration-safe config).

What was completed:
- Finalized PostgreSQL readiness config in `backend/app/core/config.py`:
	- added `DATABASE_BACKEND` policy (`sqlite`/`postgresql`/`auto`)
	- added resolved DB backend/URL properties
	- added PostgreSQL readiness and pool knobs (`POSTGRES_SSLMODE`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`)
	- added validation for PostgreSQL field requirements when backend is PostgreSQL.
- Updated `backend/app/db/connection.py` to consume resolved DB backend/URL and apply PostgreSQL pool configuration safely.
- Updated `backend/migrations/env.py` so Alembic uses resolved runtime DB URL policy.
- Updated `backend/.env.example` with PostgreSQL readiness variables.
- Updated `backend/README.md` with SQLite/PostgreSQL configuration modes and migration runbook.
- Created `docs/PART9_POSTGRESQL_READINESS.md` as the Part 9 artifact.

Exit criteria met:
- PostgreSQL settings and URL construction policy finalized.
- Migration/runtime DB target behavior aligned for SQLite and PostgreSQL.
- Environment and operational rollout guidance documented.

## Part 10 Completed Work (2026-04-06)

Part 10 objective:
- Implement GitHub ingestion with GitPython and shared repository workspace policy.

What was completed:
- Implemented shared repository workspace lifecycle policy in `backend/app/services/repository_loader.py` with retention/capacity cleanup controls.
- Standardized GitPython ingestion workflow for remote sources:
	- first-time clone
	- subsequent fetch/prune and best-effort fast-forward update in place.
- Added managed workspace flows for local path and ZIP ingestion sources.
- Introduced normalized ingestion metadata (`operation`, `workspace_path`, `workspace_policy`, `cleaned_entries`, `fetched_updates`) and propagated it into GitHub analysis responses.
- Added ingestion-specific error class and route-level normalized code mapping in:
	- `backend/app/api/routes/project.py`
	- `backend/app/api/routes/github_analysis.py`
- Updated environment and operational docs:
	- `backend/.env.example`
	- `backend/README.md`
- Created `docs/PART10_GITHUB_INGESTION_POLICY.md` as the Part 10 artifact.

Exit criteria met:
- Clone/fetch/update workflow standardized with GitPython.
- Shared workspace cleanup/retention policy implemented and configurable.
- Ingestion metadata and error handling normalized for GitHub source operations.

## Part 11 Ready (Next)

Part 11 objective:
- Implement local project and ZIP ingestion with secure extraction and validation.

Part 11 deliverables:
- Harden ZIP extraction and local path validation against traversal and unsafe content patterns.
- Add ingestion constraints (size/file count/extension policy) with clear error codes.
- Standardize upload ingestion audit metadata for local and archive sources.

## Post-Part10 Integration Note (2026-04-06)

User-selected architecture decision after Part 10:
- Keep SQLAlchemy/Alembic as the single canonical ORM/migration path.
- Port idempotent CSV seeding behavior into canonical SQLAlchemy tooling (no Peewee runtime adoption).

What was added:
- Unique constraints in `backend/app/db/models.py` for seed conflict keys:
	- `learning_paths.title`
	- `lessons(learning_path_id, title)`
	- `achievements.title`
	- `quizzes(lesson_id, question)`
- Alembic revision `backend/migrations/versions/0002_seed_idempotency_indexes.py` adding matching unique indexes.
- Canonical seed loader `backend/app/db/seed.py` implementing idempotent CSV upserts for:
	- learning paths
	- lessons
	- achievements
	- quizzes
- Backend runbook updated with seeding commands in `backend/README.md`.
