from __future__ import annotations

import json
import re
from pathlib import Path

import networkx as nx

from app.schemas.dependency_graph import (
    DependencyEdge,
    DependencyGraphResponse,
    DependencyGraphSummary,
    DependencyNode,
)

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


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

PY_IMPORT_RE = re.compile(r"^\s*import\s+([a-zA-Z0-9_\.]+)", re.MULTILINE)
PY_FROM_RE = re.compile(r"^\s*from\s+([a-zA-Z0-9_\.]+)\s+import\s+", re.MULTILINE)
JS_IMPORT_FROM_RE = re.compile(r"import\s+[^;]*?\s+from\s+[\"']([^\"']+)[\"']")
JS_IMPORT_RE = re.compile(r"import\s+[\"']([^\"']+)[\"']")
JS_REQUIRE_RE = re.compile(r"require\(\s*[\"']([^\"']+)[\"']\s*\)")


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


def _extract_imports(file_path: Path, text: str) -> set[str]:
    imports: set[str] = set()
    suffix = file_path.suffix.lower()

    if suffix == ".py":
        imports.update(match.group(1) for match in PY_IMPORT_RE.finditer(text))
        imports.update(match.group(1) for match in PY_FROM_RE.finditer(text))
    else:
        imports.update(match.group(1) for match in JS_IMPORT_FROM_RE.finditer(text))
        imports.update(match.group(1) for match in JS_IMPORT_RE.finditer(text))
        imports.update(match.group(1) for match in JS_REQUIRE_RE.finditer(text))

    return {item.strip() for item in imports if item.strip()}


def _parse_package_json(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        payload = json.loads(_read_text(path))
    except json.JSONDecodeError:
        return set()

    deps = set((payload.get("dependencies") or {}).keys())
    deps.update((payload.get("devDependencies") or {}).keys())
    return deps


def _parse_requirements_txt(path: Path) -> set[str]:
    if not path.exists():
        return set()
    packages: set[str] = set()
    for line in _read_text(path).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        name = re.split(r"[<>=!~\[]", stripped, maxsplit=1)[0].strip()
        if name:
            packages.add(name)
    return packages


def _parse_pyproject(path: Path) -> set[str]:
    if not path.exists() or tomllib is None:
        return set()

    try:
        with path.open("rb") as handle:
            payload = tomllib.load(handle)
    except Exception:
        return set()

    project = payload.get("project") or {}
    deps = project.get("dependencies") or []
    packages: set[str] = set()
    for dep in deps:
        if not isinstance(dep, str):
            continue
        name = re.split(r"[<>=!~\[]", dep, maxsplit=1)[0].strip()
        if name:
            packages.add(name)
    return packages


def _collect_declared_packages(root: Path) -> set[str]:
    packages = set()
    packages.update(_parse_package_json(root / "package.json"))
    packages.update(_parse_requirements_txt(root / "requirements.txt"))
    packages.update(_parse_pyproject(root / "pyproject.toml"))
    return packages


def _build_networkx_dependency_graph(root: Path, files: list[Path], max_files: int) -> nx.DiGraph:
    graph = nx.DiGraph()

    for file_path in files:
        rel = file_path.relative_to(root).as_posix()
        file_node_id = f"file:{rel}"
        graph.add_node(file_node_id, node_type="file", label=rel)

        text = _read_text(file_path)
        for import_name in sorted(_extract_imports(file_path, text)):
            import_node_id = f"import:{import_name}"
            if import_node_id not in graph:
                graph.add_node(import_node_id, node_type="import", label=import_name)
            graph.add_edge(file_node_id, import_node_id, edge_type="imports")

    declared_packages = _collect_declared_packages(root)
    if declared_packages:
        graph.add_node("manifest:dependencies", node_type="manifest", label="dependency-manifest")

    for package_name in sorted(declared_packages):
        pkg_node_id = f"package:{package_name}"
        graph.add_node(pkg_node_id, node_type="package", label=package_name)
        graph.add_edge("manifest:dependencies", pkg_node_id, edge_type="declares")

    graph.graph["declared_packages"] = declared_packages
    return graph


def build_dependency_graph(local_path: str, max_files: int = 2000) -> DependencyGraphResponse:
    root = Path(local_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("local_path must be an existing directory")

    files = _iter_source_files(root, max_files=max_files)

    graph = _build_networkx_dependency_graph(root, files, max_files=max_files)
    declared_packages = graph.graph.get("declared_packages", set())

    nodes = [
        DependencyNode(id=node_id, node_type=data.get("node_type", "unknown"), label=data.get("label", node_id))
        for node_id, data in graph.nodes(data=True)
    ]
    edges = [
        DependencyEdge(source=source, target=target, edge_type=data.get("edge_type", "imports"))
        for source, target, data in graph.edges(data=True)
    ]

    summary = DependencyGraphSummary(
        files_scanned=len(files),
        import_edges=sum(1 for _, _, data in graph.edges(data=True) if data.get("edge_type") == "imports"),
        package_nodes=sum(1 for _, data in graph.nodes(data=True) if data.get("node_type") == "package") or len(declared_packages),
        total_nodes=graph.number_of_nodes(),
        total_edges=graph.number_of_edges(),
    )

    return DependencyGraphResponse(
        root=str(root),
        nodes=nodes,
        edges=edges,
        summary=summary,
    )
