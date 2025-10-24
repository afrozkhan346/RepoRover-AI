# backend/lesson_generator.py
from . import llm_client
import json
import time

# --- RAG Lesson Prompt Template ---
RAG_LESSON_PROMPT_TEMPLATE = """
SYSTEM:
You are RepoRoverTeacher, an expert tutor for software projects.
Your task is to create 3 beginner-friendly lessons from the provided repository contexts.

Repository: {repo_id}
User Goal: {user_goal}

Contexts:
{context_str}

Return a single JSON object with this exact structure:
{{
  "repo_id": "{repo_id}",
  "lessons": [
    {{
      "lesson_id": "L1",
      "title": "Short clear title",
      "level": "Beginner",
      "objective": "Single learning goal",
      "duration_minutes": 5,
      "steps": [
        {{
          "order": 1,
          "instruction": "Clear step instruction",
          "evidence": ["context_id"]
        }}
      ],
      "summary": "What was learned",
      "quiz_hint": "What to test",
      "sources": ["context_id"]
    }}
  ],
  "warnings": []
}}

Rules:
1. Use only facts from the contexts
2. Each lesson needs valid context_id references
3. Return only the JSON object
"""

# --- Updated Code Explainer Template ---
# --- RAG Code Explainer Prompt Template (UPDATED Schema) ---
CODE_EXPLAIN_PROMPT_TEMPLATE = """
SYSTEM:
You are RepoRoverExplainer, a concise code explainer for learners. Use only the provided contexts (EXCERPTs) to answer. Do not invent facts or filenames. If info is missing, say so.

INPUT:
- repo_id: {repo_id}
- target: {object_name} (file path: {file_path})
- CONTEXTS: (list below, each has CONTEXT_ID, FILE, EXCERPT)

TASK:
Using ONLY the CONTEXTS below, produce EXACTLY one JSON object (no extra text) matching this schema:
{
  "summary": "string (one-sentence summary, <=140 chars)",
  "key_points": [
      "string (concise point 1, <=120 chars)",
      "string (concise point 2, <=120 chars)",
      "string (concise point 3, <=120 chars)"
   ],
  "unit_test": {
      "title": "string (Descriptive test name)",
      "code": "string (Single, runnable assert or pytest snippet)",
      "language": "python"
   },
  "example": "string (one-line example to run or use, or 'No simple example applicable.')",
  "sources": ["CONTEXT_ID", "..."],
  "warnings": []
}

CONSTRAINTS:
- Use only information present in the CONTEXTS. If insufficient info, set summary to "Insufficient context to summarize {object_name}." and add a warning.
- Base key points, test, and example strictly on provided CONTEXTS.
- At least one CONTEXT_ID must be listed in "sources".
- Return valid JSON only, starting with {{ and ending with }}.

CONTEXTS:
---BEGIN
{context_str}
---END

Return only the JSON object.
"""

def _validate_lesson_json(lesson_data: dict, source_map: dict):
    """Validates the structure and content of the lesson JSON returned by the LLM."""
    warnings = []
    if not lesson_data or not isinstance(lesson_data.get("lessons"), list):
        warnings.append("Basic structure invalid (missing 'lessons' list).")
        return warnings

    context_ids_in_map = set(source_map.keys())
    
    for i, lesson in enumerate(lesson_data.get("lessons", [])):
        lesson_id = lesson.get("lesson_id", f"Lesson_{i+1}")
        
        # Source validation
        lesson_sources = lesson.get("sources", [])
        if not lesson_sources:
            warnings.append(f"{lesson_id}: Contains no sources.")
        for src_id in lesson_sources:
            if src_id not in context_ids_in_map:
                warnings.append(f"{lesson_id}: References invalid source '{src_id}'")
        
        # Steps validation
        steps = lesson.get("steps", [])
        if len(steps) < 1:
            warnings.append(f"{lesson_id}: Contains no steps.")
        
        # Step content validation
        for j, step in enumerate(steps):
            instruction = step.get("instruction", "")
            if len(instruction) > 160:
                warnings.append(f"{lesson_id}, Step {j+1}: Instruction too long ({len(instruction)} chars)")
            
            evidence = step.get("evidence", [])
            if not evidence:
                warnings.append(f"{lesson_id}, Step {j+1}: Missing evidence")
            for ev_id in evidence:
                if ev_id not in context_ids_in_map:
                    warnings.append(f"{lesson_id}, Step {j+1}: Invalid evidence '{ev_id}'")

    if len(lesson_data.get("lessons", [])) != 3:
        warnings.append(f"Generated {len(lesson_data.get('lessons', []))} lessons instead of 3")

    return warnings

def generate_lesson_rag(contexts: list[dict], repo_id: str, user_goal: str = "Understand the repository structure and purpose"):
    """Generates a structured lesson plan using RAG."""
    if not contexts:
        print("\n❌ Error: No contexts provided for lesson generation")
        return None, []

    print("\n🎯 Starting Lesson Generation")
    print(f"Goal: {user_goal}")
    print(f"Repo: {repo_id}")
    print(f"Input Contexts: {len(contexts)} total")

    # Prepare contexts
    MAX_CONTEXT_LENGTH = 15000
    context_str = ""
    included_contexts = []
    source_map = {}

    for i, ctx in enumerate(contexts):
        context_id = ctx.get('id', f'ctx_{i}')
        source_map[context_id] = ctx
        excerpt = ctx.get('excerpt', ctx['content'][:400])
        context_part = f"--- CONTEXT_ID: {context_id}\nFILE: {ctx['file_path']}\nEXCERPT:\n{excerpt}\n--- END CONTEXT\n"
        
        if len(context_str) + len(context_part) < MAX_CONTEXT_LENGTH:
            context_str += context_part + "\n"
            included_contexts.append(ctx)
            print(f"✓ Including: {context_id} ({ctx['file_path']})")
        else:
            print(f"⚠ Skipping: {context_id} (would exceed token limit)")
            break

    if not included_contexts:
        print("❌ Error: No contexts included within length limit")
        return None, []

    # Generate lessons
    prompt = RAG_LESSON_PROMPT_TEMPLATE.format(
        user_goal=user_goal,
        repo_id=repo_id,
        context_str=context_str.strip()
    )

    print(f"\n📤 Sending prompt to LLM")
    print(f"Context length: {len(context_str)} chars")
    print(f"Using contexts: {[ctx['id'] for ctx in included_contexts]}")

    MAX_JSON_RETRIES = 1
    for attempt in range(MAX_JSON_RETRIES + 1):
        print(f"\n🤖 Attempt {attempt + 1} of {MAX_JSON_RETRIES + 1}")
        raw_response = llm_client.get_gemini_response(prompt)

        try:
            if not raw_response or raw_response.startswith("Error:"):
                print(f"❌ LLM Error: {raw_response}")
                raise ValueError(f"Invalid LLM response: {raw_response}")

            # Parse JSON
            cleaned_response = raw_response.strip()
            if cleaned_response.startswith("```json"): 
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            
            lesson_data = json.loads(cleaned_response.strip())
            
            # Validate and process
            print("\n🔍 Validating lesson data")
            validation_warnings = _validate_lesson_json(lesson_data, source_map)
            if validation_warnings:
                print("⚠ Validation warnings:")
                for warning in validation_warnings:
                    print(f"  - {warning}")
            lesson_data["warnings"] = lesson_data.get("warnings", []) + validation_warnings

            # Attach full context objects
            print("\n📎 Attaching source contexts")
            all_sources = []
            for lesson in lesson_data.get("lessons", []):
                sources_full = [source_map[src] for src in lesson.get("sources", []) if src in source_map]
                lesson["sources_full"] = sources_full
                all_sources.extend(sources_full)
                
                for step in lesson.get("steps", []):
                    evidence_full = [source_map[ev] for ev in step.get("evidence", []) if ev in source_map]
                    step["evidence_full"] = evidence_full

            unique_sources = list({ctx['id']: ctx for ctx in all_sources}.values())
            print(f"✅ Success! Generated {len(lesson_data['lessons'])} lessons using {len(unique_sources)} unique sources")
            return lesson_data, unique_sources

        except (json.JSONDecodeError, ValueError) as e:
            print(f"❌ Error parsing response (Attempt {attempt + 1}): {str(e)}")
            if attempt < MAX_JSON_RETRIES:
                print("⏳ Retrying with stricter JSON instruction...")
                prompt += "\n\nIMPORTANT: Return ONLY the valid JSON object."
                time.sleep(2)
            else:
                print("❌ Max retries reached. Failed to get valid lesson JSON.")
                return None, included_contexts

        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return None, included_contexts

    return None, included_contexts

def generate_explanation_rag(context: dict, repo_id: str, object_name: str = "file"):
    """Generates a structured explanation using the context excerpt."""
    if not context or not context.get('content'):
        print("\n❌ Error: Invalid context for explanation")
        return None, []

    context_id = context.get('id', 'N/A')
    file_path = context.get('file_path', 'N/A')
    # Use excerpt or create one from content
    excerpt = context.get('excerpt')
    if not excerpt:
        content = context.get('content', '')
        excerpt = content[:400] + ('...' if len(content) > 400 else '')

    # Ensure we have valid content to work with
    if not excerpt.strip():
        print(f"❌ Context {context_id} has empty excerpt/content")
        return None, []

    # Build prompt with excerpt
    prompt = CODE_EXPLAIN_PROMPT_TEMPLATE.format(
        repo_id=repo_id,
        context_id=context_id,
        file_path=file_path,
        excerpt=excerpt
    )

    print("\n📤 Sending explanation prompt to LLM")
    raw_response = llm_client.get_gemini_response(prompt, temperature=0.15)

    try:
        if not raw_response or raw_response.startswith("Error:"):
            raise ValueError(f"LLM Error: {raw_response}")

        # Clean and parse JSON
        cleaned_response = raw_response.strip()
        if cleaned_response.startswith("```json"): 
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        
        llm_data = json.loads(cleaned_response.strip())
        
        # Validate required fields
        required_keys = ["summary", "key_points", "unit_test", "example", "sources"]
        missing_keys = [key for key in required_keys if key not in llm_data]
        if missing_keys:
            raise ValueError(f"Missing required fields: {missing_keys}")

        # Validate key_points
        if not isinstance(llm_data.get("key_points"), list) or len(llm_data["key_points"]) != 3:
            raise ValueError("key_points must be a list of exactly 3 strings")

        # Validate unit_test structure
        unit_test = llm_data.get("unit_test", {})
        if not isinstance(unit_test, dict) or not all(k in unit_test for k in ["title", "code", "language"]):
            raise ValueError("unit_test object structure is invalid")

        # Validate sources
        if not isinstance(llm_data.get("sources"), list) or context_id not in llm_data.get("sources", []):
            print(f"⚠️ Warning: explanation sources don't match expected context_id {context_id}")

        # Construct final explanation data
        final_explanation_data = {
            "explain_id": f"{repo_id}:{file_path}:{object_name}:{context.get('start_line', 0)}:{context.get('chunk_index', 0)}",
            "repo_id": repo_id,
            "file_path": file_path,
            "object": object_name,
            "summary": llm_data["summary"],
            "key_points": llm_data["key_points"],
            "unit_test": llm_data["unit_test"],
            "example": llm_data["example"],
            "sources": llm_data["sources"],
            "warnings": []
        }

        print("✅ Successfully generated explanation")
        return final_explanation_data, [context]

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {str(e)}")
        print(f"Raw response:\n{raw_response}")
        return None, [context]
    except Exception as e:
        print(f"❌ Error generating explanation: {str(e)}")
        return None, [context]

def generate_explanation_rag(contexts: list[dict], repo_id: str, file_path: str, object_name: str = "file"):
    """Generates a structured explanation using RAG based on multiple contexts."""
    if not contexts:
        print("❌ No contexts provided for explanation generation.")
        return None, []

    MAX_CONTEXT_LENGTH = 8000
    context_str = ""
    included_context_ids = []
    source_map = {}

    # Prepare context string and source map
    for i, ctx in enumerate(contexts):
        context_id = ctx.get('id', f'ctx_{i}')
        source_map[context_id] = ctx
        excerpt = ctx.get('excerpt', ctx.get('content', '')[:400])
        current_context_part = f"""CONTEXT_ID: {context_id}
FILE: {ctx['file_path']}
EXCERPT:
{excerpt}
---END
"""
        if len(context_str) + len(current_context_part) < MAX_CONTEXT_LENGTH:
            context_str += current_context_part + "\n"
            included_context_ids.append(context_id)
        else:
            print(f"⚠️ Stopping context inclusion at {len(included_context_ids)} items")
            break

    if not included_context_ids:
        print("❌ No contexts could be included within length limit")
        return None, []

    prompt = CODE_EXPLAIN_PROMPT_TEMPLATE.format(
        repo_id=repo_id,
        object_name=object_name,
        file_path=file_path,
        context_str=context_str.strip()
    )

    print(f"\n📤 Generating explanation for '{object_name}' using {len(included_context_ids)} contexts...")
    raw_response = llm_client.get_gemini_response(prompt, temperature=0.15)

    try:
        if not raw_response or raw_response.startswith("Error:"):
            raise ValueError(f"LLM Error: {raw_response}")

        # Clean and parse JSON
        cleaned_response = raw_response.strip()
        if cleaned_response.startswith("```json"): 
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        
        llm_data = json.loads(cleaned_response.strip())
        
        # Validate response
        validation_warnings = []
        required_keys = ["summary", "key_points", "unit_test", "example", "sources"]
        missing_keys = [key for key in required_keys if key not in llm_data]
        if missing_keys:
            raise ValueError(f"Missing required fields: {missing_keys}")

        # Validate key points
        if not isinstance(llm_data.get("key_points"), list) or len(llm_data["key_points"]) != 3:
            validation_warnings.append(f"Expected 3 key points, found {len(llm_data.get('key_points', []))}")

        # Validate unit test structure
        unit_test = llm_data.get("unit_test", {})
        if not isinstance(unit_test, dict) or not all(k in unit_test for k in ["title", "code", "language"]):
            raise ValueError("unit_test object structure is invalid")

        # Validate sources
        llm_sources = llm_data.get("sources", [])
        valid_sources_cited = [src for src in llm_sources if src in included_context_ids]
        
        if not valid_sources_cited:
            validation_warnings.append("No valid sources cited")

        # Calculate confidence
        confidence = "low"
        if len(valid_sources_cited) >= 3:
            confidence = "high"
        elif len(valid_sources_cited) == 2:
            confidence = "medium"

        # Construct final data
        final_explanation_data = {
            "explain_id": f"{repo_id}:{file_path}:{object_name}:{included_context_ids[0] if included_context_ids else 'NA'}",
            "repo_id": repo_id,
            "file_path": file_path,
            "object": object_name,
            "summary": llm_data["summary"],
            "key_points": llm_data["key_points"],
            "unit_test": llm_data["unit_test"],
            "example": llm_data["example"],
            "sources": valid_sources_cited,
            "confidence": confidence,
            "warnings": validation_warnings + llm_data.get("warnings", [])
        }

        sources_full = [source_map[src_id] for src_id in valid_sources_cited]
        print(f"✅ Generated explanation. Confidence: {confidence}")
        return final_explanation_data, sources_full

    except Exception as e:
        print(f"❌ Error generating explanation: {str(e)}")
        # Return None plus the list of included context dicts (if available), else an empty list
        contexts_full = [source_map[src_id] for src_id in included_context_ids] if 'included_context_ids' in locals() else []
        return None, contexts_full
