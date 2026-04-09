from __future__ import annotations

import ast
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from tree_sitter import Node
from tree_sitter_language_pack import get_parser

from app.schemas.parsing import AstTreeNode, NormalizedAstNode, SyntaxUnit
from app.schemas.project_ast import AstCallSite, ProjectAstSnapshot
from app.services.parser_service import parse_source, parse_structure, resolve_language


def preflight_tree_sitter_language(language: str) -> tuple[bool, str | None]:
    """Validate that a Tree-sitter parser can be loaded for the language."""
    try:
        get_parser(language)
        return True, None
    except Exception as error:
        return False, str(error)


@dataclass(frozen=True)
class ImportInfo:
    module: str
    name: str | None
    alias: str | None
    line: int


@dataclass(frozen=True)
class FunctionCallInfo:
    """Represents a function call within another function."""
    called_name: str
    call_line: int


@dataclass(frozen=True)
class FunctionInfo:
    name: str
    line: int
    end_line: int
    arguments: list[str]
    returns: str | None
    decorators: list[str]
    is_async: bool
    parent_class: str | None
    calls: list[FunctionCallInfo] = field(default_factory=list)


@dataclass(frozen=True)
class ClassInfo:
    name: str
    line: int
    end_line: int
    bases: list[str]
    decorators: list[str]
    methods: list[str]


@dataclass(frozen=True)
class PythonAstSummary:
    file_path: str
    imports: list[ImportInfo]
    classes: list[ClassInfo]
    functions: list[FunctionInfo]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class _PythonAstVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: list[ImportInfo] = []
        self.classes: list[ClassInfo] = []
        self.functions: list[FunctionInfo] = []
        self._class_stack: list[str] = []
        self._function_stack: list[tuple[int, list[FunctionCallInfo]]] = []  # (func_index, calls_list)

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            self.imports.append(
                ImportInfo(
                    module=alias.name,
                    name=None,
                    alias=alias.asname,
                    line=node.lineno,
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        module_name = node.module or ""
        if node.level:
            module_name = "." * node.level + module_name

        for alias in node.names:
            self.imports.append(
                ImportInfo(
                    module=module_name,
                    name=alias.name,
                    alias=alias.asname,
                    line=node.lineno,
                )
            )
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        methods = [item.name for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))]
        class_info = ClassInfo(
            name=node.name,
            line=node.lineno,
            end_line=getattr(node, "end_lineno", node.lineno),
            bases=[_expr_to_text(base) for base in node.bases],
            decorators=[_expr_to_text(decorator) for decorator in node.decorator_list],
            methods=methods,
        )
        self.classes.append(class_info)

        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._add_function(node=node, is_async=False)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._add_function(node=node, is_async=True)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        """Track function calls within the current function."""
        if self._function_stack:
            _, calls_list = self._function_stack[-1]
            called_name = self._extract_call_name(node.func)
            if called_name:
                calls_list.append(FunctionCallInfo(called_name=called_name, call_line=node.lineno))
        self.generic_visit(node)

    def _add_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool) -> None:
        arguments = [arg.arg for arg in node.args.posonlyargs]
        arguments.extend(arg.arg for arg in node.args.args)
        if node.args.vararg:
            arguments.append(f"*{node.args.vararg.arg}")
        arguments.extend(arg.arg for arg in node.args.kwonlyargs)
        if node.args.kwarg:
            arguments.append(f"**{node.args.kwarg.arg}")

        calls_list: list[FunctionCallInfo] = []
        self._function_stack.append((len(self.functions), calls_list))

        # Visit function body to collect calls
        for child in node.body:
            self.visit(child)

        self._function_stack.pop()

        info = FunctionInfo(
            name=node.name,
            line=node.lineno,
            end_line=getattr(node, "end_lineno", node.lineno),
            arguments=arguments,
            returns=_expr_to_text(node.returns) if node.returns else None,
            decorators=[_expr_to_text(decorator) for decorator in node.decorator_list],
            is_async=is_async,
            parent_class=self._class_stack[-1] if self._class_stack else None,
            calls=calls_list,
        )
        self.functions.append(info)

    def _extract_call_name(self, func: ast.AST) -> str | None:
        """Extract the name of the called function/method."""
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
        return None


def _expr_to_text(expression: ast.AST | None) -> str:
    if expression is None:
        return ""

    try:
        return ast.unparse(expression)
    except Exception:
        return expression.__class__.__name__


def parse_python_source(source_code: str, file_path: str = "<memory>") -> dict[str, Any]:
    """Parse Python source and extract imports, classes, and functions."""

    try:
        tree = ast.parse(source_code)
    except SyntaxError as error:
        raise ValueError(f"Unable to parse Python source: {error.msg} at line {error.lineno}") from error

    visitor = _PythonAstVisitor()
    visitor.visit(tree)

    summary = PythonAstSummary(
        file_path=file_path,
        imports=visitor.imports,
        classes=visitor.classes,
        functions=visitor.functions,
    )
    return summary.to_dict()


def parse_python_file(file_path: str) -> dict[str, Any]:
    """Parse one Python file and return extracted semantic elements."""

    path = Path(file_path).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise ValueError("file_path must be an existing Python file")
    if path.suffix.lower() != ".py":
        raise ValueError("Only Python files are supported")

    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as error:
        raise ValueError(f"Unable to read file: {path}") from error

    return parse_python_source(source, file_path=str(path))


def parse_python_project(project_path: str, max_files: int = 2000) -> dict[str, Any]:
    """Parse all Python files in a project and return AST semantic data."""

    root = Path(project_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("project_path must be an existing directory")

    files = sorted(path for path in root.rglob("*.py") if path.is_file() and ".git" not in path.parts)[:max_files]

    parsed_files: list[dict[str, Any]] = []
    parse_errors: list[dict[str, Any]] = []

    total_imports = 0
    total_classes = 0
    total_functions = 0

    for path in files:
        try:
            summary = parse_python_file(str(path))
            parsed_files.append(summary)
            total_imports += len(summary["imports"])
            total_classes += len(summary["classes"])
            total_functions += len(summary["functions"])
        except ValueError as error:
            parse_errors.append({"file_path": str(path), "error": str(error)})

    return {
        "language": "Python",
        "project_path": str(root),
        "files_scanned": len(files),
        "files_parsed": len(parsed_files),
        "totals": {
            "imports": total_imports,
            "classes": total_classes,
            "functions": total_functions,
        },
        "files": parsed_files,
        "errors": parse_errors,
    }


def parse_python_file_basic(file_path: str) -> dict[str, Any]:
    """Basic AST parser that extracts functions, classes, and imports."""

    path = Path(file_path).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise ValueError("file_path must be an existing Python file")
    if path.suffix.lower() != ".py":
        raise ValueError("Only Python files are supported")

    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)
    except SyntaxError as error:
        raise ValueError(f"Unable to parse Python source: {error.msg} at line {error.lineno}") from error
    except OSError as error:
        raise ValueError(f"Unable to read file: {path}") from error

    functions: list[dict[str, Any]] = []
    classes: list[dict[str, Any]] = []
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(
                {
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                }
            )
        elif isinstance(node, ast.ClassDef):
            classes.append({"name": node.name})
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return {
        "functions": functions,
        "classes": classes,
        "imports": imports,
    }


def _point_to_line(point: tuple[int, int]) -> int:
    return max(point[0] + 1, 1)


def _point_tuple(point: tuple[int, int]) -> tuple[int, int]:
    return (point[0], point[1])


def _named_text(node: Node | None, source_bytes: bytes) -> str | None:
    if node is None:
        return None

    text = source_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="ignore").strip()
    return text or None


def _extract_call_name(node: Node, source_bytes: bytes) -> str | None:
    for field_name in ("function", "callee", "name", "target", "value"):
        named_child = node.child_by_field_name(field_name)
        text = _named_text(named_child, source_bytes)
        if text:
            return text

    for child in node.children:
        if child.is_named:
            text = _named_text(child, source_bytes)
            if text:
                return text

    return None


def _collect_call_sites(root: Node, source_bytes: bytes, max_calls: int = 1000) -> list[AstCallSite]:
    call_sites: list[AstCallSite] = []
    stack = [root]

    while stack:
        current = stack.pop()
        node_type = current.type.lower()

        if (
            node_type in {"call_expression", "call", "function_call", "invocation_expression", "method_invocation"}
            or ("call" in node_type and node_type not in {"callback", "callable", "call_signature"})
        ):
            called_name = _extract_call_name(current, source_bytes)
            if called_name:
                call_sites.append(
                    AstCallSite(
                        called_name=called_name,
                        call_line=_point_to_line((current.start_point[0], current.start_point[1])),
                        call_type=current.type,
                    )
                )
                if len(call_sites) >= max_calls:
                    break

        for child in reversed(current.children):
            stack.append(child)

    return call_sites


def _offset_to_line(source_code: str, offset: int) -> int:
    return source_code[:offset].count("\n") + 1


def _fallback_python_call_sites(source_code: str, max_calls: int = 1000) -> list[AstCallSite]:
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []

    call_sites: list[AstCallSite] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        called_name: str | None = None
        if isinstance(node.func, ast.Name):
            called_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            called_name = node.func.attr
        if not called_name:
            continue
        call_sites.append(
            AstCallSite(
                called_name=called_name,
                call_line=getattr(node, "lineno", 1),
                call_type="fallback_python_call",
            )
        )
        if len(call_sites) >= max_calls:
            break

    return call_sites


def _fallback_generic_call_sites(source_code: str, max_calls: int = 1000) -> list[AstCallSite]:
    call_sites: list[AstCallSite] = []
    excluded_names = {"if", "for", "while", "switch", "catch", "return", "new", "function", "class"}
    pattern = re.compile(r"\b([A-Za-z_$][A-Za-z0-9_$]*)\s*\(")
    for match in pattern.finditer(source_code):
        name = match.group(1)
        if name in excluded_names:
            continue
        call_sites.append(
            AstCallSite(
                called_name=name,
                call_line=_offset_to_line(source_code, match.start()),
                call_type="fallback_regex_call",
            )
        )
        if len(call_sites) >= max_calls:
            break
    return call_sites


def _collect_fallback_call_sites(source_code: str, language: str, max_calls: int = 1000) -> list[AstCallSite]:
    if language == "python":
        return _fallback_python_call_sites(source_code, max_calls=max_calls)
    return _fallback_generic_call_sites(source_code, max_calls=max_calls)


def _call_sites_from_python_functions(functions: list[dict[str, Any]], max_calls: int = 1000) -> list[AstCallSite]:
    call_sites: list[AstCallSite] = []
    for function in functions:
        for call in function.get("calls", []):
            called_name = call.get("called_name")
            call_line = call.get("call_line")
            if not called_name or not isinstance(call_line, int):
                continue
            call_sites.append(
                AstCallSite(
                    called_name=called_name,
                    call_line=call_line,
                    call_type=str(call.get("call_type") or "python_ast_call"),
                )
            )
            if len(call_sites) >= max_calls:
                return call_sites
    return call_sites


def _syntax_unit_from_import(unit: SyntaxUnit) -> dict[str, Any]:
    return {
        "module": unit.name or "",
        "name": None,
        "alias": None,
        "line": _point_to_line(unit.start_point),
        "unit_type": unit.unit_type,
        "start_point": _point_tuple(unit.start_point),
        "end_point": _point_tuple(unit.end_point),
    }


def _syntax_unit_from_class(unit: SyntaxUnit) -> dict[str, Any]:
    class_name = unit.name or "anonymous_class"
    return {
        "name": class_name,
        "line": _point_to_line(unit.start_point),
        "end_line": _point_to_line(unit.end_point),
        "bases": [],
        "decorators": [],
        "methods": [],
        "unit_type": unit.unit_type,
        "start_point": _point_tuple(unit.start_point),
        "end_point": _point_tuple(unit.end_point),
    }


def _syntax_unit_from_function(unit: SyntaxUnit, parent_class: str | None, calls: list[dict[str, Any]]) -> dict[str, Any]:
    function_name = unit.name or "anonymous_function"
    return {
        "name": function_name,
        "line": _point_to_line(unit.start_point),
        "end_line": _point_to_line(unit.end_point),
        "arguments": [],
        "returns": None,
        "decorators": [],
        "is_async": unit.unit_type.startswith("async") or "async" in unit.unit_type,
        "parent_class": parent_class,
        "calls": calls,
        "unit_type": unit.unit_type,
        "start_point": _point_tuple(unit.start_point),
        "end_point": _point_tuple(unit.end_point),
    }


def _enclosing_class(function_unit: SyntaxUnit, classes: list[SyntaxUnit]) -> str | None:
    function_start = function_unit.start_point
    for class_unit in classes:
        if class_unit.start_point <= function_start <= class_unit.end_point:
            return class_unit.name
    return None


def _calls_for_unit(function_unit: SyntaxUnit, call_sites: list[AstCallSite]) -> list[dict[str, Any]]:
    start_line = function_unit.start_point[0]
    end_line = function_unit.end_point[0]
    calls: list[dict[str, Any]] = []

    for call_site in call_sites:
        call_line = call_site.call_line - 1
        if start_line <= call_line <= end_line:
            calls.append(
                {
                    "called_name": call_site.called_name,
                    "call_line": call_site.call_line,
                    "call_type": call_site.call_type,
                }
            )

    return calls


def _parse_source_file(file_path: Path, *, parser_available: bool | None = None) -> tuple[dict[str, Any], ProjectAstSnapshot]:
    source = file_path.read_text(encoding="utf-8", errors="ignore")
    resolved_language = resolve_language(None, file_path.suffix)

    preview = parse_source(source, language=resolved_language, file_extension=file_path.suffix, max_nodes=500)
    structure = parse_structure(source, language=resolved_language, file_extension=file_path.suffix, max_tree_nodes=500, max_depth=12)

    parse_mode = "tree_sitter"
    if resolved_language == "python":
        python_summary = parse_python_source(source, file_path=str(file_path))
        imports = python_summary.get("imports", [])
        classes = python_summary.get("classes", [])
        functions = python_summary.get("functions", [])
        call_sites = _call_sites_from_python_functions(functions)
        parse_mode = "python_ast"
    elif parser_available is True or (parser_available is None and preflight_tree_sitter_language(resolved_language)[0]):
        parser = get_parser(resolved_language)
        source_bytes = source.encode("utf-8")
        tree = parser.parse(source_bytes)
        call_sites = _collect_call_sites(tree.root_node, source_bytes)
        imports = [_syntax_unit_from_import(unit) for unit in structure.imports]
        classes = [_syntax_unit_from_class(unit) for unit in structure.classes]
        function_units = structure.functions
        functions = []
        for function_unit in function_units:
            parent_class = _enclosing_class(function_unit, structure.classes)
            function_calls = _calls_for_unit(function_unit, call_sites)
            functions.append(_syntax_unit_from_function(function_unit, parent_class=parent_class, calls=function_calls))
    else:
        call_sites = _collect_fallback_call_sites(source, resolved_language)
        imports = [_syntax_unit_from_import(unit) for unit in structure.imports]
        classes = [_syntax_unit_from_class(unit) for unit in structure.classes]
        function_units = structure.functions
        functions = []
        for function_unit in function_units:
            parent_class = _enclosing_class(function_unit, structure.classes)
            function_calls = _calls_for_unit(function_unit, call_sites)
            functions.append(_syntax_unit_from_function(function_unit, parent_class=parent_class, calls=function_calls))
        parse_mode = "fallback"

    file_payload = {
        "file_path": str(file_path),
        "language": resolved_language,
        "parse_mode": parse_mode,
        "imports": imports,
        "classes": classes,
        "functions": functions,
        "normalized_ast": {
            "language": preview.language,
            "total_nodes": preview.total_nodes,
            "truncated": preview.truncated or structure.truncated,
            "preview_nodes": [node.model_dump() for node in preview.nodes],
            "tree_nodes_returned": structure.tree_nodes_returned,
            "root": structure.root.model_dump(),
            "imports": [unit.model_dump() for unit in structure.imports],
            "classes": [unit.model_dump() for unit in structure.classes],
            "functions": [unit.model_dump() for unit in structure.functions],
            "calls": [call_site.model_dump() for call_site in call_sites],
        },
    }

    snapshot = ProjectAstSnapshot(
        language=preview.language,
        total_nodes=preview.total_nodes,
        truncated=preview.truncated or structure.truncated,
        preview_nodes=preview.nodes,
        tree_nodes_returned=structure.tree_nodes_returned,
        root=structure.root,
        imports=structure.imports,
        classes=structure.classes,
        functions=structure.functions,
        calls=call_sites,
    )

    return file_payload, snapshot


def parse_project_code(project_path: str) -> list[dict[str, Any]]:
    """Parse supported source files in a project into a normalized AST payload."""

    report = parse_project_code_report(project_path)
    return report["files"]


def parse_project_code_report(project_path: str) -> dict[str, Any]:
    """Parse project files and return files plus per-file diagnostics."""

    root = Path(project_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("project_path must be an existing directory")

    result: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    files_scanned = 0
    ignored_dirs = {".git", "node_modules", ".next", "dist", "build", "venv", ".venv", "__pycache__"}
    parser_availability: dict[str, bool] = {}

    for current_root, dir_names, files in os.walk(root):
        dir_names[:] = [name for name in dir_names if name not in ignored_dirs]

        for file_name in files:
            file_path = Path(current_root) / file_name
            ext = file_path.suffix.lower()

            if ext in {".py", ".js", ".jsx", ".ts", ".tsx"}:
                files_scanned += 1
                relative_path = file_path.relative_to(root).as_posix()
                resolved_language = resolve_language(None, ext)
                parser_available: bool | None = None
                if resolved_language != "python":
                    if resolved_language not in parser_availability:
                        parser_availability[resolved_language] = preflight_tree_sitter_language(resolved_language)[0]
                    parser_available = parser_availability[resolved_language]
                try:
                    data, normalized_snapshot = _parse_source_file(file_path, parser_available=parser_available)
                    data["normalized_ast"] = normalized_snapshot.model_dump()
                except (OSError, ValueError) as error:
                    errors.append(
                        {
                            "file": relative_path,
                            "path": str(file_path),
                            "language": resolved_language,
                            "error_type": "parse_error",
                            "error": str(error),
                        }
                    )
                    continue
            else:
                continue

            relative_path = file_path.relative_to(root).as_posix()

            result.append(
                {
                    "file": relative_path,
                    "path": str(file_path),
                    "language": data.get("language") or ("Python" if ext == ".py" else ext.lstrip(".").upper()),
                    "data": data,
                }
            )

    return {
        "project_path": str(root),
        "files_scanned": files_scanned,
        "files_parsed": len(result),
        "files_failed": len(errors),
        "files": result,
        "errors": errors,
    }
