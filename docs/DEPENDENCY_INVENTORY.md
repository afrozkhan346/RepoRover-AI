# Dependency Inventory

Date: 2026-04-03
Based on: [Migration Boundaries](MIGRATION_BOUNDARIES.md)

This inventory classifies AI, auth, cache, deployment, and related packages/files for conversion to the final React + FastAPI architecture.

## AI Dependencies

### Convert or replace

- `@google/generative-ai` - replace with Python AI/NLP pipeline

### Likely remove or re-evaluate after migration

- `@babel/parser` - only keep if a transitional frontend parser is still needed
- `react-syntax-highlighter` - only keep if still needed in the new frontend

## Auth Dependencies

### Convert or replace

- `better-auth` - replace with FastAPI auth/session architecture

### Review for reuse only if needed in the new frontend

- `bcrypt` - may still be useful on the Python side conceptually, but the JavaScript package itself should not be assumed to survive the migration

## Database And Persistence Dependencies

### Convert or replace

- `drizzle-kit`
- `drizzle-orm`
- `@libsql/client`

### Likely remove after conversion

- `@types/ioredis` if Redis is removed or replaced in Python

## Cache And Performance Dependencies

### Convert or replace

- `ioredis` - replace with Python-side cache or remove if no longer required

### Keep only if explicitly reintroduced in the final backend

- Any caching helper logic that is currently tied to Next.js should be rewritten in Python rather than ported as-is

## Frontend And App-Shell Dependencies That May Become Transitional

These packages are not necessarily wrong today, but they should be re-evaluated once the React frontend is split from the FastAPI backend:

- `next`
- `next-themes`
- `eslint-config-next`
- `framer-motion`
- `motion`
- `motion-dom`
- `react-dropzone`
- `swiper`
- `recharts`
- `three`
- `@react-three/fiber`
- `@react-three/drei`
- `three-globe`
- `react-responsive-masonry`
- `react-fast-marquee`
- `react-intersection-observer`
- `cobe`
- `simplex-noise`

## UI And Utility Dependencies To Keep Or Reuse

These are likely still useful because the final frontend is still React + Tailwind:

- `react`
- `react-dom`
- `tailwindcss`
- `@tailwindcss/postcss`
- `@tailwindcss/typography`
- `tailwindcss-animate`
- `tailwind-merge`
- `class-variance-authority`
- `clsx`
- `lucide-react`
- `sonner`
- `zod`
- `react-hook-form`
- `@hookform/resolvers`
- `@radix-ui/*` primitives if the final React frontend still uses them
- `@tabler/icons-react`
- `vaul`

## Deployment Dependencies And Files

### Replace current deployment assumptions

- `next.config.ts`
- `postcss.config.mjs`
- `eslint.config.mjs`
- Next.js build/start scripts in `package.json`

### Final deployment targets

- Frontend to Vercel
- Backend to Render

### No longer needed from the Cloud Run era

- Cloud Build or Cloud Run files if they reappear
- Any deployment docs specific to Google Cloud Run or hackathon packaging

## Dependency Migration Rule

Prefer removing framework-specific packages rather than keeping them as transitional clutter. If a dependency only exists because of the current Next.js monolith, rewrite that capability in the new frontend or FastAPI backend instead of carrying the package forward.

## Notes

- Package retention depends on whether the final React frontend needs the same UI patterns.
- Backend Python dependencies such as FastAPI, PyTorch, HuggingFace, spaCy, NetworkX, Tree-sitter, GitPython, Chart.js, and Mermaid should be added in the new stack rather than kept here.
- This inventory focuses on what exists now and what should change, not on the full future Python `requirements.txt` yet.
