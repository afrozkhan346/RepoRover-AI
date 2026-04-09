from __future__ import annotations

import hashlib
import logging

from app.db.session import SessionLocal
from app.services import cache_service as cache
from app.services.parser_service import parse_source, parse_structure
from app.services.token_service import tokenize_source

logger = logging.getLogger(__name__)

_PARSER_TTL = 86400  # 24 hours — parse results rarely change for the same code


def _parser_key(source_code: str, **kwargs) -> str:
    raw = source_code + str(sorted(kwargs.items()))
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


class ParserEngine:
    def parse_ast_preview(
        self,
        source_code: str,
        *,
        language: str | None = None,
        file_extension: str | None = None,
        max_nodes: int = 200,
    ):
        # Not cached — used interactively, code changes frequently
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
        ns = "parser:structure"
        key = _parser_key(
            source_code,
            language=language,
            file_extension=file_extension,
            max_tree_nodes=max_tree_nodes,
            max_depth=max_depth,
        )
        with SessionLocal() as db:
            hit = cache.get(db, ns, key)
            if hit is not None:
                logger.debug("Cache HIT  parse_ast_structure")
                return hit
            result = parse_structure(
                source_code,
                language=language,
                file_extension=file_extension,
                max_tree_nodes=max_tree_nodes,
                max_depth=max_depth,
            )
            # parse_structure returns a dataclass — convert to dict for JSON storage
            result_dict = result if isinstance(result, dict) else vars(result)
            cache.set(db, ns, key, result_dict, ttl_seconds=_PARSER_TTL)
            logger.debug("Cache SET  parse_ast_structure")
        return result

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
