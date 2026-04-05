# Backend Migration Map (Part 3)

Date: 2026-04-06
Status: Completed
Scope: FastAPI backend endpoint/service/schema/module surface mapped to target stack contract.

## 1) FastAPI Endpoint-to-Router Map

Application wiring:

- App entry: backend/app/main.py
- API prefix: /api (from backend/app/core/config.py)
- Project router mounted separately at /project in backend/app/main.py

Router composition:

- backend/app/api/router.py includes:
  - /api/achievements
  - /api/auth
  - /api/health
  - /api/github
  - /api/lessons
  - /api/ai
  - /api/learning-paths
  - /api/parsing
  - /api/tokens
  - /api/dependency-graph
  - /api/call-graph
  - /api/graph-analysis

Endpoint inventory:

### AI and analysis

- POST /api/ai/explain-code -> backend/app/api/routes/ai_explanation.py
- GET /api/ai/explain-code -> backend/app/api/routes/ai_explanation.py
- POST /api/ai/project-summaries -> backend/app/api/routes/ai_explanation.py
- POST /api/ai/quality-analysis -> backend/app/api/routes/ai_explanation.py
- POST /api/ai/risk-scoring -> backend/app/api/routes/ai_explanation.py
- POST /api/ai/explainability-traces -> backend/app/api/routes/ai_explanation.py

### Graph and parsing

- POST /api/parsing/ast-preview -> backend/app/api/routes/parsing.py
- POST /api/parsing/ast-structure -> backend/app/api/routes/parsing.py
- POST /api/tokens/preview -> backend/app/api/routes/tokens.py
- POST /api/dependency-graph/from-path -> backend/app/api/routes/dependency_graph.py
- POST /api/call-graph/from-path -> backend/app/api/routes/call_graph.py
- POST /api/graph-analysis/from-path -> backend/app/api/routes/graph_analysis.py

### Repository ingestion and legacy project analysis

- POST /api/github/analyze -> backend/app/api/routes/github_analysis.py
- POST /api/github/analyze-local -> backend/app/api/routes/github_analysis.py
- POST /api/github/analyze-archive -> backend/app/api/routes/github_analysis.py
- POST /project/upload -> backend/app/api/routes/project.py
- POST /project/clone -> backend/app/api/routes/project.py
- GET /project/analyze/{project_name} -> backend/app/api/routes/project.py
- GET /project/code-analysis/{project_name} -> backend/app/api/routes/project.py
- GET /project/graph/{project_name} -> backend/app/api/routes/project.py
- GET /project/graph-full/{project_name} -> backend/app/api/routes/project.py
- GET /project/flow/{project_name} -> backend/app/api/routes/project.py
- GET /project/understand/{project_name} -> backend/app/api/routes/project.py
- GET /project/gaps/{project_name} -> backend/app/api/routes/project.py
- GET /project/risk/{project_name} -> backend/app/api/routes/project.py
- GET /project/priority/{project_name} -> backend/app/api/routes/project.py

### App domain endpoints (auth and learning)

- POST /api/auth/register -> backend/app/api/routes/auth.py
- POST /api/auth/login -> backend/app/api/routes/auth.py
- GET /api/auth/session -> backend/app/api/routes/auth.py
- POST /api/auth/logout -> backend/app/api/routes/auth.py
- GET /api/achievements -> backend/app/api/routes/achievements.py
- GET /api/achievements/user -> backend/app/api/routes/achievements.py
- GET /api/lessons -> backend/app/api/routes/lessons.py
- GET /api/learning-paths -> backend/app/api/routes/learning_paths.py
- POST /api/learning-paths -> backend/app/api/routes/learning_paths.py
- PUT /api/learning-paths -> backend/app/api/routes/learning_paths.py
- DELETE /api/learning-paths -> backend/app/api/routes/learning_paths.py
- GET /api/health -> backend/app/api/routes/health.py
- GET / -> backend/app/main.py (root health/info)

## 2) Service and Engine Module Map

Engine facade modules:

- Parser engine facade:
  - backend/app/engine/parser/ast_parser.py
  - delegates to parser_service + token_service
- Graph engine facade:
  - backend/app/engine/graph_builder/graph_builder.py
  - delegates to call_graph_service, dependency_graph_service, graph_analysis_service
- AI/NLP engine facade:
  - backend/app/engine/ai_nlp/ai_nlp_service.py
  - delegates to ai_explanation, project_summary_service, quality_analysis_service, risk_scoring_service
- Explainability engine facade:
  - backend/app/engine/explanation_engine/explanation_engine.py
  - delegates to explainability_trace_service
- Orchestrator:
  - backend/app/engine/orchestrator.py
  - composes parser, graph, AI/NLP, explainability bundle

Route-to-service style split:

- Engine-first route family:
  - ai_explanation, parsing, tokens, dependency_graph, call_graph, graph_analysis
- Direct service route family:
  - project, github_analysis, auth, achievements, lessons, learning_paths

Database layer modules:

- backend/app/db/connection.py
- backend/app/db/session.py
- backend/app/db/models.py
- backend/app/db/base.py

## 3) Schema Contract Map

Primary request/response schema groups:

- AI explanation:
  - backend/app/schemas/ai_explanation.py
- Project summaries:
  - backend/app/schemas/project_summaries.py
- Quality analysis:
  - backend/app/schemas/quality_analysis.py
- Risk scoring:
  - backend/app/schemas/risk_scoring.py
- Explainability traces:
  - backend/app/schemas/explainability_traces.py
- Parsing and AST structure:
  - backend/app/schemas/parsing.py
- Token extraction:
  - backend/app/schemas/tokens.py
- Dependency graph:
  - backend/app/schemas/dependency_graph.py
- Call graph:
  - backend/app/schemas/call_graph.py
- Graph analysis:
  - backend/app/schemas/graph_analysis.py
- GitHub/local/ZIP repository analysis:
  - backend/app/schemas/github_analysis.py
- Auth/session:
  - backend/app/schemas/auth.py
- Learning paths:
  - backend/app/schemas/learning_path.py
- Common status/error envelopes:
  - backend/app/schemas/common.py

## 4) Gap Analysis vs Final Stack Contract

### Gaps to resolve in upcoming parts

1. Endpoint duplication and overlap
- /api/github/* and /project/* both handle repository analysis workflows.
- Engine-based endpoints and legacy project endpoints overlap in capability.

2. Inconsistent API response style
- Some endpoints use strict pydantic response models.
- Some endpoints return raw dict/list payloads without unified envelope.

3. Architecture split across old and new layers
- Some routes call engine facades; others call legacy service modules directly.
- Migration should converge on one service entry model per domain.

4. Mixed data-access patterns
- Domain endpoints still rely on in-route session handling and ORM query patterns.
- Needs standardized dependency injection and transaction/session pattern.

5. Auth transition gap
- Backend provides /api/auth, but frontend still has Next-side better-auth dependencies.
- Requires contract alignment and token/session handling simplification in migration parts 4-6 and 18.

6. Project endpoint contract shape not fully aligned
- /project/* endpoints mix operational actions (upload/clone) and analysis reads.
- Requires versioned contract and consistent request/response schemas.

7. Database migration consistency gap
- SQLite and PostgreSQL support exists at connection level.
- Need stricter migration policy across all models and Alembic workflows for full parity.

## 5) Part 3 Exit Criteria Check

Delivered:

- Endpoint-to-router map completed.
- Service and engine module map completed.
- Schema contract map completed.
- Backend gap list completed and prioritized.

Part 3 status: Complete.