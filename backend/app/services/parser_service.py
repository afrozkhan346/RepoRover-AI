from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Any

from tree_sitter import Node
from tree_sitter_language_pack import get_language, get_parser

from app.schemas.parsing import AstTreeNode, NormalizedAstNode, SyntaxUnit


@dataclass(frozen=True)
class ParseResult:
    language: str
    total_nodes: int
    truncated: bool
    nodes: list[NormalizedAstNode]


@dataclass(frozen=True)
class AstStructureResult:
    language: str
    total_nodes: int
    tree_nodes_returned: int
    truncated: bool
    root: AstTreeNode
    imports: list[SyntaxUnit]
    classes: list[SyntaxUnit]
    functions: list[SyntaxUnit]


_LANGUAGE_BY_EXTENSION: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".json": "json",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".go": "go",
    ".java": "java",
    ".rb": "ruby",
    ".rs": "rust",
    ".php": "php",
}


def resolve_language(language: str | None, file_extension: str | None) -> str:
    if language:
        return language.strip().lower()
    if file_extension:
        normalized = file_extension.strip().lower()
        if not normalized.startswith("."):
            normalized = f".{normalized}"
        if normalized in _LANGUAGE_BY_EXTENSION:
            return _LANGUAGE_BY_EXTENSION[normalized]
    raise ValueError("Language could not be resolved. Provide language or supported file_extension.")


def _normalize_node(node: Node) -> NormalizedAstNode:
    return NormalizedAstNode(
        node_type=node.type,
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        start_point=(node.start_point[0], node.start_point[1]),
        end_point=(node.end_point[0], node.end_point[1]),
        child_count=node.child_count,
    )


def _node_text(node: Node, source_bytes: bytes) -> str:
    return source_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="ignore").strip()


def _first_named_child_text(node: Node, source_bytes: bytes) -> str | None:
    for child in node.children:
        if child.is_named:
            text = _node_text(child, source_bytes)
            if text:
                return text
    return None


def _collect_syntax_units(node: Node, source_bytes: bytes) -> tuple[list[SyntaxUnit], list[SyntaxUnit], list[SyntaxUnit], int]:
    imports: list[SyntaxUnit] = []
    classes: list[SyntaxUnit] = []
    functions: list[SyntaxUnit] = []
    total_nodes = 0

    stack = [node]
    while stack:
        current = stack.pop()
        total_nodes += 1

        node_type = current.type.lower()
        if "import" in node_type:
            imports.append(
                SyntaxUnit(
                    unit_type=current.type,
                    name=_first_named_child_text(current, source_bytes),
                    start_point=(current.start_point[0], current.start_point[1]),
                    end_point=(current.end_point[0], current.end_point[1]),
                )
            )
        elif "class" in node_type:
            classes.append(
                SyntaxUnit(
                    unit_type=current.type,
                    name=_first_named_child_text(current, source_bytes),
                    start_point=(current.start_point[0], current.start_point[1]),
                    end_point=(current.end_point[0], current.end_point[1]),
                )
            )
        elif "function" in node_type or node_type in {"method_definition", "function_definition"}:
            functions.append(
                SyntaxUnit(
                    unit_type=current.type,
                    name=_first_named_child_text(current, source_bytes),
                    start_point=(current.start_point[0], current.start_point[1]),
                    end_point=(current.end_point[0], current.end_point[1]),
                )
            )

        for child in reversed(current.children):
            stack.append(child)

    return imports, classes, functions, total_nodes


def _build_tree(
    node: Node,
    *,
    max_nodes: int,
    max_depth: int,
) -> tuple[AstTreeNode, int, bool]:
    count = 1
    truncated = False

    def walk(current: Node, depth: int) -> AstTreeNode:
        nonlocal count, truncated
        children: list[AstTreeNode] = []

        if depth < max_depth:
            for child in current.children:
                if count >= max_nodes:
                    truncated = True
                    break
                count += 1
                children.append(walk(child, depth + 1))
        elif current.child_count > 0:
            truncated = True

        return AstTreeNode(
            node_type=current.type,
            start_point=(current.start_point[0], current.start_point[1]),
            end_point=(current.end_point[0], current.end_point[1]),
            children=children,
        )

    root = walk(node, 0)
    return root, count, truncated


def _fallback_point(source_code: str, offset: int) -> tuple[int, int]:
    prefix = source_code[:offset]
    lines = prefix.splitlines()
    if not lines:
        return (0, 0)
    return (len(lines) - 1, len(lines[-1]))


def _fallback_end_point(source_code: str, text: str, start_offset: int) -> tuple[int, int]:
    return _fallback_point(source_code, start_offset + len(text))


def _fallback_node(node_type: str, source_code: str, start_offset: int, end_offset: int, child_count: int = 0) -> NormalizedAstNode:
    return NormalizedAstNode(
        node_type=node_type,
        start_byte=start_offset,
        end_byte=end_offset,
        start_point=_fallback_point(source_code, start_offset),
        end_point=_fallback_point(source_code, end_offset),
        child_count=child_count,
    )


def _fallback_tree_root(source_code: str) -> AstTreeNode:
    line_count = max(len(source_code.splitlines()), 1)
    end_column = len(source_code.splitlines()[-1]) if source_code.splitlines() else 0
    return AstTreeNode(
        node_type="module",
        start_point=(0, 0),
        end_point=(line_count - 1, end_column),
        children=[],
    )


def _fallback_python_preview(source_code: str, max_nodes: int) -> ParseResult:
    tree = ast.parse(source_code)
    nodes: list[NormalizedAstNode] = []
    total_nodes = 0

    for current in ast.walk(tree):
        total_nodes += 1
        if len(nodes) >= max_nodes:
            continue
        start_line = max(getattr(current, "lineno", 1) - 1, 0)
        start_col = max(getattr(current, "col_offset", 0), 0)
        end_line = max(getattr(current, "end_lineno", start_line + 1) - 1, start_line)
        end_col = max(getattr(current, "end_col_offset", start_col), start_col)
        nodes.append(
            NormalizedAstNode(
                node_type=type(current).__name__,
                start_byte=0,
                end_byte=0,
                start_point=(start_line, start_col),
                end_point=(end_line, end_col),
                child_count=len(list(ast.iter_child_nodes(current))),
            )
        )

    return ParseResult(
        language="python",
        total_nodes=total_nodes,
        truncated=total_nodes > max_nodes,
        nodes=nodes,
    )


def _fallback_python_structure(source_code: str, max_tree_nodes: int) -> AstStructureResult:
    tree = ast.parse(source_code)
    imports: list[SyntaxUnit] = []
    classes: list[SyntaxUnit] = []
    functions: list[SyntaxUnit] = []

    for current in ast.walk(tree):
        if isinstance(current, ast.Import):
            for alias in current.names:
                imports.append(
                    SyntaxUnit(
                        unit_type="import",
                        name=alias.name,
                        start_point=(max(current.lineno - 1, 0), max(current.col_offset, 0)),
                        end_point=(max(getattr(current, "end_lineno", current.lineno) - 1, 0), max(getattr(current, "end_col_offset", current.col_offset), 0)),
                    )
                )
        elif isinstance(current, ast.ImportFrom):
            imports.append(
                SyntaxUnit(
                    unit_type="import_from",
                    name=current.module,
                    start_point=(max(current.lineno - 1, 0), max(current.col_offset, 0)),
                    end_point=(max(getattr(current, "end_lineno", current.lineno) - 1, 0), max(getattr(current, "end_col_offset", current.col_offset), 0)),
                )
            )
        elif isinstance(current, ast.ClassDef):
            classes.append(
                SyntaxUnit(
                    unit_type="class_definition",
                    name=current.name,
                    start_point=(max(current.lineno - 1, 0), max(current.col_offset, 0)),
                    end_point=(max(getattr(current, "end_lineno", current.lineno) - 1, 0), max(getattr(current, "end_col_offset", current.col_offset), 0)),
                )
            )
        elif isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(
                SyntaxUnit(
                    unit_type="function_definition",
                    name=current.name,
                    start_point=(max(current.lineno - 1, 0), max(current.col_offset, 0)),
                    end_point=(max(getattr(current, "end_lineno", current.lineno) - 1, 0), max(getattr(current, "end_col_offset", current.col_offset), 0)),
                )
            )

    total_nodes = sum(1 for _ in ast.walk(tree))
    return AstStructureResult(
        language="python",
        total_nodes=total_nodes,
        tree_nodes_returned=min(total_nodes, max_tree_nodes),
        truncated=total_nodes > max_tree_nodes,
        root=_fallback_tree_root(source_code),
        imports=imports,
        classes=classes,
        functions=functions,
    )


def _fallback_generic_preview(source_code: str, language: str, max_nodes: int) -> ParseResult:
    pattern = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|[{}()[\].,;:+\-*/=]")
    matches = list(pattern.finditer(source_code))
    nodes = [
        _fallback_node("token", source_code, match.start(), match.end())
        for match in matches[:max_nodes]
    ]
    return ParseResult(
        language=language,
        total_nodes=len(matches),
        truncated=len(matches) > max_nodes,
        nodes=nodes,
    )


def _fallback_generic_structure(source_code: str, language: str, max_tree_nodes: int) -> AstStructureResult:
    imports: list[SyntaxUnit] = []
    classes: list[SyntaxUnit] = []
    functions: list[SyntaxUnit] = []

    for match in re.finditer(r"^\s*import\s+([A-Za-z0-9_./-]+)", source_code, flags=re.MULTILINE):
        imports.append(
            SyntaxUnit(
                unit_type="import",
                name=match.group(1),
                start_point=_fallback_point(source_code, match.start()),
                end_point=_fallback_end_point(source_code, match.group(0), match.start()),
            )
        )

    for match in re.finditer(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)", source_code):
        classes.append(
            SyntaxUnit(
                unit_type="class_definition",
                name=match.group(1),
                start_point=_fallback_point(source_code, match.start()),
                end_point=_fallback_end_point(source_code, match.group(0), match.start()),
            )
        )

    function_patterns = [
        re.compile(r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("),
        re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\([^)]*\)\s*=>"),
        re.compile(r"\bconst\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\([^)]*\)\s*=>"),
        re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*\{"),
    ]
    seen_function_spans: set[tuple[int, int]] = set()
    for pattern in function_patterns:
        for match in pattern.finditer(source_code):
            span = match.span()
            if span in seen_function_spans:
                continue
            seen_function_spans.add(span)
            functions.append(
                SyntaxUnit(
                    unit_type="function_definition",
                    name=match.group(1),
                    start_point=_fallback_point(source_code, match.start()),
                    end_point=_fallback_end_point(source_code, match.group(0), match.start()),
                )
            )

    total_nodes = len(imports) + len(classes) + len(functions) + 1
    return AstStructureResult(
        language=language,
        total_nodes=total_nodes,
        tree_nodes_returned=min(total_nodes, max_tree_nodes),
        truncated=total_nodes > max_tree_nodes,
        root=_fallback_tree_root(source_code),
        imports=imports,
        classes=classes,
        functions=functions,
    )


def _fallback_parse_source(source_code: str, resolved_language: str, max_nodes: int) -> ParseResult:
    if resolved_language == "python":
        return _fallback_python_preview(source_code, max_nodes)
    return _fallback_generic_preview(source_code, resolved_language, max_nodes)


def _fallback_parse_structure(
    source_code: str,
    resolved_language: str,
    max_tree_nodes: int,
) -> AstStructureResult:
    if resolved_language == "python":
        return _fallback_python_structure(source_code, max_tree_nodes)
    return _fallback_generic_structure(source_code, resolved_language, max_tree_nodes)


def parse_source(
    source_code: str,
    *,
    language: str | None = None,
    file_extension: str | None = None,
    max_nodes: int = 200,
) -> ParseResult:
    resolved_language = resolve_language(language, file_extension)

    try:
        get_language(resolved_language)
        parser = get_parser(resolved_language)
    except Exception as error:
        return _fallback_parse_source(source_code, resolved_language, max_nodes)

    tree = parser.parse(source_code.encode("utf-8"))
    cursor = tree.walk()

    nodes: list[NormalizedAstNode] = []
    total_nodes = 0
    truncated = False

    reached_root = False
    while not reached_root:
        current = cursor.node
        total_nodes += 1
        if len(nodes) < max_nodes:
            nodes.append(_normalize_node(current))
        else:
            truncated = True

        if cursor.goto_first_child():
            continue

        if cursor.goto_next_sibling():
            continue

        while True:
            if not cursor.goto_parent():
                reached_root = True
                break
            if cursor.goto_next_sibling():
                break

    return ParseResult(
        language=resolved_language,
        total_nodes=total_nodes,
        truncated=truncated,
        nodes=nodes,
    )


def parse_structure(
    source_code: str,
    *,
    language: str | None = None,
    file_extension: str | None = None,
    max_tree_nodes: int = 300,
    max_depth: int = 6,
) -> AstStructureResult:
    resolved_language = resolve_language(language, file_extension)

    try:
        get_language(resolved_language)
        parser = get_parser(resolved_language)
    except Exception as error:
        return _fallback_parse_structure(source_code, resolved_language, max_tree_nodes)

    source_bytes = source_code.encode("utf-8")
    tree = parser.parse(source_bytes)
    root_node = tree.root_node

    imports, classes, functions, total_nodes = _collect_syntax_units(root_node, source_bytes)
    root, tree_nodes_returned, tree_truncated = _build_tree(
        root_node,
        max_nodes=max_tree_nodes,
        max_depth=max_depth,
    )

    return AstStructureResult(
        language=resolved_language,
        total_nodes=total_nodes,
        tree_nodes_returned=tree_nodes_returned,
        truncated=tree_truncated,
        root=root,
        imports=imports,
        classes=classes,
        functions=functions,
    )
