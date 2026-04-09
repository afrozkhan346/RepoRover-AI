from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services import ast_parser


PY_SOURCE = """
import os

class Greeter:
    def hello(self, name):
        print(name)
        return name
"""


JS_SOURCE = """
import fs from "fs";
function helper(x) {
  return console.log(x);
}
helper(1);
"""


class AstParserFallbackTestCase(unittest.TestCase):
    def _make_workspace(self, name: str) -> Path:
        root = Path(__file__).resolve().parent.parent / ".tmp_tests" / name
        shutil.rmtree(root, ignore_errors=True)
        root.mkdir(parents=True, exist_ok=True)
        return root

    def test_project_code_report_uses_fallback_when_tree_sitter_unavailable(self) -> None:
        root = self._make_workspace("repo_rover_ast_fallback")
        try:
            (root / "app.py").write_text(PY_SOURCE, encoding="utf-8")
            (root / "app.js").write_text(JS_SOURCE, encoding="utf-8")

            original_preflight = ast_parser.preflight_tree_sitter_language

            def always_unavailable(language: str) -> tuple[bool, str | None]:
                return False, f"offline for {language}"

            ast_parser.preflight_tree_sitter_language = always_unavailable
            try:
                report = ast_parser.parse_project_code_report(str(root))
            finally:
                ast_parser.preflight_tree_sitter_language = original_preflight

            self.assertEqual(report["files_scanned"], 2)
            self.assertEqual(report["files_parsed"], 2)
            self.assertEqual(report["files_failed"], 0)
            self.assertEqual(len(report["errors"]), 0)

            files = {item["file"]: item for item in report["files"]}
            self.assertIn("app.py", files)
            self.assertIn("app.js", files)
            self.assertEqual(files["app.py"]["data"]["parse_mode"], "python_ast")
            self.assertEqual(files["app.js"]["data"]["parse_mode"], "fallback")
            self.assertGreaterEqual(len(files["app.py"]["data"]["functions"]), 1)
            self.assertGreaterEqual(len(files["app.js"]["data"]["normalized_ast"]["calls"]), 1)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_report_surfaces_parse_error_details(self) -> None:
        root = self._make_workspace("repo_rover_ast_error")
        try:
            (root / "ok.py").write_text("def ok():\n    return 1\n", encoding="utf-8")

            original_parse_source_file = ast_parser._parse_source_file

            def fail_js_only(file_path: Path, *, parser_available=None):  # type: ignore[no-untyped-def]
                if file_path.suffix.lower() == ".js":
                    raise ValueError("forced js parse failure")
                return original_parse_source_file(file_path, parser_available=parser_available)

            (root / "bad.js").write_text("function boom() { return 1; }\n", encoding="utf-8")
            ast_parser._parse_source_file = fail_js_only
            try:
                report = ast_parser.parse_project_code_report(str(root))
            finally:
                ast_parser._parse_source_file = original_parse_source_file

            self.assertEqual(report["files_scanned"], 2)
            self.assertEqual(report["files_parsed"], 1)
            self.assertEqual(report["files_failed"], 1)
            self.assertEqual(len(report["errors"]), 1)

            error = report["errors"][0]
            self.assertEqual(error["file"], "bad.js")
            self.assertEqual(error["error_type"], "parse_error")
            self.assertIn("forced js parse failure", error["error"])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_mixed_language_partial_failure_keeps_successful_files(self) -> None:
        root = self._make_workspace("repo_rover_ast_mixed_partial")
        try:
            (root / "ok.py").write_text("def ok():\n    return 1\n", encoding="utf-8")
            (root / "bad.ts").write_text("function bad(): number { return 1; }\n", encoding="utf-8")
            (root / "ok.js").write_text("function alive(){ return 1; }\nalive();\n", encoding="utf-8")

            original_parse_source_file = ast_parser._parse_source_file

            def fail_typescript_only(file_path: Path, *, parser_available=None):  # type: ignore[no-untyped-def]
                if file_path.suffix.lower() == ".ts":
                    raise ValueError("forced ts parse failure")
                return original_parse_source_file(file_path, parser_available=parser_available)

            ast_parser._parse_source_file = fail_typescript_only
            try:
                report = ast_parser.parse_project_code_report(str(root))
            finally:
                ast_parser._parse_source_file = original_parse_source_file

            self.assertEqual(report["files_scanned"], 3)
            self.assertEqual(report["files_parsed"], 2)
            self.assertEqual(report["files_failed"], 1)
            self.assertEqual(len(report["errors"]), 1)

            files = {item["file"]: item for item in report["files"]}
            self.assertIn("ok.py", files)
            self.assertIn("ok.js", files)
            self.assertNotIn("bad.ts", files)

            self.assertEqual(files["ok.py"]["data"]["parse_mode"], "python_ast")
            self.assertIn(files["ok.js"]["data"]["parse_mode"], {"tree_sitter", "fallback"})
            self.assertGreaterEqual(len(files["ok.py"]["data"]["functions"]), 1)
            self.assertGreaterEqual(len(files["ok.js"]["data"]["normalized_ast"]["calls"]), 1)

            error = report["errors"][0]
            self.assertEqual(error["file"], "bad.ts")
            self.assertEqual(error["error_type"], "parse_error")
            self.assertIn("forced ts parse failure", error["error"])
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
