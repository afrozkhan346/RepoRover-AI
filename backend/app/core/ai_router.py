from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from openai import OpenAI

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    backend_dir = Path(__file__).resolve().parents[2]
    env_file = backend_dir / ".env"
    load_dotenv(env_file)


def _provider_name() -> str:
    # Prefer AI_PROVIDER; keep LLM_PROVIDER as compatibility fallback.
    raw = os.getenv("AI_PROVIDER") or os.getenv("LLM_PROVIDER") or "ollama"
    return raw.strip().lower()


def _providers() -> dict[str, dict[str, str]]:
    return {
        "groq": {
            "base_url": os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            "api_key": os.getenv("GROQ_API_KEY", ""),
            "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        },
        "deepseek": {
            "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
            "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        },
        "ollama": {
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            "api_key": os.getenv("OLLAMA_API_KEY", "ollama"),
            "model": os.getenv("OLLAMA_MODEL", "codellama"),
        },
        "openai": {
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        },
    }


class AIRouter:
    def __init__(self) -> None:
        provider = _provider_name()
        providers = _providers()
        config = providers.get(provider, providers["ollama"])

        self.provider = provider if provider in providers else "ollama"
        self.model = config["model"]
        self.client = OpenAI(
            base_url=config["base_url"],
            api_key=config["api_key"] or "ollama",
        )

    def explain_file(self, file_content: str, filename: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert code explainer."},
                {"role": "user", "content": f"Explain this file `{filename}` in detail:\n\n{file_content}"},
            ],
        )
        return _extract_text(response)

    def chat(self, messages: list[dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return _extract_text(response)


def _extract_text(response: Any) -> str:
    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, KeyError, TypeError):
        return ""
    if content is None:
        return ""
    return str(content)
