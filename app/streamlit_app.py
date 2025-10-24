import streamlit as st
import streamlit.components.v1 as components
import time
import sys
import os
import json
import numpy as np
from urllib.parse import unquote

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import ingestion, db, lesson_generator, quiz_generator, llm_client, retrieval
from backend import quiz_eval, explain, graph_builder, mermaid, vis_builder
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

def render_mermaid(mermaid_src: str):
    """Embeds Mermaid diagram into Streamlit app."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <script src="https://unpkg.com/mermaid@10/dist/mermaid.min.js"></script>
      <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
      </script>
    </head>
    <body>
      <div class="mermaid" style="height: 600px; overflow: auto; background: white; padding: 20px; border-radius: 5px;">
        {mermaid_src}
      </div>
    </body>
    </html>
    """
    components.html(html, height=650, scrolling=True)

def render_vis(payload: dict, height: int = 700):
    """Embeds interactive vis-network graph into Streamlit app."""
    # Convert nodes and edges lists to JSON strings safely
    nodes_json = json.dumps(payload.get('nodes', []), ensure_ascii=False)
    edges_json = json.dumps(payload.get('edges', []), ensure_ascii=False)

    # Define groups for styling (Updated with lesson levels)
    groups_config = {
        # Lessons by Level
        "lesson_beginner":     {"color": {"background": '#ADD8E6', "border": '#6495ED'}, "shape": 'ellipse', "font": {"color": '#343434', "size": 15}}, # Light Blue
        "lesson_intermediate": {"color": {"background": '#FFD700', "border": '#FFA500'}, "shape": 'ellipse', "font": {"color": '#343434', "size": 15}}, # Gold/Amber
        "lesson_advanced":     {"color": {"background": '#D8BFD8', "border": '#8A2BE2'}, "shape": 'ellipse', "font": {"color": '#343434', "size": 15}}, # Thistle/Purple
        # Files by Language
        "python":       {"color": {"background": '#FFF0AD', "border": '#FF9900'}, "shape": 'box'},
        "javascript":   {"color": {"background": '#C2FABC', "border": '#399605'}, "shape": 'box'},
        "typescript":   {"color": {"background": '#C2FABC', "border": '#399605'}, "shape": 'box'},
        "markdown":     {"color": {"background": '#E1E1E1', "border": '#808080'}, "shape": 'box'},
        "json":         {"color": {"background": '#FADADD', "border": '#D32F2F'}, "shape": 'box'},
        "yaml":         {"color": {"background": '#D6CEDE', "border": '#6A1B9A'}, "shape": 'box'},
        "dockerfile":   {"color": {"background": '#ADD8E6', "border": '#0277BD'}, "shape": 'box'},
        "text":         {"color": {"background": '#FFFFFF', "border": '#BDBDBD'}, "shape": 'box'},
        "file":         {"color": {"background": '#FFFFFF', "border": '#BDBDBD'}, "shape": 'box'} # Default
    }
    groups_json = json.dumps(groups_config, ensure_ascii=False)

    html = f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <script type="text/javascript" src="https://unpkg.com/vis-network@9.1.9/dist/vis-network.min.js"></script>
        <link href="https://unpkg.com/vis-network@9.1.9/dist/dist/vis-network.min.css" rel="stylesheet" type="text/css" />
        <style>
          #mynetwork {{
            width: 100%;
            height: {height}px;
            border: 1px solid lightgray;
            background-color: #f8f9fa;
          }}
          .vis-tooltip {{
            position: absolute;
            visibility: hidden;
            padding: 5px;
            white-space: pre-wrap;
            max-width: 300px;
            font-family: sans-serif;
            font-size: 12px;
            color: #000;
            background-color: #f9f9f9;
            border: 1px solid #ccc;
            border-radius: 3px;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
            z-index: 10;
          }}
        </style>
      </head>
      <body>
        <div id="mynetwork"></div>
        <script type="text/javascript">
          const nodes = new vis.DataSet({nodes_json});
          const edges = new vis.DataSet({edges_json});
          const container = document.getElementById('mynetwork');
          const data = {{ nodes, edges }};
          const options = {{
            nodes: {{
              shape: 'box',
              margin: 10,
              font: {{size: 14, color: '#343434'}},
              borderWidth: 1.5,
              shapeProperties: {{
                borderRadius: 4
              }}
            }},
            edges: {{
              smooth: {{
                type: 'continuous',
                roundness: 0.2
              }},
              color: {{
                color: '#848484',
                highlight: '#343434'
              }},
              font: {{
                size: 10,
                color: '#666666'
              }}
            }},
            groups: {groups_json},
            interaction: {{
              hover: true,
              tooltipDelay: 200,
              navigationButtons: true,
              keyboard: true
            }},
            physics: {{
              solver: 'forceAtlas2Based',
              forceAtlas2Based: {{
                gravitationalConstant: -50,
                centralGravity: 0.01,
                springLength: 100,
                springConstant: 0.08,
                avoidOverlap: 0.5
              }},
              stabilization: {{ iterations: 150 }}
            }}
          }};
          const network = new vis.Network(container, data, options);

          // Click handler using query parameters
          network.on("click", function (params) {{
            if (params.nodes.length > 0) {{
              const nodeId = params.nodes[0];
              const nodeData = nodes.get(nodeId);
              if (nodeData && !nodeData.group.startsWith('lesson_')) {{
                const currentUrl = new URL(window.location.href);
                currentUrl.searchParams.set('node', nodeId);
                window.location.href = currentUrl.toString();
              }}
            }}
          }});
        </script>
      </body>
    </html>
    """
    components.html(html, height=height + 50, scrolling=False)

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
if 'current_quiz' not in st.session_state:
    st.session_state['current_quiz'] = None

# --- Read Query Parameter ---
clicked_node_id = None
query_params = st.query_params
if "node" in query_params:
    clicked_node_id = unquote(query_params["node"])
    st.session_state['selected_node_from_graph'] = clicked_node_id
    st.query_params.clear()
    print(f"Node clicked in graph: {clicked_node_id}")

repo_url = st.text_input(
    "Paste a public GitHub repository URL:",
    placeholder="https://github.com/pallets/flask"
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
                st.stop()

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
    
    # Use tabs for better organization
    tab1, tab2, tab3 = st.tabs(["🎓 Lessons & Quiz", "🧑‍💻 Code Explainer", "🗺️ Repo Map"])

    with tab1:  # Lessons & Quiz
        col1, col2 = st.columns([1, 1])
        
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
            st.subheader("🧪 Pop Quiz")
            generate_quiz_disabled = not st.session_state.get('generated_lessons')
            
            if st.button("Generate Quiz for Lesson 1", disabled=generate_quiz_disabled):
                if not st.session_state.get('generated_lessons'):
                    st.warning("Please generate a lesson plan first!")
                else:
                    with st.spinner("AI is generating quiz questions..."):
                        first_lesson = st.session_state['generated_lessons']['lessons'][0]
                        lesson_sources = first_lesson.get("sources_full", [])

                        if not lesson_sources:
                            st.warning("Lesson 1 has no source material to generate questions from.")
                        else:
                            try:
                                quiz_data, quiz_sources = quiz_generator.generate_quiz_for_lesson(
                                    first_lesson,
                                    lesson_sources,
                                    st.session_state['repo_name']
                                )

                                if quiz_data and quiz_data.get("questions"):
                                    st.success("Generated Quiz!")
                                    st.session_state['current_quiz'] = quiz_data
                            except Exception as e:
                                st.error(f"Failed to generate quiz: {str(e)}")

            # --- Render Quiz Form ---
            if st.session_state.get('current_quiz'):
                quiz_data_object = st.session_state['current_quiz']
                quiz_questions = quiz_data_object.get("questions", [])

                # Check if this is a practice quiz
                if quiz_data_object.get("is_practice_quiz"):
                    st.info("📝 This is a practice question. Please review the repository and think about your answer.")
                    practice_q = quiz_questions[0]
                    st.markdown(f"**{practice_q['question']}**")
                    user_answer = st.text_area("Your Answer:", key="practice_answer")
                    if st.button("Save Answer"):
                        st.success("Answer saved! Review the repository's README.md for the correct information.")
                else:
                    # Regular quiz display logic
                    with st.form(key="quiz_form"):
                        user_answers = {}
                        st.subheader("Quiz Questions:")
                        
                        for i, q in enumerate(quiz_questions):
                            st.markdown(f"**{q.get('qid', f'Q{i+1}')}. {q.get('question', 'N/A')}**")
                            
                            # Create radio buttons for choices
                            options = []
                            choice_map = {}
                            for choice in q.get("choices", []):
                                label = choice.get("label", "")
                                text = choice.get("text", "N/A").strip()
                                choice_map[label] = text
                                options.append(f"{label}. {text}")
                            
                            answer = st.radio(
                                f"Select your answer for Q{i+1}:",
                                options,
                                key=f"quiz_q_{i}",
                                label_visibility="collapsed",
                                index=None
                            )
                            if answer:
                                user_answers[q.get('qid')] = answer.strip()
                            st.markdown("---")

                        # Submit button for the form
                        submitted = st.form_submit_button("Submit Answers")
                        
                        if submitted:
                            # Validate all questions are answered
                            if not all(q.get('qid') in user_answers for q in quiz_questions):
                                st.warning("Please answer all questions before submitting.")
                            else:
                                # Grade the responses
                                grading_results = quiz_eval.grade_mcq_responses(quiz_data_object, user_answers)
                                
                                # Display overall score
                                st.markdown("### Quiz Results")
                                st.metric(
                                    "Score", 
                                    f"{grading_results['score']}/{grading_results['total']}", 
                                    f"{grading_results['percent']:.1f}%"
                                )
                                
                                # Display detailed results
                                incorrect_count = 0
                                for result in grading_results["results"]:
                                    st.markdown(f"**{result['qid']}. {result['question']}**")
                                    
                                    if result['correct']:
                                        st.success(f"✅ Correct! Your answer: {result['user_choice']}")
                                    else:
                                        incorrect_count += 1
                                        st.error(f"❌ Incorrect. Your answer: {result['user_choice']}")
                                        
                                        # Generate hint for incorrect answers with rate limit delay
                                        original_q = next(
                                            (q for q in quiz_questions 
                                             if q.get('qid') == result['qid']),
                                            None
                                        )
                                        if original_q and original_q.get("evidence_full"):
                                            # Add delay if this isn't the first incorrect answer
                                            if incorrect_count > 1:
                                                time.sleep(1.5)
                                            
                                            with st.spinner("Generating hint..."):
                                                hint_data = quiz_eval.generate_hint_feedback(
                                                    original_q,
                                                    original_q["evidence_full"]
                                                )
                                                if hint_data:
                                                    st.info(f"💡 Hint: {hint_data['hint']}")
                                                    with st.expander("Detailed Explanation"):
                                                        st.write(hint_data["explanation"])
                                                        if hint_data.get("sources"):
                                                            st.caption(f"Evidence from: {', '.join(hint_data['sources'])}")
                                        
                                        st.info(f"Correct answer: {result['correct_choice']}")
                                    st.caption(f"Explanation: {result.get('explanation', 'N/A')}")
                                    st.markdown("---")

                                # Final feedback
                                if grading_results['percent'] >= 70:
                                    st.balloons()
                                    st.success("🎉 Great job! You've mastered this lesson!")
                                elif grading_results['percent'] >= 50:
                                    st.info("👍 Good effort! Review the explanations above to improve.")
                                else:
                                    st.warning("📚 Keep studying! Consider reviewing the lesson again.")

    with tab2:  # Code Explainer
        st.subheader("🧑‍💻 Code Explainer / Q&A")

        file_paths = sorted(list(set([chunk['file_path'] for chunk in st.session_state['repo_data']])))

        # --- Check if a node was clicked in the graph ---
        pre_selected_file = st.session_state.get('selected_node_from_graph')
        default_index = None
        if pre_selected_file and pre_selected_file in file_paths:
            try:
                default_index = file_paths.index(pre_selected_file)
                print(f"Pre-selecting file: {pre_selected_file} at index {default_index}")
            except ValueError:
                print(f"Clicked node ID {pre_selected_file} not found in file_paths.")
                pre_selected_file = None

        selected_file = st.selectbox(
            "Choose a file to explore:",
            file_paths,
            index=default_index,
            placeholder="Select a file",
            key="explainer_selectbox"
        )

        # --- Clear the clicked node state after using it ---
        if 'selected_node_from_graph' in st.session_state:
            del st.session_state['selected_node_from_graph']

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
                            # --- Use the new explain.py for explanations ---
                            explanation_data, sources_used = explain.explain_target(
                                st.session_state['repo_name'],  # repo_id
                                selected_file,  # file_path
                                None,  # object_name (will default to "file")
                                st.session_state['repo_data'],  # all_contexts
                                top_k=6
                            )

                            if explanation_data:
                                st.success("Generated Explanation!")
                                
                                # Show confidence indicator
                                confidence = explanation_data.get("confidence", "unknown")
                                confidence_colors = {"high": "🟢", "medium": "🟡", "low": "🔴"}
                                st.caption(f"Confidence: {confidence_colors.get(confidence, '⚪')} {confidence.title()}")
                                
                                st.markdown("### Summary:")
                                st.write(explanation_data.get("summary", "N/A"))

                                st.markdown("### Key Points:")
                                key_points = explanation_data.get("key_points", [])
                                if key_points:
                                    for point in key_points:
                                        st.markdown(f"- {point}")
                                else:
                                    st.write("None identified.")

                                st.markdown("### Test Suggestion:")
                                test_sugg = explanation_data.get("unit_test", {})
                                st.write(f"**Title:** `{test_sugg.get('title', 'N/A')}`")
                                st.code(test_sugg.get('code', '# No test provided'), language=test_sugg.get('language', 'python'))

                                st.markdown("### Example Usage:")
                                example = explanation_data.get("example", "")
                                if example and example != "No simple example applicable.":
                                    st.code(example, language="python")
                                else:
                                    st.write("No simple example applicable.")

                                # Show warnings
                                warnings = explanation_data.get("warnings", [])
                                if warnings:
                                    st.warning("Notes:")
                                    for warning in warnings:
                                        st.caption(f"- {warning}")

                                # Show explainer sources
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

    with tab3:  # Repository Map (Updated)
        st.subheader("🗺️ Interactive Repository Map")
        st.caption("Visualizing key files, lessons, and their relationships. Click on a file node to explore it!")

        # --- ADD ENHANCED LEGEND ---
        st.markdown("""
        **Legend:**
        * **Nodes:** 📦 Files (colored by type), 🎓 Lessons (colored by level)
        * **Edges:** → Import/Dependency (heuristic), ⇢ Lesson Source, ⇒ Lesson Path
        * **Colors (Files):** 🟨 Python, 🟩 JS/TS, ⬜ Markdown, 🟥 JSON, 🟪 YAML, 🟦 Dockerfile, ○ Other
        * **Colors (Lessons):** 🟦 Beginner, 🟨 Intermediate, 🟪 Advanced
        * **Interactions:** Hover for details, Click file to explain, Drag to reorganize
        """)
        st.markdown("---")  # Separator
        # --- END LEGEND ---

        try:
            # Build graph data for files
            nodes, edges = graph_builder.build_graph_from_contexts(
                st.session_state['repo_data'],
                max_files=40
            )

            if nodes:
                # Get generated lessons (if available) from session state
                lessons_data = st.session_state.get('generated_lessons')

                # Create payload including lessons
                payload = vis_builder.vis_payload(nodes, edges, lessons_data)

                # Show some stats with enhanced info
                lesson_count = 0
                if lessons_data and lessons_data.get("lessons"):
                    lesson_count = len(lessons_data["lessons"])
                
                st.info(f"📊 Generated graph with {len(payload['nodes'])} nodes ({len(nodes)} files + {lesson_count} lessons) and {len(payload['edges'])} relationships")
                
                # Render the interactive Vis Network graph
                render_vis(payload, height=700)
                
                # Show enhanced controls info
                st.markdown("---")
                st.markdown("### 🎮 Controls & Features")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Navigation:**")
                    st.markdown("- **Click & Drag**: Move nodes around")
                    st.markdown("- **Mouse Wheel**: Zoom in/out")
                    st.markdown("- **Click File Node**: Jump to Code Explainer")
                    st.markdown("- **Hover**: View file excerpts")
                with col2:
                    st.markdown("**Visual Elements:**")
                    st.markdown("- **Solid Golden Lines**: Learning path between lessons")
                    st.markdown("- **Dashed Gray Lines**: Lesson sources")
                    st.markdown("- **Regular Arrows**: Import relationships")
                    st.markdown("- **Node Colors**: File types and lesson levels")
                
            else:
                st.warning("⚠️ Not enough file data to generate a meaningful map.")
                st.info("Try analyzing a repository with more interconnected files.")

        except Exception as e:
            st.error(f"❌ Error generating repository map: {e}")
            st.caption("This might happen with repositories that have complex import patterns or unusual file structures.")
            if st.checkbox("Show Debug Info"):
                st.exception(e)

    # --- End of Tabs ---