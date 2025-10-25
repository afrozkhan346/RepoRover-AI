from . import llm_client
import json
import streamlit as st # Used for @st.cache_data, though not strictly needed here
import time
from typing import List, Dict, Any, Tuple # Added Tuple
import os
import datetime
import re # Added for validation

# --- RAG Quiz Prompt Template ---
# Note: Double curly braces {{ and }} are used to escape braces for .format()
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

```json
{{
  "lesson_id": "{lesson_id}",
  "quiz_id": "{repo_id}-{lesson_id}",
  "questions": [
    {{
      "qid": "Q1",
      "type": "mcq",
      "question": "string (Question based *only* on context, <= 160 chars)",
      "choices": [
        {{"label": "A", "text": "string (Plausible answer A, <= 100 chars)", "correct": true/false}},
        {{"label": "B", "text": "string (Plausible answer B, <= 100 chars)", "correct": true/false}},
        {{"label": "C", "text": "string (Plausible answer C, <= 100 chars)", "correct": true/false}},
        {{"label": "D", "text": "string (Plausible answer D, <= 100 chars)", "correct": true/false}}
        // Exactly one choice must have "correct": true
      ],
      "explanation": "string (Short explanation for the correct answer, citing the CONTEXT_ID(s) used)",
      "evidence": ["CONTEXT_ID", "..."] // List all CONTEXT_IDs used for this question & explanation.
    }},
    {{
      "qid": "Q2",
      "type": "mcq",
      "question": "string (Question based *only* on context, <= 160 chars)",
      "choices": [
        {{"label": "A", "text": "string (Plausible answer A, <= 100 chars)", "correct": true/false}},
        {{"label": "B", "text": "string (Plausible answer B, <= 100 chars)", "correct": true/false}},
        {{"label": "C", "text": "string (Plausible answer C, <= 100 chars)", "correct": true/false}},
        {{"label": "D", "text": "string (Plausible answer D, <= 100 chars)", "correct": true/false}}
      ],
      "explanation": "string (Short explanation, citing CONTEXT_ID(s))",
      "evidence": ["CONTEXT_ID", "..."]
    }},
    {{
      "qid": "Q3",
      "type": "mcq",
      "question": "string (Question based *only* on context, <= 160 chars)",
      "choices": [
        {{"label": "A", "text": "string (Plausible answer A, <= 100 chars)", "correct": true/false}},
        {{"label": "B", "text": "string (Plausible answer B, <= 100 chars)", "correct": true/false}},
        {{"label": "C", "text": "string (Plausible answer C, <= 100 chars)", "correct": true/false}},
        {{"label": "D", "text": "string (Plausible answer D, <= 100 chars)", "correct": true/false}}
      ],
      "explanation": "string (Short explanation, citing CONTEXT_ID(s))",
      "evidence": ["CONTEXT_ID", "..."]
    }}
  ],
  "warnings": [] // Optional strings for issues
}}
```

CONSTRAINTS:

  - Use only facts from CONTEXTS. Do not invent file paths or facts.
  - Each question must be clear and solvable by reading the supplied contexts.
  - Distractors must be plausible (not obviously wrong).
  - Explanation must reference at least one CONTEXT_ID.
  - Adhere to character limits specified in the schema.
  - Return valid JSON only (starting with `{{` and ending with `}}`).
  - If you cannot generate 3 distinct MCQs from the contexts, return this exact structure instead:

```json
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
```

Settings: temperature 0.15 for stable output.
END.
"""

def build_quiz_prompt(lesson: Dict[str, Any], contexts: List[Dict[str, Any]], repo_id: str) -> Tuple[str, Dict[str, Any]]:
    """Builds the prompt string for the LLM based on the lesson and contexts."""
    contexts_text = ""
    source_map = {} # Map CONTEXT_ID back to full context object
    MAX_CONTEXT_LENGTH = 10000 # Limit context size for prompt

    print(f"Building quiz prompt, received {len(contexts)} relevant contexts...")
    for c in contexts[:8]: # Limit to top 8 relevant contexts
        context_id = c.get('id', 'N/A')
        excerpt = c.get('excerpt', c.get('content', '')[:300]).strip()
        if not excerpt: # Skip contexts with no usable text
            print(f"Skipping context {context_id} (empty excerpt)")
            continue

        source_map[context_id] = c # Add to map
        contexts_text += f"""--- CONTEXT_ID: {context_id}
FILE: {c['file_path']}
EXCERPT:
{excerpt}
--- END CONTEXT
"""
        if len(contexts_text) > MAX_CONTEXT_LENGTH:
             print("Reached max context length for quiz prompt, stopping.")
             break

    prompt_vars = {
        "lesson_id": lesson.get('lesson_id', 'L_Unknown'),
        "repo_id": repo_id,
        "title": lesson.get('title', 'N/A'),
        "objective": lesson.get('objective', ''),
        "quiz_hint": lesson.get('quiz_hint', ''),
        "contexts_text": contexts_text.strip()
    }

    prompt = QUIZ_RAG_PROMPT_TEMPLATE.format(**prompt_vars)
    return prompt, source_map

def validate_quiz_question(question: Dict[str, Any], source_map: Dict[str, Any]) -> List[str]:
    """Validates a single quiz question for quality and anti-hallucination."""
    errors = []
    qid = question.get('qid', 'Unknown')

    # Skip validation for practice questions
    if question.get("type") == "practice":
        return errors

    # Regular MCQ validation
    evidence_ids = question.get("evidence", [])
    if not evidence_ids:
        errors.append(f"Question {qid} has no evidence citations")
    else:
        invalid_sources = [src_id for src_id in evidence_ids if src_id not in source_map]
        if invalid_sources:
            errors.append(f"Question {qid} cites non-existent sources: {', '.join(invalid_sources)}")

    choices = question.get("choices", [])
    if not isinstance(choices, list) or len(choices) != 4:
         errors.append(f"Question {qid} 'choices' is not a list of 4.")
    else:
        correct_count = sum(1 for c in choices if c.get("correct") is True)
        if correct_count != 1:
            errors.append(f"Question {qid} has {correct_count} correct answers (must be exactly 1)")

    question_text = question.get("question", "")
    if not question_text:
         errors.append(f"Question {qid} is empty.")
    elif len(question_text) > 160: # Check length
        errors.append(f"Question {qid} text too long: {len(question_text)} chars (max 160)")

    for choice in choices:
        choice_text = choice.get("text", "")
        if not choice_text:
             errors.append(f"Question {qid} has an empty choice text (Label: {choice.get('label','?')}).")
        elif len(choice_text) > 100: # Check length
            errors.append(f"Question {qid} choice '{choice_text[:20]}...' too long: {len(choice_text)} chars (max 100)")

    return errors

@st.cache_data(ttl=3600, show_spinner=False)
def generate_quiz_for_lesson(lesson: Dict[str, Any], contexts: List[Dict[str, Any]], repo_id: str) -> Tuple[Dict | None, List]:
    """Generates a structured quiz with enhanced quality checks."""
    if not lesson or not contexts:
        print("❌ Missing lesson or contexts for quiz generation.")
        return None, []

    lesson_id = lesson.get('lesson_id', 'L_Unknown')

    try:
        # Filter contexts to only those relevant to the lesson
        lesson_source_ids = set(ls_ctx.get('id') for ls_ctx in lesson.get("sources_full", []))
        if not lesson_source_ids:
             print(f"⚠️ Warning: Lesson {lesson_id} has no sources_full. Using all provided contexts.")
             relevant_contexts = contexts[:8] # Limit to 8
        else:
            relevant_contexts = [ctx for ctx in contexts if ctx.get('id') in lesson_source_ids][:8] # Filter and limit
            if not relevant_contexts:
                 raise Exception(f"No lesson sources found in context list for lesson {lesson_id}")

        # Build prompt and source map
        prompt, source_map = build_quiz_prompt(lesson, relevant_contexts, repo_id)
        print(f"\n🎲 Generating Quiz for '{lesson.get('title', 'N/A')}', using {len(relevant_contexts)} contexts")

        # LLM call with retries
        MAX_JSON_RETRIES = 2 # Allow 2 retries (3 attempts total)
        for attempt in range(MAX_JSON_RETRIES + 1):
            print(f"🤖 Attempt {attempt + 1} of {MAX_JSON_RETRIES + 1}")

            raw_response = llm_client.get_gemini_response(prompt, temperature=0.15)

            try:
                if not raw_response or raw_response.startswith("Error:"):
                    raise ValueError(f"LLM Error: {raw_response}")

                # Clean and parse JSON
                cleaned_response = raw_response.strip()
                if cleaned_response.startswith("```json"): cleaned_response = cleaned_response[7:]
                if cleaned_response.endswith("```"): cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()

                if not cleaned_response.startswith("{") or not cleaned_response.endswith("}"):
                    raise ValueError("Response is not a valid JSON object (missing braces)")

                quiz_data = json.loads(cleaned_response)

                # Check for practice quiz fallback
                is_practice_quiz = quiz_data.get("is_practice_quiz", False)
                if is_practice_quiz:
                    print("ℹ️ LLM returned a practice quiz (insufficient context).")
                    questions = quiz_data.get("questions", [])
                    if len(questions) != 1 or questions[0].get("type") != "practice":
                        raise ValueError("Invalid practice quiz format returned")
                    print("📝 Practice quiz generated.")
                    return quiz_data, relevant_contexts # Return practice quiz

                # Regular quiz validation
                validation_errors = []
                questions = quiz_data.get("questions", [])
                if not isinstance(quiz_data, dict) or "questions" not in quiz_data:
                     validation_errors.append("Response is not a dict or missing 'questions' key.")
                if not isinstance(questions, list) or (len(questions) != 3 and not is_practice_quiz):
                     validation_errors.append(f"Must have exactly 3 questions, got {len(questions)}")

                for q in questions:
                    q_errors = validate_quiz_question(q, source_map)
                    validation_errors.extend([f"Q{q.get('qid', '?')}: {err}" for err in q_errors])

                if validation_errors:
                    raise ValueError(f"Validation failed: {'; '.join(validation_errors)}")

                # Attach full context objects
                all_sources = []
                for q in questions:
                    evidence_full = [source_map[src] for src in q.get("evidence", []) if src in source_map]
                    q["evidence_full"] = evidence_full
                    all_sources.extend(evidence_full)

                # Success!
                unique_sources = list({ctx['id']: ctx for ctx in all_sources}.values())

                print(f"✅ Generated {len(questions)} questions using {len(unique_sources)} sources")
                return quiz_data, unique_sources # Success

            except (json.JSONDecodeError, ValueError) as e:
                print(f"❌ Error: {str(e)}")
                if attempt < MAX_JSON_RETRIES:
                    print("⏳ Retrying with stricter quality requirements...")
                    prompt += "\n\nIMPORTANT: Previous attempt failed parsing or validation. Respond ONLY with valid JSON exactly matching the schema."
                    time.sleep(2) # Wait before retry
                else:
                     print("❌ Max retries reached.")
                     return None, relevant_contexts # Final failure

    except Exception as e:
        print(f"❌ Unexpected error in quiz generation: {str(e)}")
        return None, [] # Return empty list if contexts weren't set

    # Should not be reached
    return None, []