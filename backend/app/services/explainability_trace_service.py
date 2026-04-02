from __future__ import annotations

import re
from collections import Counter, deque
from pathlib import Path

from app.schemas.explainability_traces import (
    AstTrace,
    ExplainabilityTraceResponse,
    FindingTrace,
    GraphTrace,
    TokenTrace,
)
from app.services.call_graph_service import build_call_graph
from app.services.dependency_graph_service import build_dependency_graph
from app.services.parser_service import parse_structure
from app.services.token_service import tokenize_source

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


def _resolve_focus_file(root: Path, files: list[Path], focus_file: str | None) -> Path:
    if focus_file:
        candidate = (root / focus_file).resolve()
        if candidate.exists() and candidate.is_file() and candidate.suffix.lower() in SOURCE_EXTENSIONS:
            return candidate
        raise ValueError("focus_file must reference an existing source file under local_path")

    if not files:
        raise ValueError("No supported source files found for trace generation")

    # Choose the largest source file as the default trace target.
    return max(files, key=lambda item: item.stat().st_size if item.exists() else 0)


def _extract_findings(content: str, focus_rel: str) -> list[FindingTrace]:
    findings: list[FindingTrace] = []

    if "TODO" in content or "FIXME" in content:
        findings.append(
            FindingTrace(
                finding_id="finding-todo",
                title="Deferred work markers present",
                severity="low",
                evidence_type="text-pattern",
                evidence=f"TODO/FIXME markers detected in {focus_rel}.",
            )
        )

    if len(content.splitlines()) > 350:
        findings.append(
            FindingTrace(
                finding_id="finding-large-file",
                title="Large file footprint",
                severity="medium",
                evidence_type="size-metric",
                evidence=f"{focus_rel} has more than 350 lines.",
            )
        )

    if re.search(r"except\s+Exception\s*:", content):
        findings.append(
            FindingTrace(
                finding_id="finding-broad-exception",
                title="Broad exception handling",
                severity="high",
                evidence_type="syntax-pattern",
                evidence="Detected except Exception pattern in focus file.",
            )
        )

    if not findings:
        findings.append(
            FindingTrace(
                finding_id="finding-structural",
                title="Structural baseline finding",
                severity="low",
                evidence_type="analysis-baseline",
                evidence="No high-risk local file patterns detected; generated baseline explainability trace.",
            )
        )

    return findings


def _token_traces(findings: list[FindingTrace], focus_rel: str, content: str, extension: str) -> list[TokenTrace]:
    token_result = tokenize_source(
        content,
        file_extension=extension,
        max_tokens=400,
    )
    interesting_tokens = [
        token
        for token in token_result.tokens
        if token.token_type.lower() in {"identifier", "import", "def", "function", "class", "call_expression", "comment"}
        or (token.lexeme and token.lexeme.strip() in {"def", "class", "function", "import", "from"})
    ]

    if not interesting_tokens:
        interesting_tokens = token_result.tokens[:20]

    traces: list[TokenTrace] = []
    for finding in findings:
        for token in interesting_tokens[:6]:
            traces.append(
                TokenTrace(
                    finding_id=finding.finding_id,
                    file_path=focus_rel,
                    token_type=token.token_type,
                    lexeme=token.lexeme[:80],
                    start_point=token.start_point,
                    end_point=token.end_point,
                )
            )
    return traces


def _ast_traces(findings: list[FindingTrace], focus_rel: str, content: str, extension: str) -> list[AstTrace]:
    ast = parse_structure(
        content,
        file_extension=extension,
        max_tree_nodes=500,
        max_depth=8,
    )

    units = ast.imports[:4] + ast.classes[:4] + ast.functions[:8]
    if not units:
        units = [
            type("_Unit", (), {
                "unit_type": ast.root.node_type,
                "name": None,
                "start_point": ast.root.start_point,
                "end_point": ast.root.end_point,
            })()
        ]

    traces: list[AstTrace] = []
    for finding in findings:
        for unit in units[:8]:
            traces.append(
                AstTrace(
                    finding_id=finding.finding_id,
                    file_path=focus_rel,
                    unit_type=unit.unit_type,
                    name=unit.name,
                    start_point=unit.start_point,
                    end_point=unit.end_point,
                )
            )
    return traces


def _graph_hotspot_and_path(local_path: str, graph_type: str, max_files: int) -> tuple[str, list[str]]:
    normalized = graph_type.strip().lower()

    if normalized == "dependency":
        graph = build_dependency_graph(local_path, max_files=max_files)
        edges = [edge for edge in graph.edges if edge.edge_type in {"imports", "declares"}]
    else:
        normalized = "call"
        graph = build_call_graph(local_path, max_files=max_files)
        edges = [edge for edge in graph.edges if edge.edge_type in {"calls", "imports-context", "defines"}]

    if not edges:
        return normalized, []

    out_degree: Counter[str] = Counter()
    adjacency: dict[str, list[str]] = {}
    for edge in edges:
        out_degree[edge.source] += 1
        adjacency.setdefault(edge.source, []).append(edge.target)

    start = out_degree.most_common(1)[0][0]
    visited: set[str] = set()
    queue: deque[str] = deque([start])
    order: list[str] = []

    while queue and len(order) < 12:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        order.append(node)
        for nxt in adjacency.get(node, []):
            if nxt not in visited:
                queue.append(nxt)

    return normalized, order


def build_explainability_traces(
    *,
    local_path: str,
    max_files: int = 2000,
    focus_file: str | None = None,
    graph_type: str = "call",
) -> ExplainabilityTraceResponse:
    root = Path(local_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("local_path must be an existing directory")

    source_files = _iter_source_files(root, max_files=max_files)
    focus = _resolve_focus_file(root, source_files, focus_file)
    focus_rel = focus.relative_to(root).as_posix()
    content = _read_text(focus)

    findings = _extract_findings(content, focus_rel)
    token_traces = _token_traces(findings, focus_rel, content, focus.suffix.lower())
    ast_traces = _ast_traces(findings, focus_rel, content, focus.suffix.lower())

    normalized_graph_type, graph_path = _graph_hotspot_and_path(str(root), graph_type, max_files)
    graph_traces = [
        GraphTrace(
            finding_id=finding.finding_id,
            graph_type=normalized_graph_type,
            start_node=graph_path[0] if graph_path else "none",
            path=graph_path,
        )
        for finding in findings
    ]

    summary = (
        f"Generated explainability traces for {len(findings)} findings in {focus_rel}. "
        f"Each finding is linked to token, AST, and {normalized_graph_type} graph-path evidence."
    )

    return ExplainabilityTraceResponse(
        focus_file=focus_rel,
        findings=findings,
        token_traces=token_traces,
        ast_traces=ast_traces,
        graph_traces=graph_traces,
        summary=summary,
    )
