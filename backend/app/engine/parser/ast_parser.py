from __future__ import annotations

from app.services.parser_service import parse_source, parse_structure
from app.services.token_service import tokenize_source


class ParserEngine:
    def parse_ast_preview(
        self,
        source_code: str,
        *,
        language: str | None = None,
        file_extension: str | None = None,
        max_nodes: int = 200,
    ):
        return parse_source(
            source_code,
            language=language,
            file_extension=file_extension,
            max_nodes=max_nodes,
        )

    def parse_ast_structure(
        self,
        source_code: str,
        *,
        language: str | None = None,
        file_extension: str | None = None,
        max_tree_nodes: int = 300,
        max_depth: int = 6,
    ):
        return parse_structure(
            source_code,
            language=language,
            file_extension=file_extension,
            max_tree_nodes=max_tree_nodes,
            max_depth=max_depth,
        )

    def extract_tokens(
        self,
        source_code: str,
        *,
        language: str | None = None,
        file_extension: str | None = None,
        max_tokens: int = 500,
    ):
        return tokenize_source(
            source_code,
            language=language,
            file_extension=file_extension,
            max_tokens=max_tokens,
        )
