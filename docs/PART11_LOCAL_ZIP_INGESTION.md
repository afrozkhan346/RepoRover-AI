# Part 11 - Local Project and ZIP Ingestion Hardening

Date: 2026-04-06
Status: Completed

## Goal

Secure local-project and ZIP ingestion with traversal protection, size/count limits, extension allowlists, and normalized audit metadata.

## Implemented Changes

### 1) Shared validation for local and ZIP sources

Updated `backend/app/services/repository_loader.py` to validate repository trees before analysis:

- rejects symlinks when `PROJECTS_DISALLOW_SYMLINKS=true`
- enforces `PROJECTS_MAX_FILE_COUNT`
- enforces `PROJECTS_MAX_TOTAL_SIZE_BYTES`
- enforces `PROJECTS_ALLOWED_EXTENSIONS` when configured

This applies to:

- cloned remote workspaces once checked in
- copied local directories
- extracted ZIP content

### 2) ZIP extraction hardening

ZIP extraction now rejects:

- absolute paths
- `..` traversal segments
- symlink entries
- archives exceeding `PROJECTS_MAX_ZIP_ENTRY_COUNT`
- archives exceeding `PROJECTS_MAX_ZIP_UNCOMPRESSED_BYTES`

Extraction is performed entry-by-entry instead of using a blind bulk extract.

### 3) Upload route hardening

Updated `backend/app/api/routes/project.py` to apply the same practical limits to direct file uploads:

- file count cap
- total size cap
- optional extension allowlist

Path normalization still blocks:

- absolute paths
- drive-prefixed paths
- `.` / `..` / empty path segments

### 4) Operational docs

Updated:

- `backend/.env.example`
- `backend/README.md`

## Outcome

Part 11 is complete:

- local and ZIP ingestion are hardened against unsafe content and traversal
- upload limits are explicit and configurable
- normalized ingestion metadata remains intact for downstream analysis
