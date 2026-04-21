
# Reponium AI

Reponium AI is a next-generation developer intelligence platform that empowers you to understand, grow, and showcase your open source journey. Built with React, Vite, and FastAPI, Reponium analyzes GitHub repositories and local projects, delivering actionable insights and adaptive explanations tailored to your developer profile.

## Core Feature Pillars

### 1. AI Explanation Engine (Developer Experience Profiling Algorithm)

- Adaptive code explanations based on your experience level (beginner, intermediate, advanced)
- Natural language architecture summaries, step-by-step repo walkthroughs, and Q&A
- Developer Experience Profiling Algorithm personalizes every explanation

### 2. GitHub Profile Intelligence

- GitHub OAuth login for instant onboarding
- Automatic computation of your language proficiency, experience level, and contribution history
- Profile refresh, manual override, and last synced tracking

### 3. Personalized Developer Growth

- Repo suggestions and learning paths matched to your experience and interests
- Skill gap analysis and targeted recommendations
- Weekly personalized digest and OSS contribution matching

### 4. Career Growth Tracker

- Visual skill progression timeline and language milestones
- Repo analysis history, lesson tracking, and growth streaks
- Difficulty feedback loop to adapt your profile and recommendations

### 5. Adaptive Code Explanation Engine

- Progressive, context-aware explanations that build on your knowledge
- Concept mapping for unfamiliar patterns and human-readable risk/gap reports

### 6. OSS Readiness Scoring

- Repo readiness scoring and contribution difficulty matching
- Active repo filtering and career goal-driven recommendations

---

## Technical Highlights

- React + Vite + TypeScript frontend
- FastAPI Python backend
- Drizzle ORM with PostgreSQL via Supabase
- Groq LLM API for AI explanations (set `GROQ_API_KEY` in your backend environment)
- Tree-sitter for multi-language AST parsing
- NetworkX for graph construction and analysis
- ARQ + Upstash Redis for background job queue
- GitHub OAuth via Supabase Auth
- Vercel frontend deployment, Render backend deployment
- GitHub Actions CI pipeline

### Environment Variables (AI)

- `GROQ_API_KEY` (required for AI features)
  - Get your key from <https://console.groq.com/keys>
- `LLM_PROVIDER` (optional, defaults to `groq`)

If you previously set `ANTHROPIC_API_KEY`, it is no longer used. All AI features now require Groq.

---

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
- Production rollout and rollback steps are documented in `docs/DEPLOYMENT_RUNBOOK.md`.
- Historical legacy references have been removed from the active setup instructions.
