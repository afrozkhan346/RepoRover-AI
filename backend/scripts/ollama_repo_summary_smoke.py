from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from app.services.project_summary_service import summarize_project


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a local Ollama repo summary smoke check.")
    parser.add_argument("repo_path", help="Path to a local repository directory")
    parser.add_argument("--model", default="llama3.1", help="Ollama model name (default: llama3.1)")
    parser.add_argument("--base-url", default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--max-files", type=int, default=400, help="Max files to scan")
    parser.add_argument("--timeout", type=int, default=120, help="Ollama timeout seconds")
    args = parser.parse_args()

    repo = Path(args.repo_path).expanduser().resolve()
    if not repo.exists() or not repo.is_dir():
        raise SystemExit(f"Invalid repository path: {repo}")

    os.environ["LLM_PROVIDER"] = "ollama"
    os.environ["OLLAMA_MODEL"] = args.model
    os.environ["OLLAMA_BASE_URL"] = args.base_url
    os.environ["OLLAMA_TIMEOUT_SECONDS"] = str(max(args.timeout, 1))

    response = summarize_project(str(repo), max_files=max(args.max_files, 10))
    payload = response.model_dump()

    print("=== Repo Summary (Ollama) ===")
    print(payload["project_summary"])
    print("\n=== Architecture Summary ===")
    print(payload["architecture_summary"])
    print("\n=== Execution Flow Summary ===")
    print(payload["execution_flow_summary"])
    print("\n=== Metrics ===")
    print(json.dumps(payload["metrics"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())