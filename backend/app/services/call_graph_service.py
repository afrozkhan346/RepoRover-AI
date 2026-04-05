from __future__ import annotations

import re
from pathlib import Path

import networkx as nx

from app.schemas.call_graph import (
    CallGraphAnalytics,
    CallGraphEdge,
    CallGraphNode,
    CallGraphResponse,
    CallGraphSummary,
    CallGraphRankedNode,
)

SOURCE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx"}
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

PY_DEF_RE = re.compile(r"^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE)
PY_CALL_RE = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")
PY_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([a-zA-Z0-9_\.]+)", re.MULTILINE)

JS_FUNC_RE = re.compile(
    r"(?:function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(|const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*\([^)]*\)\s*=>|const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*function\s*\()"
)
JS_CALL_RE = re.compile(r"([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(")
JS_IMPORT_RE = re.compile(
    r"import\s+[^;]*?from\s+[\"']([^\"']+)[\"']|import\s+[\"']([^\"']+)[\"']|require\(\s*[\"']([^\"']+)[\"']\s*\)"
)


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


def _extract_functions(path: Path, text: str) -> set[str]:
    suffix = path.suffix.lower()
    names: set[str] = set()

    if suffix == ".py":
        names.update(match.group(1) for match in PY_DEF_RE.finditer(text))
    else:
        for match in JS_FUNC_RE.finditer(text):
            for group in match.groups():
                if group:
                    names.add(group)

    return names


def _extract_calls(path: Path, text: str) -> list[str]:
    suffix = path.suffix.lower()
    calls: list[str] = []

    if suffix == ".py":
        calls.extend(match.group(1) for match in PY_CALL_RE.finditer(text))
    else:
        calls.extend(match.group(1) for match in JS_CALL_RE.finditer(text))

    return calls


def _extract_import_contexts(path: Path, text: str) -> set[str]:
    suffix = path.suffix.lower()
    contexts: set[str] = set()

    if suffix == ".py":
        contexts.update(match.group(1) for match in PY_IMPORT_RE.finditer(text))
    else:
        for match in JS_IMPORT_RE.finditer(text):
            value = next((group for group in match.groups() if group), None)
            if value:
                contexts.add(value)

    return {ctx.strip() for ctx in contexts if ctx.strip()}


def _ranked(metric: dict[str, float], labels: dict[str, str], top_n: int = 10) -> list[CallGraphRankedNode]:
    ordered = sorted(metric.items(), key=lambda item: item[1], reverse=True)[:top_n]
    return [
        CallGraphRankedNode(node_id=node_id, label=labels.get(node_id, node_id), score=float(score))
        for node_id, score in ordered
    ]


def _build_networkx_call_graph(root: Path, files: list[Path]) -> nx.DiGraph:
    graph = nx.DiGraph()
    function_index: dict[str, list[str]] = {}
    file_functions: dict[str, set[str]] = {}
    file_calls: dict[str, list[str]] = {}
    file_imports: dict[str, set[str]] = {}

    for file_path in files:
        rel = file_path.relative_to(root).as_posix()
        file_node_id = f"file:{rel}"
        graph.add_node(file_node_id, node_type="file", label=rel, file_path=rel)

        text = _read_text(file_path)
        functions = _extract_functions(file_path, text)
        calls = _extract_calls(file_path, text)
        imports = _extract_import_contexts(file_path, text)

        file_functions[rel] = functions
        file_calls[rel] = calls
        file_imports[rel] = imports

        for function_name in sorted(functions):
            function_node_id = f"function:{rel}:{function_name}"
            graph.add_node(
                function_node_id,
                node_type="function",
                label=function_name,
                file_path=rel,
            )
            function_index.setdefault(function_name, []).append(function_node_id)
            graph.add_edge(file_node_id, function_node_id, edge_type="defines")

    for rel, calls in file_calls.items():
        caller_file_node = f"file:{rel}"
        caller_functions = [f"function:{rel}:{fn}" for fn in file_functions.get(rel, set())]
        caller_source = caller_functions[0] if caller_functions else caller_file_node

        for call_name in calls:
            if call_name in {"if", "for", "while", "return", "print"}:
                continue

            targets = function_index.get(call_name, [])
            if not targets:
                external_id = f"external:{call_name}"
                if external_id not in graph:
                    graph.add_node(external_id, node_type="external", label=call_name)
                graph.add_edge(caller_source, external_id, edge_type="calls")
                continue

            for target_id in targets:
                if target_id == caller_source:
                    continue
                graph.add_edge(caller_source, target_id, edge_type="calls")

    for rel, imports in file_imports.items():
        file_node_id = f"file:{rel}"
        for imported in sorted(imports):
            import_node_id = f"import-context:{imported}"
            if import_node_id not in graph:
                graph.add_node(import_node_id, node_type="import-context", label=imported)
            graph.add_edge(file_node_id, import_node_id, edge_type="imports-context")

    graph.graph["files_scanned"] = len(files)
    graph.graph["functions_found"] = sum(len(items) for items in file_functions.values())
    graph.graph["call_edges"] = sum(1 for _, _, data in graph.edges(data=True) if data.get("edge_type") == "calls")
    graph.graph["import_context_edges"] = sum(
        1 for _, _, data in graph.edges(data=True) if data.get("edge_type") == "imports-context"
    )
    return graph


def _build_response(graph: nx.DiGraph, root: Path) -> CallGraphResponse:
    nodes = [
        CallGraphNode(
            id=node_id,
            node_type=data.get("node_type", "unknown"),
            label=data.get("label", node_id),
            file_path=data.get("file_path"),
        )
        for node_id, data in graph.nodes(data=True)
    ]
    edges = [
        CallGraphEdge(source=source, target=target, edge_type=data.get("edge_type", "calls"))
        for source, target, data in graph.edges(data=True)
    ]

    summary = CallGraphSummary(
        files_scanned=int(graph.graph.get("files_scanned", 0)),
        functions_found=int(graph.graph.get("functions_found", 0)),
        call_edges=int(graph.graph.get("call_edges", 0)),
        import_context_edges=int(graph.graph.get("import_context_edges", 0)),
        total_nodes=graph.number_of_nodes(),
        total_edges=graph.number_of_edges(),
    )

    labels = {node_id: data.get("label", node_id) for node_id, data in graph.nodes(data=True)}
    degree = nx.degree_centrality(graph) if graph.number_of_nodes() else {}
    betweenness = nx.betweenness_centrality(graph) if graph.number_of_nodes() else {}
    impact = {
        node: float(degree.get(node, 0.0) * 0.45 + betweenness.get(node, 0.0) * 0.35 + graph.out_degree(node) * 0.2)
        for node in graph.nodes
    }

    analytics = CallGraphAnalytics(
        top_degree_centrality=_ranked(degree, labels),
        top_betweenness_centrality=_ranked(betweenness, labels),
        top_impact_rank=_ranked(impact, labels),
        strongly_connected_components=nx.number_strongly_connected_components(graph) if graph.number_of_nodes() else 0,
        cycle_count=sum(1 for _ in nx.simple_cycles(graph)) if graph.number_of_nodes() else 0,
    )

    return CallGraphResponse(root=str(root), nodes=nodes, edges=edges, summary=summary, analytics=analytics)


def build_call_graph(local_path: str, max_files: int = 2000) -> CallGraphResponse:
    root = Path(local_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("local_path must be an existing directory")

    files = _iter_source_files(root, max_files=max_files)
    graph = _build_networkx_call_graph(root, files)
    return _build_response(graph, root)


def build_call_graph_analytics(local_path: str, max_files: int = 2000) -> CallGraphAnalytics:
    root = Path(local_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("local_path must be an existing directory")

    files = _iter_source_files(root, max_files=max_files)
    graph = _build_networkx_call_graph(root, files)
    response = _build_response(graph, root)
    if response.analytics is None:
        return CallGraphAnalytics(
            top_degree_centrality=[],
            top_betweenness_centrality=[],
            top_impact_rank=[],
            strongly_connected_components=0,
            cycle_count=0,
        )
    return response.analytics
