from __future__ import annotations

from collections import Counter, deque
from pathlib import Path

from app.schemas.project_summaries import ProjectSummariesResponse, SummaryMetrics
from app.services.call_graph_service import build_call_graph
from app.services.dependency_graph_service import build_dependency_graph

SOURCE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".sql", ".css", ".html"}
IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".next",
    "dist",
    "build",
    "venv",
    ".venv",
    "__pycache__",
}

LANGUAGE_MAP = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".json": "JSON",
    ".md": "Markdown",
    ".sql": "SQL",
    ".css": "CSS",
    ".html": "HTML",
}


def _iter_source_files(root: Path, max_files: int) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        files.append(path)
        if len(files) >= max_files:
            break
    return files


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _language_breakdown(paths: list[Path]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for file_path in paths:
        language = LANGUAGE_MAP.get(file_path.suffix.lower(), "Other")
        counts[language] += 1
    return dict(counts)


def _top_dependencies(dependency_graph, top_n: int = 8) -> list[str]:
    imports: Counter[str] = Counter()
    for edge in dependency_graph.edges:
        if edge.edge_type != "imports":
            continue
        imports[edge.target.replace("import:", "")] += 1
    return [name for name, _ in imports.most_common(top_n)]


def _top_modules_by_outgoing(dependency_graph, top_n: int = 8) -> list[str]:
    outgoing: Counter[str] = Counter()
    for edge in dependency_graph.edges:
        if edge.edge_type == "imports" and edge.source.startswith("file:"):
            outgoing[edge.source.replace("file:", "")] += 1
    return [name for name, _ in outgoing.most_common(top_n)]


def _execution_flow(call_graph, max_steps: int = 12) -> list[str]:
    adjacency: dict[str, list[str]] = {}
    out_degree: Counter[str] = Counter()

    for edge in call_graph.edges:
        if edge.edge_type != "calls":
            continue
        adjacency.setdefault(edge.source, []).append(edge.target)
        out_degree[edge.source] += 1

    if not out_degree:
        return []

    start = out_degree.most_common(1)[0][0]
    visited: set[str] = set()
    queue: deque[str] = deque([start])
    order: list[str] = []

    while queue and len(order) < max_steps:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        order.append(node)
        for nxt in adjacency.get(node, []):
            if nxt not in visited:
                queue.append(nxt)

    return order


def _node_label_map(call_graph) -> dict[str, str]:
    return {node.id: node.label for node in call_graph.nodes}


def summarize_project(local_path: str, max_files: int = 2000) -> ProjectSummariesResponse:
    root = Path(local_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("local_path must be an existing directory")

    source_files = _iter_source_files(root, max_files=max_files)
    total_lines = sum(len(_read_text(path).splitlines()) for path in source_files)
    language_breakdown = _language_breakdown(source_files)

    dependency_graph = build_dependency_graph(str(root), max_files=max_files)
    call_graph = build_call_graph(str(root), max_files=max_files)

    key_dependencies = _top_dependencies(dependency_graph)
    key_modules = _top_modules_by_outgoing(dependency_graph)

    flow_ids = _execution_flow(call_graph)
    labels = _node_label_map(call_graph)
    flow_path = [labels.get(node_id, node_id) for node_id in flow_ids]

    project_summary = (
        f"Scanned {len(source_files)} files and {total_lines} lines across "
        f"{len(language_breakdown)} primary language groups. "
        f"Most represented language: {max(language_breakdown, key=language_breakdown.get) if language_breakdown else 'Unknown'}."
    )

    architecture_summary = (
        "Architecture appears module-centric with import-heavy files acting as coordination hubs. "
        f"Primary modules by outgoing dependencies: {', '.join(key_modules[:5]) if key_modules else 'none detected'}. "
        f"Most referenced dependencies: {', '.join(key_dependencies[:5]) if key_dependencies else 'none detected'}."
    )

    execution_flow_summary = (
        "Likely execution flow was inferred from call relationships by selecting the highest out-degree caller "
        "and traversing reachable call nodes breadth-first. "
        f"Flow preview: {' -> '.join(flow_path[:8]) if flow_path else 'insufficient call edges for flow extraction'}."
    )

    metrics = SummaryMetrics(
        files_scanned=len(source_files),
        total_lines=total_lines,
        language_breakdown=language_breakdown,
        dependency_edges=dependency_graph.summary.total_edges,
        call_edges=call_graph.summary.call_edges,
    )

    return ProjectSummariesResponse(
        project_summary=project_summary,
        architecture_summary=architecture_summary,
        execution_flow_summary=execution_flow_summary,
        key_modules=key_modules,
        key_dependencies=key_dependencies,
        flow_path=flow_path,
        metrics=metrics,
    )
