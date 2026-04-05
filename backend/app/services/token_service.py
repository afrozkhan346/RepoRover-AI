from __future__ import annotations

import io
import re
import tokenize
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


def _fallback_point(source_code: str, offset: int) -> tuple[int, int]:
    prefix = source_code[:offset]
    lines = prefix.splitlines()
    if not lines:
        return (0, 0)
    return (len(lines) - 1, len(lines[-1]))


def _fallback_token(token_type: str, lexeme: str, start_offset: int, end_offset: int, source_code: str) -> NormalizedToken:
    return NormalizedToken(
        token_type=token_type,
        lexeme=lexeme,
        start_byte=start_offset,
        end_byte=end_offset,
        start_point=_fallback_point(source_code, start_offset),
        end_point=_fallback_point(source_code, end_offset),
    )


def _fallback_python_tokens(source_code: str, max_tokens: int) -> TokenizeResult:
    tokens: list[NormalizedToken] = []
    total_tokens = 0

    for token_info in tokenize.generate_tokens(io.StringIO(source_code).readline):
        if token_info.type in {tokenize.ENCODING, tokenize.ENDMARKER, tokenize.NL}:
            continue
        total_tokens += 1
        if len(tokens) >= max_tokens:
            continue
        start_offset = sum(len(line) for line in source_code.splitlines(keepends=True)[: token_info.start[0] - 1]) + token_info.start[1]
        end_offset = sum(len(line) for line in source_code.splitlines(keepends=True)[: token_info.end[0] - 1]) + token_info.end[1]
        tokens.append(
            _fallback_token(tokenize.tok_name.get(token_info.type, "TOKEN"), token_info.string, start_offset, end_offset, source_code)
        )

    return TokenizeResult(
        language="python",
        total_tokens=total_tokens,
        truncated=total_tokens > max_tokens,
        tokens=tokens,
    )


def _fallback_generic_tokens(source_code: str, resolved_language: str, max_tokens: int) -> TokenizeResult:
    pattern = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+|==|!=|<=|>=|=>|[{}()[\].,;:+\-*/=]")
    matches = list(pattern.finditer(source_code))
    tokens = [
        _fallback_token("token", match.group(0), match.start(), match.end(), source_code)
        for match in matches[:max_tokens]
    ]
    return TokenizeResult(
        language=resolved_language,
        total_tokens=len(matches),
        truncated=len(matches) > max_tokens,
        tokens=tokens,
    )


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
        if resolved_language == "python":
            return _fallback_python_tokens(source_code, max_tokens)
        return _fallback_generic_tokens(source_code, resolved_language, max_tokens)

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
