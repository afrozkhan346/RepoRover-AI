import json
import time
import hashlib
import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

from . import llm_client
from . import retrieval

# Create logs directory
LOG_DIR = Path("data/explain_logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# --- Prompt Template ---
CODE_EXPLAIN_PROMPT_TEMPLATE = """
SYSTEM:
You are RepoRoverExplainer, a concise code explainer for learners. Use only the provided contexts (EXCERPTs) to answer. Do not invent facts or filenames. If info is missing, say so.

INPUT:
- repo_id: {repo_id}
- target: {object_name} (file path: {file_path})
- CONTEXTS: (list below, each has CONTEXT_ID, FILE, EXCERPT)

TASK:
Using ONLY the CONTEXTS below, produce EXACTLY one JSON object (no extra text) matching this schema:
{{
  "summary": "string (one-sentence summary, <=140 chars)",
  "key_points": [
      "string (concise point 1, <=120 chars)",
      "string (concise point 2, <=120 chars)",
      "string (concise point 3, <=120 chars)"
   ],
  "unit_test": {{
      "title": "string (Descriptive test name)",
      "code": "string (Single, runnable assert or pytest snippet)",
      "language": "python"
   }},
  "example": "string (one-line example to run or use, or 'No simple example applicable.')",
  "sources": ["CONTEXT_ID", "..."],
  "warnings": []
}}

CONSTRAINTS:
- Use only information present in the CONTEXTS. If insufficient info, set summary to "Insufficient context to summarize {object_name}." and add a warning.
- Base key points, test, and example strictly on provided CONTEXTS.
- At least one CONTEXT_ID must be listed in "sources".
- Return valid JSON only, starting with `{{` and ending with `}}`.

CONTEXTS:
---BEGIN
{context_str}
---END

Return only the JSON object.
"""

def _call_llm_json(prompt: str, max_tokens: int = 700, temperature: float = 0.1) -> Dict:
    """Calls the LLM, attempts to parse JSON, retries once on parse error."""
    MAX_JSON_RETRIES = 1
    last_error = None
    final_raw_response = ""

    for attempt in range(MAX_JSON_RETRIES + 1):
        print(f"📤 Calling LLM for explanation (Attempt {attempt + 1})...")
        raw_response = llm_client.get_gemini_response(prompt, temperature=temperature)
        final_raw_response = raw_response

        try:
            if not raw_response or raw_response.startswith("Error:"):
                raise ValueError(f"LLM client error: {raw_response}")

            cleaned_response = raw_response.strip()
            if cleaned_response.startswith("```json"): 
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            if not cleaned_response.startswith("{") or not cleaned_response.endswith("}"):
                raise ValueError("Response is not a valid JSON object")

            return json.loads(cleaned_response)

        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"❌ Failed to parse JSON (Attempt {attempt + 1}): {e}")
            if attempt < MAX_JSON_RETRIES:
                print("⏳ Retrying with stricter JSON instruction...")
                prompt += "\nIMPORTANT: Return ONLY valid JSON."
                time.sleep(1)
            else:
                raise ValueError(f"Failed to get valid JSON. Error: {last_error}") from last_error

    raise Exception("Exited LLM call loop unexpectedly.")

def build_explain_prompt(repo_id: str, file_path: str, object_name: str, contexts: List[Dict]) -> Tuple[str, List[str]]:
    """Builds the prompt string for the explanation LLM call."""
    contexts_text = ""
    MAX_CONTEXT_LENGTH = 8000
    included_context_ids = []

    for ctx in contexts:
        context_id = ctx.get('id', 'N/A')
        excerpt = ctx.get('excerpt', ctx.get('content', '')[:400])
        current_part = f"""CONTEXT_ID: {context_id}
FILE: {ctx['file_path']}
EXCERPT:
{excerpt}
---END
"""
        if len(contexts_text) + len(current_part) < MAX_CONTEXT_LENGTH:
            contexts_text += current_part + "\n"
            included_context_ids.append(context_id)
        else:
            break

    prompt = CODE_EXPLAIN_PROMPT_TEMPLATE.format(
        repo_id=repo_id,
        object_name=object_name,
        file_path=file_path,
        context_str=contexts_text.strip()
    )
    return prompt, included_context_ids

def explain_target(repo_id: str, file_path: str, object_name: str | None, 
                  all_contexts: List[Dict], top_k: int = 6) -> Tuple[Dict, List[Dict]]:
    """
    Retrieves contexts and generates a structured explanation.
    Returns the explanation data and the full context objects used.
    """
    target_object = object_name or "file"
    explain_id_base = f"{repo_id}:{file_path}:{target_object}"

    # Filter and retrieve contexts
    file_contexts = [ctx for ctx in all_contexts if ctx['file_path'] == file_path]
    if not file_contexts:
        return {
            "explain_id": f"{explain_id_base}:error",
            "summary": "Error: No context found for this file.",
            "warnings": ["No context found"],
            "key_points": [],
            "unit_test": {"title": "N/A", "code": "", "language": "python"},
            "example": "",
            "sources": [],
            "confidence": "low"
        }, []

    # Find relevant contexts
    query = f"explain {target_object} in {file_path}"
    print(f"🔍 Finding top {top_k} contexts for: '{query}'")
    contexts_to_use = retrieval.find_relevant_contexts(query, file_contexts, top_k=top_k)

    # Fallback to first contexts if needed
    if not contexts_to_use:
        print("⚠️ No specific contexts found, using first few contexts")
        contexts_to_use = sorted(
            file_contexts,
            key=lambda c: (c.get('priority', 99), c.get('start_line') or 0)
        )[:max(1, top_k//2)]

    if not contexts_to_use:
        return {
            "explain_id": f"{explain_id_base}:no_context",
            "summary": "Insufficient context to explain this code.",
            "warnings": ["No relevant context found"],
            "key_points": [],
            "unit_test": {"title": "N/A", "code": "", "language": "python"},
            "example": "",
            "sources": [],
            "confidence": "low"
        }, []

    try:
        # Generate explanation
        prompt, context_ids_used = build_explain_prompt(
            repo_id, file_path, target_object, contexts_to_use
        )
        llm_data = _call_llm_json(prompt)

        # Validate sources and set confidence
        validation_warnings = []
        llm_sources = llm_data.get("sources", [])
        valid_sources = [src for src in llm_sources if src in context_ids_used]
        
        if not valid_sources:
            validation_warnings.append("No valid sources cited")
        
        confidence = "low"
        if len(valid_sources) >= 3:
            confidence = "high"
        elif len(valid_sources) == 2:
            confidence = "medium"

        # Build final explanation
        explanation = {
            "explain_id": f"{explain_id_base}:{context_ids_used[0] if context_ids_used else 'NA'}",
            "repo_id": repo_id,
            "file_path": file_path,
            "object": target_object,
            "summary": llm_data["summary"],
            "key_points": llm_data["key_points"],
            "unit_test": llm_data["unit_test"],
            "example": llm_data["example"],
            "sources": valid_sources,
            "confidence": confidence,
            "warnings": validation_warnings + llm_data.get("warnings", [])
        }

        # Get full context objects for cited sources
        sources_full = [ctx for ctx in contexts_to_use if ctx.get('id') in valid_sources]

        # Log the explanation
        log_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "repo_id": repo_id,
            "file_path": file_path,
            "object": target_object,
            "context_ids_used": context_ids_used,
            "explanation": explanation
        }
        
        log_file = LOG_DIR / f"explain_{repo_id.replace('/', '_')}_{datetime.datetime.now():%Y%m%d_%H%M%S}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        return explanation, sources_full

    except Exception as e:
        print(f"❌ Error generating explanation: {e}")
        return {
            "explain_id": f"{explain_id_base}:error",
            "summary": f"Error generating explanation: {str(e)}",
            "warnings": [str(e)],
            "key_points": [],
            "unit_test": {"title": "N/A", "code": "", "language": "python"},
            "example": "",
            "sources": [],
            "confidence": "low"
        }, contexts_to_use