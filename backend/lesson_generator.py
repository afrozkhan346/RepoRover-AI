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

        print(f"\n📤 Sending prompt to LLM (Context length: {len(context_str)} chars)...")
        # print(f"Using contexts: {[ctx['id'] for ctx in included_contexts]}") # Verbose log

        # --- LLM Call with Retry Logic for JSON Parsing ---
        MAX_JSON_RETRIES = 1
        for attempt in range(MAX_JSON_RETRIES + 1):
            print(f"\n🤖 Attempt {attempt + 1} of {MAX_JSON_RETRIES + 1}")
            
            raw_response = llm_client.get_gemini_response(prompt, temperature=0.2)

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

                # Validate the parsed JSON
                print("\n🔍 Validating lesson data...")
                validation_warnings = _validate_lesson_json(lesson_data, source_map)
                if validation_warnings:
                    print("⚠ Validation warnings found:"); [print(f"  - {w}") for w in validation_warnings]
                lesson_data["warnings"] = lesson_data.get("warnings", []) + validation_warnings

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
                return lesson_data, unique_sources_used

            except (json.JSONDecodeError, ValueError) as e:
                print(f"❌ Error processing response (Attempt {attempt + 1}): {e}")
                if attempt < MAX_JSON_RETRIES:
                    print("⏳ Retrying...")
                    prompt += "\n\nIMPORTANT REMINDER: Your response MUST be ONLY the valid JSON object requested, starting with '{' and ending with '}'. Do NOT include any other text, comments, or markdown formatting."
                    time.sleep(2)
                else:
                    print("❌ Max retries reached.")
                    return None, included_contexts
        
    except Exception as e:
        print(f"❌ Unexpected error in lesson generation: {str(e)}")
        return None, []

    return None, included_contexts # Fallback
