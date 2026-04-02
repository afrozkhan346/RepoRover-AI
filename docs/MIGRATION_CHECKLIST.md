# Migration Checklist

Date: 2026-04-02
Based on: [Final Tech Stack](FINAL_TECH_STACK.md)

This checklist lists what is no longer needed in the current stack and what must be converted for the final React + FastAPI architecture.

Locked scope reference: [Migration Boundaries](MIGRATION_BOUNDARIES.md).
Frontend inventory: [Frontend Inventory](FRONTEND_INVENTORY.md).
Backend inventory: [Backend Inventory](BACKEND_INVENTORY.md).
Database inventory: [Database Inventory](DATABASE_INVENTORY.md).
Dependency inventory: [Dependency Inventory](DEPENDENCY_INVENTORY.md).
Cleanup inventory: [Cleanup Inventory](CLEANUP_INVENTORY.md).

## No Longer Needed

### Framework and backend runtime
- Next.js app-router backend routes in `src/app/api/*`
- `middleware.ts`
- `next.config.ts` Next-only server assumptions
- `next-env.d.ts` as a permanent backend contract file
- `better-auth` server/client wiring for the current Next app

### Current database stack
- `drizzle-orm`
- `drizzle-kit`
- `@libsql/client`
- `drizzle.config.ts`
- `src/db/*` TypeScript database layer

### Current AI runtime
- `@google/generative-ai`
- Current JS-based Gemini API call flow

### Current cloud and legacy stack
- `firebase`
- `firebase-admin`
- `ioredis` if caching is not retained in the new backend
- Cloud Run and Cloud Build artifacts or docs

### Current deployment assumptions
- Any code assuming one monolithic Next.js deployment for frontend and backend
- Any GCP-specific deployment logic that was left from the hackathon phase

## Need to Convert

### Frontend
- `src/app/*` pages should become a React frontend structure suitable for Vite or another React-only client app
- `src/components/*` should be retained only for reusable UI, then adapted to the new frontend architecture
- Theme handling should be re-implemented in the new client app if still required

### Backend APIs
- `src/app/api/github/analyze/route.ts` should move to a FastAPI router
- `src/app/api/ai/explain-code/route.ts` should move to a FastAPI service endpoint
- `src/app/api/learning-paths/route.ts` should move to FastAPI with a Python data layer
- Any repository, lesson, quiz, progress, or achievement routes should become FastAPI endpoints

### Database layer
- Current Drizzle schema and seed files should be translated into Python models, migrations, and seed scripts
- SQLite should be the first target database, with a later PostgreSQL migration path

### AI and NLP
- Current AI explanation logic should become Python services using PyTorch, HuggingFace, and spaCy
- Prompting and response shaping should move into a controlled Python pipeline

### Repository analysis
- GitHub repository ingestion should be reworked into Python-based repo handling with GitPython
- Local project ingestion, zip support, and parsing should be implemented in the backend

### Graph and static analysis
- Tree-sitter parsing should replace the current lightweight file-structure-only analysis
- NetworkX should power dependency graphs, call graphs, and impact tracing
- Graph output should feed summaries, risk analysis, and explainability

### Visualization
- Current chart/report UI pieces should be converted to a React frontend that renders Chart.js and Mermaid outputs from the backend

## Can Stay

### Frontend foundations
- `react`
- `tailwindcss`
- `typescript`

### Visualization and analysis targets
- `Chart.js`
- `Mermaid`
- `Tree-sitter`
- `GitPython`
- `NetworkX`

### Deployment targets
- `Vercel` for the frontend
- `Render` for the FastAPI backend

## Package-Level Actions

### Remove or replace from `package.json`
- `next`
- `next-themes`
- `better-auth`
- `drizzle-orm`
- `drizzle-kit`
- `@libsql/client`
- `@google/generative-ai`
- `firebase`
- `firebase-admin`
- `ioredis`

### Review for possible removal after frontend rewrite
- `@radix-ui/*` packages
- `framer-motion`
- `react-syntax-highlighter`
- `recharts`
- `react-dropzone`
- `three`
- `@react-three/*`
- `swiper`
- `react-responsive-masonry`

## File-Level Actions

### Remove or replace
- `src/app/api/*`
- `src/db/*`
- `drizzle.config.ts`
- `middleware.ts`
- `next.config.ts`
- `cloudbuild.yaml` if it reappears

### Convert
- `src/app/page.tsx`
- `src/app/analyze/page.tsx`
- `src/app/ai-tutor/page.tsx`
- `src/app/dashboard/*`
- `src/app/lessons/*`
- `src/app/profile/*`
- `src/components/*` used by those pages

## Recommended Order

1. Freeze the final stack and remove deployment-specific clutter.
2. Extract backend responsibilities into FastAPI.
3. Rebuild repository ingestion and parsing in Python.
4. Replace database access with Python models and migrations.
5. Rebuild the frontend as a React client aligned with the new backend.
6. Add Tree-sitter, NetworkX, and AI/NLP pipelines.
7. Reconnect visualization and reporting outputs.
