import re
import hashlib
import os
from collections import defaultdict
from typing import List, Dict, Tuple, Set, Any

# Regex to find Python imports (from X import Y, import X.Y)
IMPORT_RE_PY = re.compile(r'^\s*(?:from\s+([a-zA-Z0-9_.]+)\s+import|import\s+([a-zA-Z0-9_.]+))', re.MULTILINE)
# Regex to find JS imports (require('X'), import Y from 'X')
IMPORT_RE_JS = re.compile(r'^\s*(?:const|let|var)\s+\w+\s*=\s*require\([\'"](.+?)[\'"]\)|import\s+.*\s+from\s+[\'"](.+?)[\'"]', re.MULTILINE)

def detect_import_targets(text: str, lang: str) -> List[str]:
    """
    Uses regex to find potential module/file import targets in code text.
    Returns a list of unique target strings.
    """
    targets: Set[str] = set()
    if lang == 'python':
        for m in IMPORT_RE_PY.finditer(text):
            # Group 1 is 'from X import', Group 2 is 'import X'
            t = m.group(1) or m.group(2)
            if t:
                # Take only the first part (e.g., 'os' from 'os.path') for simplicity
                targets.add(t.split('.')[0])
    elif lang in ('javascript', 'typescript'):
        for m in IMPORT_RE_JS.finditer(text):
            # Group 1 is require('X'), Group 2 is import from 'X'
            t = m.group(1) or m.group(2)
            if t:
                # Often relative paths './component' or names 'react'
                targets.add(t)
    return list(targets)

def build_graph_from_contexts(contexts: List[Dict[str, Any]], max_files: int = 40) -> Tuple[List[Dict], List[Dict]]:
    """
    Builds node and edge lists for visualization from ingested contexts.

    Args:
        contexts: List of context dicts from ingestion.
        max_files: Maximum number of files to include in the graph.

    Returns:
        A tuple containing (nodes list, edges list).
    """
    # Group contexts by file_path and calculate rank score
    files: Dict[str, Dict[str, Any]] = {}
    for c in contexts:
        fp = c['file_path']
        if fp not in files:
            # Store first context's content/excerpt as representative for the file
            files[fp] = {
                'file_path': fp,
                'language': c.get('language', 'text'),
                'content': c.get('content', ''),  # Use full content for import detection
                'excerpt': c.get('excerpt', ''),  # Use excerpt for node title
                'contexts_count': 0,
                'total_excerpt_len': 0
            }
        files[fp]['contexts_count'] += 1
        files[fp]['total_excerpt_len'] += len(c.get('excerpt', ''))

    # Rank files: prioritize by number of contexts, then total excerpt length
    ranked_files_list = sorted(
        files.values(),
        key=lambda x: (x['contexts_count'], x['total_excerpt_len']),
        reverse=True
    )[:max_files]  # Limit to max_files

    # Create a map for quick lookup of included files
    file_map = {f['file_path']: f for f in ranked_files_list}

    # Create nodes for included files
    nodes = []
    for f in ranked_files_list:
        nodes.append({
            "id": f["file_path"],  # Use full path as unique ID
            "label": f["file_path"].split('/')[-1],  # Show only filename as label
            "title": f["excerpt"][:300] + "...",  # Tooltip hint
            "group": f.get("language", "file")  # Group by language for potential coloring
        })

    # Create edges based on naive import detection
    edges = []
    for f in ranked_files_list:
        content = f['content']  # Use the stored full content
        targets = detect_import_targets(content, f['language'])

        # Try to match target modules/paths to filenames in our included file_map
        for t in targets:
            # Handle relative JS paths (e.g., './utils', '../components/Button')
            if t.startswith('.'):
                # Basic relative path resolution
                base_dir = '/'.join(f['file_path'].split('/')[:-1])
                target_path = os.path.normpath(os.path.join(base_dir, t))
                # Check potential file extensions
                possible_paths = [
                    target_path,
                    f"{target_path}.js", f"{target_path}.ts", f"{target_path}.jsx", f"{target_path}.tsx",
                    f"{target_path}/index.js", f"{target_path}/index.ts"  # Common index file pattern
                ]
                for p_path in possible_paths:
                    if p_path in file_map:
                        # Check if it's not an import of itself
                        if f['file_path'] != p_path:
                            edges.append({"from": f['file_path'], "to": p_path})
                        break  # Found a match
            else:
                # Match Python modules or absolute JS imports by suffix
                # (e.g., import 'utils' matches 'src/utils.py')
                module_name = t  # e.g., 'os', 'react', 'utils'
                for candidate_path in file_map.keys():
                    # Check if candidate ends with /module_name.ext or is exactly module_name
                    if (candidate_path.endswith(f'/{module_name}.py') or
                        candidate_path.endswith(f'/{module_name}.js') or
                        candidate_path.endswith(f'/{module_name}.ts') or
                        candidate_path == module_name):  # Match exact name (e.g., 'setup.py')
                        # Check if it's not an import of itself
                        if f['file_path'] != candidate_path:
                            edges.append({"from": f['file_path'], "to": candidate_path})
                        # Don't break here, could match multiple files

    # Deduplicate edges
    seen: Set[Tuple[str, str]] = set()
    unique_edges = []
    for e in edges:
        key = (e['from'], e['to'])
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)

    print(f"📊 Graph built: {len(nodes)} nodes, {len(unique_edges)} edges")
    return nodes, unique_edges