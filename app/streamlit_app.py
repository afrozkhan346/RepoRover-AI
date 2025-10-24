import streamlit as st
import streamlit.components.v1 as components
import sys
import os
import json
import time
from urllib.parse import unquote
from pathlib import Path

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
st.set_page_config(
    page_title="RepoRoverAI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Initialize Session State ---
if 'repo_data' not in st.session_state:
    st.session_state['repo_data'] = None
if 'repo_name' not in st.session_state:
    st.session_state['repo_name'] = None
if 'generated_lessons' not in st.session_state:
    st.session_state['generated_lessons'] = None
if 'current_quiz' not in st.session_state:
    st.session_state['current_quiz'] = None
if 'active_panel' not in st.session_state:
    st.session_state['active_panel'] = 'graph'  # 'graph', 'explain', 'lesson', 'quiz'

# --- Left Sidebar ---
with st.sidebar:
    st.title("RepoRoverAI 🤖")
    st.markdown("---")
    
    # Repo Input
    repo_url = st.text_input(
        "GitHub Repository URL:",
        placeholder="https://github.com/owner/repo"
    )
    
    # Process URL & Show Status
    if repo_url:
        owner, repo = parse_github_url(repo_url)
        if owner and repo:
            repo_name = f"{owner}/{repo}"
            
            if st.session_state.get('repo_name') == repo_name:
                st.success(f"✅ {repo_name} loaded")
            else:
                try:
                    with st.spinner("Checking cache..."):
                        cached_data = db.get_repo_data_from_db(repo_name)
                    
                    if cached_data:
                        st.session_state['repo_data'] = cached_data
                        st.session_state['repo_name'] = repo_name
                        st.success(f"Loaded {len(cached_data)} chunks!")
                    else:
                        st.info(f"Repository not analyzed yet.")
                        if st.button("🔍 Analyze Repository"):
                            with st.spinner("Processing..."):
                                chunks = ingestion.process_repository(owner, repo)
                                if chunks:
                                    db.save_repo_data_to_db(repo_name, chunks)
                                    st.session_state['repo_data'] = chunks
                                    st.session_state['repo_name'] = repo_name
                                    st.success("Analysis complete!")
                                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.error("Invalid GitHub URL")
    
    # Controls & Legend (when repo is loaded)
    if st.session_state.get('repo_data'):
        st.markdown("---")
        st.markdown("### 🎮 Controls")
        
        # View Toggle
        view_type = st.radio(
            "Visualization Type:",
            ["Interactive Graph", "Mermaid Diagram"],
            key="viz_type"
        )
        
        # Quick Actions
        if st.button("🎓 Generate Lessons"):
            st.session_state['active_panel'] = 'lesson'
            # ... (lesson generation logic) ...
        
        st.markdown("---")
        st.markdown("### 🎨 Legend")
        st.markdown("""
        **Nodes:**
        - 📦 Files (by type)
        - 🎓 Lessons (by level)
        
        **Colors:**
        - 🟨 Python
        - 🟩 JS/TS
        - ⬜ Markdown
        - 🟪 Config
        """)

# --- Main Content Area ---
if st.session_state.get('repo_data'):
    # Two-column layout
    col1, col2 = st.columns([2, 1])  # 2:1 ratio
    
    with col1:  # Left Column - Graph/Visualization
        st.markdown("### 🗺️ Repository Map")
        
        # Build graph data
        nodes, edges = graph_builder.build_graph_from_contexts(
            st.session_state['repo_data'],
            max_files=40
        )
        
        if nodes:
            lessons_data = st.session_state.get('generated_lessons')
            
            # Render based on selected view type
            if st.session_state.get('viz_type') == "Interactive Graph":
                payload = vis_builder.vis_payload(nodes, edges, lessons_data)
                render_vis(payload, height=600)
            else:
                mermaid_src = mermaid.mermaid_from_graph(nodes, edges)
                render_mermaid(mermaid_src)
        else:
            st.warning("Not enough data to generate visualization.")
    
    with col2:  # Right Column - Context Panel
        if st.session_state['active_panel'] == 'explain':
            st.markdown("### 🔍 Code Explainer")
            # ... (explanation panel logic) ...
        
        elif st.session_state['active_panel'] == 'lesson':
            st.markdown("### 🎓 Guided Lesson")
            # ... (lesson view logic) ...
        
        elif st.session_state['active_panel'] == 'quiz':
            st.markdown("### 🧪 Quiz")
            # ... (quiz panel logic) ...
    
    # --- Footer ---
    st.markdown("---")
    footer_cols = st.columns([1, 1, 1])
    
    with footer_cols[0]:
        if Path("data/explain_logs").exists():
            st.markdown("📊 [View Explanation Logs](data/explain_logs)")
    
    with footer_cols[1]:
        st.markdown("🔗 Debug Info")
        if st.checkbox("Show Session State"):
            st.json({k: str(v) for k, v in st.session_state.items()})
    
    with footer_cols[2]:
        st.markdown(f"🏷️ Current Panel: `{st.session_state['active_panel']}`")

else:
    # Initial welcome state
    st.markdown("### Welcome to RepoRoverAI! 👋")
    st.markdown("""
    1. Paste a GitHub repository URL in the sidebar
    2. Click "Analyze Repository" if not cached
    3. Explore the interactive visualization
    4. Click on files to get explanations
    5. Generate lessons to start learning!
    """)