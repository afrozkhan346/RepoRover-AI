# Part 4 - Next Runtime Assumption Removal

Date: 2026-04-06
Status: Completed

## Goal

Remove Next.js-only runtime assumptions from the frontend workspace and establish a React client runtime baseline.

## What changed

### Runtime and build baseline

- Switched root frontend scripts to Vite runtime:
  - dev -> vite
  - build -> vite build
  - start -> vite preview
- Added Vite config with React plugin and path aliasing.
- Added index.html and React entrypoints:
  - src/main.tsx
  - src/App.tsx

### Compatibility shims (transitional)

- Added shim for next/link:
  - src/compat/next-link.tsx
- Added shim for next/navigation:
  - src/compat/next-navigation.ts

These shims allow existing page/components that still import next/link and next/navigation to run under React Router while full migration continues.

### Removed Next runtime files

- middleware.ts (Next middleware runtime)
- next.config.ts (Next build/runtime config)
- next-env.d.ts (Next type bootstrap)

### Config updates

- Updated tsconfig.json to React+Vite assumptions:
  - jsx -> react-jsx
  - include -> src + vite config
  - removed Next plugin entry
  - added vite/client types
- Updated environment access in frontend utility clients:
  - src/lib/backend.ts now resolves Vite env first
  - src/lib/auth-client.ts now resolves Vite env first

## Temporary compatibility boundaries

The following are intentionally still transitional and will be addressed in upcoming parts:

- better-auth client integration and token/session flow (Part 5+).
- Next API route folders under src/app/api (Part 18+).
- Legacy page logic that still assumes Next-era behavior even though router imports are shimmed.

## Outcome

The frontend workspace now assumes a React client runtime first, not a Next runtime first, with compatibility shims preserving migration continuity.
