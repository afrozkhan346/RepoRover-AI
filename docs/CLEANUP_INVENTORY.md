# Cleanup Inventory

Date: 2026-04-03
Based on: [Migration Boundaries](MIGRATION_BOUNDARIES.md)

This inventory marks remaining Cloud Run, Next-only, and hackathon-era artifacts for removal or rewrite.

## Remove

### Cloud Run and hackathon artifacts
- `cloudbuild.yaml` if it reappears
- Any future `CLOUD_RUN_*` deployment docs or templates
- Any future hackathon-branded README or documentation content

### Legacy environment files
- `.env.development` entries that reference Firestore, Firebase, or Cloud Run-era variables
- `.env.production` if recreated with Cloud Run-specific settings
- Any `.env` template sections that refer to GCP-only deployment behavior

### Next-only runtime artifacts
- `next.config.ts` once the frontend is moved out of Next.js
- `next-env.d.ts`
- `middleware.ts`
- `src/app/api/*` after endpoints are moved to FastAPI

## Rewrite

### App shell and routing
- `src/app/layout.tsx`
- `src/app/page.tsx`
- `src/app/*/page.tsx` route modules

### Next-specific helpers
- `src/components/theme-provider.tsx`
- `src/components/theme-toggle.tsx`
- `src/components/navigation.tsx`
- `src/components/ErrorReporter.tsx`

### Frontend build assumptions
- `postcss.config.mjs` may need revision for the final React frontend build toolchain
- Next-specific build scripts in `package.json`

## Keep Only As Temporary Reference

- `README.md` content that describes the old implementation should be replaced or removed once the final stack docs are enough
- `docs/OAUTH_SETUP.md` should remain only if its remaining instructions are updated away from Cloud Run assumptions
- `package-lock.json` may still contain legacy package references until dependencies are actually pruned

## Cleanup Rule

If an artifact exists only because of the Cloud Run hackathon or the current Next.js monolith, it should either be removed or rewritten for the final React + FastAPI architecture.

## Notes

- This inventory is intentionally removal-focused, not a full migration plan.
- Items already covered in other inventories are repeated here only when they are still relevant as cleanup targets.