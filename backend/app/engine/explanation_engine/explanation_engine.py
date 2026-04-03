from __future__ import annotations

from app.services.explainability_trace_service import build_explainability_traces


class ExplanationEngine:
    def explainability_traces(
        self,
        *,
        local_path: str,
        max_files: int = 2000,
        focus_file: str | None = None,
        graph_type: str = "call",
    ):
        return build_explainability_traces(
            local_path=local_path,
            max_files=max_files,
            focus_file=focus_file,
            graph_type=graph_type,
        )
