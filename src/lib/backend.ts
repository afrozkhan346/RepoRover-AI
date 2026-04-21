const viteEnv = typeof import.meta !== "undefined" ? (import.meta as { env?: Record<string, string | undefined> }).env : undefined;
const explicitBackendUrl =
  viteEnv?.VITE_BACKEND_URL ||
  (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_BACKEND_URL);

// In local Vite dev, default to a relative API path so requests flow through the dev proxy.
const resolvedBackendUrl = explicitBackendUrl || (viteEnv?.DEV ? "/api" : "");

export const BACKEND_API_BASE = resolvedBackendUrl.replace(/\/$/, "");

/**
 * Generates the full URL for social login redirects.
 * Prioritizes the backend base URL, falling back to localhost for local development.
 */
export function getSocialLoginUrl(provider: "google" | "github"): string {
  const base = BACKEND_API_BASE || (viteEnv?.DEV ? "http://localhost:8000/api" : "");
  return `${base}/auth/social/${provider}/login`;
}

export type ApiErrorPayload = {
  detail: string;
  code?: string | null;
};

export async function backendFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BACKEND_API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.headers || {}),
      ...(init?.body && !(init.body instanceof FormData)
        ? { "Content-Type": "application/json" }
        : {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let errorPayload: ApiErrorPayload | null = null;
    try {
      errorPayload = (await response.json()) as ApiErrorPayload;
    } catch {
      errorPayload = null;
    }

    const message = errorPayload?.detail || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return (await response.json()) as T;
}

export type ProjectSummariesResponse = {
  project_summary: string;
  architecture_summary: string;
  execution_flow_summary: string;
  key_modules: string[];
  key_dependencies: string[];
  flow_path: string[];
  metrics: {
    total_files: number;
    analyzable_files: number;
    files_scanned: number;
    total_lines: number;
    language_breakdown: Record<string, number>;
    dependency_edges: number;
    call_edges: number;
  };
};

export type QualityAnalysisResponse = {
  overall_score: number;
  issues: Array<{
    severity: string;
    category: string;
    file_path: string | null;
    detail: string;
    recommendation: string;
  }>;
  design_gaps: string[];
  summary: string;
};

export type RiskScoringResponse = {
  reliability_score: number;
  risk_score: number;
  severity_distribution: {
    high: number;
    medium: number;
    low: number;
  };
  top_signals: Array<{
    title: string;
    weight: number;
    detail: string;
  }>;
  summary: string;
};

export type GraphAnalysisResponse = {
  graph_type: string;
  metrics: {
    node_count: number;
    edge_count: number;
    connected_components: number;
  };
  top_degree_centrality: Array<{ node_id: string; label: string; score: number }>;
  top_betweenness_centrality: Array<{ node_id: string; label: string; score: number }>;
  top_impact_rank: Array<{ node_id: string; label: string; score: number }>;
  traversal: { start_node: string | null; bfs_order: string[] };
};

export type ExplainabilityTraceResponse = {
  focus_file: string;
  findings: Array<{
    finding_id: string;
    title: string;
    severity: string;
    evidence_type: string;
    evidence: string;
  }>;
  token_traces: Array<{
    finding_id: string;
    file_path: string;
    token_type: string;
    lexeme: string;
    start_point: [number, number];
    end_point: [number, number];
    evidence?: {
      kind: string;
      excerpt: string;
      start_point: [number, number];
      end_point: [number, number];
      unit_type?: string | null;
      unit_name?: string | null;
    } | null;
  }>;
  ast_traces: Array<{
    finding_id: string;
    file_path: string;
    unit_type: string;
    name: string | null;
    start_point: [number, number];
    end_point: [number, number];
    evidence?: {
      kind: string;
      excerpt: string;
      start_point: [number, number];
      end_point: [number, number];
      unit_type?: string | null;
      unit_name?: string | null;
    } | null;
  }>;
  graph_traces: Array<{
    finding_id: string;
    graph_type: string;
    start_node: string;
    path: string[];
  }>;
  summary: string;
};

export type AIExplanationResponse = {
  explanation: string;
  language: string | null;
  timestamp: string;
  pipeline?: string | null;
  model?: string | null;
  complexity_score?: number | null;
  key_concepts?: string[];
  named_entities?: string[];
  evidence?: Array<{
    kind: string;
    label: string;
    excerpt: string;
    start_point?: [number, number] | null;
    end_point?: [number, number] | null;
    related_symbols?: string[];
    note?: string | null;
  }>;
};

export type ProjectUploadResponse = {
  message: string;
  project_path: string;
  files_saved: number;
  total_size: number;
};

export type ProjectCloneResponse = {
  message: string;
  repo_url: string;
  project_path: string;
};

export type RepositoryTreeNode = {
  name: string;
  type: "file" | "folder";
  path: string;
  icon: string;
  color: string;
  language: string | null;
  size?: number;
  extension?: string;
  children?: RepositoryTreeNode[];
};

export type AnalyzeRepoRequest = {
  local_path: string;
  ignored_dirs?: string[];
  max_nodes?: number;
  max_depth?: number;
  include_errors?: boolean;
};

export type AnalyzeRepoResponse = {
  hierarchy: RepositoryTreeNode;
  truncated: boolean;
  errors: Array<{
    path: string;
    error: string;
  }>;
};

export async function fetchProjectSummaries(localPath: string, maxFiles = 1000) {
  return backendFetch<ProjectSummariesResponse>("/ai/project-summaries", {
    method: "POST",
    body: JSON.stringify({ local_path: localPath, max_files: maxFiles }),
  });
}

export async function fetchQualityAnalysis(localPath: string, maxFiles = 1000) {
  return backendFetch<QualityAnalysisResponse>("/ai/quality-analysis", {
    method: "POST",
    body: JSON.stringify({ local_path: localPath, max_files: maxFiles }),
  });
}

export async function fetchRiskScoring(localPath: string, maxFiles = 1000) {
  return backendFetch<RiskScoringResponse>("/ai/risk-scoring", {
    method: "POST",
    body: JSON.stringify({ local_path: localPath, max_files: maxFiles }),
  });
}

export async function fetchGraphAnalysis(localPath: string, graphType = "call", maxFiles = 1000) {
  return backendFetch<GraphAnalysisResponse>("/graph-analysis/from-path", {
    method: "POST",
    body: JSON.stringify({ local_path: localPath, graph_type: graphType, max_files: maxFiles }),
  });
}

export async function fetchExplainabilityTraces(
  localPath: string,
  focusFile?: string,
  graphType = "call",
  maxFiles = 1000,
) {
  return backendFetch<ExplainabilityTraceResponse>("/ai/explainability-traces", {
    method: "POST",
    body: JSON.stringify({
      local_path: localPath,
      focus_file: focusFile,
      graph_type: graphType,
      max_files: maxFiles,
    }),
  });
}

export async function explainCode(code: string, language?: string, question?: string) {
  return backendFetch<AIExplanationResponse>("/ai/explain-code", {
    method: "POST",
    body: JSON.stringify({ code, language, question }),
  });
}

export async function uploadProjectFiles(files: File[]) {
  const formData = new FormData();

  files.forEach((file) => {
    const relativePath = (file as File & { webkitRelativePath?: string }).webkitRelativePath || file.name;
    formData.append("files", file);
    formData.append("relative_paths", relativePath);
  });

  const response = await fetch(`${BACKEND_API_BASE}/project/upload`, {
    method: "POST",
    body: formData,
    cache: "no-store",
  });

  if (!response.ok) {
    let errorPayload: ApiErrorPayload | null = null;
    try {
      errorPayload = (await response.json()) as ApiErrorPayload;
    } catch {
      errorPayload = null;
    }

    const message = errorPayload?.detail || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return (await response.json()) as ProjectUploadResponse;
}

export async function cloneProjectFromGithub(repoUrl: string) {
  const formData = new FormData();
  formData.append("repo_url", repoUrl);

  const response = await fetch(`${BACKEND_API_BASE}/project/clone`, {
    method: "POST",
    body: formData,
    cache: "no-store",
  });

  if (!response.ok) {
    let errorPayload: ApiErrorPayload | null = null;
    try {
      errorPayload = (await response.json()) as ApiErrorPayload;
    } catch {
      errorPayload = null;
    }

    const message = errorPayload?.detail || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return (await response.json()) as ProjectCloneResponse;
}

export async function analyzeRepoStructure(payload: AnalyzeRepoRequest) {
  return backendFetch<AnalyzeRepoResponse>("/analyze-repo", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
