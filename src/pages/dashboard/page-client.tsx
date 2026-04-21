
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Navigation } from "@/components/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MermaidDiagram } from "@/components/analysis/mermaid-diagram";
import { MetricBarCard, SeverityDoughnutCard } from "@/components/analysis/metric-charts";
import { canRenderOnDashboard } from "@/lib/analysis-sections";
import { useSession } from "@/lib/auth-client";
import { clearInMemoryAnalysisBundle, getInMemoryAnalysisBundle } from "@/lib/analysis-memory";
import { analyzeRepoStructure, type AnalyzeRepoResponse, type RepositoryTreeNode } from "@/lib/backend";
import { Activity, ArrowRight, FileText, Folder, GitBranch, LayoutDashboard, Loader2, Sparkles, TriangleAlert, Check } from "lucide-react";

type SavedBundle = any;

type VisualTreeLine = {
  prefix: string;
  branch: string;
  node: RepositoryTreeNode;
};

const STORAGE_KEY_PREFIX = "Reponium:last-analysis";

function buildMermaidDefinition(flowPath: string[]) {
  if (!flowPath.length) {
    return "flowchart LR\n  A[No analysis saved yet]";
  }

  const nodes = flowPath.map((label, index) => `  N${index}["${label.replace(/"/g, "'")}"]`).join("\n");
  const edges = flowPath.slice(0, -1).map((_, index) => `  N${index} --> N${index + 1}`).join("\n");
  return `flowchart LR\n${nodes}\n${edges}`;
}

function sortTree(node: RepositoryTreeNode): RepositoryTreeNode {
  if (node.type === "file") {
    return node;
  }

  const children = [...(node.children || [])]
    .sort((left, right) => {
      if (left.type !== right.type) {
        return left.type === "folder" ? -1 : 1;
      }
      return left.name.localeCompare(right.name);
    })
    .map((child) => sortTree(child));

  return { ...node, children };
}

function normalizeTreeNode(value: unknown): RepositoryTreeNode | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const raw = value as Record<string, unknown>;
  const type = raw.type === "file" ? "file" : raw.type === "folder" ? "folder" : null;
  if (!type) {
    return null;
  }

  const name = typeof raw.name === "string" && raw.name.trim() ? raw.name : "repo";
  const path = typeof raw.path === "string" && raw.path.trim() ? raw.path : ".";

  if (type === "file") {
    return {
      name,
      type,
      path,
      size: typeof raw.size === "number" ? raw.size : undefined,
      extension: typeof raw.extension === "string" ? raw.extension : undefined,
    };
  }

  const childrenSource = Array.isArray(raw.children) ? raw.children : [];
  const children = childrenSource
    .map((child) => normalizeTreeNode(child))
    .filter((child): child is RepositoryTreeNode => Boolean(child));

  return {
    name,
    type,
    path,
    children,
  };
}

function buildTreeFromPaths(paths: string[], rootName = "repo"): RepositoryTreeNode {
  const root: RepositoryTreeNode = {
    name: rootName,
    type: "folder",
    path: ".",
    children: [],
  };

  for (const rawPath of paths) {
    const normalized = rawPath.replace(/\\/g, "/").replace(/^\/+|\/+$/g, "");
    if (!normalized) {
      continue;
    }

    const parts = normalized.split("/").filter(Boolean);
    let cursor = root;

    for (let index = 0; index < parts.length; index += 1) {
      const part = parts[index];
      const isLeaf = index === parts.length - 1;
      const currentPath = parts.slice(0, index + 1).join("/");

      if (isLeaf) {
        const existingFile = (cursor.children || []).find(
          (child) => child.type === "file" && child.name === part,
        );
        if (!existingFile) {
          cursor.children?.push({
            name: part,
            type: "file",
            path: currentPath,
            extension: part.includes(".") ? `.${part.split(".").pop()?.toLowerCase()}` : "",
          });
        }
        continue;
      }

      let nextFolder = (cursor.children || []).find(
        (child) => child.type === "folder" && child.name === part,
      );

      if (!nextFolder) {
        nextFolder = {
          name: part,
          type: "folder",
          path: currentPath,
          children: [],
        };
        cursor.children?.push(nextFolder);
      }

      cursor = nextFolder;
    }
  }

  return sortTree(root);
}

function collectVisualTreeLines(root: RepositoryTreeNode): VisualTreeLine[] {
  const lines: VisualTreeLine[] = [{ prefix: "", branch: "", node: root }];

  const walk = (node: RepositoryTreeNode, prefix: string) => {
    if (node.type !== "folder") {
      return;
    }

    const children = node.children || [];
    children.forEach((child, index) => {
      const isLast = index === children.length - 1;
      const branch = isLast ? "└── " : "├── ";
      lines.push({ prefix, branch, node: child });
      const childPrefix = `${prefix}${isLast ? "    " : "│   "}`;
      walk(child, childPrefix);
    });
  };

  walk(root, "");
  return lines;
}

function collectFilePathEvidence(bundle: SavedBundle): string[] {
  const filePaths = new Set<string>();

  for (const trace of bundle?.traces?.token_traces || []) {
    if (trace?.file_path) {
      filePaths.add(trace.file_path);
    }
  }

  for (const trace of bundle?.traces?.ast_traces || []) {
    if (trace?.file_path) {
      filePaths.add(trace.file_path);
    }
  }

  for (const issue of bundle?.quality?.issues || []) {
    if (issue?.file_path) {
      filePaths.add(issue.file_path);
    }
  }

  if (bundle?.traces?.focus_file) {
    filePaths.add(bundle.traces.focus_file);
  }

  return Array.from(filePaths).sort((left, right) => left.localeCompare(right));
}

export default function DashboardPageClient() {
  const { data: session, isPending: isSessionPending } = useSession();
  const [bundle, setBundle] = useState<SavedBundle | null>(null);
  const [repoTreeResponse, setRepoTreeResponse] = useState<AnalyzeRepoResponse | null>(null);
  const [isTreeLoading, setIsTreeLoading] = useState(false);
  const [treeError, setTreeError] = useState<string | null>(null);

  const storageKey = useMemo(() => {
    const userId = session?.user?.id;
    return userId ? `${STORAGE_KEY_PREFIX}:${userId}` : null;
  }, [session?.user?.id]);

  useEffect(() => {
    if (isSessionPending) {
      return;
    }

    if (!storageKey) {
      setBundle(getInMemoryAnalysisBundle<SavedBundle>());
      window.localStorage.removeItem(STORAGE_KEY_PREFIX);
      return;
    }

    const saved = window.localStorage.getItem(storageKey);
    if (!saved) {
      setBundle(getInMemoryAnalysisBundle<SavedBundle>());
      return;
    }

    try {
      setBundle(JSON.parse(saved));
    } catch {
      window.localStorage.removeItem(storageKey);
      clearInMemoryAnalysisBundle();
      setBundle(null);
    }
  }, [isSessionPending, storageKey]);

  useEffect(() => {
    const localPath = bundle?.localPath;
    if (!localPath) {
      setRepoTreeResponse(null);
      setTreeError(null);
      setIsTreeLoading(false);
      return;
    }

    let cancelled = false;
    setIsTreeLoading(true);
    setTreeError(null);

    analyzeRepoStructure({
      local_path: localPath,
      max_nodes: 200_000,
      include_errors: true,
    })
      .then((response) => {
        if (!cancelled) {
          setRepoTreeResponse(response);
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message = error instanceof Error ? error.message : "Failed to load repository tree";
          setTreeError(message);
          setRepoTreeResponse(null);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsTreeLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [bundle?.localPath]);

  const summaryPoints = useMemo(() => {
    if (!bundle?.project?.project_summary) return [];
    return bundle.project.project_summary
      .split("\n")
      .map((line: string) => line.trim().replace(/^([-*•]|\d+\.)\s*/, ""))
      .filter((line: string) => line.length > 0);
  }, [bundle?.project?.project_summary]);

  const mermaidDefinition = useMemo(
    () => buildMermaidDefinition(bundle?.project?.flow_path || bundle?.graph?.traversal?.bfs_order || []),
    [bundle],
  );

  const graphImpactNodes = useMemo(
    () => (bundle?.graph?.top_impact_rank || []).slice(0, 5),
    [bundle],
  );
  const prioritizedSignals = useMemo(
    () =>
      [...(bundle?.risk?.top_signals || [])]
        .sort((left: any, right: any) => Number(right.weight) - Number(left.weight))
        .slice(0, 6),
    [bundle],
  );

  const evidenceDistribution = useMemo(() => {
    const tokenCount = bundle?.traces?.token_traces?.filter((trace: any) => trace?.evidence?.kind === "token").length ?? 0;
    const astCount = bundle?.traces?.ast_traces?.filter((trace: any) => trace?.evidence?.kind === "ast").length ?? 0;
    const graphCount = bundle?.traces?.graph_traces?.length ?? 0;

    return { tokenCount, astCount, graphCount };
  }, [bundle]);
  const usedLanguages = useMemo(
    () =>
      Object.entries(bundle?.project?.metrics?.language_breakdown || {}).sort(
        (left, right) => Number(right[1]) - Number(left[1]),
      ),
    [bundle],
  );

  const repositoryTree = useMemo(() => {
    const apiTree = repoTreeResponse?.hierarchy;
    if (apiTree) {
      return sortTree(apiTree);
    }

    if (!bundle) {
      return null;
    }

    const directTree = normalizeTreeNode(bundle?.project?.structure);
    if (directTree) {
      return sortTree(directTree);
    }

    const fallbackPaths = collectFilePathEvidence(bundle);
    if (!fallbackPaths.length) {
      return null;
    }

    return buildTreeFromPaths(fallbackPaths, bundle?.project?.project_name || "repo");
  }, [bundle, repoTreeResponse]);

  const visualTreeLines = useMemo(
    () => (repositoryTree ? collectVisualTreeLines(repositoryTree) : []),
    [repositoryTree],
  );

  const isEmpty = !bundle;

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(15,118,110,0.12),_transparent_35%),linear-gradient(180deg,_rgba(2,6,23,0.04),_transparent_40%)]">
      <Navigation />
      <main className="container mx-auto px-4 py-8 lg:py-12 space-y-8">
        <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="space-y-4">
              <Badge className="w-fit gap-2 rounded-full px-3 py-1 text-xs uppercase tracking-[0.2em]">
                <LayoutDashboard className="h-3.5 w-3.5" /> Analysis dashboard
              </Badge>
              <div className="space-y-2">
                <CardTitle className="text-3xl md:text-4xl">Backend results at a glance.</CardTitle>
                <CardDescription className="max-w-2xl text-base">
                  The dashboard reads the last analysis saved by the analyze workspace and turns FastAPI outputs
                  into charts, summary cards, and Mermaid diagrams.
                </CardDescription>
              </div>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-3">
              <Button asChild>
                <Link to="/analyze">Open analyzer <ArrowRight className="ml-2 h-4 w-4" /></Link>
              </Button>
              <Button variant="outline" asChild>
                <Link to="/ai-tutor">Open AI tutor</Link>
              </Button>
            </CardContent>
          </Card>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
            <Card className="border-border/70 bg-card/90 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">Workspace status</CardTitle>
                <CardDescription>Loaded from local storage in the browser.</CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-3 text-sm">
                <StatTile icon={Activity} label="Loaded" value={isEmpty ? "No" : "Yes"} />
                <StatTile icon={GitBranch} label="Graph type" value={bundle?.graph?.graph_type ?? "n/a"} />
                <StatTile icon={TriangleAlert} label="Risk" value={bundle?.risk?.risk_score ?? 0} />
                <StatTile icon={Sparkles} label="Reliability" value={bundle?.risk?.reliability_score ?? 0} />
              </CardContent>
            </Card>
            {canRenderOnDashboard("used-languages") ? (
              <Card className="border-border/70 bg-card/90 shadow-sm">
                <CardHeader>
                  <CardTitle className="text-base">Used languages</CardTitle>
                  <CardDescription>Languages detected from the last saved analysis.</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-wrap gap-2">
                  {usedLanguages.length ? (
                    usedLanguages.map(([language, count]) => (
                      <Badge key={language} variant="outline">
                        {language} ({String(count)})
                      </Badge>
                    ))
                  ) : (
                    <span className="text-sm text-muted-foreground">No languages detected yet.</span>
                  )}
                </CardContent>
              </Card>
            ) : null}
          </div>
        </section>

        {isEmpty ? (
          <Card className="border-dashed border-border/70 bg-card/70 shadow-none">
            <CardContent className="flex min-h-[260px] flex-col items-center justify-center gap-4 text-center">
              <Sparkles className="h-12 w-12 text-primary" />
              <div className="space-y-2">
                <h2 className="text-2xl font-semibold">No saved analysis yet</h2>
                <p className="max-w-xl text-sm text-muted-foreground">
                  Run the analyzer on a local project path and the resulting FastAPI payload will appear here.
                </p>
              </div>
              <Button asChild>
                <Link to="/analyze">Run analysis now</Link>
              </Button>
            </CardContent>
          </Card>
        ) : (
          <section className="space-y-6">
            {canRenderOnDashboard("priority") ? (
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-1">


                {canRenderOnDashboard("priority") ? (
                  <Card className="border-border/70 bg-card/95 shadow-sm">
                    <CardHeader>
                      <CardTitle>Priority</CardTitle>
                      <CardDescription>Highest-impact risk signals ranked by backend weight.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {prioritizedSignals.length ? (
                        prioritizedSignals.map((signal: any) => (
                          <div key={`${signal.title}-${signal.detail}`} className="rounded-xl border bg-muted/20 p-3 text-sm">
                            <div className="flex items-center justify-between gap-3">
                              <span className="font-semibold text-foreground">{signal.title}</span>
                              <Badge variant="outline">{Number(signal.weight).toFixed(2)}</Badge>
                            </div>
                            <p className="mt-2 text-muted-foreground">{signal.detail}</p>
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-muted-foreground">No priority signals available.</p>
                      )}
                    </CardContent>
                  </Card>
                ) : null}
              </div>
            ) : null}

            {canRenderOnDashboard("repository-footprint") || canRenderOnDashboard("severity-mix") ? (
              <div className="grid gap-6 xl:grid-cols-2">
                {canRenderOnDashboard("repository-footprint") ? (
                  <MetricBarCard
                    title="Repository footprint"
                    description="Key metrics captured from the FastAPI project summary response."
                    labels={["Analyzable files", "Dependency edges", "Call edges"]}
                    values={[
                      bundle.project.metrics.analyzable_files ?? bundle.project.metrics.files_scanned,
                      bundle.project.metrics.dependency_edges,
                      bundle.project.metrics.call_edges,
                    ]}
                  />
                ) : null}
                {canRenderOnDashboard("severity-mix") ? (
                  <SeverityDoughnutCard
                    title="Severity mix"
                    description="Risk scoring buckets from the latest backend run."
                    labels={["High", "Medium", "Low"]}
                    values={[
                      bundle.risk.severity_distribution.high,
                      bundle.risk.severity_distribution.medium,
                      bundle.risk.severity_distribution.low,
                    ]}
                    colors={["#dc2626", "#f59e0b", "#16a34a"]}
                  />
                ) : null}
              </div>
            ) : null}

            {canRenderOnDashboard("graph-impact-ranking") || canRenderOnDashboard("evidence-mix") ? (
              <div className="grid gap-6 xl:grid-cols-2">
                {canRenderOnDashboard("graph-impact-ranking") ? (
                  <MetricBarCard
                    title="Graph impact ranking"
                    description="Top nodes surfaced by the backend NetworkX analysis."
                    labels={graphImpactNodes.map((node: any) => node.label)}
                    values={graphImpactNodes.map((node: any) => Number(node.score.toFixed(3)))}
                    accent="rgba(13, 148, 136, 0.9)"
                  />
                ) : null}
                {canRenderOnDashboard("evidence-mix") ? (
                  <SeverityDoughnutCard
                    title="Explainability evidence mix"
                    description="Token, AST, and graph traces from the last saved analysis."
                    labels={["Token", "AST", "Graph"]}
                    values={[
                      evidenceDistribution.tokenCount,
                      evidenceDistribution.astCount,
                      evidenceDistribution.graphCount,
                    ]}
                    colors={["#2563eb", "#7c3aed", "#0f766e"]}
                  />
                ) : null}
              </div>
            ) : null}

            {canRenderOnDashboard("backend-summaries") || canRenderOnDashboard("flow-path") ? (
              <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
                {canRenderOnDashboard("backend-summaries") ? (
                  <Card className="border-border/70 bg-card/95 shadow-sm border-l-4 border-l-primary/70">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Sparkles className="h-5 w-5 text-primary" />
                        Backend summaries
                      </CardTitle>
                      <CardDescription>Substantial project overview, architecture, and flow.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6 text-sm">
                      <div className="space-y-4">
                        <ul className="space-y-3">
                          {summaryPoints.length > 0 ? (
                            summaryPoints.map((point: string, i: number) => (
                              <li key={i} className="flex gap-3 leading-relaxed">
                                <div className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary/40" />
                                <span className="text-muted-foreground">{point}</span>
                              </li>
                            ))
                          ) : (
                            <li className="flex gap-3 leading-relaxed">
                              <Check className="h-4 w-4 mt-1 shrink-0 text-primary" />
                              <span className="text-muted-foreground">{bundle.project.project_summary}</span>
                            </li>
                          )}
                        </ul>
                      </div>
                      <div className="space-y-4 border-t pt-4">
                        <p className="font-medium text-foreground">Architecture Summary</p>
                        <p className="leading-6 text-muted-foreground">{bundle.project.architecture_summary}</p>
                        <p className="font-medium text-foreground">Execution Flow</p>
                        <p className="leading-6 text-muted-foreground">{bundle.project.execution_flow_summary}</p>
                      </div>
                      <div className="flex flex-wrap gap-2 pt-2">
                        {(bundle.project.key_dependencies || []).slice(0, 6).map((dependency: string) => (
                          <Badge key={dependency} variant="secondary">
                            {dependency}
                          </Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ) : null}
                {canRenderOnDashboard("flow-path") ? (
                  <MermaidDiagram
                    title="Flow path"
                    description="A rendered view of the saved execution path from the backend response."
                    definition={mermaidDefinition}
                  />
                ) : null}
              </div>
            ) : null}

          </section>
        )}
      </main>
    </div>
  );
}

function StatTile({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number | string;
}) {
  return (
    <div className="rounded-xl border bg-background/80 p-3">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Icon className="h-4 w-4" />
        <span>{label}</span>
      </div>
      <div className="mt-2 text-2xl font-semibold text-foreground">{value}</div>
    </div>
  );
}


