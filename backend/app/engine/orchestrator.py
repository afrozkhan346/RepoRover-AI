from __future__ import annotations

from app.engine.ai_nlp import AINLPEngine
from app.engine.explanation_engine import ExplanationEngine
from app.engine.graph_builder import GraphBuilderEngine
from app.engine.parser import ParserEngine


class CoreEngineOrchestrator:
    """Single entrypoint for backend capabilities mapped to the core engine architecture."""

    def __init__(self) -> None:
        self.parser = ParserEngine()
        self.graph_builder = GraphBuilderEngine()
        self.ai_nlp = AINLPEngine()
        self.explanation_engine = ExplanationEngine()

    def analyze_repository_bundle(
        self,
        *,
        local_path: str,
        max_files: int = 2000,
        graph_type: str = "call",
        focus_file: str | None = None,
    ) -> dict:
        project = self.ai_nlp.project_summaries(local_path, max_files=max_files)
        quality = self.ai_nlp.quality_analysis(local_path, max_files=max_files)
        risk = self.ai_nlp.risk_scoring(local_path, max_files=max_files)
        graph = self.graph_builder.graph_analysis(
            local_path=local_path,
            graph_type=graph_type,
            max_files=max_files,
            traversal_start=None,
        )
        traces = self.explanation_engine.explainability_traces(
            local_path=local_path,
            max_files=max_files,
            focus_file=focus_file,
            graph_type=graph_type,
        )

        return {
            "project": project.model_dump(),
            "quality": quality.model_dump(),
            "risk": risk.model_dump(),
            "graph": graph.model_dump(),
            "traces": traces.model_dump(),
        }
