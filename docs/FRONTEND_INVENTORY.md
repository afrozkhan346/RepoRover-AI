# Frontend Inventory

Date: 2026-04-03
Based on: [Migration Boundaries](MIGRATION_BOUNDARIES.md)

This inventory classifies the current frontend surface into items to convert, keep, or retire during the migration to the final React + FastAPI architecture.

## Pages To Convert

These pages contain product UI and should be rebuilt in the new React frontend, with their data sources moved to FastAPI:

- `src/app/page.tsx` - landing/home page
- `src/app/analyze/page.tsx` - repository analysis view
- `src/app/ai-tutor/page.tsx` - AI tutor and explanation view
- `src/app/dashboard/page.tsx` - dashboard
- `src/app/achievements/page.tsx` - achievements screen
- `src/app/lessons/page.tsx` - lessons list
- `src/app/lessons/[id]/page.tsx` - lesson detail screen
- `src/app/login/page.tsx` - login screen
- `src/app/register/page.tsx` - registration screen
- `src/app/profile/page.tsx` - profile screen

## App Shell To Rework

- `src/app/layout.tsx` - app shell should be re-expressed for the new frontend architecture
- `src/app/global-error.tsx` - can be reused conceptually, but should be checked for framework coupling
- `src/app/globals.css` - style foundation may be partially reusable, but will need review for the new client app

## Components To Convert

These components are tied to the current Next.js app flow or auth/navigation layer and should be rewritten or adapted:

- `src/components/navigation.tsx`
- `src/components/theme-toggle.tsx`
- `src/components/theme-provider.tsx`
- `src/components/ErrorReporter.tsx`

## UI Primitives Likely To Keep

These are reusable presentation components and are good candidates to carry into the new React frontend with minimal changes:

- `src/components/ui/*`

Examples include button, card, dialog, dropdown-menu, input, label, select, tabs, table, tooltip, and other generic primitives.

## Potentially Retire After Frontend Rewrite

These utilities are likely tied to the current app-shell experience and may not be needed once the new frontend is in place:

- `src/components/ui/container-scroll-animation.tsx`
- `src/components/ui/background-boxes.tsx`
- `src/components/ui/ComponentSeparator.tsx`
- `src/components/ui/navigation.tsx` if duplicated by the new navigation system

## Frontend Migration Rule

Keep only components that are framework-agnostic or directly useful in the new React frontend. Any component that depends on Next.js routing, Next auth flow, or the current app shell should be rewritten instead of copied unchanged.

## Notes

- The current frontend is still a transitional Next.js implementation.
- UI primitives remain useful because the target stack still uses React and Tailwind.
- The main rewrite effort is in page-level composition, data fetching, routing, and auth flow.
