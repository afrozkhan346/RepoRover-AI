# backend/quiz_eval.py
from typing import Dict, List, Any
from . import llm_client
import json
import time

# --- Hint Generation Prompt ---
HINT_PROMPT_TEMPLATE = """
SYSTEM:
You are a friendly tutor chatbot. A student answered a multiple-choice question incorrectly.
Your goal is to provide a helpful hint without giving away the answer directly, and then a clear explanation referencing the source material.

INPUT:
- Question: "{question}"
- Correct Answer Text: "{correct_text}"
- Evidence Contexts (Excerpts relevant to the question):
---
{context_str}
---

TASK:
Using *only* the provided Evidence Contexts:
1. Generate a 1-sentence hint that gently guides the student toward the correct concept or relevant part of the context, but *does not* reveal the correct answer choice.
2. Generate a 2-3 sentence explanation detailing why "{correct_text}" is the correct answer, explicitly citing the CONTEXT_ID(s) from the evidence used.

Return *only* a valid JSON object matching this schema exactly:
{{
  "hint": "string (One sentence hint, no spoilers)",
  "explanation": "string (2-3 sentences explaining the correct answer, citing CONTEXT_ID(s))",
  "sources": ["CONTEXT_ID", "..."]
}}

CONSTRAINT:
- Base everything strictly on the Evidence Contexts.
- The hint must *not* reveal the correct answer text or letter.
- Cite CONTEXT_ID(s) accurately in the explanation and sources.
- Return valid JSON only.
"""

def generate_hint_feedback(question_details: Dict[str, Any], contexts: List[Dict[str, Any]]) -> Dict | None:
    """Generates a hint and explanation for an incorrectly answered question."""
    if not question_details or not contexts:
        print("❌ Missing question details or contexts for hint generation.")
        return None

    # Find correct answer text
    correct_choice_text = None
    for choice in question_details.get("choices", []):
        if choice.get("correct"):
            correct_choice_text = choice.get("text")
            break

    if not correct_choice_text:
        print("❌ Could not find correct answer text")
        return None

    # Prepare context string
    context_str = ""
    source_map = {}
    for ctx in contexts[:3]:  # Limit to 3 most relevant contexts
        context_id = ctx.get('id', 'unknown')
        source_map[context_id] = ctx
        excerpt = ctx.get('excerpt', ctx.get('content', '')[:300])
        context_str += f"""--- CONTEXT_ID: {context_id}
FILE: {ctx['file_path']}
EXCERPT:
{excerpt}
--- END CONTEXT
"""

    # Generate hint
    prompt = HINT_PROMPT_TEMPLATE.format(
        question=question_details.get("question", ""),
        correct_text=correct_choice_text,
        context_str=context_str.strip()
    )

    MAX_RETRIES = 2
    for attempt in range(MAX_RETRIES):
        try:
            print(f"\n💡 Generating hint feedback (Attempt {attempt + 1}/{MAX_RETRIES})...")
            response = llm_client.get_gemini_response(prompt, temperature=0.25)
            
            # Check for error responses or empty content
            if not response or not response.strip():
                raise ValueError("Empty response from LLM")
            if response.startswith("Error:"):
                raise ValueError(f"LLM Error: {response}")

            # Clean and parse JSON
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"): 
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            if not cleaned_response.startswith("{") or not cleaned_response.endswith("}"):
                raise ValueError("Response is not a valid JSON object")

            # Parse and validate
            hint_data = json.loads(cleaned_response)
            if not all(k in hint_data for k in ["hint", "explanation", "sources"]):
                raise ValueError("Missing required fields in hint response")

            # Attach full context objects
            hint_data["sources_full"] = [
                source_map[src_id] 
                for src_id in hint_data.get("sources", [])
                if src_id in source_map
            ]

            print("✅ Successfully generated hint")
            return hint_data

        except (json.JSONDecodeError, ValueError) as e:
            print(f"❌ Error in attempt {attempt + 1}: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                print("⏳ Retrying after delay...")
                time.sleep(2)  # Wait 2 seconds before retry
            else:
                print("❌ Max retries reached for hint generation.")
                return None
        except Exception as e:
            print(f"❌ Unexpected error generating hint: {str(e)}")
            return None

    return None

def grade_mcq_responses(quiz_data: Dict[str, Any], responses: Dict[str, str]) -> Dict[str, Any]:
    """Grades user responses against the generated MCQ quiz."""
    questions = quiz_data.get("questions", [])
    total = len(questions)
    correct_count = 0
    results = []

    if total == 0:
        return {"score": 0, "total": 0, "results": [], "percent": 0.0}

    for q in questions:
        qid = q.get('qid', 'Unknown')
        user_choice_text = responses.get(qid, "").strip() if responses.get(qid) else None
        
        # Find correct choice
        correct_choice = next(
            (c for c in q.get("choices", []) if c.get("correct")),
            None
        )
        correct_choice_text = correct_choice.get("text", "").strip() if correct_choice else None
        
        # Compare stripped versions
        is_correct = False
        if user_choice_text and correct_choice_text:
            # Extract just the answer text after the label (e.g., "A. Some text" -> "Some text")
            user_answer = user_choice_text.split(".", 1)[-1].strip() if "." in user_choice_text else user_choice_text
            correct_answer = correct_choice_text.split(".", 1)[-1].strip() if "." in correct_choice_text else correct_choice_text
            is_correct = user_answer == correct_answer
        
        if is_correct:
            correct_count += 1

        results.append({
            "qid": qid,
            "question": q.get('question'),
            "user_choice": user_choice_text,
            "correct_choice": correct_choice_text,
            "correct": is_correct,
            "explanation": q.get('explanation'),
            "evidence": q.get('evidence', [])
        })

    score = correct_count
    percent = (score / total * 100) if total > 0 else 0.0
    return {
        "score": score, 
        "total": total, 
        "results": results, 
        "percent": percent
    }