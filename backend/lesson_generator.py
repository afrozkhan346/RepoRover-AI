# backend/lesson_generator.py
from backend.explain import CODE_EXPLAIN_PROMPT_TEMPLATE
from . import llm_client
import json
import time
from typing import List, Dict, Any, Tuple
import streamlit as st # For caching
import os
import datetime
from pathlib import Path

# --- Setup Log Directory ---
SCRIPT_DIR_LESSON = Path(__file__).resolve().parent.parent # Project root
LOG_DIR = SCRIPT_DIR_LESSON / "data" / "lesson_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# --- RAG Lesson Prompt Template (with Few-Shot Example) ---
RAG_LESSON_PROMPT_TEMPLATE = """
SYSTEM:
You are RepoRoverTeacher, an expert tutor for software projects. You transform repository context excerpts into short, teachable lessons aimed at beginners. Be concise, factual, and always cite sources.

EXAMPLE:
Input Contexts:
--- CONTEXT_ID: repoX:README.md:Section:1
FILE: README.md
EXCERPT:
## Authentication
This project uses JWT for authentication. Users log in via the /login endpoint...
--- END CONTEXT

--- CONTEXT_ID: repoX:src/auth.py:handle_login:55:0
FILE: src/auth.py
EXCERPT:
def handle_login(username, password):
  # ... checks password ...
  token = create_jwt(user_id)
  return jsonify({{"token": token}})
--- END CONTEXT

Output (lessons snippet):
```json
{{
  "repo_id": "repoX",
  "lessons": [
    {{
      "lesson_id": "L1",
      "title": "Understanding User Authentication Flow",
      "level": "Beginner",
      "objective": "Learn how users log in and receive authentication tokens.",
      "duration_minutes": 5,
      "steps": [
        {{
          "order": 1,
          "instruction": "Users initiate login by sending credentials to the /login endpoint.",
          "evidence": ["repoX:README.md:Section:1"]
        }},
        {{
          "order": 2,
          "instruction": "The `handle_login` function verifies credentials and generates a JWT token.",
          "evidence": ["repoX:src/auth.py:handle_login:55:0"]
        }}
      ],
      "summary": "Authentication uses JWT tokens generated upon successful login.",
      "quiz_hint": "Ask about the type of token used for authentication.",
      "sources": ["repoX:README.md:Section:1", "repoX:src/auth.py:handle_login:55:0"]
    }}
  ]
}}
```
END EXAMPLE.

INSTRUCTION:
You will be provided with:
1) A short user goal: "{user_goal}"
2) A list of retrieved contexts (each labeled with CONTEXT_ID, FILE_PATH and EXCERPT).
3) The repo id: {repo_id}.

TASK:
Using only the information in the CONTEXTS below, produce exactly 3 lessons (Beginner-level first). Each lesson must follow the JSON schema shown in the EXAMPLE and include "sources" entries that reference the CONTEXT_ID(s) used. Do not invent file paths or facts not in the contexts. Do not include any commentary outside the JSON object.

CONTEXTS:
{context_str}

OUTPUT FORMAT:
Return a single JSON object matching the schema shown in the EXAMPLE exactly.

CONSTRAINTS:
- Use only the CONTEXTS above for facts.
- Each lesson must reference at least one CONTEXT_ID in sources.
- Keep each step instruction short (<= 140 characters).
- Return valid JSON only (no extra text).
- If contexts lack sufficient info for 3 lessons, fill missing lessons with title="Practice Exercise", objective="Practice using the repository", steps=[{{"order": 1, "instruction": "Read the main README file carefully."}}, {{"order": 2, "instruction": "Try running the project's tests or examples."}}], summary="Hands-on practice is key to understanding.", quiz_hint="Ask about the main purpose.", sources=[] and include a warning like "Could not generate 3 distinct lessons from the provided context.".

END.
"""

# --- Helper function for Validation ---

def _validate_lesson_json(lesson_data: dict, source_map: dict) -> List[str]:
    """
    Validates the structure and content of the lesson JSON returned by the LLM.
    """
    warnings = []
    if not lesson_data or not isinstance(lesson_data.get("lessons"), list):
        warnings.append("Basic structure invalid (missing 'lessons' list).")
        return warnings # No point checking further

    context_ids_in_map = set(source_map.keys())

    for i, lesson in enumerate(lesson_data.get("lessons", [])):
        lesson_id = lesson.get("lesson_id", f"Lesson_{i+1}")

        # 1. Source Check
        lesson_sources = lesson.get("sources", [])
        if not lesson_sources and lesson.get("title") != "Practice Exercise":
             warnings.append(f"{lesson_id}: Contains no sources.")
        for src_id in lesson_sources:
            if src_id not in context_ids_in_map:
                warnings.append(f"{lesson_id}: References source '{src_id}' which was not in the provided context.")

        # 2. Step Count Check
        steps = lesson.get("steps", [])
        if len(steps) < 1:
            warnings.append(f"{lesson_id}: Contains no steps.")

        # 3. Step Length & Evidence Check
        for j, step in enumerate(steps):
            instruction = step.get("instruction", "")
            if len(instruction) > 160: # Allow buffer
                 warnings.append(f"{lesson_id}, Step {j+1}: Instruction too long ({len(instruction)} chars).")

            step_evidence = step.get("evidence", [])
            if not step_evidence and lesson.get("title") != "Practice Exercise":
                 warnings.append(f"{lesson_id}, Step {j+1}: Contains no evidence citation.")
            for ev_id in step_evidence:
                 if ev_id not in context_ids_in_map:
                       warnings.append(f"{lesson_id}, Step {j+1}: Cites evidence '{ev_id}' which was not in the provided context.")

    # 4. Lesson Count Check
    if len(lesson_data.get("lessons", [])) != 3:
         warnings.append(f"LLM did not return exactly 3 lessons (returned {len(lesson_data.get('lessons', []))}).")

    return warnings

@st.cache_data(ttl=3600, show_spinner=False)
def generate_lesson_rag(contexts: list[dict], repo_id: str, user_goal: str = "Understand the repository structure and purpose") -> Tuple[Dict | None, List]:
    """
    Generates a structured lesson plan using RAG, including JSON parsing retry and validation.
    """
    if not contexts:
        print("\n❌ Error: No contexts provided for lesson generation")
        return None, []

    print("\n🎯 Starting Lesson Generation")
    print(f"Goal: {user_goal}")
    print(f"Repo: {repo_id}")
    print(f"Input Contexts: {len(contexts)} total")

    # --- Setup Logging ---
    log_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "repo_id": repo_id,
        "user_goal": user_goal,
        "prompt": None, # Will be set
        "context_ids_used": [],
        "llm_attempts": [],
        "final_lesson_data": None,
        "validation_warnings": [],
        "status": "started"
    }
    log_filename = LOG_DIR / f"lesson_log_{repo_id.replace('/', '_')}_{datetime.datetime.now():%Y%m%d_%H%M%S}.json"
    # --- End Logging Setup ---

    try:
        # --- Prepare Contexts ---
        MAX_CONTEXT_LENGTH = 15000
        context_str = ""
        included_contexts = []
        source_map = {} # Map CONTEXT_ID back to full context object
        for i, ctx in enumerate(contexts):
            context_id = ctx.get('id', f'ctx_{i}') # Use the actual context ID from ingestion
            source_map[context_id] = ctx # Store context object by its ID
            # Use excerpt field for brevity
            excerpt = ctx.get('excerpt') or (ctx.get('content', '')[:400].strip() + "...") # Fallback to content start if no excerpt
            if not excerpt.strip(): excerpt = "..." # Ensure excerpt is not empty

            current_context_part = f"""--- CONTEXT_ID: {context_id}
FILE: {ctx['file_path']}
EXCERPT:
{excerpt}
--- END CONTEXT
"""
            if len(context_str) + len(current_context_part) < MAX_CONTEXT_LENGTH:
                context_str += current_context_part + "\n" # Add newline separation
                included_contexts.append(ctx)
                # Optional: verbose logging
                # print(f"✓ Including: {context_id} ({ctx['file_path']})")
            else:
                print(f"⚠ Skipping context {context_id} (would exceed token limit)")
                break # Stop adding contexts
        
        if not included_contexts:
             raise Exception("No contexts could be included within length limit")

        # Compose prompt with repo_id, user_goal and formatted context string
        prompt = RAG_LESSON_PROMPT_TEMPLATE.format(
            user_goal=user_goal, repo_id=repo_id, context_str=context_str.strip()
        )
        log_data["prompt"] = prompt # Add prompt to log
        log_data["context_ids_used"] = list(source_map.keys())

        print(f"\n📤 Sending prompt to LLM (Context length: {len(context_str)} chars)...")
        # print(f"Using contexts: {[ctx['id'] for ctx in included_contexts]}") # Verbose log

        # --- LLM Call with Retry Logic for JSON Parsing ---
        MAX_JSON_RETRIES = 1
        for attempt in range(MAX_JSON_RETRIES + 1):
            attempt_data = {"attempt_number": attempt + 1, "timestamp": datetime.datetime.now().isoformat(), "raw_response": None, "validation_errors": [], "status": "pending"}
            print(f"\n🤖 Attempt {attempt + 1} of {MAX_JSON_RETRIES + 1}")
            
            raw_response = llm_client.get_gemini_response(prompt, temperature=0.2)
            attempt_data["raw_response"] = raw_response

            try:
                if not raw_response or raw_response.startswith("Error:"):
                     raise ValueError(f"LLM client returned an error or empty response: {raw_response}")

                # Clean up potential markdown code fences ```json ... ```
                cleaned_response = raw_response.strip()
                if cleaned_response.startswith("```json"): cleaned_response = cleaned_response[7:]
                if cleaned_response.endswith("```"): cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()
                if not (cleaned_response.startswith("{") and cleaned_response.endswith("}")):
                     raise ValueError("Response is not a valid JSON object (missing braces).")

                lesson_data = json.loads(cleaned_response)
                attempt_data["status"] = "parsed"

                # Validate the parsed JSON
                print("\n🔍 Validating lesson data...")
                validation_warnings = _validate_lesson_json(lesson_data, source_map)
                if validation_warnings:
                    print("⚠ Validation warnings found:"); [print(f"  - {w}") for w in validation_warnings]
                lesson_data["warnings"] = lesson_data.get("warnings", []) + validation_warnings
                attempt_data["validation_errors"] = validation_warnings

                # Attach full context objects for UI display
                print("\n📎 Attaching full source contexts to lesson data...")
                all_lesson_sources_full = []
                for lesson in lesson_data.get("lessons", []):
                    lesson_sources_ids = lesson.get("sources", [])
                    lesson_sources_full = [source_map.get(src_id) for src_id in lesson_sources_ids if source_map.get(src_id)]
                    lesson["sources_full"] = lesson_sources_full
                    all_lesson_sources_full.extend(lesson_sources_full)
                    for step in lesson.get("steps", []):
                         step_evidence_ids = step.get("evidence", [])
                         step_evidence_full = [source_map.get(ev_id) for ev_id in step_evidence_ids if source_map.get(ev_id)]
                         step["evidence_full"] = step_evidence_full

                # Get a unique list of all context objects used across all lessons
                unique_sources_used = list({ctx['id']: ctx for ctx in all_lesson_sources_full}.values())

                # --- Success ---
                print(f"✅ Success! Generated {len(lesson_data['lessons'])} lessons.")
                log_data["status"] = "success"
                log_data["final_lesson_data"] = lesson_data
                log_data["llm_attempts"].append(attempt_data)
                with open(log_filename, 'w', encoding='utf-8') as f:
                    json.dump(log_data, f, indent=2, ensure_ascii=False)
                print(f"📝 Lesson log saved to {log_filename}")
                return lesson_data, unique_sources_used

            except (json.JSONDecodeError, ValueError) as e:
                print(f"❌ Error processing response (Attempt {attempt + 1}): {e}")
                attempt_data["status"] = "error_parsing"
                attempt_data["validation_errors"].append(str(e))
                log_data["llm_attempts"].append(attempt_data)
                if attempt < MAX_JSON_RETRIES:
                    print("⏳ Retrying...")
                    prompt += "\n\nIMPORTANT REMINDER: Your response MUST be ONLY the valid JSON object requested, starting with '{' and ending with '}'. Do NOT include any other text, comments, or markdown formatting."
                    time.sleep(2)
                else:
                    print("❌ Max retries reached.")
                    log_data["status"] = "failed_all_attempts"
                    with open(log_filename, 'w', encoding='utf-8') as f:
                        json.dump(log_data, f, indent=2, ensure_ascii=False)
                    return None, included_contexts
        
    except Exception as e:
        print(f"❌ Unexpected error in lesson generation: {str(e)}")
        log_data["status"] = "unexpected_error"; log_data["validation_warnings"].append(str(e))
        with open(log_filename, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        return None, []

    return None, included_contexts # Fallback

# def generate_explanation_rag(context: dict, repo_id: str, object_name: str = "file"):
#     """Generates a structured explanation using the context excerpt."""
#     if not context or not context.get('content'):
#         print("\n❌ Error: Invalid context for explanation")
#         return None, []

#     context_id = context.get('id', 'N/A')
#     file_path = context.get('file_path', 'N/A')
#     # Use excerpt or create one from content
#     excerpt = context.get('excerpt')
#     if not excerpt:
#         content = context.get('content', '')
#         excerpt = content[:400] + ('...' if len(content) > 400 else '')

#     # Ensure we have valid content to work with
#     if not excerpt.strip():
#         print(f"❌ Context {context_id} has empty excerpt/content")
#         return None, []

#     # Build prompt with excerpt
#     prompt = CODE_EXPLAIN_PROMPT_TEMPLATE.format(
#         repo_id=repo_id,
#         context_id=context_id,
#         file_path=file_path,
#         excerpt=excerpt
#     )

#     print("\n📤 Sending explanation prompt to LLM")
#     raw_response = llm_client.get_gemini_response(prompt, temperature=0.15)

#     try:
#         if not raw_response or raw_response.startswith("Error:"):
#             raise ValueError(f"LLM Error: {raw_response}")

#         # Clean and parse JSON
#         cleaned_response = raw_response.strip()
#         if cleaned_response.startswith("```json"): 
#             cleaned_response = cleaned_response[7:]
#         if cleaned_response.endswith("```"):
#             cleaned_response = cleaned_response[:-3]
        
#         llm_data = json.loads(cleaned_response.strip())
        
#         # Validate required fields
#         required_keys = ["summary", "key_points", "unit_test", "example", "sources"]
#         missing_keys = [key for key in required_keys if key not in llm_data]
#         if missing_keys:
#             raise ValueError(f"Missing required fields: {missing_keys}")

#         # Validate key_points
#         if not isinstance(llm_data.get("key_points"), list) or len(llm_data["key_points"]) != 3:
#             raise ValueError("key_points must be a list of exactly 3 strings")

#         # Validate unit_test structure
#         unit_test = llm_data.get("unit_test", {})
#         if not isinstance(unit_test, dict) or not all(k in unit_test for k in ["title", "code", "language"]):
#             raise ValueError("unit_test object structure is invalid")

#         # Validate sources
#         if not isinstance(llm_data.get("sources"), list) or context_id not in llm_data.get("sources", []):
#             print(f"⚠️ Warning: explanation sources don't match expected context_id {context_id}")

#         # Construct final explanation data
#         final_explanation_data = {
#             "explain_id": f"{repo_id}:{file_path}:{object_name}:{context.get('start_line', 0)}:{context.get('chunk_index', 0)}",
#             "repo_id": repo_id,
#             "file_path": file_path,
#             "object": object_name,
#             "summary": llm_data["summary"],
#             "key_points": llm_data["key_points"],
#             "unit_test": llm_data["unit_test"],
#             "example": llm_data["example"],
#             "sources": llm_data["sources"],
#             "warnings": []
#         }

#         print("✅ Successfully generated explanation")
#         return final_explanation_data, [context]

#     except json.JSONDecodeError as e:
#         print(f"❌ JSON parsing error: {str(e)}")
#         print(f"Raw response:\n{raw_response}")
#         return None, [context]
#     except Exception as e:
#         print(f"❌ Error generating explanation: {str(e)}")
#         return None, [context]

# def generate_explanation_rag(contexts: list[dict], repo_id: str, file_path: str, object_name: str = "file"):
#     """Generates a structured explanation using RAG based on multiple contexts."""
