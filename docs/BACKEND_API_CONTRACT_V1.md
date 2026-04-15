# Backend API Contract v1 (Part 6)

Date: 2026-04-06
Status: In Progress (revalidated incrementally through 2026-04-07)
Scope: Canonical contract for frontend-facing backend features (auth, repositories, analysis, learning, achievements, profile) with normalized request/response and error format.

Progress Note:

- This contract is being validated route-by-route in small slices.
- Sections already revalidated include auth, learning paths, lessons, achievements, GitHub analysis, parsing, tokens, dependency graph, call graph, graph analysis, and project ingest/analyze slices.

## 1) Contract Principles

- Base API URL: `/api`
- Project operations URL: `/project`
- Auth transport: `Authorization: Bearer <token>`
- Content types:
  - JSON endpoints: `application/json`
  - Upload/clone endpoints: `multipart/form-data`
- Contract convention:
  - Request fields: `snake_case`
  - Response fields: preserve current schema field names; new fields should remain `snake_case`

## 2) Error Envelope v1

Current backend behavior already returns FastAPI HTTP errors shaped as:

```json
{
  "detail": {
    "detail": "Human readable message",
    "code": "MACHINE_CODE"
  }
}
```

or, for some endpoints:

```json
{
  "detail": "Human readable message"
}
```

v1 normalization rule (target for Part 7 implementation):

```json
{
  "detail": "Human readable message",
  "code": "MACHINE_CODE"
}
```

Status code rules:

- `400`: invalid input or malformed payload
- `401`: missing/invalid auth
- `404`: resource not found
- `409`: conflict (for example existing user)
- `422`: schema validation error (FastAPI)
- `500/502`: backend or upstream failure

## 3) Endpoint Contract Matrix

### 3.1 Auth

1. `POST /api/auth/register`
   - Auth: none
   - Request:
     - `name: string` (min 1)
     - `email: string` (email)
     - `password: string` (min 8)
   - Response: `AuthSessionResponse`
     - `token: string`
     - `user: { id, name, email, email_verified, image, created_at, updated_at }`
   - Errors: `409 USER_ALREADY_EXISTS`, `400`

2. `POST /api/auth/login`
   - Auth: none
   - Request:
     - `email: string`
     - `password: string`
   - Response: `AuthSessionResponse`
   - Errors: `401 INVALID_CREDENTIALS`

3. `GET /api/auth/session`
   - Auth: optional bearer
   - Request: header only
   - Response: `SessionResponse`
     - `token: string | null`
     - `user: AuthUser | null`

4. `POST /api/auth/logout`
   - Auth: optional bearer
   - Response:
     - `message: "Signed out"`

### 3.2 Repository Ingestion and Analysis

1. `POST /project/upload`
   - Auth: none
   - Request: `multipart/form-data`
     - `files[]: UploadFile` (required)
     - `relative_paths[]: string[]` (optional, one per file)
   - Response:
     - `message: string`
     - `project_path: string`
     - `files_saved: number`
     - `total_size: number`
   - Errors:
     - `400 MISSING_FILE | PATH_MISMATCH | INVALID_PATH | UNSAFE_PATH | TOO_MANY_FILES | PROJECT_TOO_LARGE | UNSUPPORTED_FILE_EXTENSION | EMPTY_UPLOAD`

2. `POST /project/clone`
   - Auth: none
   - Request: `multipart/form-data`
     - `repo_url: string`
   - Response:
     - `message: string`
     - `repo_url: string`
     - `project_path: string`
     - `ingestion: { operation, workspace_path, workspace_policy, cleaned_entries, fetched_updates }`
   - Errors:
     - `400 MISSING_REPO_URL | CLONE_FAILED | <repository_loader_code>`

3. `GET /project/analyze/{project_name}`
   - Response: parser summary payload from `parse_project(...)`
     - `language: string`
     - `total_files: int`
     - `total_files_scanned: int`
     - `files[]: [{ name, path, extension }]`
   - Errors:
     - `400 INVALID_PROJECT | PARSE_FAILED`
     - `404 PROJECT_NOT_FOUND`

4. `GET /project/code-analysis/{project_name}`
   - Response: `list[dict]` code-analysis output
     - each item: `{ file, path, language, data }`
     - `data.normalized_ast` includes `language, total_nodes, truncated, preview_nodes[], tree_nodes_returned, root, imports[], classes[], functions[], calls[]`
   - Errors:
     - `400 INVALID_PROJECT | CODE_ANALYSIS_FAILED`
     - `404 PROJECT_NOT_FOUND`

5. `GET /project/graph/{project_name}`
   - Response: graph summary + `graph` object
     - summary keys: `total_nodes, total_edges, call_edges, contains_edges, import_edges`
     - `graph: { root, nodes[], edges[], summary }`
   - Errors:
     - `400 INVALID_PROJECT | GRAPH_BUILD_FAILED`
     - `404 PROJECT_NOT_FOUND`

6. `GET /project/graph-full/{project_name}`
   - Response:
     - `nodes: [{id, data:{label}}]`
     - `edges: [{id, source, target, label}]`
   - Errors:
     - `400 INVALID_PROJECT | GRAPH_BUILD_FAILED`
     - `404 PROJECT_NOT_FOUND`

7. `GET /project/flow/{project_name}`
   - Response:
     - `execution_flow: string[]`
   - Errors:
     - `400 INVALID_PROJECT | FLOW_BUILD_FAILED`
     - `404 PROJECT_NOT_FOUND`

8. `GET /project/understand/{project_name}`
   - Response: project understanding payload (`dict`)
   - Errors:
     - `400 INVALID_PROJECT | UNDERSTAND_FAILED`
     - `404 PROJECT_NOT_FOUND`

9. `GET /project/gaps/{project_name}`
   - Response:
     - `gaps: [{file, issue, severity}]`
   - Errors:
     - `400 INVALID_PROJECT | GAP_ANALYSIS_FAILED`
     - `404 PROJECT_NOT_FOUND`

10. `GET /project/risk/{project_name}`

- Response:
  - `risks: [{file|node, risk, score}]`
- Errors:
  - `400 INVALID_PROJECT | RISK_ANALYSIS_FAILED`
  - `404 PROJECT_NOT_FOUND`

1. `GET /project/priority/{project_name}`

- Response:
  - `top_risks: [{file, risk, score}]`
  - `important_functions: [[string, number]]`
- Errors:
  - `400 INVALID_PROJECT | PRIORITY_ANALYSIS_FAILED`
  - `404 PROJECT_NOT_FOUND`

1. `POST /api/github/analyze`

- Auth: none
- Request:
  - `github_url: string`
- Response: `GitHubAnalysisResponse`
  - Repository metadata + language stats + file structure + recent commits + ingestion metadata
- Errors:
  - `400 INVALID_INPUT | <repository_loader_code>`
  - `502 GITHUB_API_ERROR`

1. `POST /api/github/analyze-local`

- Auth: none
- Request:
  - `local_path: string`
- Response: `GitHubAnalysisResponse`
- Errors:
  - `400 INVALID_LOCAL_PATH | <repository_loader_code>`
  - `500 LOCAL_ANALYSIS_ERROR`

1. `POST /api/github/analyze-archive`

- Auth: none
- Request: `multipart/form-data`
  - `file: UploadFile` (`.zip` required)
- Response: `GitHubAnalysisResponse`
- Errors:
  - `400 INVALID_ARCHIVE | <repository_loader_code>`
  - `500 ARCHIVE_ANALYSIS_ERROR`

### 3.3 AI and Explainability

1. `POST /api/ai/explain-code`
   - Request:
     - `code: string` (required, min length 1)
     - `language?: string`
     - `question?: string`
   - Response:
     - `explanation, language, timestamp, pipeline?, model?, complexity_score?, key_concepts[], named_entities[], evidence[]`
     - `evidence[]` entries: `{ kind, label, excerpt, start_point?, end_point?, related_symbols[], note? }`
   - Errors: `400 MISSING_CODE`

2. `GET /api/ai/explain-code`
   - Response: health payload in `AIExplanationResponse` shape
     - `pipeline: "health-check"`
     - `model: null`
     - `complexity_score: null`
     - `key_concepts: []`
     - `named_entities: []`
     - `evidence: []`

3. `POST /api/ai/project-summaries`
   - Request: `{ local_path, max_files }`
   - Response: `ProjectSummariesResponse`
     - `project_summary, architecture_summary, execution_flow_summary`
     - `key_modules[], key_dependencies[], flow_path[]`
     - `metrics: { files_scanned, total_lines, language_breakdown, dependency_edges, call_edges }`

4. `POST /api/ai/quality-analysis`
   - Request: `{ local_path, max_files }`
   - Response: `QualityAnalysisResponse`
     - `overall_score, issues[], design_gaps[], summary`

5. `POST /api/ai/risk-scoring`
   - Request: `{ local_path, max_files }`
   - Response: `RiskScoringResponse`
     - `reliability_score, risk_score`
     - `severity_distribution: {high, medium, low}`
     - `top_signals[]`
     - `summary`

6. `POST /api/ai/explainability-traces`
   - Request: `{ local_path, max_files, focus_file?, graph_type }`
   - Response: `ExplainabilityTraceResponse`
     - `focus_file`
     - `findings[]`
     - `token_traces[]`
     - `ast_traces[]`
     - `graph_traces[]`
     - `summary`

### 3.4 Graph/Parser Utility Endpoints

1. `POST /api/parsing/ast-preview`
   - Request: `ParseRequest`
     - `source_code: string` (required, min length 1)
     - `language?: string`
     - `file_extension?: string`
     - `max_nodes: int = 200` (range `10..2000`)
   - Response: `ParseResponse`
     - `language, total_nodes, truncated, nodes[]`
   - Errors:
     - `400 PARSER_ERROR`

2. `POST /api/parsing/ast-structure`
   - Request: `AstStructureRequest`
     - `source_code: string` (required, min length 1)
     - `language?: string`
     - `file_extension?: string`
     - `max_nodes: int = 200` (range `10..2000`)
     - `max_tree_nodes: int = 300` (range `20..5000`)
     - `max_depth: int = 6` (range `1..20`)
   - Response: `AstStructureResponse`
     - `language, total_nodes, tree_nodes_returned, truncated, root, imports[], classes[], functions[]`
   - Errors:
     - `400 PARSER_ERROR`

3. `POST /api/tokens/preview`
   - Request: `TokenizeRequest`
     - `source_code: string` (required, min length 1)
     - `language?: string`
     - `file_extension?: string`
     - `max_tokens: int = 500` (range `20..5000`)
   - Response: `TokenizeResponse`
     - `language, total_tokens, truncated, tokens[]`
   - Errors:
     - `400 TOKENIZER_ERROR`

4. `POST /api/dependency-graph/from-path`
   - Request: `DependencyGraphRequest`
     - `local_path: string` (required, min length 1)
     - `max_files: int = 2000` (range `10..20000`)
   - Response: `DependencyGraphResponse`
     - `root, nodes[], edges[], summary`
     - `summary: { files_scanned, import_edges, package_nodes, total_nodes, total_edges }`
   - Errors:
     - `400 DEPENDENCY_GRAPH_ERROR`

5. `POST /api/call-graph/from-path`
   - Request: `CallGraphRequest`
     - `local_path: string` (required, min length 1)
     - `max_files: int = 2000` (range `10..20000`)
   - Response: `CallGraphResponse`
     - `root, nodes[], edges[], summary, analytics?`
     - `summary: { files_scanned, functions_found, call_edges, import_context_edges, total_nodes, total_edges }`
     - `analytics: { top_degree_centrality[], top_betweenness_centrality[], top_impact_rank[], strongly_connected_components, cycle_count }`
   - Errors:
     - `400 CALL_GRAPH_ERROR`

6. `POST /api/graph-analysis/from-path`
   - Request: `GraphAnalysisRequest`
     - `local_path: string` (required, min length 1)
     - `graph_type: string = "dependency"` (`dependency|call`)
     - `max_files: int = 2000` (range `10..20000`)
     - `traversal_start?: string`
   - Response: `GraphAnalysisResponse`
     - `graph_type, metrics, top_degree_centrality[], top_betweenness_centrality[], top_impact_rank[], traversal`
     - `metrics: { node_count, edge_count, connected_components }`
     - `traversal: { start_node, dfs_order[], bfs_order[] }`
   - Errors:
     - `400 GRAPH_ANALYSIS_ERROR`

### 3.5 Learning, Achievements, Profile Inputs

1. `GET /api/learning-paths`
   - Query:
     - `id?: int`
     - `search?: string`
     - `difficulty?: string`
     - `limit: int = 10` (range `1..100`)
     - `offset: int = 0` (min `0`)
     - `sort: string = "orderIndex"` (`createdAt|title|difficulty|estimatedHours|orderIndex`)
     - `order: string = "asc"` (`asc|desc`)
   - Behavior:
     - If `id` is provided and exists: returns one `LearningPath` object.
     - If `id` is provided and missing: returns `404` with code `NOT_FOUND`.
     - If `id` is omitted: returns paginated list filtered by `search` and `difficulty`, then sorted.
   - Response `LearningPath` fields:
     - `id, title, description, difficulty, estimated_hours, icon, order_index, created_at`

2. `POST /api/learning-paths`
   - Request: `LearningPathCreate`
   - Response: `201` + `LearningPath`
   - Required payload fields:
     - `title, difficulty, estimated_hours, order_index`

3. `PUT /api/learning-paths?id={id}`
   - Query:
     - `id: int` (required, `>= 1`)
   - Request: `LearningPathUpdate`
   - Response: `LearningPath`
   - Errors: `404 NOT_FOUND`

4. `DELETE /api/learning-paths?id={id}`
   - Query:
     - `id: int` (required, `>= 1`)
   - Response: `204 No Content`
   - Errors: `404 NOT_FOUND`

5. `GET /api/lessons`
   - Query:
     - `id?: int`
     - `learningPathId?: int`
   - Behavior:
     - If `id` is provided and exists: returns one lesson object.
     - If `id` is provided and missing: returns `404` with code `NOT_FOUND`.
     - If `id` is omitted: returns a list of lessons, optionally filtered by `learningPathId`.
   - Response lesson fields:
     - `id, learning_path_id, title, description, content, difficulty, xp_reward, estimated_minutes, order_index, created_at`

6. `GET /api/achievements`
   - Response:
     - `achievements: [{id, title, description, icon, xp_reward, requirement}]`
   - Notes:
     - `requirement` is returned as a formatted string: `<requirement_type>: <requirement_value>`.

7. `GET /api/achievements/user`
   - Auth: required bearer token in `Authorization` header
   - Response:
     - `achievements: [{id, user_id, achievement_id, earned_at, created_at}]`
   - Errors:
     - `401 UNAUTHORIZED` when bearer token is missing or invalid.

8. Profile contract v1
   - No dedicated profile endpoint exists yet.
   - Current frontend derives profile stats from:
     - `GET /api/auth/session`
     - `GET /api/achievements`
     - `GET /api/achievements/user`
   - v1 recommendation: add `GET /api/profile` in Part 7 or Part 18 to avoid client-side stat synthesis.

## 4) Frontend Consumer Mapping (One-to-One)

### Already aligned

- Analyzer bundle in `src/lib/backend.ts`
  - `/api/ai/project-summaries`
  - `/api/ai/quality-analysis`
  - `/api/ai/risk-scoring`
  - `/api/graph-analysis/from-path`
  - `/api/ai/explainability-traces`
- AI tutor
  - `/api/ai/explain-code`
- Project ingest
  - `/project/upload`
  - `/project/clone`

### Auth and user-facing pages

- Login/Register/Session
  - `/api/auth/register`
  - `/api/auth/login`
  - `/api/auth/session`
  - `/api/auth/logout`
- Achievements page
  - `/api/achievements`
  - `/api/achievements/user`
- Profile page
  - `/api/auth/session`
  - `/api/achievements`
  - `/api/achievements/user`

### Remaining direct call to normalize

- `src/app/analyze/page-client.tsx` still calls:
  - `GET http://127.0.0.1:8000/project/code-analysis/{project_name}`
- v1 mapping action:
  - Replace with helper using `BACKEND_ROOT_BASE` and shared error parser from `src/lib/backend.ts`.

## 5) Part 6 Exit Criteria Check

Delivered:

- Canonical API contract doc for auth, repositories, analysis, learning, achievements, and profile.
- Method/path/request/response/error behavior documented per endpoint family.
- Normalized error envelope and status-code policy specified for implementation.
- Frontend endpoint mapping notes provided for one-to-one replacement alignment.

Part 6 status: In Progress (route-by-route revalidation active).
