"use client";

import { useState } from "react";
import { toast } from "sonner";
import { explainCode, type AIExplanationResponse } from "@/lib/backend";
import { Navigation } from "@/components/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Loader2, Sparkles, ClipboardCopy, BookOpen, Brain } from "lucide-react";

const SAMPLE_CODE = `function calculateScore(items) {
  const total = items.reduce((sum, item) => sum + item.value, 0);
  if (total > 100) {
    return total * 1.1;
  }
  return total;
}`;

export default function AiTutorPageClient() {
  const [code, setCode] = useState(SAMPLE_CODE);
  const [language, setLanguage] = useState("typescript");
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<AIExplanationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleExplain = async () => {
    if (!code.trim()) {
      toast.error("Paste or type code first.");
      return;
    }

    setIsLoading(true);
    try {
      const data = await explainCode(code, language, question.trim() || undefined);
      setResponse(data);
      toast.success("Explanation generated.");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to explain code";
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const copyExplanation = async () => {
    if (!response?.explanation) {
      return;
    }
    await navigator.clipboard.writeText(response.explanation);
    toast.success("Explanation copied.");
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(168,85,247,0.12),_transparent_35%),linear-gradient(180deg,_rgba(2,6,23,0.04),_transparent_40%)]">
      <Navigation />
      <main className="container mx-auto px-4 py-8 lg:py-12 space-y-8">
        <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="space-y-4">
              <Badge className="w-fit gap-2 rounded-full px-3 py-1 text-xs uppercase tracking-[0.2em]">
                <Sparkles className="h-3.5 w-3.5" /> FastAPI explanation
              </Badge>
              <div className="space-y-2">
                <CardTitle className="text-3xl md:text-4xl">Explain code with the Python pipeline.</CardTitle>
                <CardDescription className="max-w-2xl text-base">
                  This page sends code to the FastAPI explanation endpoint and renders the returned summary,
                  model metadata, complexity score, and key concepts.
                </CardDescription>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="language">Language</Label>
                <Input id="language" value={language} onChange={(event) => setLanguage(event.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="question">Question, if any</Label>
                <Input
                  id="question"
                  placeholder="What is this function doing?"
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="code">Code</Label>
                <Textarea
                  id="code"
                  className="min-h-[280px] font-mono text-sm"
                  value={code}
                  onChange={(event) => setCode(event.target.value)}
                />
              </div>
              <div className="flex flex-wrap gap-3">
                <Button onClick={handleExplain} disabled={isLoading} className="gap-2">
                  {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Brain className="h-4 w-4" />}
                  {isLoading ? "Generating..." : "Explain with FastAPI"}
                </Button>
                <Button variant="outline" onClick={() => setCode(SAMPLE_CODE)}>
                  Load sample
                </Button>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
            <Card className="border-border/70 bg-card/90 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">Pipeline metadata</CardTitle>
                <CardDescription>What the backend returns alongside the explanation text.</CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-3 text-sm">
                <MetaTile label="Pipeline" value={response?.pipeline ?? "n/a"} />
                <MetaTile label="Model" value={response?.model ?? "n/a"} />
                <MetaTile label="Complexity" value={response?.complexity_score?.toFixed(2) ?? "n/a"} />
                <MetaTile label="Concepts" value={response?.key_concepts?.length ?? 0} />
              </CardContent>
            </Card>
            <Card className="border-border/70 bg-card/90 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">Quick tips</CardTitle>
                <CardDescription>Prompts that work well with the FastAPI explanation backend.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-muted-foreground">
                <p>Ask for flow, side effects, and data transformations.</p>
                <p>Use a real snippet from your repository for the best response.</p>
                <p>Combine this with the analyze workspace to jump from findings to explanation.</p>
              </CardContent>
            </Card>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1fr_0.95fr]">
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="flex-row items-center justify-between gap-4 space-y-0">
              <div>
                <CardTitle>Explanation</CardTitle>
                <CardDescription>Rendered output from the Python AI pipeline.</CardDescription>
              </div>
              <Button variant="outline" size="sm" onClick={copyExplanation} disabled={!response?.explanation}>
                <ClipboardCopy className="mr-2 h-4 w-4" /> Copy
              </Button>
            </CardHeader>
            <CardContent>
              {response ? (
                <div className="space-y-4">
                  <pre className="whitespace-pre-wrap rounded-xl border bg-muted/20 p-4 text-sm leading-6 text-foreground">
                    {response.explanation}
                  </pre>
                  <div className="flex flex-wrap gap-2">
                    {(response.key_concepts || []).map((concept) => (
                      <Badge key={concept} variant="secondary">
                        {concept}
                      </Badge>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="flex min-h-[260px] flex-col items-center justify-center gap-3 rounded-xl border border-dashed text-center text-sm text-muted-foreground">
                  <BookOpen className="h-10 w-10 text-primary" />
                  <p>Run the explanation pipeline to view the result here.</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader>
              <CardTitle>How it works</CardTitle>
              <CardDescription>The backend uses spaCy, PyTorch, and HuggingFace with a deterministic fallback.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm leading-6 text-muted-foreground">
              <p>1. The prompt is shaped from the snippet, language, and optional question.</p>
              <p>2. Key concepts and complexity signals are extracted in Python.</p>
              <p>3. HuggingFace produces the primary explanation when available.</p>
              <p>4. The fallback path still returns structured educational output.</p>
            </CardContent>
          </Card>
        </section>
      </main>
    </div>
  );
}

function MetaTile({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-xl border bg-background/80 p-3">
      <div className="text-xs uppercase tracking-[0.2em] text-muted-foreground">{label}</div>
      <div className="mt-2 text-lg font-semibold text-foreground">{value}</div>
    </div>
  );
}
