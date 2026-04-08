from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.services.project_summary_service import summarize_project


def _fake_dependency_graph() -> SimpleNamespace:
    edges = [
        SimpleNamespace(edge_type="imports", source="file:app/main.py", target="import:fastapi"),
        SimpleNamespace(edge_type="imports", source="file:app/main.py", target="import:pydantic"),
        SimpleNamespace(edge_type="imports", source="file:app/api.py", target="import:fastapi"),
    ]
    return SimpleNamespace(edges=edges, summary=SimpleNamespace(total_edges=len(edges)))


def _fake_call_graph() -> SimpleNamespace:
    edges = [
        SimpleNamespace(edge_type="calls", source="func:main", target="func:build_app"),
        SimpleNamespace(edge_type="calls", source="func:build_app", target="func:run"),
    ]
    nodes = [
        SimpleNamespace(id="func:main", label="main"),
        SimpleNamespace(id="func:build_app", label="build_app"),
        SimpleNamespace(id="func:run", label="run"),
    ]
    return SimpleNamespace(edges=edges, nodes=nodes, summary=SimpleNamespace(call_edges=len(edges)))


class ProjectSummaryServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="repo_summary_service_test_"))
        (self.root / "app").mkdir(parents=True, exist_ok=True)
        (self.root / "app" / "main.py").write_text("print('hello')\n", encoding="utf-8")
        (self.root / "app" / "api.py").write_text("def route():\n    return 1\n", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_falls_back_to_deterministic_summary_when_llm_unavailable(self) -> None:
        with (
            patch("app.services.project_summary_service.build_dependency_graph", return_value=_fake_dependency_graph()),
            patch("app.services.project_summary_service.build_call_graph", return_value=_fake_call_graph()),
            patch("app.services.project_summary_service.generate_repo_summaries", return_value=None),
        ):
            response = summarize_project(str(self.root), max_files=200)

        self.assertIn("This project is", response.project_summary)
        self.assertIn("Architecture appears", response.architecture_summary)
        self.assertIn("Likely execution flow", response.execution_flow_summary)
        self.assertEqual(response.metrics.dependency_edges, 3)
        self.assertEqual(response.metrics.call_edges, 2)

    def test_uses_readme_purpose_and_info_when_llm_unavailable(self) -> None:
        (self.root / "README.md").write_text(
            "# Sample Project\n\n"
            "A workflow tool for classroom task planning.\n\n"
            "- Coordinates assignments and schedules\n"
            "- Shares progress dashboards\n",
            encoding="utf-8",
        )

        with (
            patch("app.services.project_summary_service.build_dependency_graph", return_value=_fake_dependency_graph()),
            patch("app.services.project_summary_service.build_call_graph", return_value=_fake_call_graph()),
            patch("app.services.project_summary_service.generate_repo_summaries", return_value=None),
        ):
            response = summarize_project(str(self.root), max_files=200)

        self.assertIn("workflow tool for classroom task planning", response.project_summary.lower())
        self.assertIn("coordinates assignments", response.project_summary.lower())

    def test_uses_llm_structured_summary_when_available(self) -> None:
        llm_payload = {
            "project_summary": "LLM project summary.",
            "architecture_summary": "LLM architecture summary.",
            "execution_flow_summary": "LLM execution flow summary.",
        }

        with (
            patch("app.services.project_summary_service.build_dependency_graph", return_value=_fake_dependency_graph()),
            patch("app.services.project_summary_service.build_call_graph", return_value=_fake_call_graph()),
            patch("app.services.project_summary_service.generate_repo_summaries", return_value=llm_payload),
        ):
            response = summarize_project(str(self.root), max_files=200)

        self.assertEqual(response.project_summary, "LLM project summary.")
        self.assertEqual(response.architecture_summary, "LLM architecture summary.")
        self.assertEqual(response.execution_flow_summary, "LLM execution flow summary.")


if __name__ == "__main__":
    unittest.main()