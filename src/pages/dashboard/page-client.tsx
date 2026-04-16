
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
import { Activity, ArrowRight, GitBranch, LayoutDashboard, Sparkles, TriangleAlert } from "lucide-react";

type SavedBundle = any;

const STORAGE_KEY_PREFIX = "Reponium:last-analysis";

function buildMermaidDefinition(flowPath: string[]) {
  if (!flowPath.length) {
    return "flowchart LR\n  A[No analysis saved yet]";
  }

  const nodes = flowPath.map((label, index) => `  N${index}["${label.replace(/"/g, "'")}"]`).join("\n");
  const edges = flowPath.slice(0, -1).map((_, index) => `  N${index} --> N${index + 1}`).join("\n");
  return `flowchart LR\n${nodes}\n${edges}`;
}

export default function DashboardPageClient() {
  const { data: session, isPending: isSessionPending } = useSession();
  const [bundle, setBundle] = useState<SavedBundle | null>(null);

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
            {canRenderOnDashboard("risks") || canRenderOnDashboard("priority") ? (
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                {canRenderOnDashboard("risks") ? (
                  <Card className="border-border/70 bg-card/95 shadow-sm">
                    <CardHeader>
                      <CardTitle>Risks</CardTitle>
                      <CardDescription>Top reliability and quality risks detected by analysis.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {bundle.quality.issues.length ? (
                        bundle.quality.issues.slice(0, 5).map((issue: any) => (
                          <div key={`${issue.category}-${issue.detail}`} className="rounded-xl border bg-muted/20 p-3 text-sm">
                            <div className="flex items-center justify-between gap-3">
                              <span className="font-semibold text-foreground">{issue.category}</span>
                              <Badge variant="outline">{issue.severity}</Badge>
                            </div>
                            <p className="mt-2 text-muted-foreground">{issue.detail}</p>
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-muted-foreground">No risk issues reported.</p>
                      )}
                    </CardContent>
                  </Card>
                ) : null}

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
                  <Card className="border-border/70 bg-card/95 shadow-sm">
                    <CardHeader>
                      <CardTitle>Backend summaries</CardTitle>
                      <CardDescription>Project summary, architecture summary, and execution flow.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4 text-sm leading-6 text-muted-foreground">
                      <p className="text-foreground">{bundle.project.project_summary}</p>
                      <p>{bundle.project.architecture_summary}</p>
                      <p>{bundle.project.execution_flow_summary}</p>
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


