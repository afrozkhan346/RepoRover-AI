import { useEffect, useMemo, useState } from "react";
import { Folder, FileText, Loader2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { analyzeRepoStructure, type AnalyzeRepoResponse, type RepositoryTreeNode } from "@/lib/backend";

type VisualTreeLine = {
  prefix: string;
  branch: string;
  node: RepositoryTreeNode;
};

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

function collectFilePathEvidence(bundle: any): string[] {
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

export function RepositoryTree({ bundle }: { bundle: any }) {
  const [repoTreeResponse, setRepoTreeResponse] = useState<AnalyzeRepoResponse | null>(null);
  const [isTreeLoading, setIsTreeLoading] = useState(false);
  const [treeError, setTreeError] = useState<string | null>(null);

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

  if (!bundle) return null;

  return (
    <Card className="border-border/70 bg-card/95 shadow-sm">
      <CardHeader>
        <CardTitle>Repository tree</CardTitle>
        <CardDescription>Visual file/folder tree generated from the hierarchical repository structure.</CardDescription>
      </CardHeader>
      <CardContent className="max-h-[420px] overflow-auto rounded-none border-0 bg-transparent p-0">
        {isTreeLoading ? (
          <div className="flex items-center gap-2 px-6 py-4 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Scanning repository tree (optimized for large repos)...
          </div>
        ) : treeError ? (
          <div className="space-y-2 px-6 py-4">
            <p className="text-sm text-destructive">{treeError}</p>
            <p className="text-xs text-muted-foreground">
              Showing fallback tree from saved analysis evidence when available.
            </p>
          </div>
        ) : null}

        {!isTreeLoading && visualTreeLines.length ? (
          <div className="space-y-1 border-t px-6 py-4 font-mono text-xs">
            {repoTreeResponse?.truncated ? (
              <div className="mb-2 rounded-md border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-amber-700">
                Tree output truncated due to max node limit.
              </div>
            ) : null}
            {(repoTreeResponse?.errors?.length ?? 0) > 0 ? (
              <div className="mb-2 rounded-md border border-muted-foreground/30 bg-muted/30 px-2 py-1 text-muted-foreground">
                Non-fatal scan warnings: {repoTreeResponse?.errors.length}
              </div>
            ) : null}
            {visualTreeLines.map((line) => {
              const isFolder = line.node.type === "folder";
              const displayName = isFolder ? `${line.node.name}/` : line.node.name;

              return (
                <div
                  key={`${line.node.path}:${line.prefix}:${line.branch}`}
                  className="flex items-center gap-1 whitespace-pre text-foreground/90"
                >
                  <span className="text-muted-foreground">{line.prefix}{line.branch}</span>
                  {isFolder ? (
                    <Folder className="h-3.5 w-3.5" style={{ color: line.node.color || "#F59E0B" }} />
                  ) : (
                    <FileText className="h-3.5 w-3.5" style={{ color: line.node.color || "#0EA5E9" }} />
                  )}
                  <span>{displayName}</span>
                </div>
              );
            })}
          </div>
        ) : !isTreeLoading ? (
          <div className="px-6 py-4 text-sm text-muted-foreground">No repository tree data available yet.</div>
        ) : null}
      </CardContent>
    </Card>
  );
}
