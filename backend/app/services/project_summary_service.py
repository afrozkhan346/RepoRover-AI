from __future__ import annotations

from collections import Counter, deque
from pathlib import Path
import re

from app.schemas.project_summaries import ProjectSummariesResponse, SummaryMetrics
from app.services.call_graph_service import build_call_graph
from app.services.dependency_graph_service import build_dependency_graph
from app.services.llm_service import generate_repo_summaries

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


def _readme_candidates(root: Path) -> list[Path]:
    return [
        root / "README.md",
        root / "readme.md",
        root / "README.txt",
        root / "README",
    ]


def _clean_markdown_line(line: str) -> str:
    text = line.strip()
    text = re.sub(r"^#{1,6}\s*", "", text)
    text = re.sub(r"^[-*+]\s+", "", text)
    text = re.sub(r"^\d+\.\s+", "", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    return " ".join(text.split())


def _extract_readme_insights(root: Path) -> tuple[str | None, str | None]:
    for candidate in _readme_candidates(root):
        if not candidate.exists() or not candidate.is_file():
            continue

        text = _read_text(candidate)
        if not text.strip():
            continue

        lines: list[str] = []
        in_code_block = False
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            if not stripped:
                continue
            if set(stripped) <= {"-"} or set(stripped) <= {"="}:
                continue
            cleaned = _clean_markdown_line(stripped)
            if not cleaned:
                continue
            if cleaned.lower().startswith("http"):
                continue
            lines.append(cleaned)

        meaningful = [line for line in lines if len(line) >= 20]
        if not meaningful:
            return None, None

        purpose = meaningful[0][:260]
        info_bits: list[str] = []
        for line in meaningful[1:8]:
            if line == purpose:
                continue
            info_bits.append(line)
            if len(info_bits) >= 3:
                break

        info = " ".join(info_bits) if info_bits else None
        return purpose, info

    return None, None


def _project_purpose_hint(root: Path) -> str | None:
    readme_candidates = [
        root / "README.md",
        root / "readme.md",
        root / "README.txt",
        root / "README",
    ]

    for candidate in readme_candidates:
        if not candidate.exists() or not candidate.is_file():
            continue

        text = _read_text(candidate)
        if not text.strip():
            continue

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("#"):
                continue
            return line[:280]

    return None


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


def _count_total_files(root: Path, max_files: int) -> int:
    count = 0
    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        count += 1
        if count >= max_files:
            break
    return count


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
    total_files = _count_total_files(root, max_files=max_files)
    total_lines = sum(len(_read_text(path).splitlines()) for path in source_files)
    language_breakdown = _language_breakdown(source_files)
    readme_purpose, readme_info = _extract_readme_insights(root)
    purpose_hint = readme_purpose or _project_purpose_hint(root)

    dependency_graph = build_dependency_graph(str(root), max_files=max_files)
    call_graph = build_call_graph(str(root), max_files=max_files)

    key_dependencies = _top_dependencies(dependency_graph)
    key_modules = _top_modules_by_outgoing(dependency_graph)

    flow_ids = _execution_flow(call_graph)
    labels = _node_label_map(call_graph)
    flow_path = [labels.get(node_id, node_id) for node_id in flow_ids]

    if purpose_hint:
        detail_text = readme_info or "the core use-case and key capabilities documented in the repository"
        project_summary = (
            f"This project is {purpose_hint.rstrip('.')}" + ". "
            f"It focuses on {detail_text.rstrip('.')}" + ". "
            f"Technically, the scan found {total_files} files ({len(source_files)} analyzable) with {total_lines} lines of content across {len(language_breakdown)} language groups."
        )
    else:
        project_summary = (
            f"This project is a software repository named {root.name}. "
            "It helps users by implementing source code, configuration, and documentation for its target use-case. "
            f"Technically, it contains {total_files} files ({len(source_files)} analyzable) and {total_lines} lines across {len(language_breakdown)} language groups, led by {max(language_breakdown, key=language_breakdown.get) if language_breakdown else 'Unknown'}."
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
        total_files=total_files,
        analyzable_files=len(source_files),
        files_scanned=len(source_files),
        total_lines=total_lines,
        language_breakdown=language_breakdown,
        dependency_edges=dependency_graph.summary.total_edges,
        call_edges=call_graph.summary.call_edges,
    )

    llm_summaries = generate_repo_summaries(
        repo_name=root.name,
        purpose_hint=purpose_hint,
        readme_info_hint=readme_info,
        total_files=total_files,
        analyzable_files=len(source_files),
        total_lines=total_lines,
        language_breakdown=language_breakdown,
        dependency_edges=dependency_graph.summary.total_edges,
        call_edges=call_graph.summary.call_edges,
        key_modules=key_modules,
        key_dependencies=key_dependencies,
        flow_path=flow_path,
    )
    if llm_summaries:
        project_summary = llm_summaries["project_summary"]
        architecture_summary = llm_summaries["architecture_summary"]
        execution_flow_summary = llm_summaries["execution_flow_summary"]

    return ProjectSummariesResponse(
        project_summary=project_summary,
        architecture_summary=architecture_summary,
        execution_flow_summary=execution_flow_summary,
        key_modules=key_modules,
        key_dependencies=key_dependencies,
        flow_path=flow_path,
        metrics=metrics,
    )
