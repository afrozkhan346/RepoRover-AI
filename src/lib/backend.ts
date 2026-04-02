export const BACKEND_API_BASE =
  process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, "") ?? "http://localhost:8000/api";

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
  }>;
  ast_traces: Array<{
    finding_id: string;
    file_path: string;
    unit_type: string;
    name: string | null;
    start_point: [number, number];
    end_point: [number, number];
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
