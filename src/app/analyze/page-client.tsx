"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import {
  fetchExplainabilityTraces,
  fetchGraphAnalysis,
  fetchProjectSummaries,
  fetchQualityAnalysis,
  fetchRiskScoring,
  type ExplainabilityTraceResponse,
  type GraphAnalysisResponse,
  type ProjectSummariesResponse,
  type QualityAnalysisResponse,
  type RiskScoringResponse,
} from "@/lib/backend";
import { Navigation } from "@/components/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MermaidDiagram } from "@/components/analysis/mermaid-diagram";
import { MetricBarCard, SeverityDoughnutCard } from "@/components/analysis/metric-charts";
import {
  Activity,
  Brain,
  ChartColumnBig,
  Code2,
  FileText,
  GitBranch,
  Loader2,
  Route,
  Sparkles,
  TriangleAlert,
  Wand2,
} from "lucide-react";

type AnalysisBundle = {
  project: ProjectSummariesResponse;
  quality: QualityAnalysisResponse;
  risk: RiskScoringResponse;
  graph: GraphAnalysisResponse;
  traces: ExplainabilityTraceResponse;
};

const STORAGE_KEY = "repoorover:last-analysis";

function buildMermaidDefinition(flowPath: string[]) {
  if (!flowPath.length) {
    return "flowchart LR\n  A[No flow path available]";
  }

  const nodes = flowPath.map((label, index) => `  N${index}[\"${label.replace(/\"/g, "'")}\"]`).join("\n");
  const edges = flowPath.slice(0, -1).map((_, index) => `  N${index} --> N${index + 1}`).join("\n");
  return `flowchart LR\n${nodes}\n${edges}`;
}

export default function AnalyzePageClient() {
  const [localPath, setLocalPath] = useState("");
  const [graphType, setGraphType] = useState("call");
  const [focusFile, setFocusFile] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [bundle, setBundle] = useState<AnalysisBundle | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (!saved) {
      return;
    }

    try {
      setBundle(JSON.parse(saved) as AnalysisBundle);
    } catch {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  const mermaidDefinition = useMemo(
    () => buildMermaidDefinition(bundle?.project.flow_path || bundle?.graph.traversal.bfs_order || []),
    [bundle],
  );

  const handleAnalyze = async () => {
    if (!localPath.trim()) {
      toast.error("Enter a local project path first.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const [project, quality, risk, graph, traces] = await Promise.all([
        fetchProjectSummaries(localPath.trim(), 1000),
        fetchQualityAnalysis(localPath.trim(), 1000),
        fetchRiskScoring(localPath.trim(), 1000),
        fetchGraphAnalysis(localPath.trim(), graphType, 1000),
        fetchExplainabilityTraces(localPath.trim(), focusFile.trim() || undefined, graphType, 1000),
      ]);

      const nextBundle: AnalysisBundle = { project, quality, risk, graph, traces };
      setBundle(nextBundle);
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextBundle));
      toast.success("FastAPI analysis complete.");
    } catch (analysisError) {
      const message = analysisError instanceof Error ? analysisError.message : "Analysis failed";
      setError(message);
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.12),_transparent_35%),linear-gradient(180deg,_rgba(2,6,23,0.04),_transparent_40%)]">
      <Navigation />
      <main className="container mx-auto px-4 py-8 lg:py-12 space-y-8">
        <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="space-y-4">
              <Badge className="w-fit gap-2 rounded-full px-3 py-1 text-xs uppercase tracking-[0.2em]">
                <Sparkles className="h-3.5 w-3.5" /> FastAPI analysis workspace
              </Badge>
              <div className="space-y-2">
                <CardTitle className="text-3xl md:text-4xl">Repository intelligence, rendered live.</CardTitle>
                <CardDescription className="max-w-2xl text-base">
                  Point the app at a local project path and the backend will return project summaries,
                  quality findings, graph analytics, explainability traces, and Mermaid-ready flow paths.
                </CardDescription>
              </div>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="localPath">Local project path</Label>
                <Input
                  id="localPath"
                  placeholder="D:/RepoRoverAI/RepoRover-AI"
                  value={localPath}
                  onChange={(event) => setLocalPath(event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="graphType">Graph type</Label>
                <Select value={graphType} onValueChange={setGraphType}>
                  <SelectTrigger id="graphType">
                    <SelectValue placeholder="Select graph type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="call">Call graph</SelectItem>
                    <SelectItem value="dependency">Dependency graph</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="focusFile">Focus file for explainability traces</Label>
                <Input
                  id="focusFile"
                  placeholder="src/app/analyze/page.tsx"
                  value={focusFile}
                  onChange={(event) => setFocusFile(event.target.value)}
                />
              </div>
              <div className="flex flex-wrap gap-3 md:col-span-2">
                <Button onClick={handleAnalyze} disabled={isLoading} className="gap-2">
                  {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Activity className="h-4 w-4" />}
                  {isLoading ? "Analyzing..." : "Run FastAPI analysis"}
                </Button>
                <Button variant="outline" asChild>
                  <Link href="/dashboard">Open dashboard</Link>
                </Button>
              </div>
              {error ? (
                <div className="md:col-span-2 rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
                  {error}
                </div>
              ) : null}
            </CardContent>
          </Card>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
            <Card className="border-border/70 bg-card/90 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">Backend signals</CardTitle>
                <CardDescription>Metrics returned by the FastAPI analysis pipeline.</CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-3 text-sm">
                <StatTile icon={ChartColumnBig} label="Files" value={bundle?.project.metrics.files_scanned ?? 0} />
                <StatTile icon={GitBranch} label="Graph nodes" value={bundle?.graph.metrics.node_count ?? 0} />
                <StatTile icon={TriangleAlert} label="Risk score" value={bundle?.risk.risk_score ?? 0} />
                <StatTile icon={Brain} label="Reliability" value={bundle?.risk.reliability_score ?? 0} />
              </CardContent>
            </Card>
            <Card className="border-border/70 bg-card/90 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">Explainability coverage</CardTitle>
                <CardDescription>Trace counts tied back to tokens, AST nodes, and graph paths.</CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-3 gap-3 text-sm">
                <StatTile icon={Code2} label="Tokens" value={bundle?.traces.token_traces.length ?? 0} />
                <StatTile icon={FileText} label="AST nodes" value={bundle?.traces.ast_traces.length ?? 0} />
                <StatTile icon={Route} label="Paths" value={bundle?.traces.graph_traces.length ?? 0} />
              </CardContent>
            </Card>
          </div>
        </section>

        {bundle ? (
          <section className="space-y-6">
            <div className="grid gap-6 xl:grid-cols-2">
              <MetricBarCard
                title="Project size and edge footprint"
                description="Backend-provided repository metrics visualized with Chart.js."
                labels={["Files scanned", "Total lines", "Dependency edges", "Call edges"]}
                values={[
                  bundle.project.metrics.files_scanned,
                  bundle.project.metrics.total_lines,
                  bundle.project.metrics.dependency_edges,
                  bundle.project.metrics.call_edges,
                ]}
                accent="rgba(37, 99, 235, 0.9)"
              />
              <SeverityDoughnutCard
                title="Risk distribution"
                description="Severity buckets from the reliability scoring pipeline."
                labels={["High", "Medium", "Low"]}
                values={[
                  bundle.risk.severity_distribution.high,
                  bundle.risk.severity_distribution.medium,
                  bundle.risk.severity_distribution.low,
                ]}
                colors={["#dc2626", "#f59e0b", "#16a34a"]}
              />
            </div>

            <div className="grid gap-6 xl:grid-cols-[1fr_1.2fr]">
              <Card className="border-border/70 bg-card/95 shadow-sm">
                <CardHeader>
                  <CardTitle>FastAPI summaries</CardTitle>
                  <CardDescription>Project, architecture, and execution-flow summaries generated by the backend.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4 text-sm leading-6 text-muted-foreground">
                  <p className="text-foreground">{bundle.project.project_summary}</p>
                  <p>{bundle.project.architecture_summary}</p>
                  <p>{bundle.project.execution_flow_summary}</p>
                  <div className="flex flex-wrap gap-2 pt-2">
                    {bundle.project.key_modules.slice(0, 6).map((module) => (
                      <Badge key={module} variant="secondary">
                        {module}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <MermaidDiagram
                title="Execution flow diagram"
                description="The backend flow path is rendered with Mermaid from the latest analysis response."
                definition={mermaidDefinition}
              />
            </div>

            <div className="grid gap-6 xl:grid-cols-2">
              <Card className="border-border/70 bg-card/95 shadow-sm">
                <CardHeader>
                  <CardTitle>Quality issues</CardTitle>
                  <CardDescription>Structured findings and suggested fixes from the quality pipeline.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {bundle.quality.issues.length ? (
                    bundle.quality.issues.slice(0, 6).map((issue) => (
                      <div key={`${issue.category}-${issue.detail}`} className="rounded-xl border bg-muted/20 p-3 text-sm">
                        <div className="flex items-center justify-between gap-3">
                          <span className="font-semibold text-foreground">{issue.category}</span>
                          <Badge variant="outline">{issue.severity}</Badge>
                        </div>
                        <p className="mt-2 text-muted-foreground">{issue.detail}</p>
                        <p className="mt-2 text-foreground">{issue.recommendation}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No issues reported by the backend pipeline.</p>
                  )}
                </CardContent>
              </Card>

              <Card className="border-border/70 bg-card/95 shadow-sm">
                <CardHeader>
                  <CardTitle>Explainability traces</CardTitle>
                  <CardDescription>How findings are tied to code tokens, AST units, and graph paths.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {bundle.traces.findings.map((finding) => {
                    const matchingTokens = bundle.traces.token_traces.filter((trace) => trace.finding_id === finding.finding_id).length;
                    const matchingAst = bundle.traces.ast_traces.filter((trace) => trace.finding_id === finding.finding_id).length;
                    const matchingPaths = bundle.traces.graph_traces.find((trace) => trace.finding_id === finding.finding_id)?.path.length ?? 0;

                    return (
                      <div key={finding.finding_id} className="rounded-xl border bg-muted/20 p-4 text-sm space-y-2">
                        <div className="flex items-center justify-between gap-3">
                          <span className="font-semibold text-foreground">{finding.title}</span>
                          <Badge>{finding.severity}</Badge>
                        </div>
                        <p className="text-muted-foreground">{finding.evidence}</p>
                        <div className="flex flex-wrap gap-2">
                          <Badge variant="outline">{matchingTokens} token traces</Badge>
                          <Badge variant="outline">{matchingAst} AST traces</Badge>
                          <Badge variant="outline">{matchingPaths} graph steps</Badge>
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            </div>
          </section>
        ) : (
          <Card className="border-dashed border-border/70 bg-card/70 shadow-none">
            <CardContent className="flex min-h-[260px] flex-col items-center justify-center gap-4 text-center">
              <Wand2 className="h-12 w-12 text-primary" />
              <div className="space-y-2">
                <h2 className="text-2xl font-semibold">No analysis loaded yet</h2>
                <p className="max-w-xl text-sm text-muted-foreground">
                  Enter a project path and run the analysis to populate the dashboard with FastAPI summaries,
                  graphs, Mermaid flow, and explainability traces.
                </p>
              </div>
            </CardContent>
          </Card>
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
