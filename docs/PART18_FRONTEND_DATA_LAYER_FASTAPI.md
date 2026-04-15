# Part 18 - Frontend Data Layer Rewired to FastAPI

Date: 2026-04-06
Status: Completed

## Goal

Move the frontend data layer onto the FastAPI backend directly and remove the leftover Next API route shims from the React workspace.

## Implemented Changes

### 1) Shared backend client contract updated

Extended `src/lib/backend.ts` so the frontend response types match the richer backend payloads.

The shared client now includes:

- explainability token evidence
- explainability AST evidence
- AI explanation named entities
- AI explanation structured evidence items

### 2) Next API route shims removed

Deleted the unused `src/app/api/*` route handlers that had been left over from the earlier Next.js-era data layer.

This removes the local API surface from the frontend workspace and leaves the React app talking directly to FastAPI.

### 3) Direct FastAPI usage preserved

Existing frontend pages already consumed the backend directly through `src/lib/backend.ts` and `BACKEND_API_BASE`.

This part formalized that contract and removed the dead Next API layer instead of adding more proxy routes.

### 4) Validation

Validated the edited frontend client file and searched the React source for remaining `/api/*` route references.

Observed outcome:

- no React page references remain for the deleted Next API routes
- the shared backend client parses cleanly

## Outcome

Part 18 is complete:

- the frontend data layer now targets FastAPI directly
- the unused Next API route shims are removed
- the shared client contract matches the current backend payloads
