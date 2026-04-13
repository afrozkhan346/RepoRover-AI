from __future__ import annotations

import hashlib
import logging

from app.db.session import SessionLocal
from app.services import cache_service as cache
from app.schemas.call_graph import CallGraphResponse
from app.schemas.call_graph import CallGraphAnalytics
from app.schemas.dependency_graph import DependencyGraphResponse
from app.schemas.graph_analysis import GraphAnalysisResponse
from app.services.call_graph_service import build_call_graph, build_call_graph_analytics
from app.services.dependency_graph_service import build_dependency_graph
from app.services.graph_analysis_service import analyze_graph
from app.services.graph_builder import build_system_graph

logger = logging.getLogger(__name__)

# Default TTL: 1 hour.  Set to None for no expiry.
_DEFAULT_TTL = 3600


def _graph_key(local_path: str, max_files: int, suffix: str = "") -> str:
    """Stable, compact cache key from path + params."""
    raw = f"{local_path}|{max_files}|{suffix}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


class GraphBuilderEngine:
    """Graph-building facade with transparent SQLite-backed cache."""

    # ------------------------------------------------------------------ #
    # System graph
    # ------------------------------------------------------------------ #
    def system_graph(self, local_path: str, max_files: int = 2000):
        ns, key = "graph:system", _graph_key(local_path, max_files)
        with SessionLocal() as db:
            hit = cache.get(db, ns, key)
            if hit is not None:
                logger.info("Cache HIT  system_graph  %s", local_path)
                return hit
            result = build_system_graph(local_path, max_files=max_files)
            cache.set(db, ns, key, result, ttl_seconds=_DEFAULT_TTL)
            logger.info("Cache SET  system_graph  %s", local_path)
        return result

    # ------------------------------------------------------------------ #
    # Dependency graph
    # ------------------------------------------------------------------ #
    def dependency_graph(self, local_path: str, max_files: int = 2000):
        ns, key = "graph:dependency", _graph_key(local_path, max_files)
        with SessionLocal() as db:
            hit = cache.get(db, ns, key)
            if hit is not None:
                logger.info("Cache HIT  dependency_graph  %s", local_path)
                return DependencyGraphResponse(**hit)
            result = build_dependency_graph(local_path, max_files=max_files)
            cache.set(db, ns, key, result.model_dump(), ttl_seconds=_DEFAULT_TTL)
            logger.info("Cache SET  dependency_graph  %s", local_path)
        return result

    # ------------------------------------------------------------------ #
    # Call graph
    # ------------------------------------------------------------------ #
    def call_graph(self, local_path: str, max_files: int = 2000):
        ns, key = "graph:call", _graph_key(local_path, max_files)
        with SessionLocal() as db:
            hit = cache.get(db, ns, key)
            if hit is not None:
                logger.info("Cache HIT  call_graph  %s", local_path)
                return CallGraphResponse(**hit)
            result = build_call_graph(local_path, max_files=max_files)
            cache.set(db, ns, key, result.model_dump(), ttl_seconds=_DEFAULT_TTL)
            logger.info("Cache SET  call_graph  %s", local_path)
        return result

    def call_graph_analytics(self, local_path: str, max_files: int = 2000):
        ns, key = "graph:call_analytics", _graph_key(local_path, max_files)
        with SessionLocal() as db:
            hit = cache.get(db, ns, key)
            if hit is not None:
                logger.info("Cache HIT  call_graph_analytics  %s", local_path)
                return CallGraphAnalytics(**hit)
            result = build_call_graph_analytics(local_path, max_files=max_files)
            cache.set(db, ns, key, result.model_dump(), ttl_seconds=_DEFAULT_TTL)
            logger.info("Cache SET  call_graph_analytics  %s", local_path)
        return result

    # ------------------------------------------------------------------ #
    # Graph analysis
    # ------------------------------------------------------------------ #
    def graph_analysis(
        self,
        *,
        local_path: str,
        graph_type: str = "dependency",
        max_files: int = 2000,
        traversal_start: str | None = None,
    ):
        ns = "graph:analysis"
        key = _graph_key(local_path, max_files, suffix=f"{graph_type}|{traversal_start}")
        with SessionLocal() as db:
            hit = cache.get(db, ns, key)
            if hit is not None:
                logger.info("Cache HIT  graph_analysis  %s", local_path)
                return GraphAnalysisResponse(**hit)
            result = analyze_graph(
                local_path=local_path,
                graph_type=graph_type,
                max_files=max_files,
                traversal_start=traversal_start,
            )
            cache.set(db, ns, key, result.model_dump(), ttl_seconds=_DEFAULT_TTL)
            logger.info("Cache SET  graph_analysis  %s", local_path)
        return result
