RepoRoverAI 🤖

An AI web app that converts any GitHub repository into an interactive learning experience, featuring guided lessons, code explainers, visualizations, and quizzes.

This is an entry for the Halothon 2025 hackathon.

Features (Planned)

[ ] Analyze entire repo structure.

[ ] Generate step-by-step guided lessons.

[ ] Explain individual code files or functions on demand.

[ ] Visualize code dependencies and architecture.

[ ] Auto-generate quizzes to test understanding.

Tech Stack

UI: Streamlit

LLM: Gemini API

Code Fetching: GitHub REST API

Local Setup

Clone the repo.

Create a virtual environment:

python -m venv venv
source venv/Scripts/activate  # Or venv/bin/activate on Mac/Linux


Install requirements:

pip install -r requirements.txt


Create a .env file in the root directory and add your API key:

GEMINI_API_KEY="YOUR_API_KEY_HERE"


Run the app:

streamlit run app/streamlit_app.py
