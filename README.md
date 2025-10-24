# RepoRoverAI 🤖

An AI web app that converts any GitHub repository into an interactive learning experience, featuring guided lessons, code explainers, visualizations, and quizzes.

This is an entry for the Halothon 2025 hackathon.

## Features

* **Guided Lessons:** Generates structured lessons based on repository context (READMEs, manifests).
* **Explain-on-Click / Q&A:**
    * Select any processed file.
    * Leave the question blank to get an AI-generated summary, key points, test suggestion, and example usage based on relevant code chunks (using top-8 contexts).
    * Ask a specific question about the file to get a targeted answer based on the most relevant code chunks (using top-6 contexts).
    * All explanations and answers include **source provenance** (file paths, line numbers/sections, context IDs).
    * **Smart Caching:** Explanation results are cached based on input arguments for instant retrieval on repeat queries.
    * **Confidence Scoring:** Explanations include confidence levels based on:
        * Number of valid sources cited (3+ = high, 2 = medium, 1 = low)
        * Mix of code and documentation sources (both = higher confidence)
    * Explanation logs saved to `data/explain_logs/` for reproducibility.
* **Auto-Graded Quizzes:** Generates multiple-choice quizzes based on lesson content, provides instant feedback, hints for incorrect answers, and explanations.

## Tech Stack

-   **UI:** Streamlit
-   **LLM:** Gemini API
-   **Code Fetching:** GitHub REST API

## Key Design Choices

* **Reproducibility:** All LLM interactions are logged with full context and timestamps
* **Source Validation:** Strict validation of cited sources against provided context
* **Smart Caching:** Uses Streamlit's `@st.cache_data` for efficient response times
* **Confidence Metrics:** Clear indication of explanation reliability based on sources

(Note: Understandability and distractor plausibility are primarily driven by the LLM based on the prompt constraints.)