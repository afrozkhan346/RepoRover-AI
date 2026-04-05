# Part 10 - GitHub Ingestion + Workspace Policy

Date: 2026-04-06
Status: Completed

## Goal

Implement GitHub ingestion using GitPython with a shared repository workspace policy, plus normalized ingestion metadata and error handling.

## Implemented Changes

### 1) Shared Repository Workspace Policy

Updated `backend/app/services/repository_loader.py` to implement managed workspace behavior:

- Added policy-controlled workspace lifecycle:
  - `PROJECTS_WORKSPACE_PATH`
  - `PROJECTS_RETENTION_DAYS`
  - `PROJECTS_MAX_ENTRIES`
  - `PROJECTS_CLEANUP_ENABLED`
- Added retention + capacity cleanup before ingestion jobs.
- Added deterministic workspace policy string in metadata for auditability.

### 2) GitPython Clone/Fetch/Update Standardization

Remote repository ingestion now follows a unified path:

- If repo does not exist in shared workspace: `clone`.
- If repo already exists:
  - `fetch --prune`
  - best-effort checkout default branch
  - best-effort `pull --ff-only`
- Operation mode is captured as metadata (`cloned` or `updated`).

Local and ZIP source ingestion also run under managed workspace flow:

- Local folder ingestion: copied into managed `local` workspace.
- ZIP ingestion: extracted into managed `upload` workspace.

### 3) Normalized Ingestion Metadata

Added ingestion metadata models and response propagation:

- New metadata dataclass: `IngestionMetadata`
- Included in `RepositoryLoadResult`
- Added schema support in `backend/app/schemas/github_analysis.py`:
  - `ingestion` object in `GitHubAnalysisResponse`

Metadata includes:

- `operation`
- `workspace_path`
- `workspace_policy`
- `cleaned_entries`
- `fetched_updates`

### 4) Normalized Ingestion Error Handling

Added ingestion-specific error class in repository loader:

- `RepositoryLoadError(detail, code)`

Routes now map ingestion errors to structured API errors consistently:

- `backend/app/api/routes/project.py`
- `backend/app/api/routes/github_analysis.py`

This preserves consistent machine-readable codes for clone/analyze failures.

### 5) Operational Documentation

Updated:

- `backend/.env.example` with workspace policy knobs
- `backend/README.md` with ingestion policy and runtime behavior

## Outcome

Part 10 deliverables are met:

- Clone/fetch/update workflows are standardized with GitPython.
- Shared workspace retention and cleanup policy is implemented and configurable.
- Ingestion metadata and error handling are normalized across GitHub source operations.
