# Backend Inventory

Date: 2026-04-03
Based on: [Migration Boundaries](MIGRATION_BOUNDARIES.md)

This inventory classifies the current backend surface into items to convert, keep, or retire during the migration to the final FastAPI architecture.

## API Routes To Convert

These routes are part of product behavior and should become FastAPI endpoints:

- `src/app/api/github/analyze/route.ts` - GitHub repository analysis
- `src/app/api/ai/explain-code/route.ts` - AI code explanation
- `src/app/api/ai/generate-quiz/route.ts` - quiz generation
- `src/app/api/learning-paths/route.ts` - learning path management
- `src/app/api/lessons/route.ts` - lessons API
- `src/app/api/quizzes/route.ts` - quizzes API
- `src/app/api/quiz-attempts/route.ts` - quiz attempt tracking
- `src/app/api/lesson-progress/route.ts` - lesson progress tracking
- `src/app/api/user-progress/route.ts` - user progress API
- `src/app/api/user-achievements/route.ts` - user achievement API
- `src/app/api/achievements/route.ts` - achievements API
- `src/app/api/repositories/route.ts` - saved repository data
- `src/app/api/db/stats/route.ts` - database/reporting stats

## API Routes To Retire Or Fold Into Backend Internals

These routes are implementation helpers rather than product-facing core APIs and should be folded into the new backend architecture or removed if no longer needed:

- `src/app/api/cache/stats/route.ts`
- `src/app/api/achievements/cached/route.ts`
- `src/app/api/learning-paths/cached/route.ts`
- `src/app/api/lessons/cached/route.ts`

## Auth And Session Layer To Replace

- `src/app/api/auth/[...all]/route.ts`
- `src/lib/auth.ts`
- `src/lib/auth-client.ts`

These are tied to the current Next.js auth flow and should be redesigned for the new React + FastAPI split.

## Shared Backend Utilities

These utilities may contain reusable logic but need review for stack coupling:

- `src/lib/utils.ts`
- `src/lib/hooks/use-mobile.tsx`

## Cache And Performance Layer

These are currently tied to the transitional stack and should be replaced or rewritten in Python if still needed:

- `src/lib/cache/redis.ts`
- `src/lib/cache/middleware.ts`
- `src/lib/cache/index.ts`

## Data Layer To Convert

These files represent the current TypeScript database system and should be converted to Python models/migrations/seeds:

- `src/db/index.ts`
- `src/db/schema.ts`
- `src/db/schema.optimized.ts`
- `src/db/queries.optimized.ts`
- `src/db/optimization.ts`
- `src/db/seeds/learning_paths.ts`
- `src/db/seeds/lessons.ts`
- `src/db/seeds/quizzes.ts`
- `src/db/seeds/achievements.ts`

## Backend Migration Rule

Anything that handles business logic, persistence, analytics, or AI should move into FastAPI or Python service modules. The current Next.js backend should only remain as a transition shell until each endpoint is replaced.

## Notes

- Cache-related endpoints and Redis utilities are not a first-class part of the final architecture unless a Python equivalent is explicitly chosen.
- Database optimization helpers may be useful as reference, but not as direct runtime code.
- The conversion effort should favor clearer Python service boundaries over preserving the current route structure.
