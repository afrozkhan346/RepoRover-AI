# Project Input System — Feature Coverage

**Features:**

- Supports GitHub projects
- Supports local projects
- Handles multiple formats (folders, ZIPs)
- Normalizes input (path safety, extension allowlist, size/count limits)

**Working:**

- GitHub project ingestion (clone via URL) — working
- Local project ingestion (folder upload) — working
- ZIP project ingestion — working
- Path normalization and safety checks — working
- File count and size limits — working
- Extension allowlist (optional) — working

**Not working / Not found:**

- No support for non-GitHub remote sources (e.g., GitLab, Bitbucket)
- No explicit support for non-code formats (e.g., binary-only projects)
- No user-facing error for unsupported formats (not confirmed)

**Summary:**
All major features for GitHub/local/ZIP input and normalization are implemented and working. Only non-GitHub remote sources and non-code/binary-only projects are not covered.
