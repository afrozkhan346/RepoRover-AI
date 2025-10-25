import json
import time
import hashlib
import datetime # For logging timestamp
from pathlib import Path
from typing import List, Dict, Any, Tuple
import streamlit as st # For caching decorator
import re # For parsing retry delay

# Use relative imports within the backend package
from . import llm_client
from . import retrieval

# --- Setup Log Directory ---
# Define the log directory relative to this file
# (backend/explain.py -> backend/ -> RepoRover-AI/ -> data/explain_logs)
try:
    SCRIPT_DIR = Path(__file__).resolve().parent.parent
    LOG_DIR = SCRIPT_DIR / "data" / "explain_logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Explain logger initialized. Log directory set to: {LOG_DIR}")
except Exception as e:
    print(f"Warning: Could not create explain log directory at {LOG_DIR}. Error: {e}")
    LOG_DIR = None # Set to None to prevent write errors

# --- Prompt Template (from 6.4) ---
# Note: Use f-string compatible escaping {{ }} for JSON schema parts
CODE_EXPLAIN_PROMPT_TEMPLATE = """
SYSTEM:
You are RepoRoverExplainer, a concise code explainer for learners. Use only the provided contexts (EXCERPTs) to answer. Do not invent facts or filenames. If info is missing, say so.

INPUT:
- repo_id: {repo_id}
- target: {object_name} (file path: {file_path})
- CONTEXTS: (list below, each has CONTEXT_ID, FILE, EXCERPT)

TASK:
Using ONLY the CONTEXTS below, produce EXACTLY one JSON object (no extra text) matching this schema:
```json
{{
  "summary": "string (one-sentence summary, <=140 chars)",
  "key_points": [
      "string (concise point 1, <=120 chars)",
      "string (concise point 2, <=120 chars)",
      "string (concise point 3, <=120 chars)"
      // Exactly 3 points
   ],
  "unit_test": {{
      "title": "string (Descriptive test name)",
      "code": "string (Single, runnable assert or pytest snippet)",
      "language": "python" // Always python
   }},
  "example": "string (one-line example to run or use, or 'No simple example applicable.')",
  "sources": ["CONTEXT_ID", "..."], // List CONTEXT_IDs used
  "warnings": [] // Optional strings for missing info etc.
}}
```

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

# --- Helper to Call LLM and Parse JSON (with Retry) ---

def _call_llm_json(prompt: str, max_tokens: int = 700, temperature: float = 0.1) -> Dict:
    """
    Calls the LLM, attempts to parse JSON, retries once on parse error.
    Raises ValueError with detailed message on failure.
    """
    MAX_JSON_RETRIES = 1
    last_error = None
    final_raw_response = "" # Store last response for error reporting

    for attempt in range(MAX_JSON_RETRIES + 1):
        print(f"📤 Calling LLM for explanation (Attempt {attempt + 1})...")
        # Use the get_gemini_response which includes its own retry for API errors
        raw_response = llm_client.get_gemini_response(prompt, temperature=temperature)
        final_raw_response = raw_response

        try:
            # Check if llm_client returned an error message
            if raw_response is None or not raw_response.strip() or raw_response.startswith("Error:"):
                 # Propagate the error message from the client
                 raise ValueError(f"LLM client error: {raw_response}")

            # Clean up potential markdown fences and extra whitespace
            cleaned_response = raw_response.strip()
            if cleaned_response.startswith("```json"): cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"): cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            # Basic check for JSON object format
            if not cleaned_response.startswith("{") or not cleaned_response.endswith("}"):
                 raise ValueError("Response is not wrapped in {}")

            # Attempt to parse
            parsed_json = json.loads(cleaned_response)
            print("✅ LLM response parsed successfully.")
            return parsed_json # Success!

        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"❌ Failed to parse JSON (Attempt {attempt + 1}): {e}")
            if attempt < MAX_JSON_RETRIES:
                print("⏳ Retrying with stricter JSON instruction...")
                # Append stricter instruction for the retry
                prompt += "\n\nIMPORTANT REMINDER: Your response MUST be ONLY the valid JSON object requested, starting with '{' and ending with '}'. Do NOT include any other text, comments, or markdown formatting."
                time.sleep(1) # Short delay before retry
            else:
                # Raise final error after retries fail
                error_msg = f"Failed to get valid JSON explanation after {MAX_JSON_RETRIES + 1} attempts. Last error: {last_error}"
                print(f"❌ {error_msg}")
                # print(f"Raw response: {final_raw_response}") # Optionally print for debug
                raise ValueError(error_msg) from last_error

    # Should not be reached, but needed for safety
    raise Exception("Exited LLM call loop unexpectedly.")

# --- Helper to Build Prompt ---

def build_explain_prompt(repo_id: str, file_path: str, object_name: str, contexts: List[Dict]) -> Tuple[str, List[str]]:
    """Builds the prompt string for the explanation LLM call and returns used context IDs."""
    contexts_text = ""
    MAX_CONTEXT_LENGTH_EXPLAIN = 8000 # Keep context length reasonable
    included_context_ids = []

    print(f"Building explanation prompt for '{object_name}' using {len(contexts)} provided contexts...")
    for c in contexts:
        context_id = c.get('id', 'N/A')
        # Use excerpt, fallback to start of content if excerpt is missing/empty
        excerpt = c.get('excerpt') or (c.get('content', '')[:400].strip() + "...")
        if not excerpt.strip(): # Skip contexts with no usable text
            print(f"Skipping context {context_id} due to empty excerpt/content.")
            continue

        current_part = f"""CONTEXT_ID: {context_id}
FILE: {c['file_path']}
EXCERPT:
{excerpt}
---END
"""
        # Check length before adding
        if len(contexts_text) + len(current_part) < MAX_CONTEXT_LENGTH_EXPLAIN:
            contexts_text += current_part + "\n"
            included_context_ids.append(context_id)
        else:
            print(f"Context length limit reached. Included {len(included_context_ids)} contexts.")
            break # Stop adding context

    if not included_context_ids:
         print("Warning: No contexts could be included in the prompt due to length or empty content.")

    # Format the main template
    prompt = CODE_EXPLAIN_PROMPT_TEMPLATE.format(
        repo_id=repo_id,
        object_name=object_name,
        file_path=file_path,
        context_str=contexts_text.strip() # Ensure no leading/trailing whitespace
    )
    return prompt, included_context_ids # Return prompt and list of IDs actually used


# --- Helper Function for Logging ---
def log_error(error_data: Dict, contexts: List[Dict], error_message: str):
    """Saves error details to a log file."""
    if not LOG_DIR:
        print("Log directory not initialized. Skipping error log.")
        return
    try:
        log_content = {
            "timestamp": datetime.datetime.now().isoformat(),
            "error_details": error_data,
            "error_message": error_message,
            "contexts_provided_ids": [ctx.get('id') for ctx in contexts if ctx]
        }
        repo_id = error_data.get("repo_id", "unknown_repo")
        file_path = error_data.get("file_path", "unknown_file")
        target_object = error_data.get("object", "unknown_object")
        
        safe_filename = f"error_{repo_id.replace('/','_')}_{file_path.replace('/','_')}_{target_object}_{datetime.datetime.now():%Y%m%d_%H%M%S}.json"
        log_filepath = LOG_DIR / safe_filename
        with open(log_filepath, 'w', encoding='utf-8') as f:
            json.dump(log_content, f, indent=2, ensure_ascii=False)
        print(f"📝 Error log saved to {log_filepath}")
    except Exception as log_e:
        print(f"⚠️ Warning: Failed to save error log: {log_e}")


# --- Main Explanation Function (Cached) ---
@st.cache_data(show_spinner=False, ttl=3600) # Cache explanations for 1 hour
def explain_target(repo_id: str, file_path: str, object_name: str | None,
                   all_contexts: List[Dict], top_k: int = 8) -> Tuple[Dict, List[Dict]]:
    """
    Retrieves contexts, generates a structured explanation via LLM, validates,
    calculates confidence, and returns the explanation object and sources used.
    Results are cached based on input arguments.
    """
    target_object = object_name or "file" # Use "file" if object_name is None/empty
    explain_id_base = f"{repo_id.replace('/', '_')}:{file_path.replace('/', '_')}:{target_object}" # Make ID filesystem-safe

    # --- Helper for creating structured error responses ---
    def create_error_response(error_type: str, message: str, contexts_to_return: List[Dict] = None) -> Tuple[Dict, List[Dict]]:
        error_data = {
            "explain_id": f"{explain_id_base}:{error_type}",
            "repo_id": repo_id, "file_path": file_path, "object": target_object,
            "summary": f"Error: {message}",
            "key_points": [],
            "unit_test": {"title": "N/A", "code": "", "language": "python"},
            "example": "N/A", "sources": [], "confidence": "low",
            "warnings": [f"{error_type.upper()}: {message}"]
        }
        # Log the error occurrence
        log_error(error_data, contexts_to_return or [], f"{error_type}: {message}")
        return error_data, contexts_to_return or []

    # --- Input Validation ---
    if not all_contexts:
        return create_error_response("input_error", "No repository context data available.")

    # --- File Context Filtering ---
    file_contexts = [ctx for ctx in all_contexts if ctx['file_path'] == file_path]
    if not file_contexts:
        return create_error_response("no_content", f"No processed content found for file: {file_path}")

    # --- Find Relevant Contexts ---
    if object_name and object_name != "file":
        query = f"Explanation for {object_name} in {file_path}"
        print(f"🔍 Finding top {top_k} contexts for: '{query}'")
        contexts_to_use = retrieval.find_relevant_contexts(query, file_contexts, top_k=top_k)
    else:
        print(f"Selecting top contexts for explaining file: {file_path}")
        contexts_to_use = sorted(
            file_contexts,
            key=lambda c: (c.get('priority', 99), c.get('start_line') or 0, c.get('chunk_index', 0))
        )[:top_k]

    if not contexts_to_use:
        print("⚠️ No specific contexts found via retrieval, using first few contexts from file as fallback.")
        contexts_to_use = sorted(
            file_contexts,
            key=lambda c: (c.get('priority', 99), c.get('start_line') or 0, c.get('chunk_index', 0))
        )[:max(1, top_k // 2)]

    if not contexts_to_use:
        return create_error_response("no_context", "Could not find any relevant context within the file.")

    # --- Build Prompt & Call LLM ---
    prompt, context_ids_used_in_prompt = build_explain_prompt(
        repo_id, file_path, target_object, contexts_to_use
    )
    llm_data = {}
    validation_warnings = []

    try:
        llm_data = _call_llm_json(prompt) # Uses temperature=0.1 by default

        # --- Validate Response Structure ---
        required_keys = ["summary", "key_points", "unit_test", "example", "sources"]
        if not all(key in llm_data for key in required_keys):
             missing = [key for key in required_keys if key not in llm_data]
             validation_warnings.append(f"LLM response missing required keys: {missing}")
             # Provide defaults for missing keys to prevent downstream errors
             if "key_points" not in llm_data: llm_data["key_points"] = []
             if "unit_test" not in llm_data: llm_data["unit_test"] = {"title":"N/A","code":"","language":"python"}
             if "example" not in llm_data: llm_data["example"] = "N/A"
             if "sources" not in llm_data: llm_data["sources"] = []

        key_points = llm_data.get("key_points", [])
        if not isinstance(key_points, list):
             validation_warnings.append(f"'key_points' should be a list.")
             if isinstance(key_points, str): llm_data["key_points"] = [key_points] # Attempt to fix

        unit_test = llm_data.get("unit_test", {})
        if not isinstance(unit_test, dict) or not all(k in unit_test for k in ["title", "code", "language"]):
             validation_warnings.append("'unit_test' object structure is invalid.")
             llm_data["unit_test"] = {"title":"N/A","code":"","language":"python"} # Reset

        llm_sources = llm_data.get("sources", [])
        if not isinstance(llm_sources, list):
             validation_warnings.append("LLM 'sources' field is not a list.")
             llm_sources = [] # Reset

        valid_sources_cited_ids = []
        invalid_sources_cited = []
        for src_id in llm_sources:
            if src_id in context_ids_used_in_prompt:
                 valid_sources_cited_ids.append(src_id)
            else:
                 invalid_sources_cited.append(src_id)

        if invalid_sources_cited:
             validation_warnings.append(f"LLM cited sources not in prompt: {invalid_sources_cited}")

        # --- Refined Confidence Calculation ---
        confidence = "low"
        num_valid_sources = len(valid_sources_cited_ids)
        valid_sources_full = [ctx for ctx in contexts_to_use if ctx.get('id') in valid_sources_cited_ids]

        if num_valid_sources >= 3:
            has_code = any(ctx.get('language') in ['python', 'javascript', 'typescript'] for ctx in valid_sources_full)
            has_docs = any(ctx.get('language') == 'markdown' or 'readme' in ctx.get('file_path','').lower() for ctx in valid_sources_full)
            if has_code and has_docs: confidence = "high"
            elif has_code or has_docs: confidence = "medium"
            else: confidence = "medium"
        elif num_valid_sources == 2: confidence = "medium"

        if confidence == "low":
            validation_warnings.append("Confidence is low due to limited source material cited.")

        # --- Construct Final Output ---
        final_explanation = {
            "explain_id": f"{explain_id_base}:{context_ids_used_in_prompt[0] if context_ids_used_in_prompt else 'NA'}",
            "repo_id": repo_id, "file_path": file_path, "object": target_object,
            "summary": llm_data.get("summary", "Summary not generated."),
            "key_points": llm_data.get("key_points", []),
            "unit_test": llm_data.get("unit_test", {"title":"N/A","code":"","language":"python"}),
            "example": llm_data.get("example", "N/A"),
            "sources": valid_sources_cited_ids,
            "confidence": confidence,
            "warnings": validation_warnings + llm_data.get("warnings", [])
        }
        sources_full_for_ui = valid_sources_full
        print(f"✅ Successfully generated explanation for '{target_object}'. Confidence: {confidence}")

    except Exception as e:
        print(f"❌ Error during explanation generation or validation: {e}")
        # Return structured error using helper
        return create_error_response("llm_error", str(e), contexts_to_use)

    # --- Logging (Moved helper function) ---
    def log_explanation(prompt_hash: str, final_explanation_data: Dict):
        """Saves explanation details to a log file."""
        if not LOG_DIR: return # Skip if log dir failed
        try:
            log_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "repo_id": repo_id, "file_path": file_path, "object": target_object,
                "context_ids_used_in_prompt": context_ids_used_in_prompt,
                "prompt_hash": prompt_hash,
                "explanation_result": final_explanation_data
            }
            safe_filename = f"explain_{explain_id_base}_{datetime.datetime.now():%Y%m%d_%H%M%S}.json"
            log_filepath = LOG_DIR / safe_filename
            with open(log_filepath, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False, default=str)
            print(f"📝 Explanation log saved to {log_filepath}")
        except Exception as log_e:
            print(f"⚠️ Warning: Failed to save explanation log: {log_e}")

    log_explanation(hashlib.sha256(prompt.encode('utf-8')).hexdigest(), final_explanation)

    # Return the structured data and the full context objects cited
    return final_explanation, sources_full_for_ui