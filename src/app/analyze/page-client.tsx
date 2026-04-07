"use client";

import axios from "axios";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import {
  cloneProjectFromGithub,
  fetchExplainabilityTraces,
  fetchGraphAnalysis,
  fetchProjectSummaries,
  fetchQualityAnalysis,
  fetchRiskScoring,
  uploadProjectFiles,
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

  const nodes = flowPath.map((label, index) => `  N${index}["${label.replace(/"/g, "'")}"]`).join("\n");
  const edges = flowPath.slice(0, -1).map((_, index) => `  N${index} --> N${index + 1}`).join("\n");
  return `flowchart LR\n${nodes}\n${edges}`;
}

export default function AnalyzePageClient() {
  const folderInputRef = useRef<HTMLInputElement | null>(null);
  const [githubUrl, setGithubUrl] = useState("");
  const [localPath, setLocalPath] = useState("");
  const [codeProjectName, setCodeProjectName] = useState("");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [graphType, setGraphType] = useState("call");
  const [focusFile, setFocusFile] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzingCode, setIsAnalyzingCode] = useState(false);
  const [isUploadingProject, setIsUploadingProject] = useState(false);
  const [bundle, setBundle] = useState<AnalysisBundle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [level, setLevel] = useState<"beginner" | "intermediate" | "advanced">("beginner");

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

  useEffect(() => {
    if (!folderInputRef.current) {
      return;
    }

    folderInputRef.current.setAttribute("webkitdirectory", "");
    folderInputRef.current.setAttribute("directory", "");
  }, []);

  const mermaidDefinition = useMemo(
    () => buildMermaidDefinition(bundle?.project.flow_path || bundle?.graph.traversal.bfs_order || []),
    [bundle],
  );

  const explanationByLevel = useMemo(
    () => ({
      beginner: bundle?.project.project_summary || "No beginner explanation available.",
      intermediate: bundle?.project.architecture_summary || "No intermediate explanation available.",
      advanced: bundle?.project.execution_flow_summary || "No advanced explanation available.",
    }),
    [bundle],
  );

  const prioritizedSignals = useMemo(
    () =>
      [...(bundle?.risk.top_signals || [])]
        .sort((left, right) => right.weight - left.weight)
        .slice(0, 6),
    [bundle],
  );

  const graphImpactNodes = useMemo(
    () => (bundle?.graph.top_impact_rank || []).slice(0, 5),
    [bundle],
  );

  const evidenceDistribution = useMemo(() => {
    const tokenCount = bundle?.traces.token_traces.filter((trace) => trace.evidence?.kind === "token").length ?? 0;
    const astCount = bundle?.traces.ast_traces.filter((trace) => trace.evidence?.kind === "ast").length ?? 0;
    const graphCount = bundle?.traces.graph_traces.length ?? 0;

    return { tokenCount, astCount, graphCount };
  }, [bundle]);

  const deriveProjectNameFromPath = (projectPath: string) => {
    const normalized = projectPath.replace(/\\/g, "/").replace(/\/+$/, "");
    const segments = normalized.split("/").filter(Boolean);
    return segments.length ? segments[segments.length - 1] : "";
  };

  const handleAnalyze = async () => {
    if (!localPath.trim() && !githubUrl.trim()) {
      toast.error("Enter a local path or GitHub URL first.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      let analysisPath = localPath.trim();

      if (!analysisPath && githubUrl.trim()) {
        const cloneResponse = await cloneProjectFromGithub(githubUrl.trim());
        analysisPath = cloneResponse.project_path;
        setLocalPath(analysisPath);

        const inferredName = deriveProjectNameFromPath(analysisPath);
        if (inferredName) {
          setCodeProjectName(inferredName);
        }

        toast.success("Repository cloned. Running analysis...");
      }

      const [project, quality, risk, graph, traces] = await Promise.all([
        fetchProjectSummaries(analysisPath, 1000),
        fetchQualityAnalysis(analysisPath, 1000),
        fetchRiskScoring(analysisPath, 1000),
        fetchGraphAnalysis(analysisPath, graphType, 1000),
        fetchExplainabilityTraces(analysisPath, focusFile.trim() || undefined, graphType, 1000),
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

  const openFolderPicker = () => {
    folderInputRef.current?.click();
  };

  const handleProjectUpload = async () => {
    if (!selectedFiles.length) {
      toast.error("Choose a local project folder first.");
      return;
    }

    setIsUploadingProject(true);
    setError(null);

    try {
      const response = await uploadProjectFiles(selectedFiles);
      setLocalPath(response.project_path);
      const inferredName = deriveProjectNameFromPath(response.project_path);
      if (inferredName) {
        setCodeProjectName(inferredName);
      }
      toast.success(`Project uploaded (${response.files_saved} files).`);
    } catch (uploadError) {
      const message = uploadError instanceof Error ? uploadError.message : "Upload failed";
      setError(message);
      toast.error(message);
    } finally {
      setIsUploadingProject(false);
    }
  };

  const analyzeCode = async () => {
    const inferredName = deriveProjectNameFromPath(localPath);
    const projectName = codeProjectName.trim() || inferredName;

    if (!projectName) {
      toast.error("Upload/clone a project first so project name can be detected.");
      return;
    }

    if (!codeProjectName.trim() && inferredName) {
      setCodeProjectName(inferredName);
    }

    setIsAnalyzingCode(true);
    setError(null);

    try {
      const res = await axios.get(`http://127.0.0.1:8000/project/code-analysis/${encodeURIComponent(projectName)}`);

      console.log(res.data);
      toast.success("Code analysis loaded. Check the console.");
    } catch (analysisError) {
      const message = analysisError instanceof Error ? analysisError.message : "Code analysis failed";
      setError(message);
      toast.error(message);
    } finally {
      setIsAnalyzingCode(false);
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
                <Label htmlFor="githubUrl">GitHub URL (optional)</Label>
                <Input
                  id="githubUrl"
                  placeholder="https://github.com/owner/repo"
                  value={githubUrl}
                  onChange={(event) => setGithubUrl(event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="localPath">Local project path</Label>
                <Input
                  id="localPath"
                  placeholder="D:/RepoRoverAI/RepoRover-AI"
                  value={localPath}
                  onChange={(event) => setLocalPath(event.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  You can paste a path, or upload a local folder with the plus button below.
                </p>
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
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="codeProjectName">Project name for code analysis</Label>
                <Input
                  id="codeProjectName"
                  placeholder="Auto-filled after upload/clone"
                  value={codeProjectName}
                  onChange={(event) => setCodeProjectName(event.target.value)}
                />
              </div>
              <div className="md:col-span-2 rounded-xl border bg-muted/20 p-3">
                <input
                  ref={folderInputRef}
                  id="project-folder-input"
                  type="file"
                  className="hidden"
                  multiple
                  onChange={(event) => setSelectedFiles(Array.from(event.target.files ?? []))}
                />
                <div className="flex flex-wrap items-center gap-3">
                  <Button type="button" variant="outline" onClick={openFolderPicker} className="gap-2">
                    <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
                      +
                    </span>
                    {selectedFiles.length ? "Change project folder" : "Choose project folder"}
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={handleProjectUpload}
                    disabled={isUploadingProject || !selectedFiles.length}
                  >
                    {isUploadingProject ? "Uploading folder..." : "Upload selected folder"}
                  </Button>
                  <span className="text-xs text-muted-foreground">
                    {selectedFiles.length ? `${selectedFiles.length} files selected` : "No folder selected"}
                  </span>
                </div>
              </div>
              <div className="flex flex-wrap gap-3 md:col-span-2">
                <Button onClick={handleAnalyze} disabled={isLoading} className="gap-2">
                  {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Activity className="h-4 w-4" />}
                  {isLoading ? "Analyzing..." : "Run FastAPI analysis"}
                </Button>
                <Button onClick={analyzeCode} disabled={isAnalyzingCode} variant="secondary" className="gap-2">
                  {isAnalyzingCode ? <Loader2 className="h-4 w-4 animate-spin" /> : <Code2 className="h-4 w-4" />}
                  {isAnalyzingCode ? "Analyzing code..." : "Analyze Code"}
                </Button>
                <Button variant="outline" asChild>
                  <Link to="/dashboard">Open dashboard</Link>
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
                <StatTile
                  icon={ChartColumnBig}
                  label="Total files"
                  value={bundle?.project.metrics.total_files ?? bundle?.project.metrics.files_scanned ?? 0}
                />
                <StatTile
                  icon={FileText}
                  label="Analyzable files"
                  value={bundle?.project.metrics.analyzable_files ?? bundle?.project.metrics.files_scanned ?? 0}
                />
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
            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <CardTitle>Project Dashboard</CardTitle>
                <CardDescription>{"Upload project -> Analyze -> Show dashboard -> Explain results."}</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2 text-xs">
                <Badge variant="secondary">Upload project</Badge>
                <Badge variant="secondary">Analyze</Badge>
                <Badge variant="secondary">Show dashboard</Badge>
                <Badge variant="secondary">Explain results</Badge>
              </CardContent>
            </Card>

            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <CardTitle>Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                <p className="text-foreground">{bundle.project.project_summary}</p>
                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-lg border p-4">Modules: {bundle.project.key_modules.length}</div>
                  <div className="rounded-lg border p-4">Dependencies: {bundle.project.key_dependencies.length}</div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <CardTitle>Explanation (Tabs)</CardTitle>
                <CardDescription>Switch explanation depth for beginner, intermediate, and advanced audiences.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    variant={level === "beginner" ? "default" : "outline"}
                    onClick={() => setLevel("beginner")}
                  >
                    Beginner
                  </Button>
                  <Button
                    type="button"
                    variant={level === "intermediate" ? "default" : "outline"}
                    onClick={() => setLevel("intermediate")}
                  >
                    Intermediate
                  </Button>
                  <Button
                    type="button"
                    variant={level === "advanced" ? "default" : "outline"}
                    onClick={() => setLevel("advanced")}
                  >
                    Advanced
                  </Button>
                </div>
                <p className="rounded-xl border bg-muted/20 p-4 text-sm leading-6 text-foreground">{explanationByLevel[level]}</p>
              </CardContent>
            </Card>

            <MermaidDiagram
              title="Graph Visualization"
              description="Execution graph from backend flow path rendered as a product-ready visual."
              definition={mermaidDefinition}
            />

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <Card className="border-border/70 bg-card/95 shadow-sm">
                <CardHeader>
                  <CardTitle>Risks</CardTitle>
                  <CardDescription>Top reliability and quality risks detected by analysis.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {bundle.quality.issues.length ? (
                    bundle.quality.issues.slice(0, 5).map((issue) => (
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

              <Card className="border-border/70 bg-card/95 shadow-sm">
                <CardHeader>
                  <CardTitle>Priority</CardTitle>
                  <CardDescription>Highest-impact risk signals ranked by backend weight.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {prioritizedSignals.length ? (
                    prioritizedSignals.map((signal) => (
                      <div key={`${signal.title}-${signal.detail}`} className="rounded-xl border bg-muted/20 p-3 text-sm">
                        <div className="flex items-center justify-between gap-3">
                          <span className="font-semibold text-foreground">{signal.title}</span>
                          <Badge variant="outline">{signal.weight.toFixed(2)}</Badge>
                        </div>
                        <p className="mt-2 text-muted-foreground">{signal.detail}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No priority signals available.</p>
                  )}
                </CardContent>
              </Card>
            </div>

            <div className="grid gap-6 xl:grid-cols-2">
              <MetricBarCard
                title="Project size and edge footprint"
                description="Backend-provided repository metrics visualized with Chart.js."
                labels={["Total files", "Analyzable files", "Total lines", "Dependency edges", "Call edges"]}
                values={[
                  bundle.project.metrics.total_files ?? bundle.project.metrics.files_scanned,
                  bundle.project.metrics.analyzable_files ?? bundle.project.metrics.files_scanned,
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

            <div className="grid gap-6 xl:grid-cols-2">
              <MetricBarCard
                title="Graph impact ranking"
                description="Top nodes surfaced by the backend NetworkX analysis."
                labels={graphImpactNodes.map((node) => node.label)}
                values={graphImpactNodes.map((node) => Number(node.score.toFixed(3)))}
                accent="rgba(13, 148, 136, 0.9)"
              />
              <SeverityDoughnutCard
                title="Explainability evidence mix"
                description="Token, AST, and graph traces returned by the explainability pipeline."
                labels={["Token", "AST", "Graph"]}
                values={[
                  evidenceDistribution.tokenCount,
                  evidenceDistribution.astCount,
                  evidenceDistribution.graphCount,
                ]}
                colors={["#2563eb", "#7c3aed", "#0f766e"]}
              />
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


