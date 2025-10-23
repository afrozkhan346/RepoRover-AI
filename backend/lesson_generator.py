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

# --- Code Explainer Template ---
CODE_EXPLAIN_PROMPT_TEMPLATE = """
You are RepoRoverExplainer, a code assistant for beginners.

Analyzing code from:
File: {file_path}
Context ID: {context_id}
Repository: {repo_id}

Code:
{content}

Return only a JSON object with this structure:
{{
  "summary": "One-line explanation of the code's purpose",
  "edge_cases": [
    "First potential issue",
    "Second potential issue",
    "Third potential issue"
  ],
  "test_suggestion": {{
    "title": "test_descriptive_name",
    "assert": "assert function(input) == expected"
  }},
  "sources": ["{context_id}"]
}}
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

def generate_explanation_rag(context: dict, repo_id: str):
    """Generates a structured explanation for a code snippet."""
    if not context or not context.get('content'):
        print("\n❌ Error: Invalid context for explanation")
        return None, []

    print("\n🔍 Starting Code Explanation")
    print(f"Repo: {repo_id}")
    print(f"File: {context.get('file_path', 'unknown')}")
    print(f"Context ID: {context.get('id', 'unknown')}")
    print(f"Content length: {len(context.get('content', ''))} chars")

    try:
        prompt = CODE_EXPLAIN_PROMPT_TEMPLATE.format(
            repo_id=repo_id,
            context_id=context.get('id', 'unknown'),
            file_path=context.get('file_path', 'unknown'),
            content=context.get('content', '')
        )

        print("\n📤 Sending explanation prompt to LLM")
        response = llm_client.get_gemini_response(prompt)
        
        if not response or response.startswith("Error:"):
            print(f"❌ LLM Error: {response}")
            raise ValueError(f"Invalid LLM response: {response}")

        print("\n🔍 Parsing explanation response")
        explanation = json.loads(response.strip())
        
        required_fields = ["summary", "edge_cases", "test_suggestion", "sources"]
        if not all(field in explanation for field in required_fields):
            missing = [f for f in required_fields if f not in explanation]
            print(f"❌ Missing required fields: {missing}")
            raise ValueError("Incomplete explanation data")

        print("✅ Successfully generated explanation")
        return explanation, [context]

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {str(e)}")
        print(f"Raw response:\n{response}")
        return None, [context]
    except Exception as e:
        print(f"❌ Error generating explanation: {str(e)}")
        return None, [context]
