from __future__ import annotations

from app.services.call_graph_service import build_call_graph
from app.services.dependency_graph_service import build_dependency_graph
from app.services.graph_analysis_service import analyze_graph
from app.services.graph_builder import build_system_graph


class GraphBuilderEngine:
    def system_graph(self, local_path: str, max_files: int = 2000):
        return build_system_graph(local_path, max_files=max_files)

    def dependency_graph(self, local_path: str, max_files: int = 2000):
        return build_dependency_graph(local_path, max_files=max_files)

    def call_graph(self, local_path: str, max_files: int = 2000):
        return build_call_graph(local_path, max_files=max_files)

    def graph_analysis(
        self,
        *,
        local_path: str,
        graph_type: str = "dependency",
        max_files: int = 2000,
        traversal_start: str | None = None,
    ):
        return analyze_graph(
            local_path=local_path,
            graph_type=graph_type,
            max_files=max_files,
            traversal_start=traversal_start,
        )
