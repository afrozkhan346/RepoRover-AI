from __future__ import annotations

import re
from pathlib import Path

from app.schemas.quality_analysis import QualityAnalysisResponse, QualityIssue
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


def _function_lengths_python(content: str) -> list[int]:
    lines = content.splitlines()
    lengths: list[int] = []
    current_start: int | None = None
    current_indent: int | None = None

    for index, line in enumerate(lines):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if stripped.startswith("def "):
            if current_start is not None:
                lengths.append(index - current_start)
            current_start = index
            current_indent = indent
            continue

        if current_start is not None and stripped and current_indent is not None and indent <= current_indent:
            lengths.append(index - current_start)
            current_start = None
            current_indent = None

    if current_start is not None:
        lengths.append(len(lines) - current_start)

    return lengths


def analyze_quality(local_path: str, max_files: int = 2000) -> QualityAnalysisResponse:
    root = Path(local_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("local_path must be an existing directory")

    files = _iter_source_files(root, max_files=max_files)
    issues: list[QualityIssue] = []
    penalty = 0.0

    for file_path in files:
        rel = file_path.relative_to(root).as_posix()
        content = _read_text(file_path)
        lines = content.splitlines()

        if len(lines) > 450:
            issues.append(
                QualityIssue(
                    severity="medium",
                    category="maintainability",
                    file_path=rel,
                    detail=f"Large file with {len(lines)} lines may be difficult to maintain.",
                    recommendation="Split into smaller modules by responsibility.",
                )
            )
            penalty += 4

        if "TODO" in content or "FIXME" in content:
            issues.append(
                QualityIssue(
                    severity="low",
                    category="code-hygiene",
                    file_path=rel,
                    detail="Contains TODO/FIXME markers.",
                    recommendation="Track and resolve deferred work items.",
                )
            )
            penalty += 1

        if re.search(r"except\s+Exception\s*:\s*\n\s*pass", content):
            issues.append(
                QualityIssue(
                    severity="high",
                    category="reliability",
                    file_path=rel,
                    detail="Catches broad Exception and suppresses it with pass.",
                    recommendation="Handle specific exceptions and emit structured error context.",
                )
            )
            penalty += 8

        if file_path.suffix.lower() == ".py":
            function_lengths = _function_lengths_python(content)
            if function_lengths and max(function_lengths) > 90:
                issues.append(
                    QualityIssue(
                        severity="medium",
                        category="complexity",
                        file_path=rel,
                        detail=f"Contains long Python function (~{max(function_lengths)} lines).",
                        recommendation="Extract helper functions and isolate side effects.",
                    )
                )
                penalty += 5

    dependency_graph = build_dependency_graph(str(root), max_files=max_files)
    edge_set = {(edge.source, edge.target) for edge in dependency_graph.edges if edge.edge_type == "imports"}
    cyclic_pairs = sum(1 for source, target in edge_set if (target, source) in edge_set and source != target) // 2
    if cyclic_pairs > 0:
        issues.append(
            QualityIssue(
                severity="medium",
                category="architecture",
                file_path=None,
                detail=f"Detected {cyclic_pairs} potential cyclical import pairs.",
                recommendation="Introduce clear layering and move shared concerns to neutral modules.",
            )
        )
        penalty += min(10.0, cyclic_pairs * 1.5)

    design_gaps: list[str] = []
    if not (root / "tests").exists():
        design_gaps.append("No top-level tests directory detected.")
        penalty += 6
    if not (root / "docs").exists():
        design_gaps.append("No docs directory detected for architecture and API contracts.")
        penalty += 3
    if not (root / ".github" / "workflows").exists():
        design_gaps.append("No CI workflow detected under .github/workflows.")
        penalty += 4

    overall_score = round(max(0.0, 100.0 - penalty), 2)
    summary = (
        f"Quality analysis scanned {len(files)} files and found {len(issues)} issues with "
        f"{len(design_gaps)} design gap signals."
    )

    return QualityAnalysisResponse(
        overall_score=overall_score,
        issues=issues,
        design_gaps=design_gaps,
        summary=summary,
    )
