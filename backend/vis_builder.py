import json
from typing import List, Dict, Any

def vis_payload(nodes: List[Dict], edges: List[Dict], lessons_data: Dict | None = None) -> Dict:
    """
    Creates the JSON payload (nodes and edges lists) for vis-network.
    Includes file nodes, lesson nodes, and edges between them.
    """
    vis_nodes = []
    vis_edges = []

    # Process file nodes
    file_ids = set()
    for n in nodes:
        node_id = n['id']
        file_ids.add(node_id)
        vis_nodes.append({
            "id": node_id,
            "label": n['label'], # Filename
            "title": n.get('title', ''), # Excerpt for tooltip
            "group": n.get('group', 'file'), # Language or 'file'
            "shape": "box",
            "margin": 10,
            "font": {"size": 14}
        })

    # Process file-to-file edges (only include if both nodes exist)
    for e in edges:
        if e['from'] in file_ids and e['to'] in file_ids:
            vis_edges.append({"from": e['from'], "to": e['to'], "arrows": "to"})

    # Process lesson nodes and edges (if lessons_data exists)
    lesson_node_ids = []  # Store node IDs for sequential linking
    if lessons_data and isinstance(lessons_data.get("lessons"), list):
        lessons = lessons_data["lessons"]
        for i, lesson in enumerate(lessons):
            lesson_node_id = f"lesson_{lesson.get('lesson_id', f'L{i+1}')}"
            lesson_node_ids.append(lesson_node_id)  # Store the ID for sequential edges
            
            # Group by lesson level for color coding
            lesson_level = lesson.get('level', 'Beginner').lower()
            lesson_group = f"lesson_{lesson_level}"
            
            vis_nodes.append({
                "id": lesson_node_id,
                # Enhanced label with duration
                "label": f"{lesson.get('lesson_id', f'L{i+1}')}: {lesson.get('title', 'Untitled')} ({lesson.get('duration_minutes', '?')}m)",
                "title": lesson.get('summary', lesson.get('objective', '')), # Tooltip
                "group": lesson_group,  # Group by level: lesson_beginner, lesson_intermediate, lesson_advanced
                "shape": "ellipse",
                # Add level info for potential styling
                "level": lesson.get('level', 'Beginner')
            })

            # Connect lesson -> each source file
            lesson_sources_full = lesson.get('sources_full', [])
            if lesson_sources_full:
                for source_ctx in lesson_sources_full:
                    if isinstance(source_ctx, dict):
                        file_path = source_ctx.get('file_path')
                        if file_path and file_path in file_ids:
                            vis_edges.append({
                                "from": lesson_node_id,
                                "to": file_path,
                                "arrows": "to",
                                "color": {"color": "#a0a0a0", "highlight": "#808080"},
                                "dashes": True,
                                "label": "source"  # Add edge label for clarity
                            })

        # --- ADD SEQUENTIAL LESSON EDGES ---
        if len(lesson_node_ids) > 1:
            for i in range(len(lesson_node_ids) - 1):
                vis_edges.append({
                    "from": lesson_node_ids[i],
                    "to": lesson_node_ids[i+1],
                    "arrows": "to",
                    "color": {"color": "#ffcc00", "highlight": "#ffa500"}, # Golden path edges
                    "dashes": False, # Solid line for lesson sequence
                    "width": 3, # Make path edge thicker to stand out
                    "label": "next"  # Add edge label
                })
        # --- END SEQUENTIAL EDGES ---

    return {"nodes": vis_nodes, "edges": vis_edges}