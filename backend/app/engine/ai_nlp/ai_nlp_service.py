from __future__ import annotations

from app.services.ai_explanation import explain_code
from app.services.project_summary_service import summarize_project
from app.services.quality_analysis_service import analyze_quality
from app.services.risk_scoring_service import score_risk
from app.services.understanding import understand_project


class AINLPEngine:
    def explain_code(self, code: str, language: str | None = None, question: str | None = None):
        return explain_code(code, language, question)

    def project_summaries(self, local_path: str, max_files: int = 2000):
        return summarize_project(local_path, max_files=max_files)

    def quality_analysis(self, local_path: str, max_files: int = 2000):
        return analyze_quality(local_path, max_files=max_files)

    def risk_scoring(self, local_path: str, max_files: int = 2000):
        return score_risk(local_path, max_files=max_files)

    def project_understanding(self, local_path: str, max_files: int = 2000):
        return understand_project(local_path, max_files=max_files)
