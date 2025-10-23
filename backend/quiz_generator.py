from . import llm_client

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

def generate_quiz(content):
    """
    Generates a quiz based on the provided content (e.g., README).
    """
    prompt = QUIZ_PROMPT_TEMPLATE.format(content=content)
    return llm_client.stream_gemini_response(prompt)