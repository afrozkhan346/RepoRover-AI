import streamlit as st
import sys
import os
import re

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import your backend modules
from backend import gh_fetch, llm_client, lesson_generator, quiz_generator, ingestion

def parse_github_url(url):
    # ... (existing function) ...
    pattern = r"https:\/\/github\.com\/([a-zA-Z0-9_-]+)\/([a-zA-Z0-9_-]+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1), match.group(2)
    return None, None

# --- Streamlit UI ---
st.set_page_config(page_title="RepoRoverAI", layout="wide")

st.title("RepoRoverAI 🤖")
st.write("Turn any GitHub repository into an interactive learning experience.")

# Initialize session state
if 'repo_data' not in st.session_state:
    st.session_state['repo_data'] = None
if 'repo_name' not in st.session_state:
    st.session_state['repo_name'] = None

repo_url = st.text_input(
    "Paste a public GitHub repository URL:",
    placeholder="https://github.com/streamlit/streamlit-demo"
)

if repo_url:
    owner, repo = parse_github_url(repo_url)
    
    if owner and repo:
        repo_name = f"{owner}/{repo}"
        
        # --- 1. Ingestion Button ---
        # Only show button if this repo isn't already loaded
        if st.session_state['repo_name'] != repo_name:
            if st.button(f"Analyze Repository: {repo_name}"):
                try:
                    with st.spinner(f"Ingesting {repo_name}... This may take a few moments."):
                        # --- THIS IS THE MAIN INGESTION CALL ---
                        chunks = ingestion.process_repository(owner, repo)
                        
                        # --- 6. Persist to local JSON / DB (using session_state) ---
                        st.session_state['repo_data'] = chunks
                        st.session_state['repo_name'] = repo_name
                    
                    # --- 7. Return ingestion status to UI ---
                    st.success(f"Successfully ingested {len(chunks)} text chunks from {repo_name}!")
                    st.balloons()

                except Exception as e:
                    st.error(f"Failed to ingest repository: {e}")
                    st.session_state['repo_data'] = None
                    st.session_state['repo_name'] = None

    else:
        st.error("Invalid GitHub URL. Please enter a URL like: https://github.com/owner/repo")


# --- 2. Display Features (if data is loaded) ---

if st.session_state['repo_data']:
    st.header(f"Learning Dashboard: {st.session_state['repo_name']}")
    
    # Simple check: Display how many chunks we have
    st.write(f"Total processed chunks: {len(st.session_state['repo_data'])}")
    
    # --- Feature: Generate Lesson (using README) ---
    if st.button("Generate Guided Lesson"):
        with st.spinner("🤖 AI is generating a lesson plan..."):
            readme_content = ""
            # Find the README chunk(s)
            readme_chunks = [c['content'] for c in st.session_state['repo_data'] if 'README.md' in c['path']]
            if readme_chunks:
                readme_content = " ".join(readme_chunks)
            
            if readme_content:
                lesson = lesson_generator.generate_lesson(readme_content)
                st.subheader("Guided Lesson")
                st.markdown(lesson)
            else:
                st.warning("Could not find a README.md to generate a lesson.")

    # --- Feature: Explain File ---
    # (This section will need to be updated to use the 'repo_data' chunks)
    
    # --- Feature: Generate Quiz ---
    if st.button("Generate Quiz"):
        # (This can also be updated to use README chunks)
        st.info("Quiz feature coming soon!")