import streamlit as st
import streamlit.components.v1 as components
import sys
import os
import json
import time
from urllib.parse import unquote
from pathlib import Path
import datetime # For logging
import numpy as np # For metrics calc

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Backend Imports ---
from backend import ingestion, db, lesson_generator, quiz_generator, llm_client, retrieval
from backend import quiz_eval, explain, graph_builder, vis_builder
from backend.utils import parse_github_url

# --- Constants ---
LOG_DIR_VIS = Path("data/visualization_logs")
LOG_DIR_VIS.mkdir(parents=True, exist_ok=True)

# --- Session State Initialization (Two-Column Layout) ---
REQUIRED_STATE_KEYS = [
    'repo_url', 'repo_id', 'ingested', 'contexts',
    'graph_payload', 'graph_lessons_hash', 'selected_node_id', # Added graph_lessons_hash
    'current_explain', 'current_explain_sources', 'current_lesson_data', 'current_quiz_data', # Added current_explain_sources
    'current_view', # Controls right panel: 'welcome', 'explain', 'lesson', 'quiz', 'loading'
    'active_lesson_id', # Which lesson to show/quiz
    'logs'
]
DEFAULT_VALUES = {
    'repo_url': '', 'repo_id': None, 'ingested': False, 'contexts': [],
    'graph_payload': None, 'graph_lessons_hash': None, 'selected_node_id': None,
    'current_explain': None, 'current_explain_sources': [], 'current_lesson_data': None, 'current_quiz_data': None,
    'current_view': 'welcome', # Start with welcome message
    'active_lesson_id': None,
    'logs': []
}
if 'initialized' not in st.session_state:
    print("--- Initializing Session State ---")
    for key in REQUIRED_STATE_KEYS:
        if key not in st.session_state: st.session_state[key] = DEFAULT_VALUES[key]
    st.session_state['initialized'] = True

# --- Helper Functions ---

def calculate_lesson_metrics(lesson_data):
    """Calculates quality metrics based on the generated lesson JSON."""
    metrics = { "source_coverage_pct": 0.0, "avg_steps_per_lesson": 0.0, "avg_step_length_chars": 0.0, "lessons_with_sources": 0, "total_lessons": 0, "total_steps": 0, "total_step_chars": 0 }
    if not lesson_data: return metrics
    lessons = lesson_data.get("lessons", [])
    metrics["total_lessons"] = len(lessons);
    if not lessons: return metrics
    for lesson in lessons:
        # Check 'sources_full' which contains the actual mapped contexts
        if lesson.get("sources_full"): metrics["lessons_with_sources"] += 1
        steps = lesson.get("steps", []); metrics["total_steps"] += len(steps)
        for step in steps: metrics["total_step_chars"] += len(step.get("instruction", ""))
    if metrics["total_lessons"] > 0: metrics["source_coverage_pct"] = (metrics["lessons_with_sources"] / metrics["total_lessons"]) * 100; metrics["avg_steps_per_lesson"] = metrics["total_steps"] / metrics["total_lessons"]
    if metrics["total_steps"] > 0: metrics["avg_step_length_chars"] = metrics["total_step_chars"] / metrics["total_steps"]
    return metrics

def render_vis(payload: dict, height: int = 700):
    """Embeds interactive vis-network graph into Streamlit app."""
    if not payload or not payload.get('nodes'):
        st.warning("No graph data to render.")
        return
    nodes_json = json.dumps(payload.get('nodes', []), ensure_ascii=False)
    edges_json = json.dumps(payload.get('edges', []), ensure_ascii=False)
    # Define groups for styling
    groups_config = {
        "lesson_beginner":     {"color": {"background": '#ADD8E6', "border": '#6495ED'}, "shape": 'ellipse', "font": {"color": '#343434', "size": 15}},
        "lesson_intermediate": {"color": {"background": '#FFD700', "border": '#FFA500'}, "shape": 'ellipse', "font": {"color": '#343434', "size": 15}},
        "lesson_advanced":   {"color": {"background": '#D8BFD8', "border": '#8A2BE2'}, "shape": 'ellipse', "font": {"color": '#343434', "size": 15}},
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
    <!doctype html><html><head><meta charset="utf-8"/><script type="text/javascript" src="https://unpkg.com/vis-network@9.1.9/dist/vis-network.min.js"></script><link href="https://unpkg.com/vis-network@9.1.9/dist/dist/vis-network.min.css" rel="stylesheet" type="text/css"/><style>#mynetwork{{width:100%;height:{height}px;border:1px solid lightgray;background-color:#f8f9fa;border-radius:5px;}}.vis-tooltip{{position:absolute;visibility:hidden;padding:5px;white-space:pre-wrap;max-width:300px;font-family:sans-serif;font-size:12px;color:#000;background-color:#f9f9f9;border:1px solid #ccc;border-radius:3px;box-shadow:2px 2px 5px rgba(0,0,0,.1);z-index:10}}</style></head><body><div id="mynetwork"></div><script type="text/javascript">const nodes=new vis.DataSet({nodes_json});const edges=new vis.DataSet({edges_json});const container=document.getElementById("mynetwork");const data={{nodes,edges}};const options={{nodes:{{shape:"box",margin:10,font:{{size:14,color:"#343434"}},borderWidth:1.5,shapeProperties:{{borderRadius:4}}}},edges:{{smooth:{{type:"continuous",roundness:.2}},color:{{color:"#848484",highlight:"#343434"}}}},groups:{groups_json},interaction:{{hover:!0,tooltipDelay:200,navigationButtons:!0,keyboard:!0}},physics:{{solver:"forceAtlas2Based",forceAtlas2Based:{{gravitationalConstant:-50,centralGravity:.01,springLength:100,springConstant:.08,avoidOverlap:.5}},stabilization:{{iterations:150}}}}}};const network=new vis.Network(container,data,options);network.on("click",function(params){{if(params.nodes.length>0){{const nodeId=params.nodes[0];const nodeData=nodes.get(nodeId);if(nodeData&&!nodeData.group.startsWith("lesson_")){{const currentUrl=new URL(window.location.href);currentUrl.searchParams.set("node",nodeId);window.location.href=currentUrl.toString();console.log('Navigating for node:', nodeId);}}}}}});</script></body></html>
    """
    components.html(html, height=height + 50, scrolling=False)


# --- UI Rendering Functions for Right Panel ---

def render_welcome_panel():
    """Renders the initial welcome message in the right panel."""
    st.markdown("### Welcome to RepoRoverAI! 👋")
    st.info("Analyze a repository using the sidebar, then click nodes in the graph to explore files or generate lessons!")
    st.markdown("""
    **Getting Started:**
    1.  Paste a public GitHub repo URL in the sidebar.
    2.  Wait for analysis (or loading from cache).
    3.  Click file nodes (📦) in the graph to get AI explanations.
    4.  Click "Generate Guided Lessons" in the sidebar to create a learning path.
    """)

def render_explain_panel(explain_data, sources_used):
    """Renders the explanation view in the right panel."""
    if not explain_data:
        st.error("Could not generate explanation data.")
        # Optionally show sources sent for debugging
        if sources_used:
            st.subheader("Contexts Sent (Debug):")
            for ctx in sources_used: st.caption(f"- `{ctx.get('id', 'N/A')}`")
        return

    # Use file_path for title if object name is generic 'file'
    display_name = explain_data.get('object', explain_data.get('file_path','N/A'))
    if display_name == 'file': display_name = explain_data.get('file_path','N/A')

    st.subheader(f"🧑‍💻 Explain: `{display_name}`")
    confidence = explain_data.get("confidence", "unknown")
    confidence_colors = {"high": "🟢", "medium": "🟡", "low": "🔴"}
    st.caption(f"Confidence: {confidence_colors.get(confidence, '⚪')} {confidence.title()}")
    st.markdown("---")

    st.markdown("**Summary:**")
    st.write(explain_data.get("summary", "_Not available._"))

    st.markdown("**Key Points:**")
    key_points = explain_data.get("key_points", [])
    if key_points:
        for point in key_points: st.markdown(f"- {point}")
    else: st.write("_None identified._")

    test_sugg = explain_data.get("unit_test", {})
    with st.expander("🧪 Test Suggestion"):
        st.write(f"**Title:** `{test_sugg.get('title', 'N/A')}`")
        st.code(test_sugg.get('code', '# No test provided'), language=test_sugg.get('language', 'python'))

    example = explain_data.get("example", "")
    if example and example != "No simple example applicable.":
        with st.expander("📝 Example Usage"):
            # Try to guess language for code block
            lang = "bash" # Default
            if ("python" in explain_data.get("file_path", "") or
                "(" in example or "=" in example or "import" in example):
                 lang="python"
            st.code(example, language=lang)
    else:
        st.markdown("**Example Usage:**")
        st.write("_No simple example applicable._")

    # Sources section
    with st.expander("📚 Sources Used"):
        if sources_used:
            sources_used.sort(key=lambda x: x.get('start_line') or 0)
            for ctx in sources_used:
                line_info = f"Lines: {ctx.get('start_line', '?')}-{ctx.get('end_line', '?')}" if ctx.get('start_line') else "Section"
                st.caption(f"- `{ctx['file_path']}` ({line_info}) ID: `{ctx.get('id', 'N/A')}`")
        else: st.caption("No specific sources cited by the AI.")

    # Warnings
    warnings = explain_data.get("warnings", [])
    if warnings:
        with st.expander("⚠️ Notes & Warnings", expanded=True):
            for w in warnings: st.caption(f"- {w}")

# --- UI Rendering Functions for Right Panel (Continued) ---

def render_lesson_panel(lesson_data):
    """Renders the lesson view in the right panel."""
    st.subheader("🎓 Guided Lessons")

    if not lesson_data or not lesson_data.get("lessons"):
        st.error("No lesson data available. Generate lessons using the button in the sidebar.")
        return

    # Metrics
    metrics = calculate_lesson_metrics(lesson_data)
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1: st.metric("Source Coverage", f"{metrics['source_coverage_pct']:.1f}%")
    with m_col2: st.metric("Avg Steps/Lesson", f"{metrics['avg_steps_per_lesson']:.1f}")
    with m_col3: st.metric("Avg Step Length", f"{metrics['avg_step_length_chars']:.0f} chars")
    st.markdown("---")

    # Lessons with Quiz Buttons
    lessons = lesson_data.get("lessons", [])
    for i, lesson in enumerate(lessons):
        lesson_id = lesson.get('lesson_id', f'L{i+1}')
        with st.expander(f"**{lesson_id}: {lesson.get('title', 'N/A')}** ({lesson.get('level','?')}, {lesson.get('duration_minutes','?')}min)", expanded=(i==0)):
            st.markdown(f"**Objective:** {lesson.get('objective', 'N/A')}")
            st.markdown("**Steps:**")
            for step in sorted(lesson.get("steps", []), key=lambda s: s.get('order', 0)):
                st.markdown(f"{step.get('order', '?')}. {step.get('instruction', 'N/A')}")
            st.markdown(f"**Summary:** {lesson.get('summary', 'N/A')}")

            # Button to trigger quiz for THIS lesson
            if st.button(f"Start Quiz for {lesson_id}", key=f"start_quiz_{lesson_id}"):
                 # Check if sources are available on the lesson object
                 lesson_sources = lesson.get("sources_full", [])
                 if lesson_sources:
                      st.session_state['current_quiz_data'] = None # Clear previous quiz
                      with st.spinner(f"Generating quiz for {lesson_id}..."):
                            quiz_data, _ = quiz_generator.generate_quiz_for_lesson(lesson, lesson_sources, st.session_state['repo_id'])
                            st.session_state['current_quiz_data'] = quiz_data
                            if quiz_data:
                                 st.session_state['current_view'] = 'quiz' # Switch view
                                 st.session_state['active_lesson_id'] = lesson_id # Set active quiz
                            else: st.error("Failed to generate quiz.")
                      st.rerun() # Rerun to show quiz view
                 else:
                     st.warning("Lesson source context not available to generate quiz.")

    # Display overall warnings from lesson generation
    warnings = lesson_data.get("warnings", [])
    if warnings:
        with st.expander("⚠️ Notes & Validation Warnings", expanded=True):
            for w in warnings: st.caption(f"- {w}")


def render_quiz_panel(quiz_data, lesson_title="Lesson"):
    """Renders the quiz view in the right panel."""
    st.subheader(f"🧪 Quiz: {lesson_title}")

    if not quiz_data or not quiz_data.get("questions"):
        st.error("No quiz data available.")
        if st.button("Back to Lessons", key="quiz_back_lesson_alt"):
            st.session_state['current_view'] = 'lesson'; st.session_state['current_quiz_data'] = None; st.rerun()
        return

    quiz_questions = quiz_data.get("questions", [])

    # Handle practice quiz
    if quiz_data.get("is_practice_quiz"):
        st.info("📝 This is a practice question...")
        practice_q = quiz_questions[0]
        st.markdown(f"**{practice_q['question']}**")
        st.text_area("Your Answer:", key="practice_answer", disabled=True)
        st.caption(practice_q.get("explanation", "Review the README."))
        if st.button("Back to Lessons", key="practice_quiz_back"):
            st.session_state['current_view'] = 'lesson'; st.session_state['current_quiz_data'] = None; st.rerun()
    # Handle regular MCQ quiz
    elif quiz_questions:
        with st.form(key="quiz_form"):
            user_answers = {} # Stores the full selected option string ("A. Text")
            st.markdown("**Answer the questions below:**")
            for i, q in enumerate(quiz_questions):
                 q_id = q.get('qid', f'Q{i+1}')
                 st.markdown(f"**{q_id}. {q.get('question', 'N/A')}**")
                 options = []
                 choice_map = {}
                 # Ensure choices is a list before iterating
                 choices_list = q.get("choices", [])
                 if isinstance(choices_list, list):
                      for choice in choices_list:
                           label = choice.get("label", "")
                           text = choice.get("text", "N/A").strip()
                           choice_map[label] = text
                           options.append(f"{label}. {text}")

                 answer = st.radio(f"Select answer for {q_id}:", options, key=f"quiz_q_{i}", label_visibility="collapsed", index=None)
                 if answer: user_answers[q_id] = answer.strip()
                 # Removed separator inside radio group for cleaner look

            submitted = st.form_submit_button("Submit Answers")

            if submitted:
                 # Check if all answered
                 if len(user_answers) != len(quiz_questions):
                     st.warning("Please answer all questions.")
                 else:
                     # Map submitted option string back to choice text for grading
                     user_answers_text = {}
                     for qid, selected_option_string in user_answers.items():
                         user_answers_text[qid] = selected_option_string.split('. ', 1)[1] if '. ' in selected_option_string else selected_option_string

                     # Grade using the selected text answers
                     grading_results = quiz_eval.grade_mcq_responses(quiz_data, user_answers_text)

                     st.subheader(f"Results: {grading_results['score']}/{grading_results['total']} ({grading_results['percent']:.1f}%)")
                     st.markdown("---")

                     # Display detailed results & hints
                     incorrect_count = 0
                     for result in grading_results["results"]:
                         original_q = next((q for q in quiz_questions if q.get('qid') == result['qid']), None)
                         st.markdown(f"**{result['qid']}. {result['question']}**")

                         if result['correct']:
                             st.success(f"✓ Correct! Your answer: {user_answers.get(result['qid'])}") # Show original selection
                             st.caption(f"Explanation: {result.get('explanation', 'N/A')}")
                         else:
                             st.error(f"✗ Incorrect. Your answer: {user_answers.get(result['qid'], 'Not Answered')}")
                             incorrect_count += 1
                             # Generate hint
                             if original_q and original_q.get("evidence_full"):
                                 if incorrect_count > 1: time.sleep(1.0) # Delay between hints
                                 with st.spinner("Generating hint..."):
                                     hint_data = quiz_eval.generate_hint_feedback(original_q, original_q["evidence_full"])
                                 if hint_data and hint_data.get("hint"): st.info(f"💡 Hint: {hint_data['hint']}")
                                 else: st.caption("Could not generate hint.")
                             else: st.caption("Evidence contexts not available for hint.")

                             st.info(f"Correct answer: {result['correct_choice']}") # Show correct text
                             st.caption(f"Explanation: {result.get('explanation', 'N/A')}")
                         st.markdown("---") # Separator

                     # Pass/Fail message
                     pass_threshold = 66.0
                     if grading_results['percent'] >= pass_threshold: st.balloons(); st.success("Passed!")
                     else: st.warning("Keep practicing!")

        # Button to go back to lessons after submitting/viewing results or if stuck
        if st.button("Back to Lessons", key="quiz_back_lesson"):
            st.session_state['current_view'] = 'lesson'; st.session_state['current_quiz_data'] = None; st.rerun()


# --- Streamlit App ---
st.set_page_config(page_title="RepoRoverAI", layout="wide", initial_sidebar_state="expanded")

# --- Sidebar ---
with st.sidebar:
    # st.image("assets/logo.png", width=150) # Assuming you have a logo in assets/
    st.title("RepoRoverAI")
    st.caption("AI-Powered Code Learning")
    st.markdown("---")

    repo_url_input = st.text_input(
        "GitHub URL",
        value=st.session_state.get('repo_url', ''),
        key="repo_input_key",
        placeholder="e.g., pallets/flask or owner/repo"
    )

    # Auto-trigger analysis on valid URL change
    owner, repo = parse_github_url(repo_url_input)
    if repo_url_input and owner and repo:
         repo_id_new = f"{owner}/{repo}"
         if st.session_state.get('repo_id') != repo_id_new:
              print(f"URL changed/validated: {repo_id_new}. Clearing state.")
              # Clear state, keep new URL/ID
              for key in REQUIRED_STATE_KEYS: st.session_state[key] = DEFAULT_VALUES[key]
              st.session_state['initialized'] = True
              st.session_state['repo_url'] = repo_url_input
              st.session_state['repo_id'] = repo_id_new
              st.session_state['current_view'] = 'loading' # Indicate loading needed
              st.rerun() # Trigger analysis flow below
    elif repo_url_input and st.session_state.get('repo_id'): # URL became invalid, clear state
         print("URL became invalid. Clearing state.")
         for key in REQUIRED_STATE_KEYS: st.session_state[key] = DEFAULT_VALUES[key]
         st.session_state['initialized'] = True
         st.session_state['repo_url'] = repo_url_input # Keep invalid input
         st.rerun()


    # --- Analysis / Loading Logic ---
    # Show status or trigger analysis/cache check if needed
    if st.session_state.get('current_view') == 'loading' and st.session_state.get('repo_id'):
        repo_id = st.session_state['repo_id']
        owner, repo = repo_id.split('/', 1)
        # Check Cache
        try:
            with st.spinner(f"Checking cache for {repo_id}..."): cached_data = db.get_repo_data_from_db(repo_id)
        except Exception as e: st.error(f"DB Error: {e}", icon="🔥"); st.stop()

        if cached_data: # Cache Hit
            st.session_state['contexts'] = cached_data
            st.session_state['ingested'] = True
            st.session_state['current_view'] = 'welcome' # Ready
            st.success(f"Loaded {len(cached_data)} chunks!")
            time.sleep(1) # Brief pause to show message
            st.rerun()
        else: # Cache Miss -> Ingest
            try:
                st.info(f"'{repo_id}' not cached. Analyzing...")
                with st.spinner(f"Ingesting {repo_id}... (can take minutes)"): chunks = ingestion.process_repository(owner, repo)
                if len(chunks) > 0:
                    with st.spinner("Saving to database..."): db.save_repo_data_to_db(repo_id, chunks)
                    st.session_state['contexts'] = chunks; st.session_state['ingested'] = True
                    st.session_state['current_view'] = 'welcome' # Ready
                    st.success(f"Analyzed & Saved {len(chunks)} chunks!")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
                else: st.warning("Ingested 0 chunks."); st.session_state['current_view'] = 'welcome'; st.rerun()
            except Exception as e:
                st.error(f"Ingestion failed: {e}", icon="🔥")
                st.session_state['ingested'] = False; st.session_state['contexts'] = []; st.session_state['current_view'] = 'welcome'; st.rerun()

    # --- Sidebar Controls (Only show if ingested) ---
    st.markdown("---")
    if st.session_state.get('ingested') and st.session_state.get('repo_id'):
        st.markdown(f"**Current Repo:**\n`{st.session_state['repo_id']}`")
        st.metric("Context Chunks", len(st.session_state.get('contexts', [])))

        # Lesson Generation Button
        lesson_button_text = "🔄 Regenerate Lessons" if st.session_state.get('current_lesson_data') else "🚀 Generate Guided Lessons"
        if st.button(lesson_button_text, key="generate_lessons_sidebar", use_container_width=True):
             st.session_state['current_lesson_data'] = None; st.session_state['current_quiz_data'] = None
             with st.spinner("AI generating lessons..."):
                 contexts_for_lesson = retrieval.find_relevant_contexts(
                     "repository overview, project goal, setup, key files",
                     st.session_state['contexts'], top_k=12)
                 high_priority_contexts = [ctx for ctx in contexts_for_lesson if ctx.get('priority', 99) <= 2][:8] # Limit context
                 if not high_priority_contexts: st.warning("Not enough context for lessons.")
                 else:
                     lesson_data, sources = lesson_generator.generate_lesson_rag(
                         high_priority_contexts, st.session_state['repo_id'])
                     if lesson_data:
                          st.session_state['current_lesson_data'] = lesson_data
                          st.session_state['current_view'] = 'lesson' # Switch view
                          st.session_state['active_lesson_id'] = lesson_data['lessons'][0]['lesson_id'] if lesson_data.get('lessons') else None
                          st.session_state['graph_payload'] = None # Force graph regeneration
                          st.success("Lessons generated!")
                     else: st.error("Failed to generate lessons.")
             st.rerun()

    # Debug Clear Button
    st.markdown("---")
    st.markdown("⚙️ **Debug**")
    if st.button("Clear Session & Cache", key="clear_session_sidebar", use_container_width=True):
        repo_id_to_clear = st.session_state.get('repo_id')
        keys_to_clear = list(DEFAULT_VALUES.keys()) + ['initialized']
        for key in keys_to_clear:
            if key in st.session_state: del st.session_state[key]
        # Optional: Add Firestore delete here? Needs db.py function
        st.success("Session cleared. Re-enter URL.")
        st.rerun()


# --- Main Panel Layout ---
col_left, col_right = st.columns([3, 2]) # Left column wider (3 parts vs 2)

# --- Left Column: Graph ---
with col_left:
    st.subheader("🗺️ Repository Map")
    if not st.session_state.get('ingested'):
        st.info("Analyze a repository in the sidebar to visualize its structure.")
    else:
        # Generate graph payload if needed or if lessons updated
        graph_lessons_hash = hash(json.dumps(st.session_state.get('current_lesson_data'), sort_keys=True))
        if not st.session_state.get('graph_payload') or st.session_state.get('graph_lessons_hash') != graph_lessons_hash:
            print("Generating/Updating graph payload...")
            try:
                nodes, edges = graph_builder.build_graph_from_contexts(st.session_state['contexts'], max_files=40)
                st.session_state['graph_payload'] = vis_builder.vis_payload(
                    nodes, edges, st.session_state.get('current_lesson_data')
                )
                st.session_state['graph_lessons_hash'] = graph_lessons_hash # Store hash
            except Exception as e:
                 print(f"Error building graph: {e}")
                 st.session_state['graph_payload'] = {"nodes": [], "edges": []} # Set empty on error

        # Render Graph
        if st.session_state['graph_payload'] and st.session_state['graph_payload'].get("nodes"):
            render_vis(st.session_state['graph_payload'], height=700)
        else:
            st.warning("Could not generate graph data.")

# --- Right Column: Dynamic Content ---
with col_right:
    st.subheader("💡 Inspector Panel")
    st.markdown("---")

    # --- Read Query Parameter and Update State ---
    query_params = st.query_params
    if "node" in query_params:
        clicked_node_id = unquote(query_params["node"])
        if clicked_node_id != st.session_state.get('selected_node_id'): # Check if different node
             st.session_state['selected_node_id'] = clicked_node_id
             st.session_state['current_view'] = 'explain' # Switch view
             st.session_state['current_explain'] = None # Force re-fetch/re-render
             st.session_state['active_lesson_id'] = None; st.session_state['current_quiz_data'] = None
             st.query_params.clear()
             print(f"Node clicked: {clicked_node_id}, switching to explain view.")
             # Log click
             try:
                 log_entry = { "timestamp": datetime.datetime.now().isoformat(), "event_type": "node_click", "node_id": clicked_node_id, "repo_id": st.session_state.get('repo_id', 'N/A')}
                 log_filename = LOG_DIR_VIS / f"vis_log_{datetime.datetime.now():%Y%m%d}.jsonl"
                 with open(log_filename, 'a', encoding='utf-8') as f: f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
             except Exception as log_e: print(f"Error logging node click: {log_e}")
             st.rerun() # Rerun immediately

    # --- Determine what to display ---
    current_view = st.session_state.get('current_view', 'welcome')
    if not st.session_state.get('ingested'): current_view = 'welcome' # Force welcome

    if current_view == 'explain':
        node_id_to_explain = st.session_state.get('selected_node_id')
        if not node_id_to_explain:
             st.info("Click a file node on the graph to see details.")
        else:
             # Fetch/Generate Explanation only if needed
             if not st.session_state.get('current_explain') or st.session_state['current_explain'].get('file_path') != node_id_to_explain:
                  with st.spinner(f"Generating explanation for `{node_id_to_explain}`..."):
                       # Pass object_name=None for file explanation
                       explanation_data, sources_used = explain.explain_target(
                            repo_id=st.session_state['repo_id'], file_path=node_id_to_explain, object_name=None,
                            all_contexts=st.session_state['contexts'], top_k=8
                       )
                       st.session_state['current_explain'] = explanation_data
                       st.session_state['current_explain_sources'] = sources_used

             # Render panel using data from session state
             render_explain_panel(st.session_state.get('current_explain'), st.session_state.get('current_explain_sources', []))
             # Button to switch back to Lessons
             if st.session_state.get('current_lesson_data'):
                 if st.button("View Lessons", key="explain_view_lessons"):
                     st.session_state['current_view'] = 'lesson'; st.session_state['selected_node_id'] = None; st.rerun()

    elif current_view == 'lesson':
         lesson_data = st.session_state.get('current_lesson_data')
         render_lesson_panel(lesson_data) # Renders lessons and includes quiz buttons

    elif current_view == 'quiz':
         quiz_data = st.session_state.get('current_quiz_data')
         active_lesson_id = st.session_state.get('active_lesson_id')
         lesson_title = f"Lesson {active_lesson_id}"
         if st.session_state.get('current_lesson_data') and active_lesson_id:
             lessons = st.session_state['current_lesson_data'].get('lessons', [])
             active_lesson = next((l for l in lessons if l.get('lesson_id') == active_lesson_id), None)
             if active_lesson: lesson_title = active_lesson.get('title', lesson_title)

         render_quiz_panel(quiz_data, lesson_title) # Renders quiz form and results

    elif current_view == 'loading':
         st.spinner("Analyzing repository...") # Show spinner while sidebar handles logic

    else: # Welcome
         render_welcome_panel()


# --- Footer ---
st.markdown("---")
st.caption(f"RepoRoverAI © 2025 | Current Repo: {st.session_state.get('repo_id', 'None')}")