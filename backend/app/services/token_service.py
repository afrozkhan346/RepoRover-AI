from __future__ import annotations

from dataclasses import dataclass

from tree_sitter import Node
from tree_sitter_language_pack import get_language, get_parser

from app.schemas.tokens import NormalizedToken
from app.services.parser_service import resolve_language


@dataclass(frozen=True)
class TokenizeResult:
    language: str
    total_tokens: int
    truncated: bool
    tokens: list[NormalizedToken]


def _is_leaf(node: Node) -> bool:
    return node.child_count == 0


def _normalize_token(node: Node, source_bytes: bytes) -> NormalizedToken:
    lexeme = source_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="ignore")
    return NormalizedToken(
        token_type=node.type,
        lexeme=lexeme,
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        start_point=(node.start_point[0], node.start_point[1]),
        end_point=(node.end_point[0], node.end_point[1]),
    )


def tokenize_source(
    source_code: str,
    *,
    language: str | None = None,
    file_extension: str | None = None,
    max_tokens: int = 500,
) -> TokenizeResult:
    resolved_language = resolve_language(language, file_extension)

    try:
        get_language(resolved_language)
        parser = get_parser(resolved_language)
    except Exception as error:
        raise ValueError(f"Unsupported Tree-sitter language: {resolved_language}") from error

    source_bytes = source_code.encode("utf-8")
    tree = parser.parse(source_bytes)
    cursor = tree.walk()

    tokens: list[NormalizedToken] = []
    total_tokens = 0
    truncated = False

    reached_root = False
    while not reached_root:
        current = cursor.node
        if _is_leaf(current):
            total_tokens += 1
            if len(tokens) < max_tokens:
                tokens.append(_normalize_token(current, source_bytes))
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

    return TokenizeResult(
        language=resolved_language,
        total_tokens=total_tokens,
        truncated=truncated,
        tokens=tokens,
    )
