import streamlit as st
import sys
import os
import json
import numpy as np

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import ingestion, db, lesson_generator, quiz_generator, llm_client, retrieval
from backend.utils import parse_github_url

def calculate_lesson_metrics(lesson_data):
    """Calculates quality metrics based on the generated lesson JSON."""
    metrics = {
        "source_coverage_pct": 0.0,
        "avg_steps_per_lesson": 0.0,
        "avg_step_length_chars": 0.0,
        "lessons_with_sources": 0,
        "total_lessons": 0,
        "total_steps": 0,
        "total_step_chars": 0
    }
    
    lessons = lesson_data.get("lessons", [])
    metrics["total_lessons"] = len(lessons)
    if not lessons:
        return metrics

    for lesson in lessons:
        # Source Coverage
        if lesson.get("sources"):
            metrics["lessons_with_sources"] += 1

        # Completeness (Steps per lesson)
        steps = lesson.get("steps", [])
        metrics["total_steps"] += len(steps)

        # Conciseness (Step length)
        for step in steps:
            instruction = step.get("instruction", "")
            metrics["total_step_chars"] += len(instruction)

    # Calculate averages safely
    if metrics["total_lessons"] > 0:
        metrics["source_coverage_pct"] = (metrics["lessons_with_sources"] / metrics["total_lessons"]) * 100
        metrics["avg_steps_per_lesson"] = metrics["total_steps"] / metrics["total_lessons"]

    if metrics["total_steps"] > 0:
        metrics["avg_step_length_chars"] = metrics["total_step_chars"] / metrics["total_steps"]

    return metrics

# --- Streamlit UI ---
st.set_page_config(page_title="RepoRoverAI", layout="wide")
st.title("RepoRoverAI 🤖")
st.write("Turn any GitHub repository into an interactive, persistent learning experience.")

# Initialize session state
if 'repo_data' not in st.session_state:
    st.session_state['repo_data'] = None
if 'repo_name' not in st.session_state:
    st.session_state['repo_name'] = None
if 'generated_lessons' not in st.session_state:
    st.session_state['generated_lessons'] = None

repo_url = st.text_input(
    "Paste a public GitHub repository URL:",
    placeholder="https://github.com/pallets/flask" # Updated placeholder
)

if repo_url:
    owner, repo = parse_github_url(repo_url)

    if owner and repo:
        repo_name = f"{owner}/{repo}"

        # 1. Check if this repo is already in our session
        if st.session_state.get('repo_name') == repo_name:
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
    col1, col2 = st.columns([2,3])

    with col1:
        st.subheader("🤖 Guided Lesson")
        # --- THIS SECTION HAS UPDATED RENDERING LOGIC ---
        if st.button("Generate Guided Lesson"):
            with st.spinner("AI is analyzing the repo and generating a lesson plan..."):
                # 1. Retrieve relevant contexts
                relevant_contexts = retrieval.find_relevant_contexts(
                    "repository overview, project goal, setup instructions, key technologies, and main code files or folders",
                    st.session_state['repo_data'],
                    top_k=12
                )
                high_priority_contexts = [ctx for ctx in relevant_contexts if ctx.get('priority', 99) <= 2]
                if len(high_priority_contexts) < 4 and len(relevant_contexts) > 4:
                    high_priority_contexts = relevant_contexts[:8]

                if not high_priority_contexts:
                    st.warning("Could not find enough relevant context to generate a lesson.")
                else:
                    # 2. Call RAG lesson generator (passing user_goal)
                    lesson_data, sources_used = lesson_generator.generate_lesson_rag(
                        high_priority_contexts,
                        st.session_state['repo_name'], # Pass repo_name as repo_id
                        user_goal="Understand the repository structure and purpose" # Provide a goal
                    )

                    # --- 5. UI Render (FIXED RENDERING LOGIC) ---
                    if lesson_data and lesson_data.get("lessons"):
                        st.success("Generated Lesson Plan!")
                        st.session_state['generated_lessons'] = lesson_data

                        # Display metrics
                        metrics = calculate_lesson_metrics(lesson_data)
                        st.subheader("📊 Quality Metrics")
                        m_col1, m_col2, m_col3 = st.columns(3)
                        with m_col1:
                            st.metric("Source Coverage", f"{metrics['source_coverage_pct']:.1f}%", 
                                    help="Percentage of lessons citing sources")
                        with m_col2:
                            st.metric("Steps/Lesson", f"{metrics['avg_steps_per_lesson']:.1f}", 
                                    help="Average steps per lesson")
                        with m_col3:
                            st.metric("Step Length", f"{metrics['avg_step_length_chars']:.0f} chars", 
                                    help="Average step instruction length")
                        st.markdown("---")

                        # Display lessons
                        for i, lesson in enumerate(lesson_data["lessons"]):
                            with st.expander(f"**Lesson {i+1}: {lesson.get('title', 'Untitled')}** ({lesson.get('level', '?')} - {lesson.get('duration_minutes', '?')} min)", expanded=(i==0)):
                                st.markdown(f"**Objective:** {lesson.get('objective', 'Not specified.')}")
                                st.markdown("---")
                                st.markdown("**Steps:**")
                                for step in sorted(lesson.get("steps", []), key=lambda s: s.get('order', 0)):
                                    st.markdown(f"{step.get('order', '?')}. {step.get('instruction', 'No instruction.')}")
                                st.markdown("---")
                                st.markdown(f"**Summary:** {lesson.get('summary', 'Not specified.')}")

                        # Show sources
                        if sources_used:
                            st.subheader("Sources Used:")
                            sources_used.sort(key=lambda x: (x.get('priority', 99), x.get('start_line') or 0))
                            for ctx in sources_used:
                                line_info = f"Lines: {ctx.get('start_line', '?')}-{ctx.get('end_line', '?')}" if ctx.get('start_line') else "Section"
                                st.caption(f"- `{ctx['file_path']}` ({line_info}) - Context ID: `{ctx.get('id', 'N/A')}`")

                        # Display warnings
                        warnings = lesson_data.get("warnings", [])
                        if warnings:
                            st.warning("Notes from AI:")
                            for warning in warnings:
                                st.caption(f"- {warning}")
                    else:
                        st.error("Failed to generate the lesson plan.")
                        if sources_used:
                            st.subheader("Contexts Sent to AI (for debugging):")
                            for ctx in sources_used:
                                st.caption(f"- `{ctx['file_path']}` - Context ID: `{ctx.get('id', 'N/A')}`")

        # Show stored lessons
        elif st.session_state.get('generated_lessons'):
            lessons = st.session_state['generated_lessons'].get("lessons", [])
            st.info(f"Displaying previously generated lesson plan ({len(lessons)} lessons).")
            
            # Display metrics for stored lessons
            metrics = calculate_lesson_metrics(st.session_state['generated_lessons'])
            st.subheader("📊 Quality Metrics")
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                st.metric("Source Coverage", f"{metrics['source_coverage_pct']:.1f}%")
            with m_col2:
                st.metric("Steps/Lesson", f"{metrics['avg_steps_per_lesson']:.1f}")
            with m_col3:
                st.metric("Step Length", f"{metrics['avg_step_length_chars']:.0f} chars")
            st.markdown("---")

            # Display stored lessons
            for i, lesson in enumerate(lessons):
                with st.expander(f"**Lesson {i+1}: {lesson.get('title', 'Untitled')}**", expanded=(i==0)):
                    st.markdown(f"**Objective:** {lesson.get('objective', 'Not specified.')}")
                    st.markdown("---")
                    st.markdown("**Steps:**")
                    for step in sorted(lesson.get("steps", []), key=lambda s: s.get('order', 0)):
                        st.markdown(f"{step.get('order', '?')}. {step.get('instruction', 'No instruction.')}")
                    st.markdown("---")
                    st.markdown(f"**Summary:** {lesson.get('summary', 'Not specified.')}")

    with col2:
        # --- Code Explainer / Q&A Section (Updated) ---
        st.subheader("🧑‍💻 Code Explainer / Q&A")

        file_paths = sorted(list(set([chunk['file_path'] for chunk in st.session_state['repo_data']])))
        selected_file = st.selectbox(
            "Choose a file to explore:",
            file_paths, index=None, placeholder="Select a file"
        )
        # Allow user to ask specific question OR get a summary
        query = st.text_input(
            "Ask a question (or leave blank for a summary/explanation):",
            key="qa_query"
        )

        if selected_file:
            if st.button(f"Explain / Answer", key="qa_button"):
                # Filter contexts for the selected file
                file_contexts = [ctx for ctx in st.session_state['repo_data'] if ctx['file_path'] == selected_file]
                if not file_contexts:
                    st.error("No processed content found for this file.")
                else:
                    with st.spinner(f"AI is analyzing '{selected_file}'..."):

                        # --- If the user asked a specific question: do RAG Q&A ---
                        if query:
                            search_term = query
                            relevant_contexts = retrieval.find_relevant_contexts(
                                search_term, file_contexts, top_k=6
                            )
                            if not relevant_contexts:
                                st.warning("Could not find relevant sections for your query.")
                            else:
                                context_str = "\n\n---\n\n".join([ctx['content'] for ctx in relevant_contexts])
                                prompt = (
                                    "SYSTEM:\n"
                                    "You are RepoRoverAI, an expert code assistant. "
                                    "Answer the user's question using only the CONTEXT below. "
                                    "Be concise and cite file paths and line ranges when relevant.\n\n"
                                    f"QUESTION: {search_term}\n\n"
                                    "CONTEXT:\n---\n"
                                    f"{context_str}\n"
                                    "---\n\nAnswer:"
                                )
                                st.markdown(f"### 🤖 Answer:")
                                response_generator = llm_client.stream_gemini_response(prompt)
                                st.write_stream(response_generator)

                                # Show Q&A sources
                                st.subheader("Sources Used:")
                                relevant_contexts.sort(key=lambda x: x.get('start_line') or 0)
                                for ctx in relevant_contexts:
                                    line_info = (
                                        f"Lines: {ctx.get('start_line', '?')}-{ctx.get('end_line', '?')}"
                                        if ctx.get('start_line') else "Section/Chunk"
                                    )
                                    st.caption(
                                        f"- `{ctx['file_path']}` ({line_info}) - Context ID: `{ctx.get('id', 'N/A')}`"
                                    )

                        else:
                            # --- NEW RAG Explainer Flow (No specific question) ---
                            # Choose the highest-priority context (lower number = higher priority),
                            # breaking ties by longer content to be more representative
                            representative_context = sorted(
                                file_contexts,
                                key=lambda c: (c.get('priority', 99), -len(c.get('content', '')))
                            )[0]

                            explanation_data, sources_used = lesson_generator.generate_explanation_rag(
                                representative_context,
                                st.session_state['repo_name']
                            )

                            if explanation_data:
                                st.success("Generated Explanation!")
                                st.markdown("### Summary:")
                                st.write(explanation_data.get("summary", "N/A"))

                                st.markdown("### Potential Edge Cases / Gotchas:")
                                edge_cases = explanation_data.get("edge_cases", [])
                                if edge_cases:
                                    for case in edge_cases:
                                        st.markdown(f"- {case}")
                                else:
                                    st.write("None identified.")

                                st.markdown("### Test Suggestion:")
                                test_sugg = explanation_data.get("test_suggestion", {})
                                st.write(f"**Title:** `{test_sugg.get('title', 'N/A')}`")
                                st.code(test_sugg.get('assert', '# No assertion provided'), language='python')

                                # Show explainer sources (should be just the one context)
                                st.subheader("Source Used:")
                                for ctx in sources_used:
                                    line_info = (
                                        f"Lines: {ctx.get('start_line', '?')}-{ctx.get('end_line', '?')}"
                                        if ctx.get('start_line') else "Section/Chunk"
                                    )
                                    st.caption(
                                        f"- `{ctx['file_path']}` ({line_info}) - Context ID: `{ctx.get('id', 'N/A')}`"
                                    )
                            else:
                                st.error("Failed to generate the explanation. The AI might have returned an invalid format or encountered an error.")
                                if sources_used:
                                    st.subheader("Context Sent to AI (for debugging):")
                                    for ctx in sources_used:
                                        st.caption(f"- `{ctx['file_path']}` - Context ID: `{ctx.get('id', 'N/A')}`")