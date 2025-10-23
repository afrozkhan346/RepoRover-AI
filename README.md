# RepoRoverAI 🤖

An AI web app that converts any GitHub repository into an interactive learning experience, featuring guided lessons, code explainers, visualizations, and quizzes.

This is an entry for the Halothon 2025 hackathon.

## Features (Planned)

-   [ ] Analyze entire repo structure.
-   [ ] Generate step-by-step guided lessons.
-   [ ] Explain individual code files or functions on demand.
-   [ ] Visualize code dependencies and architecture.
-   [ ] Auto-generate quizzes to test understanding.

## Tech Stack

-   **UI:** Streamlit
-   **LLM:** Gemini API
-   **Code Fetching:** GitHub REST API

## Key Design Choices

-   **GitHub REST API over `git clone`:** We are using the GitHub API directly (specifically the `/git/trees` endpoint) instead of cloning the repository.
    -   **Serverless-Friendly:** This avoids the need to install `git` on the host or manage temporary directories, making it perfect for Streamlit Cloud.
    -   **Faster & Lighter:** It's a lightweight HTTP request, avoiding disk I/O and the overhead of a full clone.
    -   **Rate Limits:** It works for public repos without auth, and using an optional `GITHUB_TOKEN` easily bypasses the lower anonymous rate limits.

## Local Setup

1.  Clone the repo.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/Scripts/activate  # Or venv/bin/activate on Mac/Linux
    ```
3.  Install requirements:
    ```bash
    pip install -r requirements.txt
    ```
4.  Create a `.env` file in the root directory and add your API key:
    ```
    GEMINI_API_KEY="YOUR_API_KEY_HERE"
    ```
5.  Run the app:
    ```bash
    streamlit run app/streamlit_app.py
    ```

## 🧪 Quiz Quality Metrics (Self-Assessment)

To ensure the generated quizzes are effective, we ran basic quality checks:

* Questions Generated per Lesson: The prompt explicitly requests 3 MCQs per lesson, which the LLM consistently provides.
* Source Coverage: All generated question explanations and evidence fields are validated to ensure they reference CONTEXT_IDs that were provided in the prompt. (Target: 100%.)
* Average Explanation Length: Explanations typically fall within the target range of 20–60 words, providing concise reasoning.
* Average Correctness (Internal Pilot): In a small internal pilot test (e.g., 1 reviewer attempting quizzes for 2-3 lessons), the average score was approximately [Your Score Here, e.g., 80-90]%. This suggests the questions are generally well-grounded in the context.

(Note: Understandability and distractor plausibility are primarily driven by the LLM based on the prompt constraints.)