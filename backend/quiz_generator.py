from . import llm_client
import json
import streamlit as st
import time
from typing import List, Dict, Any

# --- RAG Quiz Prompt Template ---
QUIZ_RAG_PROMPT_TEMPLATE = """
SYSTEM:
You are a careful quiz writer. Produce three multiple-choice questions (MCQs) for the provided lesson. Each MCQ must be answerable from the supplied contexts only, include 1 correct answer and 3 plausible distractors, and include a short explanation citing the context IDs.

INPUT:
- Lesson title: "{title}"
- Lesson objective: "{objective}"
- Quiz hint (optional): "{quiz_hint}"
- CONTEXTS:
---
{contexts_text}
---

TASK:
Return a JSON object exactly matching the schema below. Use the provided lesson_id "{lesson_id}" and repo_id "{repo_id}".

{{
  "lesson_id": "{lesson_id}",
  "quiz_id": "{repo_id}-{lesson_id}",
  "questions": [
    {{
      "qid": "Q1",
      "type": "mcq",
      "question": "string (Question based *only* on context)",
      "choices": [
        {{"label": "A", "text": "string (Plausible answer A)", "correct": true/false}},
        {{"label": "B", "text": "string (Plausible answer B)", "correct": true/false}},
        {{"label": "C", "text": "string (Plausible answer C)", "correct": true/false}},
        {{"label": "D", "text": "string (Plausible answer D)", "correct": true/false}}
      ],
      "explanation": "string (Short explanation for the correct answer, citing the CONTEXT_ID(s) used)",
      "evidence": ["CONTEXT_ID", "..."]
    }}
  ]
}}

CONSTRAINTS:
- Use only facts from CONTEXTS. Do not invent file paths or facts.
- Each question must be clear and solvable by reading the supplied contexts.
- Distractors must be plausible (not obviously wrong).
- Explanation must reference at least one CONTEXT_ID.
- Return valid JSON only (no extra text or comments).

Settings: temperature 0.15 for stable output.
END.
"""

def build_quiz_prompt(lesson: Dict[str, Any], contexts: List[Dict[str, Any]], repo_id: str) -> str:
    """Builds the prompt string for the LLM based on the lesson and contexts."""
    contexts_text = ""
    for c in contexts[:8]:
        context_id = c.get('id', 'N/A')
        excerpt = c.get('excerpt', c.get('content', '')[:300])
        contexts_text += f"""--- CONTEXT_ID: {context_id}
FILE: {c['file_path']}
EXCERPT:
{excerpt}
--- END CONTEXT
"""

    prompt_vars = {
        "lesson_id": lesson.get('lesson_id', 'L_Unknown'),
        "repo_id": repo_id,
        "title": lesson.get('title', 'N/A'),
        "objective": lesson.get('objective', ''),
        "quiz_hint": lesson.get('quiz_hint', ''),
        "contexts_text": contexts_text.strip()
    }

    return QUIZ_RAG_PROMPT_TEMPLATE.format(**prompt_vars)

def generate_quiz_for_lesson(lesson: Dict[str, Any], contexts: List[Dict[str, Any]], repo_id: str) -> tuple[Dict | None, List]:
    """
    Generates a structured quiz for a given lesson using RAG.
    Returns (quiz_data_object | None, unique_sources_used).
    """
    if not lesson or not contexts:
        print("❌ Missing lesson or contexts for quiz generation.")
        return None, []

    # Filter contexts to lesson sources
    lesson_source_ids = set(ls_ctx.get('id') for ls_ctx in lesson.get("sources_full", []))
    if not lesson_source_ids:
        print(f"⚠️ Warning: Lesson {lesson.get('lesson_id','N/A')} has no sources_full. Using all contexts.")
        relevant_contexts = contexts[:8]
    else:
        relevant_contexts = [ctx for ctx in contexts if ctx.get('id') in lesson_source_ids][:8]
        if not relevant_contexts:
            print(f"❌ Error: No lesson sources found for {lesson.get('lesson_id','N/A')}")
            return None, []

    # Build prompt and source map
    prompt = build_quiz_prompt(lesson, relevant_contexts, repo_id)
    source_map = {ctx.get('id'): ctx for ctx in relevant_contexts}

    print(f"\n🎲 Generating Quiz")
    print(f"Lesson: {lesson.get('title', 'N/A')}")
    print(f"Using {len(relevant_contexts)} contexts")

    # LLM call with retry logic
    MAX_JSON_RETRIES = 1
    for attempt in range(MAX_JSON_RETRIES + 1):
        print(f"\n🤖 Attempt {attempt + 1} of {MAX_JSON_RETRIES + 1}")
        raw_response = llm_client.get_gemini_response(prompt, temperature=0.15)

        try:
            if not raw_response or raw_response.startswith("Error:"):
                raise ValueError(f"LLM Error: {raw_response}")

            # Parse JSON
            cleaned_response = raw_response.strip()
            if cleaned_response.startswith("```json"): 
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            
            if not cleaned_response.startswith("{"):
                raise ValueError("Response is not a JSON object")
            
            quiz_data = json.loads(cleaned_response.strip())

            # Validate structure
            print("\n🔍 Validating quiz data")
            if not isinstance(quiz_data, dict):
                raise ValueError("Response is not a JSON object")
            
            questions = quiz_data.get("questions", [])
            if not isinstance(questions, list):
                raise ValueError("Questions must be a list")
            
            if len(questions) != 3:
                print(f"⚠️ Warning: Got {len(questions)} questions instead of 3")

            # Validate each question
            for q in questions:
                qid = q.get('qid', 'Unknown')
                if not all(k in q for k in ["qid", "type", "question", "choices", "explanation", "evidence"]):
                    raise ValueError(f"Question {qid} missing required fields")
                
                choices = q.get("choices", [])
                if len(choices) != 4:
                    raise ValueError(f"Question {qid} must have exactly 4 choices")
                
                correct_count = sum(1 for c in choices if c.get("correct"))
                if correct_count != 1:
                    raise ValueError(f"Question {qid} must have exactly one correct answer")

            # Attach context objects
            print("\n📎 Attaching source contexts")
            all_sources = []
            for q in questions:
                evidence_full = [
                    source_map[src] 
                    for src in q.get("evidence", []) 
                    if src in source_map
                ]
                q["evidence_full"] = evidence_full
                all_sources.extend(evidence_full)

            unique_sources = list({ctx['id']: ctx for ctx in all_sources}.values())
            print(f"✅ Generated {len(questions)} questions using {len(unique_sources)} sources")
            return quiz_data, unique_sources

        except (json.JSONDecodeError, ValueError) as e:
            print(f"❌ Error parsing quiz response (Attempt {attempt + 1}): {str(e)}")
            if attempt < MAX_JSON_RETRIES:
                print("⏳ Retrying with stricter JSON instruction...")
                prompt += "\n\nIMPORTANT: Return ONLY the valid JSON object."
                time.sleep(2)
            else:
                print("❌ Max retries reached. Failed to generate valid quiz.")
                return None, relevant_contexts

    return None, relevant_contexts