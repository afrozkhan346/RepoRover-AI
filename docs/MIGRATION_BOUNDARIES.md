# Migration Boundaries

Date: 2026-04-03
Status: Locked for migration planning

This document defines what is in scope for the migration to the final React + FastAPI architecture and what stays temporarily in the current repository during the transition.

## Locked Final Target

- Frontend: React + Tailwind
- Backend: FastAPI (Python)
- AI/NLP: PyTorch + HuggingFace + spaCy
- Graph: NetworkX
- Database: SQLite to PostgreSQL
- Parsing: Tree-sitter
- Repo handling: GitPython
- Visualization: Chart.js + Mermaid
- Deployment: Vercel + Render

## In Scope

### Backend replacement

- Convert all `src/app/api/*` routes into FastAPI endpoints
- Replace Next.js auth/API flow with Python backend services
- Replace current JS AI endpoints with Python AI/NLP pipelines
- Replace current DB access with Python models, migrations, and seeds

### Data and analysis

- Add local project ingestion
- Add zip archive ingestion
- Add Tree-sitter parsing pipeline
- Add token-level, AST-level, and graph-level representations
- Add NetworkX graph analysis

### Frontend conversion

- Rebuild current UI pages as a React frontend
- Keep only reusable visual patterns where they still fit the new stack
- Reconnect charts and diagrams to FastAPI outputs

## Temporarily Kept During Transition

- Current Next.js app remains the working shell until replacement screens and backend services are ready
- Existing UI components may be reused where they are framework-agnostic
- Existing product documentation remains until each section is rewritten or superseded

## Out of Scope for New Development

- New Next.js backend routes
- New Drizzle/Turso work
- New Better Auth work in the current architecture
- New Cloud Run or Cloud Build work
- New Firebase or Firestore work
- New Gemini JS SDK work

## Migration Rule

If a feature can be implemented cleanly in the final stack, do not expand the current Next.js architecture further. Prefer conversion work that moves the feature into the target React + FastAPI shape.

## Current Repo Reality

The repository still contains a transitional Next.js implementation. That is acceptable only as a migration shell while backend and frontend responsibilities are moved in phases.
