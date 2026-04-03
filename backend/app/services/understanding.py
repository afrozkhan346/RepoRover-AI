from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from textwrap import dedent
from typing import Any

import networkx as nx

from app.services.call_graph_service import build_call_graph
from app.services.dependency_graph_service import build_dependency_graph
from app.services.ast_parser import parse_project_code
from app.services.graph_builder import build_graph
from app.services.parser import parse_project
from app.services.project_summary_service import summarize_project

SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".md",
    ".toml",
    ".yml",
    ".yaml",
}

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

ENTRY_FILE_NAMES = {
    "__main__.py",
    "app.py",
    "main.py",
    "run.py",
    "server.py",
    "wsgi.py",
    "asgi.py",
    "manage.py",
    "index.js",
    "main.js",
    "server.js",
    "index.ts",
    "main.ts",
    "index.tsx",
    "main.tsx",
    "app.tsx",
    "App.tsx",
}

ENTRY_HINTS = (
    (re.compile(r"if\s+__name__\s*==\s*['\"]__main__['\"]"), 100, "contains a Python main guard"),
    (re.compile(r"uvicorn\.run\("), 50, "starts a Uvicorn server"),
    (re.compile(r"FastAPI\("), 35, "creates a FastAPI application"),
    (re.compile(r"ReactDOM\.createRoot|createRoot\("), 35, "bootstraps a React application"),
    (re.compile(r"app\.listen\(|createServer\("), 20, "starts a Node server"),
    (re.compile(r"def\s+main\s*\("), 20, "defines a Python main function"),
)


@dataclass(frozen=True)
class EntryFileInfo:
    path: str
    reason: str
    confidence: float


@dataclass(frozen=True)
class CoreFunctionInfo:
    name: str
    file_path: str | None
    score: float
    incoming_calls: int
    outgoing_calls: int


@dataclass(frozen=True)
class ProjectUnderstandingResult:
    project_path: str
    project_summary: str
    architecture_summary: str
    execution_summary: str
    entry_file: EntryFileInfo | None
    core_functions: list[CoreFunctionInfo]
    technology_signals: list[str]
    metrics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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


def detect_entry_point(files: list[dict[str, str]]) -> str | None:
    """
    Detect project entry file using common bootstrap names.

    Expected input shape:
    [{"name": "main.py"}, {"name": "src/index.ts"}, ...]
    """
    for file in files:
        name = (file.get("name") or "").lower()
        base = Path(name).name

        if base in {"main.py", "app.py", "index.js", "server.js"}:
            return file.get("name")

    return files[0].get("name") if files else None


def find_core_functions(g: nx.Graph) -> list[str]:
    """
    Rank function nodes by graph degree and return top 5.
    """
    importance: dict[str, int] = {}

    for node in g.nodes:
        if isinstance(node, str) and ("func:" in node or "function:" in node):
            importance[node] = int(g.degree(node))

    sorted_funcs = sorted(importance.items(), key=lambda item: item[1], reverse=True)
    return [func for func, _ in sorted_funcs[:5]]


def infer_project_type(files: list[dict[str, str]]) -> str:
    """Infer a coarse project type from file extensions."""
    extensions = [file.get("extension", "").lower().lstrip(".") for file in files]

    if "py" in extensions:
        return "Python Application"
    if "js" in extensions:
        return "JavaScript Application"
    return "General Software Project"


def generate_summary(entry: str | None, core_funcs: list[str], project_type: str) -> str:
    """Generate a simple natural-language summary for project understanding."""
    entry_text = entry or "an inferred startup module"
    core_text = ", ".join(core_funcs) if core_funcs else "no dominant functions detected"

    summary = dedent(
        f"""
    This is a {project_type}.

    The main entry point is {entry_text}.

    Core functionalities are handled by functions like:
    {core_text}.

    The system processes data and executes operations based on modular structure.
    """
    )

    return summary.strip()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _guess_technology_signals(root: Path) -> list[str]:
    signals: list[str] = []

    if (root / "frontend").exists():
        signals.append("Frontend directory detected")
    if (root / "backend").exists():
        signals.append("Backend directory detected")
    if (root / "frontend" / "package.json").exists() or (root / "package.json").exists():
        signals.append("JavaScript/TypeScript application detected")
    if (root / "backend" / "pyproject.toml").exists() or (root / "backend" / "requirements.txt").exists():
        signals.append("Python backend detected")

    package_json = root / "package.json"
    if package_json.exists():
        try:
            payload = json.loads(_read_text(package_json))
        except json.JSONDecodeError:
            payload = {}

        dependencies = {**(payload.get("dependencies") or {}), **(payload.get("devDependencies") or {})}
        if "next" in dependencies:
            signals.append("Next.js stack detected")
        if "react" in dependencies:
            signals.append("React stack detected")
        if "vite" in dependencies:
            signals.append("Vite build tooling detected")

    pyproject = root / "backend" / "pyproject.toml"
    requirements = root / "backend" / "requirements.txt"
    backend_manifest = pyproject if pyproject.exists() else requirements
    backend_text = _read_text(backend_manifest) if backend_manifest.exists() else ""
    if "fastapi" in backend_text.lower():
        signals.append("FastAPI backend detected")
    if "networkx" in backend_text.lower():
        signals.append("Graph analysis library detected")

    return signals


def _score_entry_candidate(path: Path, text: str, root: Path) -> tuple[float, str]:
    score = 0.0
    reasons: list[str] = []

    if path.name in ENTRY_FILE_NAMES:
        score += 20.0
        reasons.append("matches a common entry file name")

    if path.parent == root:
        score += 3.0
        reasons.append("lives at the project root")

    for pattern, bonus, reason in ENTRY_HINTS:
        if pattern.search(text):
            score += float(bonus)
            reasons.append(reason)

    if "src" in path.parts and path.suffix.lower() in {".tsx", ".ts", ".js", ".jsx"}:
        score += 5.0
        reasons.append("is located in a common frontend entry folder")

    if path.suffix.lower() == ".py" and "class" not in text.lower():
        score += 2.0
        reasons.append("looks like a small bootstrap module")

    if not reasons:
        reasons.append("no explicit entry hint found")

    return score, "; ".join(reasons)


def _detect_entry_file(root: Path, files: list[Path]) -> EntryFileInfo | None:
    simple_entry = detect_entry_point([{"name": path.relative_to(root).as_posix()} for path in files])
    if simple_entry:
        return EntryFileInfo(path=simple_entry, reason="matches common entry-point naming", confidence=0.7)

    best_path: Path | None = None
    best_score = 0.0
    best_reason = ""

    for path in files:
        text = _read_text(path)
        score, reason = _score_entry_candidate(path, text, root)
        if score > best_score:
            best_path = path
            best_score = score
            best_reason = reason

    if best_path is None or best_score <= 0:
        return None

    confidence = min(0.99, round(best_score / 120.0, 2))
    return EntryFileInfo(path=best_path.relative_to(root).as_posix(), reason=best_reason, confidence=confidence)


def _extract_core_functions(call_graph, root: Path, top_n: int = 8) -> list[CoreFunctionInfo]:
    nx_graph = nx.DiGraph()
    for node in call_graph.nodes:
        nx_graph.add_node(node.id)
    for edge in call_graph.edges:
        nx_graph.add_edge(edge.source, edge.target)

    top_nodes = find_core_functions(nx_graph)
    if top_nodes:
        node_lookup = {node.id: node for node in call_graph.nodes}
        incoming = Counter[str]()
        outgoing = Counter[str]()
        for edge in call_graph.edges:
            if edge.edge_type != "calls":
                continue
            outgoing[edge.source] += 1
            incoming[edge.target] += 1

        ranked: list[CoreFunctionInfo] = []
        for node_id in top_nodes[:top_n]:
            node = node_lookup.get(node_id)
            if not node:
                continue
            degree_score = float(nx_graph.degree(node_id))
            ranked.append(
                CoreFunctionInfo(
                    name=node.label,
                    file_path=node.file_path,
                    score=degree_score,
                    incoming_calls=incoming.get(node_id, 0),
                    outgoing_calls=outgoing.get(node_id, 0),
                )
            )
        if ranked:
            return ranked

    function_nodes = [node for node in call_graph.nodes if node.node_type == "function"]
    if not function_nodes:
        return []

    labels = {node.id: node.label for node in function_nodes}
    file_paths = {node.id: node.file_path for node in function_nodes}
    incoming = Counter[str]()
    outgoing = Counter[str]()

    for edge in call_graph.edges:
        if edge.edge_type != "calls":
            continue
        outgoing[edge.source] += 1
        incoming[edge.target] += 1

    scores: list[CoreFunctionInfo] = []
    for node in function_nodes:
        out_count = outgoing.get(node.id, 0)
        in_count = incoming.get(node.id, 0)
        score = float(out_count * 2 + in_count * 3)

        if node.file_path and Path(node.file_path).name in ENTRY_FILE_NAMES:
            score += 4.0

        if node.label.lower() in {"main", "run", "start", "create_app", "app"}:
            score += 3.0

        scores.append(
            CoreFunctionInfo(
                name=labels.get(node.id, node.id),
                file_path=file_paths.get(node.id),
                score=round(score, 2),
                incoming_calls=in_count,
                outgoing_calls=out_count,
            )
        )

    scores.sort(key=lambda item: (item.score, item.incoming_calls, item.outgoing_calls), reverse=True)
    return scores[:top_n]


def _build_execution_summary(entry_file: EntryFileInfo | None, core_functions: list[CoreFunctionInfo]) -> str:
    if not entry_file:
        return "No explicit entry file was detected, so the project execution path was inferred from the highest-scoring core functions."

    if not core_functions:
        return f"Execution likely starts in {entry_file.path}, but no callable core functions were found to trace further."

    core_preview = ", ".join(function.name for function in core_functions[:4])
    return (
        f"Execution likely begins in {entry_file.path} and flows through core functions such as {core_preview}. "
        f"The entry file was selected because it {entry_file.reason}."
    )


def _build_project_summary(root: Path, source_file_count: int, technology_signals: list[str], entry_file: EntryFileInfo | None) -> str:
    project_kind = "mixed full-stack" if any("Frontend" in signal for signal in technology_signals) and any("Backend" in signal for signal in technology_signals) else "software"
    signal_text = "; ".join(technology_signals[:4]) if technology_signals else "no strong technology signals detected"
    entry_text = entry_file.path if entry_file else "no obvious entry file"

    return (
        f"This {project_kind} repository contains {source_file_count} source files under {root.name}. "
        f"Detected signals: {signal_text}. Entry point candidate: {entry_text}."
    )


def _build_architecture_summary(dependency_graph, call_graph) -> str:
    dependency_edges = getattr(getattr(dependency_graph, "summary", None), "total_edges", 0)
    call_edges = getattr(getattr(call_graph, "summary", None), "call_edges", 0)

    if dependency_edges and call_edges:
        return (
            "Architecture appears layered around module dependencies and function call flow. "
            f"Dependency edges: {dependency_edges}; call edges: {call_edges}."
        )
    if dependency_edges:
        return f"Architecture appears dependency-driven with {dependency_edges} import relationships detected."
    if call_edges:
        return f"Architecture appears behavior-driven with {call_edges} call relationships detected."
    return "Not enough graph structure was detected to describe the architecture confidently."


def understand_project(local_path: str, max_files: int = 2000) -> dict[str, Any]:
    """Combine metadata parsing, AST parsing, graph building, and heuristic summarization."""

    root = Path(local_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("local_path must be an existing directory")

    meta = parse_project(str(root))
    ast_data = parse_project_code(str(root))
    graph_result = build_graph(ast_data)
    graph = graph_result[0] if isinstance(graph_result, tuple) else graph_result

    files = meta.get("files", []) if isinstance(meta, dict) else []
    entry = detect_entry_point(files)
    core_funcs = find_core_functions(graph)
    project_type = infer_project_type(files)
    summary = generate_summary(entry, core_funcs, project_type)

    return {
        "entry_point": entry,
        "core_functions": core_funcs,
        "project_type": project_type,
        "summary": summary,
    }
