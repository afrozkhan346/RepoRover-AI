from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def _fake_dependency_graph() -> SimpleNamespace:
    edges = [
        SimpleNamespace(edge_type="imports", source="file:app/main.py", target="import:fastapi"),
        SimpleNamespace(edge_type="imports", source="file:app/main.py", target="import:pydantic"),
    ]
    return SimpleNamespace(edges=edges, summary=SimpleNamespace(total_edges=len(edges)))


def _fake_call_graph() -> SimpleNamespace:
    edges = [
        SimpleNamespace(edge_type="calls", source="func:main", target="func:build_app"),
    ]
    nodes = [
        SimpleNamespace(id="func:main", label="main"),
        SimpleNamespace(id="func:build_app", label="build_app"),
    ]
    return SimpleNamespace(edges=edges, nodes=nodes, summary=SimpleNamespace(call_edges=len(edges)))


class AIProjectSummariesRouteTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="repo_summary_route_test_"))
        (self.root / "app").mkdir(parents=True, exist_ok=True)
        (self.root / "app" / "main.py").write_text("print('hello')\n", encoding="utf-8")
        (self.root / "app" / "api.py").write_text("def route():\n    return 1\n", encoding="utf-8")
        self.client = TestClient(app)

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_route_uses_llm_summaries_when_available(self) -> None:
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
            response = self.client.post(
                "/api/ai/project-summaries",
                json={"local_path": str(self.root), "max_files": 200},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["project_summary"], "LLM project summary.")
        self.assertEqual(payload["architecture_summary"], "LLM architecture summary.")
        self.assertEqual(payload["execution_flow_summary"], "LLM execution flow summary.")

    def test_route_falls_back_when_llm_unavailable(self) -> None:
        with (
            patch("app.services.project_summary_service.build_dependency_graph", return_value=_fake_dependency_graph()),
            patch("app.services.project_summary_service.build_call_graph", return_value=_fake_call_graph()),
            patch("app.services.project_summary_service.generate_repo_summaries", return_value=None),
        ):
            response = self.client.post(
                "/api/ai/project-summaries",
                json={"local_path": str(self.root), "max_files": 200},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("Detected", payload["project_summary"])
        self.assertIn("Architecture appears", payload["architecture_summary"])
        self.assertIn("Likely execution flow", payload["execution_flow_summary"])


if __name__ == "__main__":
    unittest.main()