from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch
from urllib import error as urllib_error

from app.services import llm_service


class _FakeHTTPResponse:
    def __init__(self, payload: str):
        self._payload = payload.encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class OllamaRepoSummaryTestCase(unittest.TestCase):
    def test_generate_text_ollama_timeout_returns_none(self) -> None:
        with (
            patch.dict(
                os.environ,
                {
                    "LLM_PROVIDER": "ollama",
                    "OLLAMA_BASE_URL": "http://localhost:11434",
                    "OLLAMA_MODEL": "llama3.1",
                    "OLLAMA_TIMEOUT_SECONDS": "2",
                    "GEMINI_API_KEY": "",
                    "OPENAI_API_KEY": "",
                },
                clear=False,
            ),
            patch("app.services.llm_service.urllib_request.urlopen", side_effect=urllib_error.URLError("timeout")),
        ):
            result = llm_service.generate_text(
                system_prompt="You are concise.",
                user_prompt="Return only OK.",
                max_tokens=20,
            )
        self.assertIsNone(result)

    def test_generate_text_ollama_invalid_json_returns_none(self) -> None:
        with (
            patch.dict(
                os.environ,
                {
                    "LLM_PROVIDER": "ollama",
                    "OLLAMA_BASE_URL": "http://localhost:11434",
                    "OLLAMA_MODEL": "llama3.1",
                    "OLLAMA_TIMEOUT_SECONDS": "2",
                    "GEMINI_API_KEY": "",
                    "OPENAI_API_KEY": "",
                },
                clear=False,
            ),
            patch("app.services.llm_service.urllib_request.urlopen", return_value=_FakeHTTPResponse("not-json")),
        ):
            result = llm_service.generate_text(
                system_prompt="You are concise.",
                user_prompt="Return only OK.",
                max_tokens=20,
            )
        self.assertIsNone(result)

    def test_generate_text_ollama_valid_message_content(self) -> None:
        response_payload = json.dumps({"message": {"content": "Repo summary is ready."}})
        with (
            patch.dict(
                os.environ,
                {
                    "LLM_PROVIDER": "ollama",
                    "OLLAMA_BASE_URL": "http://localhost:11434",
                    "OLLAMA_MODEL": "llama3.1",
                    "OLLAMA_TIMEOUT_SECONDS": "2",
                    "GEMINI_API_KEY": "",
                    "OPENAI_API_KEY": "",
                },
                clear=False,
            ),
            patch("app.services.llm_service.urllib_request.urlopen", return_value=_FakeHTTPResponse(response_payload)),
        ):
            result = llm_service.generate_text(
                system_prompt="You are concise.",
                user_prompt="Return only OK.",
                max_tokens=20,
            )
        self.assertEqual(result, "Repo summary is ready.")

    def test_generate_repo_summaries_returns_none_for_malformed_output(self) -> None:
        with patch("app.services.llm_service.generate_text", return_value="this is not json"):
            result = llm_service.generate_repo_summaries(
                repo_name="demo",
                total_files=10,
                analyzable_files=8,
                total_lines=120,
                language_breakdown={"Python": 6, "TypeScript": 2},
                dependency_edges=14,
                call_edges=25,
                key_modules=["backend/app/main.py"],
                key_dependencies=["fastapi"],
                flow_path=["main", "handler"],
            )
        self.assertIsNone(result)

    def test_generate_repo_summaries_returns_sections_for_valid_json(self) -> None:
        llm_output = json.dumps(
            {
                "project_summary": "This repository is a mixed backend and frontend application.",
                "architecture_summary": "The architecture is organized around API routes, services, and graph analysis modules.",
                "execution_flow_summary": "Execution starts in the API app bootstrap and continues through service-layer orchestration.",
            }
        )
        with patch("app.services.llm_service.generate_text", return_value=llm_output):
            result = llm_service.generate_repo_summaries(
                repo_name="demo",
                total_files=10,
                analyzable_files=8,
                total_lines=120,
                language_breakdown={"Python": 6, "TypeScript": 2},
                dependency_edges=14,
                call_edges=25,
                key_modules=["backend/app/main.py"],
                key_dependencies=["fastapi"],
                flow_path=["main", "handler"],
            )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertIn("project_summary", result)
        self.assertIn("architecture_summary", result)
        self.assertIn("execution_flow_summary", result)


if __name__ == "__main__":
    unittest.main()