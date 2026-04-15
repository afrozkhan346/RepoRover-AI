# 30-Part Migration Plan

Date: 2026-04-03
Based on: [Migration Checklist](MIGRATION_CHECKLIST.md) and [Final Tech Stack](FINAL_TECH_STACK.md)

This plan breaks the full stack migration into 30 equal work items so the next chat can continue from a fixed sequence.

Locked scope reference: [Migration Boundaries](MIGRATION_BOUNDARIES.md).
Frontend inventory: [Frontend Inventory](FRONTEND_INVENTORY.md).
Backend inventory: [Backend Inventory](BACKEND_INVENTORY.md).
Database inventory: [Database Inventory](DATABASE_INVENTORY.md).
Dependency inventory: [Dependency Inventory](DEPENDENCY_INVENTORY.md).
Cleanup inventory: [Cleanup Inventory](CLEANUP_INVENTORY.md).

## Phase 1: Freeze and map current scope

1. Freeze the final target stack and lock the migration boundaries.
2. Catalog every current frontend page and component that must move or stay.
3. Catalog every current API route and backend utility that must move or stay.
4. Catalog every current database file, schema, seed, and migration file.
5. Catalog every current AI, auth, cache, and deployment dependency.
6. Mark all Cloud Run, Next-only, and hackathon-era artifacts for removal.

## Phase 2: Backend conversion foundation

Progress: backend/ scaffold created with FastAPI app, config, router, and health endpoint.

Progress: shared settings now parse environment, debug, log level, optional database URL, and CORS origins.

Progress: GitHub repository analysis FastAPI router, service, and schemas are in place.

Progress: AI explanation FastAPI router, service, and schemas are in place.

Progress: learning paths FastAPI router, service, and schemas are in place.

Progress: shared backend error and success response helpers are in place.

Progress: Python ORM models and the initial SQL migration scaffold are in place.

Progress: SQLite is now the default backend database target with startup table creation.

Progress: PostgreSQL migration path and shared connection layer are in place.

Progress: GitPython-based repository loading service is in place.

Progress: local folder ingestion endpoint and loader support are in place.

Progress: ZIP archive ingestion and secure extraction support are in place.

Progress: Tree-sitter parsing service and normalized AST preview endpoint are in place.

Progress: token-level lexical extraction endpoint and normalization are in place.

Progress: AST structure extraction endpoint with syntax-unit summaries is in place.

Progress: dependency graph generation from imports and package metadata is in place.

Progress: call graph generation endpoint with intra-file and import-context relationships is in place.

Progress: NetworkX graph analytics endpoint with centrality, impact ranking, and traversal is in place.

Progress: AI explanation pipeline now uses PyTorch, HuggingFace, and spaCy with deterministic fallback.

Progress: project summary, architecture summary, and execution-flow summary endpoint is in place.

Progress: code-quality and design-gap analysis endpoint with structured findings is in place.

Progress: risk and reliability scoring endpoint with severity distribution is in place.

Progress: explainability traces endpoint now links findings to token, AST, and graph-path evidence.

Progress: React frontend now consumes FastAPI outputs through the analyzer, dashboard, home page, and AI tutor views with Chart.js and Mermaid.

1. Create the FastAPI project skeleton and base application layout.
2. Define shared settings, environment loading, and configuration structure in Python. ✅
3. Add the first FastAPI router for GitHub repository analysis. ✅
4. Add the first FastAPI router for AI explanation requests. ✅
5. Add the first FastAPI router for learning path data. ✅
6. Establish response models and error handling conventions for the backend. ✅

## Phase 3: Data and repository handling

1. Replace the current TypeScript data layer with Python models and migrations. ✅
2. Set up SQLite as the initial database target. ✅
3. Design the PostgreSQL migration path and connection layer. ✅
4. Implement GitPython-based repository loading for GitHub URLs. ✅
5. Implement local folder ingestion for uploaded or selected projects. ✅
6. Implement zip archive ingestion and extraction for project imports. ✅

## Phase 4: Parsing and graph intelligence

1. Integrate Tree-sitter and normalize parser output across languages. ✅
2. Add token-level extraction for lexical understanding. ✅
3. Add AST-level extraction for syntax and structure understanding. ✅
4. Build dependency graph generation from imports and package metadata. ✅
5. Build call graph generation from intra-file and inter-file relationships. ✅
6. Add NetworkX analysis for centrality, traversal, and impact ranking. ✅

## Phase 5: AI, explanation, and analysis

1. Move AI/NLP pipelines to Python with PyTorch, HuggingFace, and spaCy. ✅
2. Add project summary, architecture summary, and execution-flow explanation generation. ✅
3. Add code-quality and design-gap detection outputs. ✅
4. Add risk, reliability, and severity scoring outputs. ✅
5. Add explainability traces that tie findings back to tokens, AST nodes, and graph paths. ✅
6. Rebuild the React frontend and visualization layer to consume FastAPI outputs with Chart.js and Mermaid. ✅

## Next Chat Entry Rule

When the user starts the next chat, resume at the first unfinished item in this list and continue in order.
