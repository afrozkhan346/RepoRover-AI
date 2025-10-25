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

# --- CORRECTED Grading Function ---
def grade_mcq_responses(quiz_data: Dict[str, Any], responses: Dict[str, str]) -> Dict[str, Any]:
    """
    Grades user responses (full option strings like "A. Text") against the generated MCQ quiz.
    Compares only the text part of the user's selection to the correct answer text.
    """
    questions = quiz_data.get("questions", [])
    total = len(questions)
    correct_count = 0
    results = []

    if total == 0:
        return {"score": 0, "total": 0, "results": [], "percent": 0.0}

    for q in questions:
        qid = q.get('qid', 'Unknown')
        # User response is the full option string like "A. Some text" or None
        user_selected_option_string = responses.get(qid)
        user_selected_text = None
        if user_selected_option_string and '. ' in user_selected_option_string:
             # Extract text after "A. "
             user_selected_text = user_selected_option_string.split('. ', 1)[1].strip()
        elif user_selected_option_string: # Handle case where maybe label wasn't included?
             user_selected_text = user_selected_option_string.strip()

        correct_choice_label = None
        correct_choice_text = None
        is_correct = False

        # Find the correct choice text and label
        choices_list = q.get("choices", [])
        if isinstance(choices_list, list):
             for choice_dict in choices_list:
                 # Check if the dictionary structure is {"label": "A", "text": "...", "correct": True/False}
                 if "label" in choice_dict and "text" in choice_dict and "correct" in choice_dict:
                      if choice_dict.get('correct') is True:
                           correct_choice_label = choice_dict.get("label")
                           correct_choice_text = choice_dict.get("text", "").strip()
                           # --- Perform Comparison ---
                           if user_selected_text is not None and user_selected_text == correct_choice_text:
                                is_correct = True
                           break # Found the correct answer

        if is_correct:
            correct_count += 1

        results.append({
            "qid": qid,
            "question": q.get('question'),
            "user_choice": user_selected_option_string, # Store the full string user selected
            "correct_choice": f"{correct_choice_label}. {correct_choice_text}" if correct_choice_label else correct_choice_text, # Store formatted correct choice
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