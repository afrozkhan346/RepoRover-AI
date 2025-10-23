from . import llm_client
import json
import streamlit as st
import time
from typing import List, Dict, Any
import os
import datetime

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
  ],
  "warnings": []
}}

CONSTRAINTS:
- Use only facts from CONTEXTS. Do not invent file paths or facts.
- Each question must be clear and solvable by reading the supplied contexts.
- Distractors must be plausible (not obviously wrong).
- Explanation must reference at least one CONTEXT_ID.
- Return valid JSON only.
- If you cannot generate 3 distinct MCQs from the contexts, return this exact structure instead:
  {{
    "lesson_id": "{lesson_id}",
    "quiz_id": "{repo_id}-{lesson_id}",
    "is_practice_quiz": true,
    "warnings": ["Insufficient context to generate full MCQ quiz."],
    "questions": [
      {{
        "qid": "P1",
        "type": "practice",
        "question": "Review the repository's main README.md file. What is the primary purpose or license of this project?",
        "choices": [],
        "explanation": "Refer to the main README for project details.",
        "evidence": []
      }}
    ]
  }}

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

def validate_quiz_question(question: Dict[str, Any], source_map: Dict[str, Any]) -> List[str]:
    """Validates a single quiz question for quality and anti-hallucination."""
    errors = []
    
    # Skip validation for practice questions
    if question.get("type") == "practice":
        return errors

    # Regular MCQ validation
    evidence_ids = question.get("evidence", [])
    if not evidence_ids:
        errors.append(f"Question {question.get('qid', 'Unknown')} has no evidence citations")
    else:
        invalid_sources = [src_id for src_id in evidence_ids if src_id not in source_map]
        if invalid_sources:
            errors.append(f"Question cites non-existent sources: {', '.join(invalid_sources)}")

    choices = question.get("choices", [])
    correct_count = sum(1 for c in choices if c.get("correct"))
    if correct_count != 1:
        errors.append(f"Question has {correct_count} correct answers (must be exactly 1)")

    question_text = question.get("question", "")
    if len(question_text) > 160:
        errors.append(f"Question text too long: {len(question_text)} chars (max 160)")
    
    for choice in choices:
        choice_text = choice.get("text", "")
        if len(choice_text) > 100:
            errors.append(f"Choice too long: {len(choice_text)} chars (max 100)")

    return errors

def generate_quiz_for_lesson(lesson: Dict[str, Any], contexts: List[Dict[str, Any]], repo_id: str) -> tuple[Dict | None, List]:
    """Generates a structured quiz with enhanced quality checks and logging."""
    if not lesson or not contexts:
        print("❌ Missing lesson or contexts for quiz generation.")
        return None, []

    # Setup logging data structure
    lesson_id = lesson.get('lesson_id', 'L_Unknown')
    quiz_id = f"{repo_id.replace('/', '_')}-{lesson_id}"
    log_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "quiz_id": quiz_id,
        "lesson_id": lesson_id,
        "repo_id": repo_id,
        "lesson_title": lesson.get('title', 'Untitled'),
        "prompt": None,  # Will be set after building
        "context_ids_used": [],
        "llm_attempts": [],
        "validation_errors": [],
        "final_quiz_data": None,
        "status": "started"
    }

    # Ensure data directory exists
    log_dir = os.path.join("data", "quiz_logs")
    os.makedirs(log_dir, exist_ok=True)
    log_filename = os.path.join(log_dir, f"quiz_log_{quiz_id}_{datetime.datetime.now():%Y%m%d_%H%M%S}.json")

    try:
        # Filter contexts to lesson sources
        lesson_source_ids = set(ls_ctx.get('id') for ls_ctx in lesson.get("sources_full", []))
        if not lesson_source_ids:
            print(f"⚠️ Warning: Lesson {lesson_id} has no sources_full. Using all contexts.")
            relevant_contexts = contexts[:8]
        else:
            relevant_contexts = [ctx for ctx in contexts if ctx.get('id') in lesson_source_ids][:8]
            if not relevant_contexts:
                log_data["status"] = "error_no_contexts"
                log_data["validation_errors"].append("No lesson sources found in context list")
                return None, []

        # Build prompt and source map
        prompt = build_quiz_prompt(lesson, relevant_contexts, repo_id)
        source_map = {ctx.get('id'): ctx for ctx in relevant_contexts}
        
        # Update log data with prompt info
        log_data["prompt"] = prompt
        log_data["context_ids_used"] = list(source_map.keys())

        print(f"\n🎲 Generating Quiz")
        print(f"Lesson: {lesson.get('title', 'N/A')}")
        print(f"Using {len(relevant_contexts)} contexts")

        # LLM call with retries
        MAX_JSON_RETRIES = 2
        for attempt in range(MAX_JSON_RETRIES + 1):
            attempt_data = {
                "attempt_number": attempt + 1,
                "timestamp": datetime.datetime.now().isoformat(),
                "raw_response": None,
                "cleaned_response": None,
                "validation_errors": [],
                "status": "pending"
            }

            print(f"\n🤖 Attempt {attempt + 1} of {MAX_JSON_RETRIES + 1}")
            raw_response = llm_client.get_gemini_response(prompt, temperature=0.15)
            attempt_data["raw_response"] = raw_response

            try:
                if not raw_response or raw_response.startswith("Error:"):
                    raise ValueError(f"LLM Error: {raw_response}")

                # Clean and parse JSON
                cleaned_response = raw_response.strip()
                if cleaned_response.startswith("```json"): 
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]
                
                attempt_data["cleaned_response"] = cleaned_response
                quiz_data = json.loads(cleaned_response.strip())

                # Check for practice quiz
                is_practice_quiz = quiz_data.get("is_practice_quiz", False)
                if is_practice_quiz:
                    print("ℹ️ LLM indicated insufficient context and returned a practice quiz.")
                    questions = quiz_data.get("questions", [])
                    if len(questions) != 1 or questions[0].get("type") != "practice":
                        raise ValueError("Invalid practice quiz format")
                    return quiz_data, relevant_contexts

                # Regular quiz validation
                validation_errors = []
                questions = quiz_data.get("questions", [])
                
                if not isinstance(quiz_data, dict):
                    validation_errors.append("Response is not a JSON object")
                if not isinstance(questions, list) or len(questions) != 3:
                    validation_errors.append(f"Must have exactly 3 questions, got {len(questions)}")

                # Validate each question
                for q in questions:
                    q_errors = validate_quiz_question(q, source_map)
                    validation_errors.extend([f"Q{q.get('qid', '?')}: {err}" for err in q_errors])

                attempt_data["validation_errors"] = validation_errors
                log_data["validation_errors"].extend(validation_errors)

                if validation_errors:
                    if attempt < MAX_JSON_RETRIES:
                        attempt_data["status"] = "failed_validation"
                        raise ValueError("Regenerating due to quality issues")
                    else:
                        log_data["status"] = "failed_final_validation"
                        return None, relevant_contexts

                # Attach context objects
                all_sources = []
                for q in questions:
                    evidence_full = [
                        source_map[src] 
                        for src in q.get("evidence", []) 
                        if src in source_map
                    ]
                    q["evidence_full"] = evidence_full
                    all_sources.extend(evidence_full)

                # Success! Update log data
                attempt_data["status"] = "success"
                log_data["status"] = "success"
                log_data["final_quiz_data"] = quiz_data
                unique_sources = list({ctx['id']: ctx for ctx in all_sources}.values())

                # Save final log
                log_data["llm_attempts"].append(attempt_data)
                with open(log_filename, 'w', encoding='utf-8') as f:
                    json.dump(log_data, f, indent=2, ensure_ascii=False)

                print(f"✅ Generated {len(questions)} questions using {len(unique_sources)} sources")
                print(f"📝 Log saved to: {log_filename}")
                return quiz_data, unique_sources

            except Exception as e:
                attempt_data["status"] = "error"
                attempt_data["validation_errors"].append(str(e))
                log_data["llm_attempts"].append(attempt_data)
                
                if attempt < MAX_JSON_RETRIES:
                    print(f"❌ Error: {str(e)}")
                    print("⏳ Retrying with stricter quality requirements...")
                    prompt += "\n\nIMPORTANT: Previous attempt had quality issues. Ensure:\n"
                    prompt += "1. Questions ≤ 160 chars\n"
                    prompt += "2. Choices ≤ 100 chars\n"
                    prompt += "3. Evidence IDs match provided contexts\n"
                    prompt += "4. Exactly one correct answer per question"
                    time.sleep(2)
                else:
                    log_data["status"] = "failed_all_attempts"
                    # Save final failure log
                    with open(log_filename, 'w', encoding='utf-8') as f:
                        json.dump(log_data, f, indent=2, ensure_ascii=False)
                    print(f"❌ Max retries reached. Log saved to: {log_filename}")
                    return None, relevant_contexts

    except Exception as e:
        log_data["status"] = "unexpected_error"
        log_data["validation_errors"].append(str(e))
        with open(log_filename, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        print(f"❌ Unexpected error: {str(e)}")
        return None, relevant_contexts

    return None, relevant_contexts