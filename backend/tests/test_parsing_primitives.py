from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from git import Repo

from app.core.config import Settings
from app.main import app
from app.services.ast_parser import parse_project_code, parse_python_source
from app.services.parser_service import parse_source, parse_structure
from app.services.token_service import tokenize_source


PY_SOURCE = '''
import os
from math import sqrt as root

class Greeter:
    def hello(self, name):
        print(name)
        return root(4)

def helper(x):
    return Greeter().hello(x)
'''


JS_SOURCE = '''
import fs from 'fs';
class Greeter {
  hello(name) {
    console.log(name);
  }
}
function helper(x) {
  return Greeter.prototype.hello(x);
}
'''


class ParsingPrimitivesTestCase(unittest.TestCase):
    def test_token_extraction_uses_tree_sitter_for_supported_languages(self) -> None:
        python_tokens = tokenize_source(PY_SOURCE, language="python", max_tokens=100)
        javascript_tokens = tokenize_source(JS_SOURCE, language="javascript", max_tokens=100)

        self.assertEqual(python_tokens.language, "python")
        self.assertEqual(javascript_tokens.language, "javascript")
        self.assertGreater(python_tokens.total_tokens, 0)
        self.assertGreater(javascript_tokens.total_tokens, 0)
        self.assertFalse(python_tokens.truncated)

    def test_ast_preview_returns_normalized_nodes(self) -> None:
        preview = parse_source(PY_SOURCE, language="python", max_nodes=20)

        self.assertEqual(preview.language, "python")
        self.assertGreater(preview.total_nodes, 0)
        self.assertGreater(len(preview.nodes), 0)
        self.assertEqual(preview.nodes[0].node_type, "module")

    def test_ast_structure_extracts_imports_classes_and_functions(self) -> None:
        structure = parse_structure(PY_SOURCE, language="python", max_tree_nodes=20, max_depth=6)

        import_names = [unit.name for unit in structure.imports if unit.name]
        class_names = [unit.name for unit in structure.classes if unit.name]
        function_names = [unit.name for unit in structure.functions if unit.name]

        self.assertIn("os", import_names)
        self.assertIn("math", import_names)
        self.assertIn("Greeter", class_names)
        self.assertIn("hello", function_names)
        self.assertIn("helper", function_names)

    def test_python_semantic_parser_extracts_calls(self) -> None:
        summary = parse_python_source(PY_SOURCE)

        self.assertEqual([item["module"] for item in summary["imports"]], ["os", "math"])
        self.assertEqual(summary["classes"][0]["name"], "Greeter")
        self.assertEqual(summary["classes"][0]["methods"], ["hello"])

        function_calls = {item["name"]: [call["called_name"] for call in item["calls"]] for item in summary["functions"]}
        self.assertEqual(function_calls["hello"], ["print", "root"])
        self.assertEqual(function_calls["helper"], ["hello", "Greeter"])

    def test_project_parser_emits_normalized_ast_for_supported_files(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="repo_rover_parsing_test_"))
        try:
            (root / "app.py").write_text(PY_SOURCE, encoding="utf-8")
            (root / "app.js").write_text(JS_SOURCE, encoding="utf-8")

            project = parse_project_code(str(root))
            files = {item["file"]: item for item in project}

            self.assertIn("app.py", files)
            self.assertIn("app.js", files)

            python_snapshot = files["app.py"]["data"]["normalized_ast"]
            javascript_snapshot = files["app.js"]["data"]["normalized_ast"]

            self.assertEqual(python_snapshot["language"], "python")
            self.assertEqual(javascript_snapshot["language"], "javascript")
            self.assertGreaterEqual(len(python_snapshot["calls"]), 1)
            self.assertGreaterEqual(len(javascript_snapshot["calls"]), 1)
        finally:
            shutil.rmtree(root)

    def test_public_api_routes_return_expected_payload_shapes(self) -> None:
        client = TestClient(app)

        preview_response = client.post(
            "/api/parsing/ast-preview",
            json={"language": "python", "source_code": PY_SOURCE, "max_nodes": 20},
        )
        structure_response = client.post(
            "/api/parsing/ast-structure",
            json={"language": "python", "source_code": PY_SOURCE, "max_tree_nodes": 20, "max_depth": 6},
        )
        token_response = client.post(
            "/api/tokens/preview",
            json={"language": "python", "source_code": PY_SOURCE, "max_tokens": 20},
        )

        self.assertEqual(preview_response.status_code, 200)
        self.assertEqual(structure_response.status_code, 200)
        self.assertEqual(token_response.status_code, 200)

        self.assertEqual(sorted(preview_response.json().keys()), ["language", "nodes", "total_nodes", "truncated"])
        self.assertEqual(sorted(structure_response.json().keys()), ["classes", "functions", "imports", "language", "root", "total_nodes", "tree_nodes_returned", "truncated"])
        self.assertEqual(sorted(token_response.json().keys()), ["language", "tokens", "total_tokens", "truncated"])

    def test_projects_allowed_extensions_accepts_json_and_csv_formats(self) -> None:
        empty_settings = Settings(projects_allowed_extensions="[]")
        json_settings = Settings(projects_allowed_extensions='["py", ".js", ""]')
        csv_settings = Settings(projects_allowed_extensions="py, .ts, jsx")

        self.assertEqual(empty_settings.projects_allowed_extensions, [])
        self.assertEqual(json_settings.projects_allowed_extensions, [".py", ".js"])
        self.assertEqual(csv_settings.projects_allowed_extensions, [".py", ".ts", ".jsx"])

    def test_github_analyze_repo_url_computes_file_count(self) -> None:
        source_root = Path(tempfile.mkdtemp(prefix="repo_rover_url_source_"))
        workspace_copy: Path | None = None
        try:
            (source_root / "main.py").write_text("print('ok')\n", encoding="utf-8")
            (source_root / "README.md").write_text("# Demo\n", encoding="utf-8")
            (source_root / "src").mkdir(parents=True, exist_ok=True)
            (source_root / "src" / "util.js").write_text("export const x = 1;\n", encoding="utf-8")

            repo = Repo.init(source_root)
            repo.index.add(["main.py", "README.md", "src/util.js"])
            repo.index.commit("Initial commit")

            client = TestClient(app)
            response = client.post("/api/github/analyze", json={"github_url": source_root.as_uri()})

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["file_count"], 3)
            self.assertEqual(len(payload["file_structure"]), 3)

            workspace_copy = Path(payload["ingestion"]["workspace_path"])
        finally:
            shutil.rmtree(source_root, ignore_errors=True)
            if workspace_copy and workspace_copy.exists():
                shutil.rmtree(workspace_copy, ignore_errors=True)

    def test_explainability_traces_support_notebook_projects(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="repo_rover_notebook_trace_"))
        notebook = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": ["# Notebook title\n"],
                },
                {
                    "cell_type": "code",
                    "execution_count": 1,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "import math\n",
                        "\n",
                        "def square(x):\n",
                        "    return x * x\n",
                    ],
                },
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }

        try:
            (root / "analysis.ipynb").write_text(json.dumps(notebook), encoding="utf-8")

            client = TestClient(app)
            response = client.post(
                "/api/ai/explainability-traces",
                json={"local_path": str(root), "max_files": 200, "graph_type": "call"},
            )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["focus_file"], "analysis.ipynb")
            self.assertGreaterEqual(len(payload["findings"]), 1)
            self.assertGreaterEqual(len(payload["token_traces"]), 1)
            self.assertGreaterEqual(len(payload["ast_traces"]), 1)
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()