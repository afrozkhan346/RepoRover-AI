"use client";

import { useEffect, useId, useState } from "react";
import mermaid from "mermaid";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function MermaidDiagram({
  title,
  description,
  definition,
}: {
  title: string;
  description?: string;
  definition: string;
}) {
  const diagramId = useId().replace(/:/g, "-");
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    mermaid.initialize({
      startOnLoad: false,
      theme: "neutral",
      securityLevel: "strict",
      fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif",
    });

    async function renderDiagram() {
      try {
        const { svg } = await mermaid.render(`mermaid-${diagramId}`, definition);
        if (alive) {
          setSvg(svg);
          setError(null);
        }
      } catch (renderError) {
        if (alive) {
          setError(renderError instanceof Error ? renderError.message : "Unable to render diagram");
        }
      }
    }

    void renderDiagram();

    return () => {
      alive = false;
    };
  }, [definition, diagramId]);

  return (
    <Card className="border-border/70 bg-card/95 shadow-sm">
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
        {description ? <CardDescription>{description}</CardDescription> : null}
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
            {error}
          </div>
        ) : svg ? (
          <div
            className="overflow-x-auto rounded-lg border bg-background/70 p-4"
            dangerouslySetInnerHTML={{ __html: svg }}
          />
        ) : (
          <div className="flex h-64 items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground">
            Rendering diagram...
          </div>
        )}
      </CardContent>
    </Card>
  );
}
