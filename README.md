# RepoRover AI

RepoRover AI is a repository intelligence platform with a React + Vite frontend and a FastAPI backend. It analyzes local projects or cloned GitHub repositories, then renders summaries, graph analytics, explainability traces, and AI-assisted explanations in the browser.

[![React](https://img.shields.io/badge/React-19-61DAFB)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4-cyan)](https://tailwindcss.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)](https://fastapi.tiangolo.com/)
[![Chart.js](https://img.shields.io/badge/Chart.js-4-f5788d)](https://www.chartjs.org/)
[![Mermaid](https://img.shields.io/badge/Mermaid-11-ff6b6b)](https://mermaid.js.org/)

## Architecture

Browser UI (React + Vite)
  -> FastAPI backend (`backend/app`)
  -> core engines
    - parsing and AST extraction
    - dependency and call graph analysis
    - AI/NLP and explanation generation
    - repository ingestion and validation
  -> SQLite for development, PostgreSQL for deployment

## Deployment Split

- Frontend: Vercel
- Backend: Render

The frontend reads backend responses directly through `VITE_BACKEND_URL`, and the backend is the single source of truth for analysis, explanation, and repository processing.

## Features

- Analyze GitHub repos or local projects (Tree-sitter, AST, NetworkX)
- Visualize dependencies, call graphs, and code structure
- Detect code smells, design gaps, and complexity risks
- AI-powered code explanations (beginner to advanced, groq API)
- Guided repo walkthroughs and Q&A
- GitHub OAuth login and profile insights
- Personalized repo suggestions and growth tracking
- Auto-generated, shareable contribution portfolio
- Interactive dashboards and visualizations
- PDF/JSON report export and improvement suggestions
- Weekly digest, notifications, and OSS matching
- Self-hostable open core, paid advanced features
- Modern stack: React, Vite, FastAPI, Drizzle, Supabase, groq, Redis, GitHub Actions

## Getting Started

### Prerequisites

- Node.js 18 or newer
- Python 3.11 or newer
- npm

### Frontend

```bash
npm ci
npm run dev
```

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
uvicorn app.main:app --reload
```

### Environment

Copy the example files and set the backend URL for the frontend:

```bash
copy .env.example .env.development
copy backend\.env.example backend\.env
```

Frontend env:

```env
VITE_BACKEND_URL=http://localhost:8000/api
```

Backend env defaults to SQLite for local development and can switch to PostgreSQL for deployment.

### Final Validation

```bash
npm run build
npm run lint
python -m compileall backend/app
```

## Repository Layout

- `src/app` - React application pages and layouts
- `src/components` - shared UI and analysis widgets
- `src/lib` - frontend backend/client helpers
- `backend/app` - FastAPI routes, services, schemas, and engines
- `docs` - migration tracker and part artifacts

## Notes

- The migration tracker lives in `docs/MIGRATION_20_PART_PLAN.md`.
- Backend deployment and environment details are documented in `backend/README.md`.
- Historical legacy references have been removed from the active setup instructions.
