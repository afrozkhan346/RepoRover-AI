from __future__ import annotations

import ast
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import networkx as nx

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

JS_IMPORT_RE = re.compile(
    r"import\s+[^;]*?from\s+[\"']([^\"']+)[\"']|import\s+[\"']([^\"']+)[\"']|require\(\s*[\"']([^\"']+)[\"']\s*\)"
)
JS_CLASS_RE = re.compile(r"\bclass\s+([a-zA-Z_$][a-zA-Z0-9_$]*)")
JS_FUNCTION_RE = re.compile(
    r"(?:function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(|const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:async\s*)?function\s*\()"
)
JS_CALL_RE = re.compile(r"([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(")


@dataclass(frozen=True)
class GraphNode:
    id: str
    node_type: str
    label: str
    file_path: str | None = None


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    edge_type: str


@dataclass(frozen=True)
class GraphSummary:
    files_scanned: int
    file_nodes: int
    class_nodes: int
    function_nodes: int
    module_nodes: int
    contains_edges: int
    calls_edges: int
    import_edges: int
    total_nodes: int
    total_edges: int


@dataclass(frozen=True)
class SystemGraph:
    root: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    summary: GraphSummary

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class _PythonGraphVisitor(ast.NodeVisitor):
    def __init__(self, *, file_rel: str) -> None:
        self.file_rel = file_rel
        self.classes: list[str] = []
        self.functions: list[tuple[str, str | None]] = []
        self.calls_by_caller: dict[str, list[str]] = {}
        self.imports: set[str] = set()
        self._class_stack: list[str] = []
        self._function_stack: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            if alias.name:
                self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        module = node.module or ""
        if node.level:
            module = "." * node.level + module
        if module:
            self.imports.add(module)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self.classes.append(node.name)
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._push_function(node.name)
        self.generic_visit(node)
        self._pop_function()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._push_function(node.name)
        self.generic_visit(node)
        self._pop_function()

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        called = _python_call_name(node.func)
        if called:
            caller = self._function_stack[-1] if self._function_stack else f"file:{self.file_rel}"
            self.calls_by_caller.setdefault(caller, []).append(called)
        self.generic_visit(node)

    def _push_function(self, name: str) -> None:
        parent_class = self._class_stack[-1] if self._class_stack else None
        qualified = f"{parent_class}.{name}" if parent_class else name
        function_node_id = f"function:{self.file_rel}:{qualified}"
        self.functions.append((qualified, parent_class))
        self._function_stack.append(function_node_id)

    def _pop_function(self) -> None:
        self._function_stack.pop()


def _python_call_name(func: ast.AST) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _iter_source_files(root: Path, max_files: int) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if not path.is_file() or path.suffix.lower() not in SOURCE_EXTENSIONS:
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


def _parse_python_file(file_rel: str, source: str) -> tuple[list[str], list[tuple[str, str | None]], dict[str, list[str]], set[str]]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [], [], {}, set()

    visitor = _PythonGraphVisitor(file_rel=file_rel)
    visitor.visit(tree)
    return visitor.classes, visitor.functions, visitor.calls_by_caller, visitor.imports


def _parse_javascript_like_file(file_rel: str, source: str) -> tuple[list[str], list[tuple[str, str | None]], dict[str, list[str]], set[str]]:
    classes = sorted({match.group(1) for match in JS_CLASS_RE.finditer(source)})

    functions: list[tuple[str, str | None]] = []
    for match in JS_FUNCTION_RE.finditer(source):
        name = next((group for group in match.groups() if group), None)
        if name:
            functions.append((name, None))

    function_node_ids = [f"function:{file_rel}:{name}" for name, _ in functions]
    caller = function_node_ids[0] if function_node_ids else f"file:{file_rel}"
    calls_by_caller = {caller: [m.group(1) for m in JS_CALL_RE.finditer(source)]}

    imports: set[str] = set()
    for match in JS_IMPORT_RE.finditer(source):
        value = next((group for group in match.groups() if group), None)
        if value:
            imports.add(value)

    return classes, functions, calls_by_caller, imports


def build_graph(ast_data: list[dict[str, Any]]) -> tuple[nx.DiGraph, dict[str, int]]:
    """
    Build a directed graph from normalized AST payloads with call relationships.

    Expected shape per item:
    {
        "file": "path/to/file.py",
        "path": "absolute/path/to/file.py",
        "data": {
            "functions": [
                {
                    "name": "foo",
                    "calls": [{"called_name": "bar", "call_line": 10}, ...]
                },
                ...
            ],
            "classes": [{"name": "Bar"}, ...],
            "imports": ["os", "typing", ...],
        }
    }
    """

    graph = nx.DiGraph()
    call_edges = 0
    function_nodes: dict[str, str] = {}  # Map from function_name to node_id

    for file_data in ast_data:
        file_name = str(file_data.get("file") or file_data.get("file_path") or "unknown")
        file_node = f"file:{file_name}"
        graph.add_node(file_node, type="file")

        data = file_data.get("data") if isinstance(file_data.get("data"), dict) else file_data

        # Process functions and track them
        for func in data.get("functions", []):
            if isinstance(func, dict):
                func_name = str(func.get("name") or "unknown")
                parent_class = func.get("parent_class")
            else:
                func_name = str(func)
                parent_class = None

            func_node = f"func:{func_name}"
            graph.add_node(func_node, type="function", full_name=func_name)
            graph.add_edge(file_node, func_node, relation="contains")
            function_nodes[func_name] = func_node

            # Process function calls
            if isinstance(func, dict) and "calls" in func:
                for call in func.get("calls", []):
                    if isinstance(call, dict):
                        called_name = call.get("called_name") or call.get("name")
                    else:
                        called_name = call
                    
                    if called_name:
                        # Create a call edge - target may be resolved later
                        called_node = f"func:{called_name}"
                        if called_node not in graph:
                            graph.add_node(called_node, type="function", full_name=called_name)
                        graph.add_edge(func_node, called_node, relation="calls")
                        call_edges += 1

        # Process classes
        for cls in data.get("classes", []):
            if isinstance(cls, dict):
                class_name = str(cls.get("name") or "unknown")
            else:
                class_name = str(cls)

            class_node = f"class:{class_name}"
            graph.add_node(class_node, type="class")
            graph.add_edge(file_node, class_node, relation="contains")

        # Process imports
        for imp in data.get("imports", []):
            if isinstance(imp, dict):
                module_name = str(imp.get("module") or imp.get("name") or "unknown")
            else:
                module_name = str(imp)

            import_node = f"module:{module_name}"
            graph.add_node(import_node, type="module")
            graph.add_edge(file_node, import_node, relation="imports")

    return graph, {"call_edges": call_edges}


def analyze_graph(graph: nx.DiGraph, call_edge_info: dict[str, int] | None = None) -> dict[str, int]:
    """Analyze graph and return statistics including call relationships."""
    call_edges = call_edge_info.get("call_edges", 0) if call_edge_info else 0
    
    # Count edge types
    contains_edges = sum(1 for _, _, d in graph.edges(data=True) if d.get("relation") == "contains")
    import_edges = sum(1 for _, _, d in graph.edges(data=True) if d.get("relation") == "imports")
    if call_edges == 0:
        call_edges = sum(1 for _, _, d in graph.edges(data=True) if d.get("relation") == "calls")
    
    return {
        "total_nodes": graph.number_of_nodes(),
        "total_edges": graph.number_of_edges(),
        "call_edges": call_edges,
        "contains_edges": contains_edges,
        "import_edges": import_edges,
    }


def build_system_graph(local_path: str, max_files: int = 2000) -> dict[str, Any]:
    """
    Convert project source code into a connected system graph.

    Nodes:
    - file
    - class
    - function
    - module (for import targets)

    Edges:
    - contains (file -> class/function, class -> method)
    - calls (function/file -> function/module)
    - imports (file -> module)
    """

    root = Path(local_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("local_path must be an existing directory")

    files = _iter_source_files(root, max_files=max_files)

    nodes: dict[str, GraphNode] = {}
    edges: list[GraphEdge] = []

    contains_edges = 0
    calls_edges = 0
    import_edges = 0

    function_index: dict[str, list[str]] = {}
    file_call_targets: list[tuple[str, str]] = []

    for file_path in files:
        rel = file_path.relative_to(root).as_posix()
        source = _read_text(file_path)
        if not source:
            continue

        file_node_id = f"file:{rel}"
        nodes[file_node_id] = GraphNode(
            id=file_node_id,
            node_type="file",
            label=rel,
            file_path=rel,
        )

        if file_path.suffix.lower() == ".py":
            classes, functions, calls_by_caller, imports = _parse_python_file(rel, source)
        else:
            classes, functions, calls_by_caller, imports = _parse_javascript_like_file(rel, source)

        for class_name in classes:
            class_node_id = f"class:{rel}:{class_name}"
            nodes[class_node_id] = GraphNode(
                id=class_node_id,
                node_type="class",
                label=class_name,
                file_path=rel,
            )
            edges.append(GraphEdge(source=file_node_id, target=class_node_id, edge_type="contains"))
            contains_edges += 1

        for function_name, parent_class in functions:
            function_node_id = f"function:{rel}:{function_name}"
            nodes[function_node_id] = GraphNode(
                id=function_node_id,
                node_type="function",
                label=function_name,
                file_path=rel,
            )
            function_index.setdefault(function_name.split(".")[-1], []).append(function_node_id)

            if parent_class:
                class_node_id = f"class:{rel}:{parent_class}"
                if class_node_id in nodes:
                    edges.append(GraphEdge(source=class_node_id, target=function_node_id, edge_type="contains"))
                else:
                    edges.append(GraphEdge(source=file_node_id, target=function_node_id, edge_type="contains"))
            else:
                edges.append(GraphEdge(source=file_node_id, target=function_node_id, edge_type="contains"))
            contains_edges += 1

        for imported in sorted(imports):
            module_node_id = f"module:{imported}"
            if module_node_id not in nodes:
                nodes[module_node_id] = GraphNode(
                    id=module_node_id,
                    node_type="module",
                    label=imported,
                )
            edges.append(GraphEdge(source=file_node_id, target=module_node_id, edge_type="imports"))
            import_edges += 1

        for caller, call_targets in calls_by_caller.items():
            for called_name in call_targets:
                file_call_targets.append((caller, called_name))

    for caller, called_name in file_call_targets:
        targets = function_index.get(called_name, [])
        if targets:
            for target_id in targets:
                if target_id == caller:
                    continue
                edges.append(GraphEdge(source=caller, target=target_id, edge_type="calls"))
                calls_edges += 1
            continue

        module_node_id = f"module:{called_name}"
        if module_node_id not in nodes:
            nodes[module_node_id] = GraphNode(id=module_node_id, node_type="module", label=called_name)
        edges.append(GraphEdge(source=caller, target=module_node_id, edge_type="calls"))
        calls_edges += 1

    summary = GraphSummary(
        files_scanned=len(files),
        file_nodes=sum(1 for node in nodes.values() if node.node_type == "file"),
        class_nodes=sum(1 for node in nodes.values() if node.node_type == "class"),
        function_nodes=sum(1 for node in nodes.values() if node.node_type == "function"),
        module_nodes=sum(1 for node in nodes.values() if node.node_type == "module"),
        contains_edges=contains_edges,
        calls_edges=calls_edges,
        import_edges=import_edges,
        total_nodes=len(nodes),
        total_edges=len(edges),
    )

    graph = SystemGraph(
        root=str(root),
        nodes=list(nodes.values()),
        edges=edges,
        summary=summary,
    )
    return graph.to_dict()
