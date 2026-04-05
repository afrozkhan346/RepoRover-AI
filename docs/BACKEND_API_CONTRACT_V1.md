# Backend API Contract v1 (Part 6)

Date: 2026-04-06
Status: Completed
Scope: Canonical contract for frontend-facing backend features (auth, repositories, analysis, learning, achievements, profile) with normalized request/response and error format.

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
   - Request: multipart
     - `files[]`
     - `relative_paths[]` (optional, one per file)
   - Response:
     - `message: string`
     - `project_path: string`
     - `files_saved: number`
     - `total_size: number`
   - Errors: `400 MISSING_FILE | PATH_MISMATCH | UNSAFE_PATH | EMPTY_UPLOAD`

2. `POST /project/clone`
   - Auth: none
   - Request: multipart/form field
     - `repo_url: string`
   - Response:
     - `message: string`
     - `repo_url: string`
     - `project_path: string`
   - Errors: `400 MISSING_REPO_URL | CLONE_FAILED`

3. `GET /project/analyze/{project_name}`
   - Response: parser summary payload from `parse_project(...)`
   - Errors: `400 INVALID_PROJECT | PARSE_FAILED`, `404 PROJECT_NOT_FOUND`

4. `GET /project/code-analysis/{project_name}`
   - Response: `list[dict]` code-analysis output
   - Errors: `400 INVALID_PROJECT | CODE_ANALYSIS_FAILED`, `404 PROJECT_NOT_FOUND`

5. `GET /project/graph/{project_name}`
   - Response: graph summary + `graph` object
   - Errors: `400 GRAPH_BUILD_FAILED`, `404 PROJECT_NOT_FOUND`

6. `GET /project/graph-full/{project_name}`
   - Response:
     - `nodes: [{id, data:{label}}]`
     - `edges: [{id, source, target, label}]`

7. `GET /project/flow/{project_name}`
   - Response:
     - `execution_flow: string[]`

8. `GET /project/understand/{project_name}`
   - Response: project understanding payload

9. `GET /project/gaps/{project_name}`
   - Response:
     - `gaps: [{file, issue, severity}]`

10. `GET /project/risk/{project_name}`
   - Response:
     - `risks: [{file|node, risk, score}]`

11. `GET /project/priority/{project_name}`
   - Response:
     - `top_risks: [{file, risk, score}]`
     - `important_functions: [[string, number]]`

### 3.3 AI and Explainability

1. `POST /api/ai/explain-code`
   - Request:
     - `code: string`
     - `language?: string`
     - `question?: string`
   - Response:
     - `explanation, language, timestamp, pipeline?, model?, complexity_score?, key_concepts[]`
   - Errors: `400 MISSING_CODE`

2. `GET /api/ai/explain-code`
   - Response: health payload in `AIExplanationResponse` shape

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
   - Response: `ParseResponse`

2. `POST /api/parsing/ast-structure`
   - Request: `AstStructureRequest`
   - Response: `AstStructureResponse`

3. `POST /api/tokens/preview`
   - Request: `TokenizeRequest`
   - Response: `TokenizeResponse`

4. `POST /api/dependency-graph/from-path`
   - Request: `{ local_path, max_files }`
   - Response: `DependencyGraphResponse`

5. `POST /api/call-graph/from-path`
   - Request: `{ local_path, max_files }`
   - Response: `CallGraphResponse`

6. `POST /api/graph-analysis/from-path`
   - Request: `{ local_path, graph_type, max_files, traversal_start? }`
   - Response: `GraphAnalysisResponse`

### 3.5 Learning, Achievements, Profile Inputs

1. `GET /api/learning-paths`
   - Query:
     - `id?`, `search?`, `difficulty?`, `limit?`, `offset?`, `sort?`, `order?`
   - Response:
     - `LearningPath[]` or `LearningPath` (if `id` provided)

2. `POST /api/learning-paths`
   - Request: `LearningPathCreate`
   - Response: `LearningPath`

3. `PUT /api/learning-paths?id={id}`
   - Request: `LearningPathUpdate`
   - Response: `LearningPath`

4. `DELETE /api/learning-paths?id={id}`
   - Response: `204 No Content`

5. `GET /api/lessons`
   - Query:
     - `id?`, `learningPathId?`
   - Response:
     - list of lessons or one lesson object

6. `GET /api/achievements`
   - Response:
     - `achievements: [{id, title, description, icon, xp_reward, requirement}]`

7. `GET /api/achievements/user`
   - Auth: required
   - Response:
     - `achievements: [{id, user_id, achievement_id, earned_at, created_at}]`

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

Part 6 status: Complete.
