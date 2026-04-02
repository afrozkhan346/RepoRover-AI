"use client";

import Link from "next/link";
import { Navigation } from "@/components/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, BarChart3, Brain, Code2, GitBranch, Sparkles, Wand2 } from "lucide-react";

const pillars = [
  {
    icon: GitBranch,
    title: "Repository intelligence",
    description: "Analyze local projects with dependency graphs, call graphs, and explainability traces.",
  },
  {
    icon: BarChart3,
    title: "Chart.js dashboards",
    description: "Turn backend metrics into charts that show file counts, edge density, risk, and reliability.",
  },
  {
    icon: Wand2,
    title: "Mermaid flow paths",
    description: "Render execution flow from FastAPI outputs directly in the browser.",
  },
  {
    icon: Brain,
    title: "Python AI pipeline",
    description: "Use the FastAPI explanation backend for code tutoring, summarization, and design insights.",
  },
];

export default function HomePageClient() {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(14,165,233,0.14),_transparent_35%),linear-gradient(180deg,_rgba(2,6,23,0.04),_transparent_40%)]">
      <Navigation />
      <main className="container mx-auto px-4 py-8 lg:py-12 space-y-10">
        <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr] items-center">
          <div className="space-y-6">
            <Badge className="w-fit gap-2 rounded-full px-3 py-1 text-xs uppercase tracking-[0.2em]">
              <Sparkles className="h-3.5 w-3.5" /> FastAPI-backed frontend
            </Badge>
            <div className="space-y-4">
              <h1 className="text-4xl font-bold tracking-tight md:text-6xl">
                Rebuilt for repository analysis, explanation, and visual diagnostics.
              </h1>
              <p className="max-w-2xl text-lg text-muted-foreground">
                RepoRoverAI now consumes FastAPI outputs for summaries, charts, Mermaid graphs, and code explanation.
                Use the analyzer to inspect a local project and the dashboard to revisit the latest result.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button asChild size="lg" className="gap-2">
                <Link href="/analyze">
                  Open analyzer <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link href="/dashboard">View dashboard</Link>
              </Button>
            </div>
          </div>

          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader>
              <CardTitle>What the new stack does</CardTitle>
              <CardDescription>Frontend views now consume backend metrics instead of proxying the old Next routes.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <div className="rounded-xl border bg-background/80 p-3">FastAPI returns project summaries, quality findings, risk scores, and explainability traces.</div>
              <div className="rounded-xl border bg-background/80 p-3">Chart.js renders the numeric data, while Mermaid renders execution flow and graph paths.</div>
              <div className="rounded-xl border bg-background/80 p-3">The AI tutor page sends snippets to the Python explanation pipeline with a deterministic fallback.</div>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {pillars.map((pillar) => {
            const Icon = pillar.icon;
            return (
              <Card key={pillar.title} className="border-border/70 bg-card/95 shadow-sm">
                <CardHeader>
                  <div className="mb-2 flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <Icon className="h-5 w-5" />
                  </div>
                  <CardTitle className="text-lg">{pillar.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-sm leading-6">{pillar.description}</CardDescription>
                </CardContent>
              </Card>
            );
          })}
        </section>

        <section className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader>
              <CardTitle>Start here</CardTitle>
              <CardDescription>Open the pages that are now wired to the Python backend.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button asChild variant="secondary" className="w-full justify-between">
                <Link href="/analyze">
                  Analyze a local repo <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="secondary" className="w-full justify-between">
                <Link href="/dashboard">
                  Review the latest dashboard <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="secondary" className="w-full justify-between">
                <Link href="/ai-tutor">
                  Explain a code snippet <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader>
              <CardTitle>Backend outputs now surfaced in the UI</CardTitle>
              <CardDescription>The frontend consumes these FastAPI responses directly.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2">
              {[
                "Project summaries",
                "Graph analysis",
                "Quality findings",
                "Risk scoring",
                "Explainability traces",
                "AI explanations",
              ].map((item) => (
                <div key={item} className="rounded-xl border bg-background/80 p-3 text-sm font-medium text-foreground">
                  {item}
                </div>
              ))}
            </CardContent>
          </Card>
        </section>
      </main>
    </div>
  );
}
