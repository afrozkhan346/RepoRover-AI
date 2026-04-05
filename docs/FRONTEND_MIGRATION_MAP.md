# Frontend Migration Map (Part 2)

Date: 2026-04-06
Status: Completed
Scope: Route/component/API-consumer mapping for migration from Next.js-coupled frontend to React + Tailwind client aligned to FastAPI backend.

## 1) Feature-to-Route Map

Current user-facing route inventory under src/app:

- / -> src/app/page.tsx
- /dashboard -> src/app/dashboard/page.tsx -> src/app/dashboard/page-client.tsx
- /analyze -> src/app/analyze/page.tsx -> src/app/analyze/page-client.tsx
- /ai-tutor -> src/app/ai-tutor/page.tsx -> src/app/ai-tutor/page-client.tsx
- /lessons -> src/app/lessons/page.tsx
- /lessons/[id] -> src/app/lessons/[id]/page.tsx
- /achievements -> src/app/achievements/page.tsx
- /profile -> src/app/profile/page.tsx
- /login -> src/app/login/page.tsx -> src/app/login/page-client.tsx
- /register -> src/app/register/page.tsx

Operational notes:

- Analyze, AI Tutor, and Dashboard are already aligned with FastAPI-driven analysis UX.
- Achievements and Profile still depend on local Next API route handlers.
- Lessons pages are transitional and still contain Next-specific language and link usage.

## 2) Component Reuse vs Deprecation Map

### Reuse as-is or with minimal adaptation

- Shared primitives in src/components/ui/*.tsx (buttons, cards, badges, inputs, charts wrappers).
- Analysis visualization components:
  - src/components/analysis/mermaid-diagram.tsx
  - src/components/analysis/metric-charts.tsx
- Error and toast surfaces:
  - src/components/ErrorReporter.tsx
  - src/components/ui/sonner.tsx

### Keep but refactor for router/auth decoupling

- src/components/navigation.tsx
  - Replace next/link, next/navigation usage.
  - Replace better-auth session dependency with backend-auth/session abstraction.
- Theme layer:
  - src/components/theme-provider.tsx
  - src/components/theme-toggle.tsx
  - Remove next-themes coupling in migration phase.

### Candidate deprecations after frontend migration finalization

- Any component only referenced by removed Next-only pages or route handlers.
- Legacy UI primitives with zero imports after route migration sweep.

## 3) API Consumer Map (Frontend -> Backend)

### Already FastAPI-aligned via src/lib/backend.ts

- AI explain code: POST /api/ai/explain-code (backend base)
- Project summaries: POST /api/ai/project-summaries
- Quality analysis: POST /api/ai/quality-analysis
- Risk scoring: POST /api/ai/risk-scoring
- Graph analysis: POST /api/graph-analysis/from-path
- Explainability traces: POST /api/ai/explainability-traces
- Project upload: POST /project/upload (root backend base)
- Project clone: POST /project/clone (root backend base)

Primary consumers:

- src/app/analyze/page-client.tsx
- src/app/ai-tutor/page-client.tsx

### Still bound to Next API route handlers (must migrate)

- src/app/achievements/page.tsx
  - GET /api/achievements
  - GET /api/user-achievements
- src/app/profile/page.tsx
  - GET /api/user-progress

### Next API route inventory still present under src/app/api

- src/app/api/achievements/route.ts
- src/app/api/achievements/cached/route.ts
- src/app/api/user-achievements/route.ts
- src/app/api/user-progress/route.ts
- src/app/api/lesson-progress/route.ts
- src/app/api/lessons/route.ts
- src/app/api/lessons/cached/route.ts
- src/app/api/learning-paths/route.ts
- src/app/api/learning-paths/cached/route.ts
- src/app/api/repositories/route.ts
- src/app/api/quizzes/route.ts
- src/app/api/quiz-attempts/route.ts
- src/app/api/ai/explain-code/route.ts
- src/app/api/ai/generate-quiz/route.ts
- src/app/api/github/analyze/route.ts
- src/app/api/cache/stats/route.ts
- src/app/api/db/stats/route.ts
- src/app/api/auth/[...all]/route.ts

## 4) Next.js-Only Gap List

Core coupling points identified:

- Router/link APIs:
  - next/link imports across route components.
  - next/navigation hooks in auth-gated pages and navigation.
- App Router shell:
  - src/app/layout.tsx metadata and App Router entry assumptions.
- Next API handlers:
  - src/app/api/* route handlers still active and used by some pages.
- Next auth wiring:
  - better-auth + custom bearer token handling in src/lib/auth-client.ts.
- Next theming:
  - next-themes dependency via src/components/theme-provider.tsx and src/components/theme-toggle.tsx.

## 5) Part 2 Exit Criteria Check

Delivered:

- Feature-to-route map.
- Reuse/refactor/deprecation component map.
- Frontend API consumer map.
- Explicit Next.js-only dependency gap list.

Part 2 status: Complete.