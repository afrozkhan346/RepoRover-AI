export type AnalysisSectionId =
  | "workspace"
  | "backend-signals"
  | "explainability-coverage"
  | "file-tree"
  | "used-languages"
  | "repo-summary"
  | "code-explanation"
  | "risks"
  | "priority"
  | "repository-footprint"
  | "severity-mix"
  | "graph-impact-ranking"
  | "evidence-mix"
  | "backend-summaries"
  | "flow-path";

const ANALYZE_MINIMAL_SECTIONS = new Set<AnalysisSectionId>([
  "workspace",
  "backend-signals",
  "explainability-coverage",
  "file-tree",
  "used-languages",
  "repo-summary",
  "code-explanation",
]);

const DASHBOARD_SECTIONS = new Set<AnalysisSectionId>([
  "used-languages",
  "risks",
  "priority",
  "repository-footprint",
  "severity-mix",
  "graph-impact-ranking",
  "evidence-mix",
  "backend-summaries",
  "flow-path",
]);

export function canRenderOnAnalyze(section: AnalysisSectionId): boolean {
  return ANALYZE_MINIMAL_SECTIONS.has(section);
}

export function canRenderOnDashboard(section: AnalysisSectionId): boolean {
  return DASHBOARD_SECTIONS.has(section);
}

