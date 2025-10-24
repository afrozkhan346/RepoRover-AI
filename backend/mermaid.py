from typing import List, Dict

def mermaid_from_graph(nodes: List[Dict], edges: List[Dict], max_nodes: int = 40) -> str:
    """
    Generates a Mermaid flowchart definition string from node and edge lists.
    
    Args:
        nodes: List of node dictionaries with 'id' and 'label' keys
        edges: List of edge dictionaries with 'from' and 'to' keys
        max_nodes: Maximum number of nodes to include in the diagram
    
    Returns:
        Mermaid flowchart definition string
    """
    lines = ["flowchart LR"]  # LR = Left to Right

    # Node IDs need to be Mermaid-safe (no special chars like /, ., -)
    node_id_map = {}
    safe_node_ids = set()

    # Create safe IDs and define nodes
    for i, n in enumerate(nodes[:max_nodes]):
        original_id = n['id']
        # Replace problematic characters with underscores
        safe_id = f"node_{i}_{original_id.replace('/', '_').replace('.', '_').replace('-', '_').replace(':', '_')}"
        node_id_map[original_id] = safe_id
        safe_node_ids.add(safe_id)

        label = n['label']
        # Escape quotes in label if needed
        safe_label = label.replace('"', '#quot;')
        lines.append(f'  {safe_id}["{safe_label}"]')

    # Define edges using safe IDs, only if both nodes are included
    for e in edges:
        from_orig = e['from']
        to_orig = e['to']
        # Only add edge if both nodes were included in the top max_nodes
        if from_orig in node_id_map and to_orig in node_id_map:
            from_safe = node_id_map[from_orig]
            to_safe = node_id_map[to_orig]
            # Ensure edge isn't pointing to itself
            if from_safe != to_safe:
                lines.append(f"  {from_safe} --> {to_safe}")

    return "\n".join(lines)