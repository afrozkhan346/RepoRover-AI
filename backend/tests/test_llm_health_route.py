from __future__ import annotations

import os
import unittest
from unittest.mock import patch
from urllib import error as urllib_error

from fastapi.testclient import TestClient

from app.main import app


class _FakeHTTPResponse:
    def __init__(self, payload: str = "{}", status: int = 200):
        self._payload = payload.encode("utf-8")
        self.status = status

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class LLMHealthRouteTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_llm_health_reports_ollama_reachable(self) -> None:
        with (
            patch.dict(
                os.environ,
                {
                    "LLM_PROVIDER": "ollama",
                    "OLLAMA_BASE_URL": "http://localhost:11434",
                    "OLLAMA_MODEL": "llama3.1",
                    "OLLAMA_TIMEOUT_SECONDS": "3",
                    "GEMINI_API_KEY": "",
                    "OPENAI_API_KEY": "",
                },
                clear=False,
            ),
            patch("app.services.llm_service.urllib_request.urlopen", return_value=_FakeHTTPResponse(status=200)),
        ):
            response = self.client.get("/api/health/llm")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["provider"], "ollama")
        self.assertTrue(payload["ollama"]["reachable"])
        self.assertIsNone(payload["ollama"]["error"])

    def test_llm_health_reports_ollama_unreachable(self) -> None:
        with (
            patch.dict(
                os.environ,
                {
                    "LLM_PROVIDER": "ollama",
                    "OLLAMA_BASE_URL": "http://localhost:11434",
                    "OLLAMA_MODEL": "llama3.1",
                    "OLLAMA_TIMEOUT_SECONDS": "3",
                },
                clear=False,
            ),
            patch("app.services.llm_service.urllib_request.urlopen", side_effect=urllib_error.URLError("refused")),
        ):
            response = self.client.get("/api/health/llm")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["provider"], "ollama")
        self.assertFalse(payload["ollama"]["reachable"])
        self.assertTrue(isinstance(payload["ollama"]["error"], str) and payload["ollama"]["error"])


if __name__ == "__main__":
    unittest.main()
