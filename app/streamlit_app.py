import streamlit as st
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Correct Imports ---
from backend import ingestion
from backend.utils import parse_github_url
from backend import db
from backend import lesson_generator, quiz_generator, llm_client # Added llm_client
from backend import retrieval # Import retrieval

# --- Streamlit UI ---
st.set_page_config(page_title="RepoRoverAI", layout="wide")
st.title("RepoRoverAI 🤖")
st.write("Turn any GitHub repository into an interactive, persistent learning experience.")

# Initialize session state
if 'repo_data' not in st.session_state:
    st.session_state['repo_data'] = None
if 'repo_name' not in st.session_state:
    st.session_state['repo_name'] = None

repo_url = st.text_input(
    "Paste a public GitHub repository URL:",
    placeholder="https://github.com/pallets/flask" # Updated placeholder
)

if repo_url:
    owner, repo = parse_github_url(repo_url)

    if owner and repo:
        repo_name = f"{owner}/{repo}"

        # 1. Check if this repo is already in our session
        if st.session_state['repo_name'] == repo_name:
            pass # Data is already loaded, do nothing
        else:
            # 2. It's a new repo. Check Firestore for it.
            try:
                with st.spinner(f"Checking cache for {repo_name}..."):
                    cached_data = db.get_repo_data_from_db(repo_name)
            except Exception as e:
                st.error(f"Error connecting to database: {e}")
                st.stop() # Stop the app if DB connection fails

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
                            st.warning(f"Ingested 0 text chunks. This might be a private, empty, or mega-repo.")

                    except Exception as e:
                        st.error(f"Failed to ingest repository. Is it private? Error: {e}")
                        st.session_state['repo_data'] = None
                        st.session_state['repo_name'] = None

    elif repo_url:
        st.error("Invalid GitHub URL. Please enter a URL like: https://github.com/owner/repo")


# --- 2. Display Features (if data is loaded) ---

if st.session_state.get('repo_data'):
    st.header(f"Learning Dashboard: {st.session_state['repo_name']}")

    # --- Create two columns for features ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🤖 Guided Lesson")
        # --- Feature: Generate Lesson (using README) ---
        if st.button("Generate Guided Lesson"):
            with st.spinner("AI is generating a lesson plan..."):
                readme_content = ""
                # --- CORRECTED README FINDING ---
                readme_chunks = [
                    c['content'] for c in st.session_state['repo_data']
                    if 'readme' in c['file_path'].lower() and c.get('priority', 99) == 1
                ]
                if readme_chunks:
                    readme_content = " ".join(readme_chunks)

                if readme_content:
                    st.markdown("### Here's your lesson plan:")
                    response_generator = lesson_generator.generate_lesson(readme_content)
                    st.write_stream(response_generator)
                else:
                    st.warning("Could not find a high-priority README file to generate a lesson.")

        # --- Feature: Generate Quiz ---
        st.subheader("🧪 Pop Quiz!")
        if st.button("Generate Quiz"):
            with st.spinner("AI is generating a quiz..."):
                readme_content = ""
                # --- CORRECTED README FINDING ---
                readme_chunks = [
                    c['content'] for c in st.session_state['repo_data']
                    if 'readme' in c['file_path'].lower() and c.get('priority', 99) == 1
                ]
                if readme_chunks:
                    readme_content = " ".join(readme_chunks)

                if readme_content:
                    st.markdown("### Here's your quiz:")
                    response_generator = quiz_generator.generate_quiz(readme_content)
                    st.write_stream(response_generator)
                else:
                    st.warning("Could not find a high-priority README file to generate a quiz from.")

    with col2:
        # --- THIS IS THE UPDATED Q&A SECTION ---
        st.subheader("🧑‍💻 Code Explainer / Q&A")

        # Get unique file paths
        file_paths = sorted(list(set([chunk['file_path'] for chunk in st.session_state['repo_data']])))

        selected_file = st.selectbox(
            "Choose a file to explore:",
            file_paths,
            index=None,
            placeholder="Select a file"
        )

        query = st.text_input("Ask a question about the selected file (or leave blank to summarize):", key="qa_query")

        if selected_file:
            if st.button(f"Explain / Answer", key="qa_button"):

                # Filter contexts to only include those from the selected file
                file_contexts = [
                    ctx for ctx in st.session_state['repo_data']
                    if ctx['file_path'] == selected_file
                ]

                if not file_contexts:
                    st.error("No processed content found for this file.")
                else:
                    with st.spinner(f"AI is analyzing '{selected_file}'..."):

                        # --- USE RETRIEVAL ---
                        search_term = query if query else selected_file
                        relevant_contexts = retrieval.find_relevant_contexts(
                            search_term,
                            file_contexts,
                            top_k=6 # Get top 6 relevant chunks/functions
                        )

                        if not relevant_contexts:
                            st.warning("Could not find relevant sections for your query.")
                        else:
                            # --- AUGMENT & GENERATE ---
                            context_str = "\n\n---\n\n".join([ctx['content'] for ctx in relevant_contexts])

                            prompt = f"""You are RepoRoverAI, an expert code assistant. Based *only* on the following context provided from the file '{selected_file}', please answer the user's question clearly and concisely. If the context doesn't contain the answer, say "I couldn't find information about that in the provided context."

                            Context:
                            ---
                            {context_str}
                            ---

                            User's Question: {search_term}

                            Answer:"""

                            st.markdown(f"### 🤖 Answer:")
                            # Send to Gemini chat model
                            response_generator = llm_client.stream_gemini_response(prompt)
                            st.write_stream(response_generator)

                            # --- Show Sources (Provenance) ---
                            st.subheader("Sources Used:")
                            # Sort sources by start line if available
                            relevant_contexts.sort(key=lambda x: x.get('start_line') or 0)
                            for ctx in relevant_contexts:
                                line_info = f"Lines: {ctx.get('start_line', '?')}-{ctx.get('end_line', '?')}" if ctx.get('start_line') else "Section/Chunk"
                                st.caption(f"- `{ctx['file_path']}` ({line_info})")

        # --- END OF UPDATED Q&A SECTION ---

