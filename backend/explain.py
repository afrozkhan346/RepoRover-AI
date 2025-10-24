import json
import time
import hashlib
import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple
import streamlit as st  # Add streamlit import

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
    """
    Calls the LLM, attempts to parse JSON, retries once on parse error.
    Raises ValueError with detailed message on failure.
    """
    MAX_JSON_RETRIES = 1
    last_error = None
    final_raw_response = ""

    for attempt in range(MAX_JSON_RETRIES + 1):
        print(f"📤 Calling LLM for explanation (Attempt {attempt + 1})...")
        raw_response = llm_client.get_gemini_response(prompt, temperature=temperature)
        final_raw_response = raw_response

        try:
            if not raw_response:
                raise ValueError("Empty response from LLM")
            if raw_response.startswith("Error:"):
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
                prompt += "\nIMPORTANT: Return ONLY valid JSON starting with { and ending with }."
                time.sleep(1)
            else:
                raise ValueError(f"Failed to get valid JSON after {MAX_JSON_RETRIES + 1} attempts. Error: {last_error}")

    raise Exception("Exited LLM call loop unexpectedly.")  # Should never reach here

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

@st.cache_data(show_spinner=False)
def explain_target(repo_id: str, file_path: str, object_name: str | None, 
                  all_contexts: List[Dict], top_k: int = 6) -> Tuple[Dict, List[Dict]]:
    """
    Retrieves contexts and generates a structured explanation.
    Results are cached based on input arguments.
    """
    target_object = object_name or "file"
    explain_id_base = f"{repo_id}:{file_path}:{target_object}"

    # Enhanced error response helper
    def create_error_response(error_type: str, message: str, contexts_to_return: List[Dict] = None) -> Tuple[Dict, List[Dict]]:
        return {
            "explain_id": f"{explain_id_base}:{error_type}",
            "repo_id": repo_id,
            "file_path": file_path,
            "object": target_object,
            "summary": "Explanation temporarily unavailable.",
            "key_points": [],
            "unit_test": {"title": "N/A", "code": "", "language": "python"},
            "example": "No example available due to error.",
            "sources": [],
            "confidence": "low",
            "warnings": [f"{error_type}: {message}"]
        }, contexts_to_return or []

    # Input validation
    if not all_contexts:
        return create_error_response("input_error", "No repository data available.")

    # File context filtering
    file_contexts = [ctx for ctx in all_contexts if ctx['file_path'] == file_path]
    if not file_contexts:
        return create_error_response("no_content", f"No processed content found for file: {file_path}")

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
        return create_error_response("no_context", "Could not find relevant context within the file.")

    # Initialize warnings list
    validation_warnings = []

    try:
        # Generate explanation
        prompt, context_ids_used = build_explain_prompt(
            repo_id, file_path, target_object, contexts_to_use
        )
        llm_data = _call_llm_json(prompt)

        # Validate sources and calculate confidence
        llm_sources = llm_data.get("sources", [])
        if not isinstance(llm_sources, list):
            validation_warnings.append("LLM 'sources' field is not a list")
            llm_sources = []

        # Validate cited sources
        valid_sources_cited_ids = []
        invalid_sources_cited = []
        for src_id in llm_sources:
            if src_id in context_ids_used:
                valid_sources_cited_ids.append(src_id)
            else:
                invalid_sources_cited.append(src_id)

        if invalid_sources_cited:
            validation_warnings.append(f"LLM cited invalid sources: {invalid_sources_cited}")
        if not valid_sources_cited_ids:
            validation_warnings.append("No valid sources cited from prompt context")

        # Map valid IDs back to full context objects
        valid_sources_full = [ctx for ctx in contexts_to_use if ctx.get('id') in valid_sources_cited_ids]

        # Calculate refined confidence
        confidence = "low"
        num_valid_sources = len(valid_sources_cited_ids)

        if num_valid_sources >= 3:
            # Check for mix of code and documentation
            has_code = any(ctx.get('language') in ['python', 'javascript', 'typescript'] 
                         for ctx in valid_sources_full)
            has_docs = any(ctx.get('language') == 'markdown' or 
                         'readme' in ctx.get('file_path', '').lower() 
                         for ctx in valid_sources_full)
            
            if has_code and has_docs:
                confidence = "high"
            elif has_code or has_docs:
                confidence = "medium"
            else:
                confidence = "medium"
        elif num_valid_sources == 2:
            confidence = "medium"

        if confidence == "low":
            validation_warnings.append("Confidence is low due to limited source material cited")

        # Build final explanation
        final_explanation = {
            "explain_id": f"{explain_id_base}:{context_ids_used[0] if context_ids_used else 'NA'}",
            "repo_id": repo_id,
            "file_path": file_path,
            "object": target_object,
            "summary": llm_data["summary"],
            "key_points": llm_data.get("key_points", []),
            "unit_test": llm_data.get("unit_test", {"title": "N/A", "code": "", "language": "python"}),
            "example": llm_data.get("example", ""),
            "sources": valid_sources_cited_ids,
            "confidence": confidence,
            "warnings": validation_warnings + llm_data.get("warnings", [])
        }

        # Log the explanation (outside cache)
        try:
            log_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "repo_id": repo_id,
                "file_path": file_path,
                "object": target_object,
                "context_ids_used": context_ids_used,
                "explanation": final_explanation
            }
            
            log_file = LOG_DIR / f"explain_{repo_id.replace('/', '_')}_{datetime.datetime.now():%Y%m%d_%H%M%S}.json"
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
        except Exception as log_e:
            print(f"Warning: Failed to save explanation log: {log_e}")

        return final_explanation, valid_sources_full

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