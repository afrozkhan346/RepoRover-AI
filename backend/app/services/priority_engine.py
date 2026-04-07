from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import networkx as nx

from app.services.ast_parser import parse_project_code
from app.services.call_graph_service import build_call_graph
from app.services.risk_analyzer import analyze_risk


@dataclass(frozen=True)
class RankedIssue:
    rank: int
    target_type: str
    target: str
    priority_score: float
    risk_score: float
    centrality_score: float
    complexity_score: float
    reason: str
    recommended_action: str


@dataclass(frozen=True)
class RankedFunction:
    rank: int
    function_id: str
    function_name: str
    file_path: str | None
    priority_score: float
    risk_score: float
    centrality_score: float
    complexity_score: float
    call_count: int


@dataclass(frozen=True)
class PriorityReport:
    formula: str
    files_scanned: int
    functions_scanned: int
    critical_issues: list[RankedIssue]
    important_functions: list[RankedFunction]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def rank_risks(risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(risks, key=lambda item: float(item.get("score", 0.0)), reverse=True)


def rank_functions(graph: nx.DiGraph, top_n: int = 5) -> list[tuple[str, float]]:
    centrality = nx.degree_centrality(graph) if graph.number_of_nodes() else {}

    func_scores: dict[str, float] = {}
    for node, score in centrality.items():
        if "func:" in node or "function:" in node:
            func_scores[node] = float(score)

    ranked = sorted(func_scores.items(), key=lambda item: item[1], reverse=True)
    return ranked[:top_n]


def generate_priority(
    ast_data: list[dict[str, Any]],
    graph: nx.DiGraph,
    risks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Combine risk ranking and function-importance ranking into one payload."""

    _ = ast_data
    ranked_risks = rank_risks(risks)
    top_functions = rank_functions(graph, top_n=5)

    normalized_risks: list[dict[str, Any]] = []
    for risk in ranked_risks[:5]:
        label = risk.get("file") or risk.get("node") or "unknown"
        normalized_risks.append(
            {
                "file": str(label),
                "risk": str(risk.get("risk") or "Risk signal"),
                "score": float(risk.get("score") or 0.0),
            }
        )

    return {
        "top_risks": normalized_risks,
        "important_functions": [
            [node_id, round(score, 6)] for node_id, score in top_functions
        ],
    }


def _safe_rel(root: Path, maybe_path: str | None) -> str | None:
    if not maybe_path:
        return None
    candidate = Path(maybe_path)
    try:
        return candidate.resolve().relative_to(root).as_posix()
    except Exception:
        normalized = maybe_path.replace("\\", "/")
        return normalized.strip("/")


def _build_function_complexity(ast_data: list[dict[str, Any]]) -> dict[str, float]:
    """
    Approximate function complexity from AST-like payloads.

    Score range: 0..100
    """

    complexity: dict[str, float] = {}

    for file_entry in ast_data:
        if not isinstance(file_entry, dict):
            continue

        file_name = str(file_entry.get("file") or file_entry.get("path") or "")
        data = file_entry.get("data") if isinstance(file_entry.get("data"), dict) else file_entry
        functions = data.get("functions") if isinstance(data.get("functions"), list) else []

        for function in functions:
            if not isinstance(function, dict):
                continue

            func_name = str(function.get("name") or "unknown")
            start_line = int(function.get("line") or 0)
            end_line = int(function.get("end_line") or 0)
            line_span = max(0, end_line - start_line + 1) if start_line and end_line and end_line >= start_line else 0

            calls = function.get("calls") if isinstance(function.get("calls"), list) else []
            call_count = len(calls)
            arg_count = len(function.get("arguments") or []) if isinstance(function.get("arguments"), list) else 0

            line_component = min(50.0, line_span * 1.2)
            call_component = min(35.0, call_count * 4.0)
            arg_component = min(15.0, arg_count * 2.0)

            # For JS/TS payloads where line spans may be missing, keep a sensible floor.
            if line_span == 0:
                line_component = 12.0

            score = round(min(100.0, line_component + call_component + arg_component), 2)
            function_id = f"function:{file_name}:{func_name}"
            complexity[function_id] = score

    return complexity


def _build_function_graph_scores(local_path: str) -> tuple[dict[str, float], dict[str, int], dict[str, tuple[str, str | None]]]:
    call_graph = build_call_graph(local_path)
    graph = nx.DiGraph()

    labels: dict[str, tuple[str, str | None]] = {}

    for node in call_graph.nodes:
        graph.add_node(node.id, node_type=node.node_type)
        labels[node.id] = (node.label, node.file_path)

    for edge in call_graph.edges:
        graph.add_edge(edge.source, edge.target)

    degree = nx.degree_centrality(graph) if graph.number_of_nodes() else {}

    function_scores: dict[str, float] = {}
    function_calls: dict[str, int] = {}

    for node_id, data in graph.nodes(data=True):
        if data.get("node_type") != "function":
            continue

        out_degree = graph.out_degree(node_id)
        score = degree.get(node_id, 0.0) * 100.0
        function_scores[node_id] = round(min(100.0, score), 2)
        function_calls[node_id] = int(out_degree)

    # Keep an explicit top list helper available for callers that only need the top N.
    _ = rank_functions(graph, top_n=5)

    return function_scores, function_calls, labels


def analyze_priority(local_path: str, top_n: int = 5, max_files: int = 2000) -> dict[str, Any]:
    """
    Priority Engine (Ranking + Importance Scoring).

    Priority Score = Risk Score + Graph Centrality + Complexity
    """

    root = Path(local_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("local_path must be an existing directory")

    risk_report = analyze_risk(str(root), max_files=max_files)
    ast_data = parse_project_code(str(root))

    file_risks = risk_report.get("files") if isinstance(risk_report.get("files"), list) else []
    file_risk_map: dict[str, dict[str, Any]] = {}
    for entry in file_risks:
        if not isinstance(entry, dict):
            continue
        rel = str(entry.get("file_path") or "")
        if rel:
            file_risk_map[rel] = entry

    function_complexity = _build_function_complexity(ast_data)
    function_centrality, function_call_count, function_meta = _build_function_graph_scores(str(root))

    ranked_functions: list[RankedFunction] = []
    for function_id, centrality in function_centrality.items():
        parts = function_id.split(":", 2)
        file_path = parts[1] if len(parts) > 2 else None
        function_name = function_meta.get(function_id, (parts[-1], file_path))[0]

        file_risk = file_risk_map.get(file_path or "", {})
        risk_score = float(file_risk.get("risk_score") or 0.0)
        complexity_score = float(function_complexity.get(function_id) or 12.0)

        priority_score = round(risk_score + centrality + complexity_score, 2)

        ranked_functions.append(
            RankedFunction(
                rank=0,
                function_id=function_id,
                function_name=function_name,
                file_path=file_path,
                priority_score=priority_score,
                risk_score=round(risk_score, 2),
                centrality_score=round(centrality, 2),
                complexity_score=round(complexity_score, 2),
                call_count=int(function_call_count.get(function_id, 0)),
            )
        )

    ranked_functions.sort(key=lambda item: item.priority_score, reverse=True)
    top_functions = ranked_functions[:top_n]
    top_functions = [
        RankedFunction(
            rank=index + 1,
            function_id=item.function_id,
            function_name=item.function_name,
            file_path=item.file_path,
            priority_score=item.priority_score,
            risk_score=item.risk_score,
            centrality_score=item.centrality_score,
            complexity_score=item.complexity_score,
            call_count=item.call_count,
        )
        for index, item in enumerate(top_functions)
    ]

    ranked_risk_items = rank_risks(
        [
            {
                "file_path": item.get("file_path"),
                "risk_score": item.get("risk_score", 0.0),
                "centrality_score": item.get("centrality_score", 0.0),
                "complexity_score": item.get("complexity_score", 0.0),
                "signals": item.get("signals", []),
                "score": float(item.get("risk_score") or 0.0)
                + float(item.get("centrality_score") or 0.0)
                + float(item.get("complexity_score") or 0.0),
            }
            for item in file_risks
            if isinstance(item, dict)
        ]
    )

    critical_issues: list[RankedIssue] = []
    for index, file_item in enumerate(ranked_risk_items):
        if not isinstance(file_item, dict):
            continue
        if index >= top_n:
            break

        file_path = str(file_item.get("file_path") or "unknown")
        risk_score = float(file_item.get("risk_score") or 0.0)
        centrality_score = float(file_item.get("centrality_score") or 0.0)
        complexity_score = float(file_item.get("complexity_score") or 0.0)
        priority_score = round(float(file_item.get("score") or 0.0), 2)

        signals = file_item.get("signals") if isinstance(file_item.get("signals"), list) else []
        reason = "; ".join(str(signal) for signal in signals[:3]) if signals else "High combined score"

        if complexity_score >= 60:
            action = "Refactor long/high-branching functions into smaller units"
        elif centrality_score >= 60:
            action = "Reduce coupling by extracting interfaces and isolating dependencies"
        elif risk_score >= 60:
            action = "Add tests and error handling around this high-risk file"
        else:
            action = "Review this file for maintainability and dependency reduction"

        critical_issues.append(
            RankedIssue(
                rank=index + 1,
                target_type="file",
                target=file_path,
                priority_score=priority_score,
                risk_score=round(risk_score, 2),
                centrality_score=round(centrality_score, 2),
                complexity_score=round(complexity_score, 2),
                reason=reason,
                recommended_action=action,
            )
        )

    summary = (
        f"Priority engine scanned {risk_report.get('files_scanned', 0)} files and "
        f"{len(ranked_functions)} functions. "
        f"Top issue: {critical_issues[0].target if critical_issues else 'none'}. "
        f"Top function: {top_functions[0].function_name if top_functions else 'none'}."
    )

    report = PriorityReport(
        formula="Priority Score = Risk Score + Graph Centrality + Complexity",
        files_scanned=int(risk_report.get("files_scanned") or 0),
        functions_scanned=len(ranked_functions),
        critical_issues=critical_issues,
        important_functions=top_functions,
        summary=summary,
    )
    return report.to_dict()
