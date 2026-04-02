from __future__ import annotations

import re
from pathlib import Path

from app.schemas.call_graph import (
    CallGraphEdge,
    CallGraphNode,
    CallGraphResponse,
    CallGraphSummary,
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


def build_call_graph(local_path: str, max_files: int = 2000) -> CallGraphResponse:
    root = Path(local_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("local_path must be an existing directory")

    files = _iter_source_files(root, max_files=max_files)

    nodes: dict[str, CallGraphNode] = {}
    edges: list[CallGraphEdge] = []

    function_index: dict[str, list[str]] = {}
    file_functions: dict[str, set[str]] = {}
    file_calls: dict[str, list[str]] = {}
    file_imports: dict[str, set[str]] = {}

    for file_path in files:
        rel = file_path.relative_to(root).as_posix()
        file_node_id = f"file:{rel}"
        nodes[file_node_id] = CallGraphNode(id=file_node_id, node_type="file", label=rel, file_path=rel)

        text = _read_text(file_path)
        functions = _extract_functions(file_path, text)
        calls = _extract_calls(file_path, text)
        imports = _extract_import_contexts(file_path, text)

        file_functions[rel] = functions
        file_calls[rel] = calls
        file_imports[rel] = imports

        for function_name in sorted(functions):
            function_node_id = f"function:{rel}:{function_name}"
            nodes[function_node_id] = CallGraphNode(
                id=function_node_id,
                node_type="function",
                label=function_name,
                file_path=rel,
            )
            function_index.setdefault(function_name, []).append(function_node_id)
            edges.append(CallGraphEdge(source=file_node_id, target=function_node_id, edge_type="defines"))

    call_edges = 0
    import_context_edges = 0

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
                if external_id not in nodes:
                    nodes[external_id] = CallGraphNode(
                        id=external_id,
                        node_type="external",
                        label=call_name,
                    )
                edges.append(CallGraphEdge(source=caller_source, target=external_id, edge_type="calls"))
                call_edges += 1
                continue

            for target_id in targets:
                if target_id == caller_source:
                    continue
                edges.append(CallGraphEdge(source=caller_source, target=target_id, edge_type="calls"))
                call_edges += 1

    for rel, imports in file_imports.items():
        file_node_id = f"file:{rel}"
        for imported in sorted(imports):
            import_node_id = f"import-context:{imported}"
            if import_node_id not in nodes:
                nodes[import_node_id] = CallGraphNode(
                    id=import_node_id,
                    node_type="import-context",
                    label=imported,
                )
            edges.append(CallGraphEdge(source=file_node_id, target=import_node_id, edge_type="imports-context"))
            import_context_edges += 1

    summary = CallGraphSummary(
        files_scanned=len(files),
        functions_found=sum(len(items) for items in file_functions.values()),
        call_edges=call_edges,
        import_context_edges=import_context_edges,
        total_nodes=len(nodes),
        total_edges=len(edges),
    )

    return CallGraphResponse(
        root=str(root),
        nodes=list(nodes.values()),
        edges=edges,
        summary=summary,
    )
