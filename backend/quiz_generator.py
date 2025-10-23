from . import llm_client
import json
import streamlit as st

QUIZ_PROMPT_TEMPLATE = """
You are RepoRoverAI, an expert teacher. Your goal is to create a short quiz to test a developer's understanding of a project.

Based on the project's README file provided below, generate a 3-question multiple-choice quiz.
-   Each question should be relevant to the project's purpose or setup.
-   Provide 3 possible answers (A, B, C) for each question.
-   Indicate the correct answer clearly for each question.

Here is the README content:
---
{content}
---

Format the quiz clearly using Markdown.
Example:
**1. What is the primary goal of this project?**
A) To manage databases
B) To build user interfaces
C) To analyze data
*Correct Answer: C*
"""
# --- NEW RAG Quiz Prompt Template ---
QUIZ_RAG_PROMPT_TEMPLATE = """
SYSTEM:
You are RepoRoverQuizzer, an expert quiz generator for coding lessons. You create multiple-choice questions based *only* on provided context.

INPUT:
Lesson Title: "{lesson_title}"
Lesson Objective: "{lesson_objective}"
Quiz Hint: "{quiz_hint}"
Key Contexts (Excerpts from the repository):
---
{context_str}
---

TASK:
Produce exactly 3 multiple-choice questions related to the lesson title, objective, and hint, using *only* information found in the Key Contexts provided. Format the output as a JSON array of question objects. Each question object must follow this schema exactly:
```json
{{
  "id": "Q1", // Q1, Q2, Q3
  "question": "string (Question based on context)",
  "choices": [
    {{ "A": "string (Plausible answer A)", "correct": boolean }},
    {{ "B": "string (Plausible answer B)", "correct": boolean }},
    {{ "C": "string (Plausible answer C)", "correct": boolean }},
    {{ "D": "string (Plausible answer D)", "correct": boolean }}
    // Exactly one choice must have "correct": true
  ],
  "explanation": "string (Short explanation for the correct answer, citing the CONTEXT_ID(s) used, e.g., 'Based on CONTEXT_ID: repo/file.py:func:10:0, the correct answer is...')",
  "sources": ["CONTEXT_ID", "..."] // List all CONTEXT_IDs used for this question & explanation.
}}
"""
def generate_quiz(content):
    """
    Generates a quiz based on the provided content (e.g., README).
    """
    prompt = QUIZ_PROMPT_TEMPLATE.format(content=content)
    return llm_client.stream_gemini_response(prompt)