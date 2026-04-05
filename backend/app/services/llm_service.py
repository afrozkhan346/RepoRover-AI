from __future__ import annotations

import json
import os
from typing import Any

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()


def _provider() -> str:
    return os.getenv("LLM_PROVIDER", "gemini").strip().lower()


def _get_openai_client() -> Any | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except Exception:
        return None

    base_url = os.getenv("OPENAI_BASE_URL")
    try:
        if base_url:
            return OpenAI(api_key=api_key, base_url=base_url)
        return OpenAI(api_key=api_key)
    except Exception:
        return None


def _generate_text_gemini(*, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> str | None:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None

    prompt = f"System:\n{system_prompt}\n\nUser:\n{user_prompt}"

    try:
        from google import genai

        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )
        text = getattr(response, "text", None)
        if text and str(text).strip():
            return str(text).strip()
    except Exception:
        return None


def _generate_text_openai(
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    model: str | None = None,
) -> str | None:
    client = _get_openai_client()
    if client is None:
        return None

    model_name = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    try:
        response = client.chat.completions.create(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception:
        return None

    try:
        content = response.choices[0].message.content
    except Exception:
        return None

    if not content:
        return None
    return str(content).strip()


def generate_text(*, system_prompt: str, user_prompt: str, temperature: float = 0.3, max_tokens: int = 700) -> str | None:
    provider = _provider()

    if provider == "gemini":
        return _generate_text_gemini(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        ) or _generate_text_openai(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider == "openai":
        return _generate_text_openai(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        ) or _generate_text_gemini(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    return _generate_text_gemini(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    ) or _generate_text_openai(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def generate_llm_response(prompt: str) -> str | None:
    return generate_text(
        system_prompt="You are a software expert.",
        user_prompt=prompt,
        temperature=0.5,
        max_tokens=700,
    )


def llm_project_summary(entry: str | None, core_funcs: list[str], project_type: str) -> str | None:
    prompt = (
        "Explain this software project:\n\n"
        f"Type: {project_type}\n"
        f"Entry Point: {entry or 'an inferred entry module'}\n"
        f"Core Functions: {core_funcs}\n\n"
        "Give a clear and structured explanation of what this project does."
    )
    return generate_llm_response(prompt)


def llm_explanations(entry: str | None, core_funcs: list[str], project_type: str) -> dict[str, str] | None:
    prompt = (
        "Explain this project in 3 levels and return JSON with keys beginner, intermediate, advanced.\n\n"
        f"Project Type: {project_type}\n"
        f"Entry: {entry or 'an inferred entry module'}\n"
        f"Functions: {core_funcs}\n\n"
        "1. Beginner (simple explanation)\n"
        "2. Intermediate (technical explanation)\n"
        "3. Advanced (architecture explanation)\n"
    )

    raw = generate_llm_response(prompt)
    if not raw:
        return None

    payload = _extract_json_block(raw)
    if not payload:
        return None

    beginner = payload.get("beginner")
    intermediate = payload.get("intermediate")
    advanced = payload.get("advanced")
    if not all(isinstance(item, str) and item.strip() for item in (beginner, intermediate, advanced)):
        return None

    return {
        "beginner": beginner.strip(),
        "intermediate": intermediate.strip(),
        "advanced": advanced.strip(),
    }


def _extract_json_block(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def generate_project_summary(entry: str | None, core_funcs: list[str], project_type: str) -> str | None:
    entry_text = entry or "an inferred entry module"
    core_text = ", ".join(core_funcs[:6]) if core_funcs else "no dominant functions detected"

    system_prompt = (
        "You are a software architecture educator. "
        "Write concise, human-like project summaries for developers and learners."
    )
    user_prompt = (
        "Generate a clear project summary in 4-6 sentences.\n"
        f"Project type: {project_type}\n"
        f"Entry point: {entry_text}\n"
        f"Core functions: {core_text}\n"
        "Mention purpose, execution flow, and modular structure."
    )

    return generate_text(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.35, max_tokens=350)


def generate_learning_explanations(
    *,
    summary: str,
    entry: str | None,
    core_funcs: list[str],
    project_type: str,
) -> dict[str, str] | None:
    entry_text = entry or "an inferred entry module"
    core_text = ", ".join(core_funcs[:8]) if core_funcs else "no dominant functions detected"

    system_prompt = (
        "You are an expert programming teacher. "
        "Return JSON only with keys beginner, intermediate, advanced."
    )
    user_prompt = (
        "Create three learning-level explanations for a project.\n"
        f"Project type: {project_type}\n"
        f"Entry point: {entry_text}\n"
        f"Core functions: {core_text}\n"
        f"Current summary: {summary}\n"
        "Requirements:\n"
        "- beginner: simple, non-jargon\n"
        "- intermediate: technical flow\n"
        "- advanced: architecture and design reasoning\n"
        "Output JSON only."
    )

    raw = generate_text(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.4, max_tokens=750)
    if not raw:
        return None

    payload = _extract_json_block(raw)
    if not payload:
        return None

    beginner = payload.get("beginner")
    intermediate = payload.get("intermediate")
    advanced = payload.get("advanced")
    if not all(isinstance(item, str) and item.strip() for item in (beginner, intermediate, advanced)):
        return None

    return {
        "beginner": beginner.strip(),
        "intermediate": intermediate.strip(),
        "advanced": advanced.strip(),
    }
