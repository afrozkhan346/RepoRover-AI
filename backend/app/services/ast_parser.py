from __future__ import annotations

import ast
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ImportInfo:
    module: str
    name: str | None
    alias: str | None
    line: int


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

    def _add_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool) -> None:
        arguments = [arg.arg for arg in node.args.posonlyargs]
        arguments.extend(arg.arg for arg in node.args.args)
        if node.args.vararg:
            arguments.append(f"*{node.args.vararg.arg}")
        arguments.extend(arg.arg for arg in node.args.kwonlyargs)
        if node.args.kwarg:
            arguments.append(f"**{node.args.kwarg.arg}")

        info = FunctionInfo(
            name=node.name,
            line=node.lineno,
            end_line=getattr(node, "end_lineno", node.lineno),
            arguments=arguments,
            returns=_expr_to_text(node.returns) if node.returns else None,
            decorators=[_expr_to_text(decorator) for decorator in node.decorator_list],
            is_async=is_async,
            parent_class=self._class_stack[-1] if self._class_stack else None,
        )
        self.functions.append(info)


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


def parse_project_code(project_path: str) -> list[dict[str, Any]]:
    """Parse every Python file in a project using parse_python_file."""

    root = Path(project_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("project_path must be an existing directory")

    result: list[dict[str, Any]] = []

    for current_root, _, files in os.walk(root):
        for file_name in files:
            if not file_name.endswith(".py"):
                continue

            file_path = Path(current_root) / file_name
            data = parse_python_file(str(file_path))

            result.append(
                {
                    "file": file_name,
                    "path": str(file_path),
                    "data": data,
                }
            )

    return result
