from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    # Load .env from backend directory
    backend_dir = Path(__file__).resolve().parent.parent.parent
    env_file = backend_dir / ".env"
    load_dotenv(env_file)


def _provider() -> str:
    # Prefer AI_PROVIDER and keep LLM_PROVIDER as compatibility fallback.
    return (os.getenv("AI_PROVIDER") or os.getenv("LLM_PROVIDER") or "groq").strip().lower()


def _ollama_runtime_config() -> tuple[str, str, int]:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip().rstrip("/")
    model_name = os.getenv("OLLAMA_MODEL", "llama3.1").strip()
    timeout_raw = os.getenv("OLLAMA_TIMEOUT_SECONDS", "120").strip()

    try:
        timeout_seconds = max(int(timeout_raw), 1)
    except (TypeError, ValueError):
        timeout_seconds = 120

    return base_url, model_name, timeout_seconds


def _get_openai_client() -> Any | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        return None

    base_url = os.getenv("OPENAI_BASE_URL")
    try:
        if base_url:
            return OpenAI(api_key=api_key, base_url=base_url)
        return OpenAI(api_key=api_key)
    except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
        return None


def _get_groq_client() -> Any | None:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        return None

    base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()
    try:
        return OpenAI(api_key=api_key, base_url=base_url)
    except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
        return None


def _generate_text_gemini(*, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> str | None:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None

    prompt = f"System:\n{system_prompt}\n\nUser:\n{user_prompt}"

    try:
        from google import genai
    except ImportError:
        return None

    try:
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
    except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
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
    except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
        return None

    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, KeyError, TypeError):
        return None

    if not content:
        return None
    return str(content).strip()


def _generate_text_groq(
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    model: str | None = None,
) -> str | None:
    client = _get_groq_client()
    if client is None:
        return None

    model_name = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

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
    except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
        return None

    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, KeyError, TypeError):
        return None

    if not content:
        return None
    return str(content).strip()


def _generate_text_ollama(*, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> str | None:
    base_url, model_name, timeout_seconds = _ollama_runtime_config()

    if not base_url or not model_name:
        return None

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib_request.Request(
        f"{base_url}/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib_request.urlopen(req, timeout=timeout_seconds) as response:
            response_text = response.read().decode("utf-8", errors="ignore")
    except (urllib_error.URLError, urllib_error.HTTPError, TimeoutError, OSError):
        return None

    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError:
        return None

    message = parsed.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

    direct_text = parsed.get("response")
    if isinstance(direct_text, str) and direct_text.strip():
        return direct_text.strip()

    return None


def _is_ollama_reachable() -> tuple[bool, str | None]:
    base_url, _, timeout_seconds = _ollama_runtime_config()
    if not base_url:
        return False, "OLLAMA_BASE_URL is empty"

    req = urllib_request.Request(f"{base_url}/api/tags", method="GET")
    try:
        with urllib_request.urlopen(req, timeout=timeout_seconds) as response:
            status = getattr(response, "status", 200)
            if status >= 400:
                return False, f"HTTP {status}"
            return True, None
    except urllib_error.HTTPError as error:
        return False, f"HTTP {error.code}"
    except (urllib_error.URLError, TimeoutError, OSError) as error:
        return False, str(error)


def get_llm_runtime_status() -> dict[str, Any]:
    provider = _provider()
    status: dict[str, Any] = {
        "provider": provider,
        "fallback_order": ["groq", "ollama", "openai", "gemini"],
        "groq": {
            "configured": bool(os.getenv("GROQ_API_KEY", "").strip()),
            "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            "base_url": os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        },
        "ollama": {
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "model": os.getenv("OLLAMA_MODEL", "llama3.1"),
            "timeout_seconds": int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120") or "120"),
        },
        "gemini": {
            "configured": bool(os.getenv("GEMINI_API_KEY", "").strip()),
            "model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        },
        "openai": {
            "configured": bool(os.getenv("OPENAI_API_KEY", "").strip()),
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "base_url": os.getenv("OPENAI_BASE_URL", ""),
        },
    }

    reachable, error_message = _is_ollama_reachable()
    status["ollama"]["reachable"] = reachable
    status["ollama"]["error"] = error_message
    return status


def generate_text(*, system_prompt: str, user_prompt: str, temperature: float = 0.3, max_tokens: int = 700) -> str | None:
    provider = _provider()

    if provider == "groq":
        return _generate_text_groq(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider == "ollama":
        return _generate_text_ollama(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider == "gemini":
        return _generate_text_gemini(
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
        )

    return _generate_text_groq(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    ) or _generate_text_gemini(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    ) or _generate_text_ollama(
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


def generate_repo_summaries(
    *,
    repo_name: str,
    purpose_hint: str | None = None,
    readme_info_hint: str | None = None,
    total_files: int,
    analyzable_files: int,
    total_lines: int,
    language_breakdown: dict[str, int],
    dependency_edges: int,
    call_edges: int,
    key_modules: list[str],
    key_dependencies: list[str],
    flow_path: list[str],
) -> dict[str, str] | None:
    """Generate structured repo summaries from aggregated metadata.

    Returns JSON-like text parsed into:
    - project_summary
    - architecture_summary
    - execution_flow_summary
    """

    system_prompt = (
        "You are a senior software architect producing repository summaries for engineers. "
        "Be factual, concise, and avoid speculation."
    )

    user_prompt = (
        "Produce JSON only with keys: project_summary, architecture_summary, execution_flow_summary.\n"
        "Constraints:\n"
        "- Each field must be 2-4 sentences.\n"
        "- project_summary must be exactly 3 sentences using this order:\n"
        "  1) This project is ... (what it is).\n"
        "  2) It helps ... (who it serves / use-case).\n"
        "  3) Technically ... (high-level implementation with metrics only as support).\n"
        "- Do not start project_summary with file counts or raw metrics.\n"
        "- architecture_summary should focus on structure, modules, and dependencies.\n"
        "- execution_flow_summary should describe runtime behavior or user flow.\n"
        "- Mention concrete metrics where available as supporting detail.\n"
        "- Do not include markdown, code fences, or extra keys.\n\n"
        f"Repository: {repo_name}\n"
        f"Purpose hint from README (if available): {purpose_hint or 'not available'}\n"
        f"Additional README info (if available): {readme_info_hint or 'not available'}\n"
        f"Total files: {total_files}\n"
        f"Analyzable files: {analyzable_files}\n"
        f"Total lines: {total_lines}\n"
        f"Language breakdown: {language_breakdown}\n"
        f"Dependency edges: {dependency_edges}\n"
        f"Call edges: {call_edges}\n"
        f"Key modules: {key_modules[:8]}\n"
        f"Key dependencies: {key_dependencies[:8]}\n"
        f"Execution flow preview: {flow_path[:12]}\n"
    )

    raw = generate_text(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.2, max_tokens=850)
    if not raw:
        return None

    payload = _extract_json_block(raw)
    if not payload:
        return None

    project_summary = payload.get("project_summary")
    architecture_summary = payload.get("architecture_summary")
    execution_flow_summary = payload.get("execution_flow_summary")

    if not all(
        isinstance(item, str) and item.strip()
        for item in (project_summary, architecture_summary, execution_flow_summary)
    ):
        return None

    return {
        "project_summary": project_summary.strip(),
        "architecture_summary": architecture_summary.strip(),
        "execution_flow_summary": execution_flow_summary.strip(),
    }


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
