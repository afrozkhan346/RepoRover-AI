from __future__ import annotations

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
        raise ValueError(f"Unsupported Tree-sitter language: {resolved_language}") from error

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
        raise ValueError(f"Unsupported Tree-sitter language: {resolved_language}") from error

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
