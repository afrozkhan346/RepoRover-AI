from __future__ import annotations

import ast
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.services.dependency_graph_service import build_dependency_graph
from app.services.llm_service import generate_text

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

MAGIC_NUMBER_RE = re.compile(r"\b\d{3,}\b")
URL_RE = re.compile(r"https?://[^\s'\"]+")
TOKEN_RE = re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]")
HARD_CODED_LITERAL_RE = re.compile(r"[\"'][A-Za-z0-9_\-]{2,}[\"']")
JS_FUNCTION_RE = re.compile(
    r"(?:function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(|const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:async\s*)?function\s*\()"
)


@dataclass(frozen=True)
class DesignGapFinding:
    gap_type: str
    severity: str
    file_path: str | None
    evidence: str
    suggestion: str
    score_impact: float


@dataclass(frozen=True)
class DesignGapReport:
    overall_score: float
    findings: list[DesignGapFinding]
    totals: dict[str, int]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def detect_gaps(ast_data: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Start-simple, rule-based gap detection over parsed AST payloads."""

    gaps: list[dict[str, str]] = []

    for file_entry in ast_data:
        data = file_entry.get("data")
        if not isinstance(data, dict):
            continue

        functions = data.get("functions")
        if not isinstance(functions, list):
            continue

        file_name = str(file_entry.get("file") or file_entry.get("path") or "unknown")

        if len(functions) > 10:
            gaps.append(
                {
                    "file": file_name,
                    "issue": "Too many functions in a single file",
                    "severity": "Medium",
                }
            )

        if len(functions) == 0:
            gaps.append(
                {
                    "file": file_name,
                    "issue": "No functional structure found",
                    "severity": "Low",
                }
            )

    return gaps


def detect_hardcoded_values(file_path: str) -> list[str]:
    """Simple hardcoded-value detector requested for baseline analysis."""

    issues: list[str] = []
    path = Path(file_path).expanduser().resolve()

    if not path.exists() or not path.is_file():
        return issues

    content = _read_text(path)

    if HARD_CODED_LITERAL_RE.search(content):
        issues.append("Possible hardcoded values detected")

    return issues


def analyze_gaps(project_path: str, ast_data: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Combine file-level hardcoded checks with AST-driven structural gap detection."""

    _ = project_path
    results: list[dict[str, str]] = []

    for file_entry in ast_data:
        file_path = str(file_entry.get("path") or "")
        issues = detect_hardcoded_values(file_path)

        for issue in issues:
            results.append(
                {
                    "file": str(file_entry.get("file") or file_path or "unknown"),
                    "issue": issue,
                    "severity": "Low",
                }
            )

    results.extend(detect_gaps(ast_data))
    return results


def generate_gap_suggestions(gaps: list[dict[str, str]]) -> str:
    """Generate improvement suggestions for detected gaps, using LLM when available."""

    if not gaps:
        return "No design gaps detected. Keep monitoring maintainability and error handling as the codebase grows."

    prompt = (
        "Suggest practical code and architecture improvements for these detected issues.\n"
        "Return concise bullet points grouped by priority.\n\n"
        f"Detected gaps:\n{gaps}"
    )

    llm_result = generate_text(
        system_prompt="You are a senior software reviewer focused on maintainability and architecture.",
        user_prompt=prompt,
        temperature=0.3,
        max_tokens=500,
    )
    if llm_result and llm_result.strip():
        return llm_result.strip()

    high_count = sum(1 for item in gaps if item.get("severity", "").lower() == "high")
    medium_count = sum(1 for item in gaps if item.get("severity", "").lower() == "medium")

    fallback_lines = [
        "1. Prioritize high-severity files first and add targeted refactors with tests.",
        "2. Extract repeated literals/configuration into environment-driven constants.",
        "3. Introduce structured error handling around network, file, and database boundaries.",
        "4. Split overloaded files into smaller modules with single responsibilities.",
        "5. Track gap metrics over time to verify reliability improvements.",
        f"Current gap profile: high={high_count}, medium={medium_count}, total={len(gaps)}.",
    ]
    return "\n".join(fallback_lines)


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


def _python_function_lengths(content: str) -> list[tuple[str, int]]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    lengths: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, "end_lineno", node.lineno)
            lengths.append((node.name, max(1, end - node.lineno + 1)))
    return lengths


def _javascript_function_count(content: str) -> int:
    return sum(1 for _ in JS_FUNCTION_RE.finditer(content))


def _detect_large_functions(root: Path, files: list[Path]) -> list[DesignGapFinding]:
    findings: list[DesignGapFinding] = []

    for file_path in files:
        rel = file_path.relative_to(root).as_posix()
        content = _read_text(file_path)
        if not content:
            continue

        if file_path.suffix.lower() == ".py":
            functions = _python_function_lengths(content)
            for name, length in functions:
                if length >= 80:
                    findings.append(
                        DesignGapFinding(
                            gap_type="large_function",
                            severity="high" if length >= 120 else "medium",
                            file_path=rel,
                            evidence=f"Function '{name}' is {length} lines long.",
                            suggestion="Split long functions into smaller helpers with single responsibilities.",
                            score_impact=8.0 if length >= 120 else 5.0,
                        )
                    )
        else:
            lines = content.splitlines()
            if len(lines) >= 350 and _javascript_function_count(content) > 0:
                findings.append(
                    DesignGapFinding(
                        gap_type="large_function",
                        severity="medium",
                        file_path=rel,
                        evidence=f"Large JS/TS file with {len(lines)} lines likely contains oversized functions.",
                        suggestion="Extract reusable modules/components and reduce per-file cognitive load.",
                        score_impact=4.0,
                    )
                )

    return findings


def _detect_missing_error_handling(root: Path, files: list[Path]) -> list[DesignGapFinding]:
    findings: list[DesignGapFinding] = []
    risk_markers = ("fetch(", "axios.", "requests.", "open(", "sqlite", "db.", "subprocess")

    for file_path in files:
        rel = file_path.relative_to(root).as_posix()
        content = _read_text(file_path)
        if not content:
            continue

        has_risky_ops = any(marker in content for marker in risk_markers)
        if not has_risky_ops:
            continue

        suffix = file_path.suffix.lower()
        has_error_handling = ("try:" in content and "except" in content) if suffix == ".py" else ("try {" in content and "catch" in content)

        if not has_error_handling:
            findings.append(
                DesignGapFinding(
                    gap_type="missing_error_handling",
                    severity="high",
                    file_path=rel,
                    evidence="File performs IO/network/database operations without clear try/catch handling.",
                    suggestion="Wrap risky operations with structured error handling and user-safe fallback paths.",
                    score_impact=7.0,
                )
            )

    return findings


def _detect_hardcoded_values(root: Path, files: list[Path]) -> list[DesignGapFinding]:
    findings: list[DesignGapFinding] = []

    for file_path in files:
        rel = file_path.relative_to(root).as_posix()
        content = _read_text(file_path)
        if not content:
            continue

        if TOKEN_RE.search(content):
            findings.append(
                DesignGapFinding(
                    gap_type="hardcoded_value",
                    severity="high",
                    file_path=rel,
                    evidence="Potential secret/token-like literal found in source.",
                    suggestion="Move secrets to environment variables and rotate any exposed credentials.",
                    score_impact=10.0,
                )
            )

        if URL_RE.search(content):
            findings.append(
                DesignGapFinding(
                    gap_type="hardcoded_value",
                    severity="medium",
                    file_path=rel,
                    evidence="Hardcoded URL detected.",
                    suggestion="Use configuration files or environment-driven endpoints per environment.",
                    score_impact=3.0,
                )
            )

        magic_numbers = len(MAGIC_NUMBER_RE.findall(content))
        if magic_numbers >= 8:
            findings.append(
                DesignGapFinding(
                    gap_type="hardcoded_value",
                    severity="low",
                    file_path=rel,
                    evidence=f"Detected {magic_numbers} numeric literals >= 3 digits.",
                    suggestion="Extract repeated constants into named configuration or domain constants.",
                    score_impact=2.0,
                )
            )

    return findings


def _detect_missing_modularity(root: Path, files: list[Path]) -> list[DesignGapFinding]:
    findings: list[DesignGapFinding] = []

    for file_path in files:
        rel = file_path.relative_to(root).as_posix()
        content = _read_text(file_path)
        if not content:
            continue

        lines = len(content.splitlines())
        function_count = len(_python_function_lengths(content)) if file_path.suffix.lower() == ".py" else _javascript_function_count(content)

        if lines >= 500 or function_count >= 20:
            findings.append(
                DesignGapFinding(
                    gap_type="missing_modularity",
                    severity="medium",
                    file_path=rel,
                    evidence=f"File has {lines} lines and {function_count} functions.",
                    suggestion="Break large files into domain modules with clearer boundaries.",
                    score_impact=5.0,
                )
            )

    return findings


def _detect_tight_coupling(local_path: str, root: Path, max_files: int) -> list[DesignGapFinding]:
    findings: list[DesignGapFinding] = []

    graph = build_dependency_graph(local_path, max_files=max_files)
    outgoing: Counter[str] = Counter()
    edge_set: set[tuple[str, str]] = set()

    for edge in graph.edges:
        if edge.edge_type != "imports":
            continue
        outgoing[edge.source] += 1
        edge_set.add((edge.source, edge.target))

    for source, count in outgoing.items():
        if count < 12:
            continue
        file_path = source.replace("file:", "") if source.startswith("file:") else None
        severity = "high" if count >= 20 else "medium"
        findings.append(
            DesignGapFinding(
                gap_type="tight_coupling",
                severity=severity,
                file_path=file_path,
                evidence=f"Module imports {count} dependencies, indicating high coupling.",
                suggestion="Introduce façade/service layers and reduce direct dependency fan-out.",
                score_impact=7.0 if severity == "high" else 4.0,
            )
        )

    cyclic_pairs = sum(1 for source, target in edge_set if (target, source) in edge_set and source != target) // 2
    if cyclic_pairs > 0:
        findings.append(
            DesignGapFinding(
                gap_type="tight_coupling",
                severity="medium",
                file_path=None,
                evidence=f"Detected {cyclic_pairs} potential cyclical import pairs.",
                suggestion="Refactor shared abstractions into neutral modules to break dependency cycles.",
                score_impact=min(10.0, float(cyclic_pairs) * 1.5),
            )
        )

    return findings


def detect_design_gaps(local_path: str, max_files: int = 2000) -> dict[str, Any]:
    root = Path(local_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("local_path must be an existing directory")

    files = _iter_source_files(root, max_files=max_files)

    findings: list[DesignGapFinding] = []
    findings.extend(_detect_large_functions(root, files))
    findings.extend(_detect_missing_error_handling(root, files))
    findings.extend(_detect_tight_coupling(str(root), root, max_files))
    findings.extend(_detect_hardcoded_values(root, files))
    findings.extend(_detect_missing_modularity(root, files))

    total_penalty = sum(item.score_impact for item in findings)
    overall_score = round(max(0.0, 100.0 - total_penalty), 2)

    severity_totals = {
        "high": sum(1 for item in findings if item.severity == "high"),
        "medium": sum(1 for item in findings if item.severity == "medium"),
        "low": sum(1 for item in findings if item.severity == "low"),
    }

    summary = (
        f"Design gap analysis scanned {len(files)} source files and found {len(findings)} findings "
        f"(high={severity_totals['high']}, medium={severity_totals['medium']}, low={severity_totals['low']})."
    )

    report = DesignGapReport(
        overall_score=overall_score,
        findings=findings,
        totals=severity_totals,
        summary=summary,
    )
    return report.to_dict()
