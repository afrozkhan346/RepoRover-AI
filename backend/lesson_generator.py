from . import llm_client

LESSON_PROMPT_TEMPLATE = """
You are RepoRoverAI, an expert developer and teacher. Your goal is to create a guided lesson plan for a developer new to a GitHub repository.

Based on the repository's README file provided below, generate a high-level "Guided Lesson" to help a new developer understand the project's purpose, structure, and how to get started.

The lesson should include:
1.  **Project Goal:** A one-sentence summary of what this project does.
2.  **Key Technologies:** A bulleted list of the main technologies used (if mentioned).
3.  **"How to Start" Guide:** A 3-step guide on how to set up and run the project locally.
4.  **"Where to Look" Tour:** Suggest 2-3 key files or folders from the repo that a new developer should explore first to understand the core logic.

Here is the README content:
---
{content}
---
"""

EXPLANATION_PROMPT_TEMPLATE = """
You are RepoRoverAI, an expert code explainer. A developer has asked for help understanding a file from a repository.

Below is the content of a code file. Please provide a clear, concise explanation.

Your explanation must include:
1.  **File Purpose:** What is the single most important job of this file?
2.  **Key Functions/Classes:** A bulleted list of the 1-3 most important functions or classes in this file and what they do.
3.  **Dependencies:** What other parts of the project (or external libraries) does this file seem to depend on?

Explain it simply, as if you're talking to a junior developer.

Here is the file content:
---
{content}
---
"""

def generate_lesson(content):
    """
    Generates a guided lesson based on README or file list.
    """
    prompt = LESSON_PROMPT_TEMPLATE.format(content=content)
    # Using stream_gemini_response for a better UX
    return llm_client.stream_gemini_response(prompt)

def generate_explanation(content):
    """
    Generates an explanation for a single file's content.
    """
    prompt = EXPLANATION_PROMPT_TEMPLATE.format(content=content)
    # Using stream_gemini_response for a better UX
    return llm_client.stream_gemini_response(prompt)