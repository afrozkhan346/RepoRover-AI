import streamlit as st
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your backend modules
from backend import ingestion
from backend.utils import parse_github_url
from backend import db  # <-- IMPORT YOUR NEW DB MODULE
from backend import lesson_generator, quiz_generator # (Keep these)

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
        
       # --- THIS IS THE NEW LOGIC ---
        
        # 1. Check if this repo is already in our session
        if st.session_state['repo_name'] == repo_name:
            pass # Data is already loaded, do nothing
        else:
            # 2. It's a new repo. Check Firestore for it.
            with st.spinner(f"Checking cache for {repo_name}..."):
                cached_data = db.get_repo_data_from_db(repo_name)
            
            if cached_data:
                # 3. YAY! Data was in Firestore.
                st.session_state['repo_data'] = cached_data
                st.session_state['repo_name'] = repo_name
                st.success(f"Loaded {len(cached_data)} cached chunks for {repo_name} from database!")
            
            else:
                # 4. NOT in cache. Show the button to ingest it.
                st.info(f"Repository {repo_name} not found in cache.")
                if st.button(f"Analyze and Save: {repo_name}"):
                    try:
                        with st.spinner(f"Ingesting {repo_name}... This may take a few moments."):
                            chunks = ingestion.process_repository(owner, repo)
                            
                        if len(chunks) > 0:
                            # 5. Save to DB AND session state
                            with st.spinner("Saving to database..."):
                                db.save_repo_data_to_db(repo_name, chunks)
                                
                            st.session_state['repo_data'] = chunks
                            st.session_state['repo_name'] = repo_name
                            st.success(f"Successfully ingested and saved {len(chunks)} chunks!")
                            st.balloons()
                        else:
                            st.warning(f"Ingested 0 text chunks...")

                    except Exception as e:
                        st.error(f"Failed to ingest repository: {e}")
                        st.session_state['repo_data'] = None
                        st.session_state['repo_name'] = None

    elif repo_url: 
        st.error("Invalid GitHub URL...")


# --- 2. Display Features (if data is loaded) ---

if st.session_state['repo_data']:
    st.header(f"Learning Dashboard: {st.session_state['repo_name']}")
    
    st.write(f"Total processed chunks: {len(st.session_state['repo_data'])}")
    
    # --- Feature: Generate Lesson (using README) ---
    if st.button("Generate Guided Lesson"):
        with st.spinner("🤖 AI is generating a lesson plan..."):
            readme_content = ""
            # Find the README chunk(s)
            readme_chunks = [c['content'] for c in st.session_state['repo_data'] if 'README.md' in c['path'].lower()]
            if readme_chunks:
                readme_content = " ".join(readme_chunks)
            
            if readme_content:
                lesson = lesson_generator.generate_lesson(readme_content)
                st.subheader("Guided Lesson")
                st.markdown(lesson)
            else:
                st.warning("Could not find a README.md to generate a lesson.")

    # --- Feature: Explain File ---
    st.info("File explanation feature coming soon!")
    
    # --- Feature: Generate Quiz ---
    if st.button("Generate Quiz"):
        st.info("Quiz feature coming soon!")
