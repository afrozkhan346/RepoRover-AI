from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.services.ast_parser import parse_project_code
from app.services.call_graph_service import build_call_graph
from app.services.dependency_graph_service import build_dependency_graph

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

PY_FUNCTION_RE = re.compile(r"^\s*(?:async\s+def|def)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE)
JS_FUNCTION_RE = re.compile(
    r"(?:function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(|const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:async\s*)?function\s*\()"
)
BRANCH_RE = re.compile(r"\b(if|elif|else|for|while|try|except|catch|switch|case)\b")


@dataclass(frozen=True)
class FileRisk:
    file_path: str
    complexity_score: float
    dependency_score: float
    centrality_score: float
    risk_score: float
    risk_level: str
    signals: list[str]


@dataclass(frozen=True)
class RiskReport:
    overall_risk_score: float
    formula: str
    files_scanned: int
    high_risk_files: list[FileRisk]
    failure_points: list[FileRisk]
    files: list[FileRisk]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def calculate_file_risk(ast_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Calculate file complexity risk from parsed AST payloads."""

    risks: list[dict[str, Any]] = []

    for file_entry in ast_data:
        data = file_entry.get("data") if isinstance(file_entry, dict) else None
        if not isinstance(data, dict):
            continue

        functions = data.get("functions")
        if not isinstance(functions, list):
            continue

        file_name = str(file_entry.get("file") or file_entry.get("path") or "unknown")
        num_funcs = len(functions)

        if num_funcs > 15:
            risks.append(
                {
                    "file": file_name,
                    "risk": "High complexity (too many functions)",
                    "score": 8,
                }
            )
        elif num_funcs > 8:
            risks.append(
                {
                    "file": file_name,
                    "risk": "Moderate complexity",
                    "score": 5,
                }
            )

    return risks


def calculate_graph_risk(G: Any) -> list[dict[str, Any]]:
    """Calculate graph centrality risk from a graph-like object with degree() support."""

    risks: list[dict[str, Any]] = []

    for node in getattr(G, "nodes", []):
        degree = G.degree(node)

        if degree > 10:
            risks.append(
                {
                    "node": node,
                    "risk": "Highly connected (single point of failure)",
                    "score": 9,
                }
            )

    return risks


def calculate_dependency_risk(ast_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Calculate dependency risk from import counts in parsed AST payloads."""

    risks: list[dict[str, Any]] = []

    for file_entry in ast_data:
        data = file_entry.get("data") if isinstance(file_entry, dict) else None
        if not isinstance(data, dict):
            continue

        imports = data.get("imports")
        if not isinstance(imports, list):
            continue

        file_name = str(file_entry.get("file") or file_entry.get("path") or "unknown")
        if len(imports) > 10:
            risks.append(
                {
                    "file": file_name,
                    "risk": "Too many dependencies",
                    "score": 7,
                }
            )

    return risks


def analyze_risks(ast_data: list[dict[str, Any]], G: Any) -> list[dict[str, Any]]:
    """Combine file, graph, and dependency risks into one list."""

    results: list[dict[str, Any]] = []

    results.extend(calculate_file_risk(ast_data))
    results.extend(calculate_graph_risk(G))
    results.extend(calculate_dependency_risk(ast_data))

    return results


class _GraphAdapter:
    def __init__(self, degree_map: dict[str, int]) -> None:
        self.nodes = list(degree_map.keys())
        self._degree_map = degree_map

    def degree(self, node: str) -> int:
        return self._degree_map.get(node, 0)


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


def _function_count(path: Path, content: str) -> int:
    if path.suffix.lower() == ".py":
        return len(PY_FUNCTION_RE.findall(content))

    count = 0
    for match in JS_FUNCTION_RE.finditer(content):
        if any(group for group in match.groups() if group):
            count += 1
    return count


def _complexity_score(path: Path, content: str) -> tuple[float, list[str]]:
    lines = len(content.splitlines())
    function_count = _function_count(path, content)
    branch_count = len(BRANCH_RE.findall(content))

    line_score = min(40.0, lines / 12.0)
    function_score = min(30.0, function_count * 2.5)
    branch_score = min(30.0, branch_count * 1.5)

    score = round(line_score + function_score + branch_score, 2)

    signals: list[str] = []
    if lines >= 450:
        signals.append(f"large file ({lines} lines)")
    if function_count >= 12:
        signals.append(f"many functions ({function_count})")
    if branch_count >= 20:
        signals.append(f"high branching density ({branch_count})")

    return score, signals


def _build_file_call_edges(call_graph) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    node_to_file: dict[str, str] = {}
    for node in call_graph.nodes:
        if node.file_path:
            node_to_file[node.id] = node.file_path

    outgoing_calls: dict[str, int] = {}
    incoming_calls: dict[str, int] = {}
    degree: dict[str, int] = {}

    for edge in call_graph.edges:
        if edge.edge_type != "calls":
            continue

        source_file = node_to_file.get(edge.source)
        target_file = node_to_file.get(edge.target)
        if not source_file or not target_file:
            continue
        if source_file == target_file:
            continue

        outgoing_calls[source_file] = outgoing_calls.get(source_file, 0) + 1
        incoming_calls[target_file] = incoming_calls.get(target_file, 0) + 1

        degree[source_file] = degree.get(source_file, 0) + 1
        degree[target_file] = degree.get(target_file, 0) + 1

    return outgoing_calls, incoming_calls, degree


def analyze_risk(local_path: str, max_files: int = 2000) -> dict[str, Any]:
    """
    Risk Analysis Engine (Failure & Impact Detection).

    Risk model:
        Risk = Complexity + Dependency + Centrality

    Each component is normalized to 0..100 and combined as a simple average.
    """

    root = Path(local_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("local_path must be an existing directory")

    files = _iter_source_files(root, max_files=max_files)
    rel_paths = [path.relative_to(root).as_posix() for path in files]

    ast_data = parse_project_code(str(root))
    file_complexity_risks = calculate_file_risk(ast_data)
    dependency_risks = calculate_dependency_risk(ast_data)

    dependency_graph = build_dependency_graph(str(root), max_files=max_files)
    call_graph = build_call_graph(str(root), max_files=max_files)

    import_outgoing: dict[str, int] = {}
    for edge in dependency_graph.edges:
        if edge.edge_type != "imports":
            continue
        if not edge.source.startswith("file:"):
            continue
        source_file = edge.source.replace("file:", "")
        import_outgoing[source_file] = import_outgoing.get(source_file, 0) + 1

    call_outgoing, call_incoming, file_degree = _build_file_call_edges(call_graph)
    graph_adapter = _GraphAdapter(file_degree)
    graph_centrality_risks = calculate_graph_risk(graph_adapter)
    combined_risks = analyze_risks(ast_data, graph_adapter)
    max_degree = max(file_degree.values(), default=0)

    scored_files: list[FileRisk] = []

    for path in files:
        rel = path.relative_to(root).as_posix()
        content = _read_text(path)

        complexity, complexity_signals = _complexity_score(path, content)

        if any(risk.get("file") == rel and risk.get("score") == 8 for risk in file_complexity_risks):
            complexity = min(100.0, complexity + 20.0)
            complexity_signals.append("file-level complexity risk: too many functions")
        elif any(risk.get("file") == rel and risk.get("score") == 5 for risk in file_complexity_risks):
            complexity = min(100.0, complexity + 10.0)
            complexity_signals.append("file-level complexity risk: moderate function density")

        if any(risk.get("file") == rel and risk.get("score") == 7 for risk in dependency_risks):
            dependency = min(100.0, dependency + 15.0)
            complexity_signals.append("dependency risk: too many imports")

        imports_count = import_outgoing.get(rel, 0)
        call_out = call_outgoing.get(rel, 0)
        call_in = call_incoming.get(rel, 0)
        dependency = round(min(100.0, imports_count * 4.0 + call_out * 6.0 + call_in * 4.0), 2)

        if max_degree > 0:
            centrality = round(min(100.0, (file_degree.get(rel, 0) / max_degree) * 100.0), 2)
        else:
            centrality = 0.0

        if any(str(risk.get("node", "")).endswith(rel) for risk in graph_centrality_risks):
            centrality = min(100.0, centrality + 25.0)
            signals.append("graph centrality risk: highly connected node")

        risk = round((complexity + dependency + centrality) / 3.0, 2)

        if risk >= 70:
            level = "high"
        elif risk >= 40:
            level = "medium"
        else:
            level = "low"

        signals = list(complexity_signals)
        if imports_count >= 10:
            signals.append(f"many imports ({imports_count})")
        if call_out >= 8:
            signals.append(f"high outward call coupling ({call_out})")
        if call_in >= 8:
            signals.append(f"central dependency target ({call_in} inbound calls)")
        if not signals:
            signals.append("no major risk signals detected")

        if any(item.get("file") == rel for item in combined_risks if "file" in item):
            signals.append("combined risk: flagged by rule-based engine")

        scored_files.append(
            FileRisk(
                file_path=rel,
                complexity_score=complexity,
                dependency_score=dependency,
                centrality_score=centrality,
                risk_score=risk,
                risk_level=level,
                signals=signals,
            )
        )

    scored_files.sort(key=lambda item: item.risk_score, reverse=True)

    high_risk_files = [item for item in scored_files if item.risk_level == "high"]
    failure_points = scored_files[: min(5, len(scored_files))]
    overall_risk = round(sum(item.risk_score for item in scored_files) / len(scored_files), 2) if scored_files else 0.0

    summary = (
        f"Risk analysis scanned {len(scored_files)} files. "
        f"High-risk files: {len(high_risk_files)}. "
        f"Top failure point: {failure_points[0].file_path if failure_points else 'none'}."
    )

    report = RiskReport(
        overall_risk_score=overall_risk,
        formula="Risk = Complexity + Dependency + Centrality (averaged)",
        files_scanned=len(scored_files),
        high_risk_files=high_risk_files,
        failure_points=failure_points,
        files=scored_files,
        summary=summary,
    )
    return report.to_dict()
