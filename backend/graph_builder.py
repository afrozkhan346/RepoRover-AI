import re
import hashlib
from collections import defaultdict
from typing import List, Dict, Tuple, Set, Any
import ast  # Add AST module
import os

# Keep JS regex for now (will be moved to a separate function)
IMPORT_RE_JS = re.compile(r'^\s*(?:const|let|var)\s+\w+\s*=\s*require\([\'"](.+?)[\'"]\)|import\s+.*\s+from\s+[\'"](.+?)[\'"]', re.MULTILINE)

def detect_python_imports_ast(code: str) -> Set[str]:
    """
    Parses Python code using AST to find imported top-level modules.
    Returns a set of module names (e.g., {'os', 'flask', 'my_module'}).
    """
    imports = set()
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Add the top-level module (e.g., 'os' from 'os.path')
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                # Add the module being imported from (e.g., 'flask' from 'from flask import ...')
                # Ignore relative imports for simplicity for now (level > 0)
                if node.module and node.level == 0:
                    imports.add(node.module.split('.')[0])
    except SyntaxError:
        # Ignore files with syntax errors that AST can't parse
        print(f"⚠️ AST parse error in Python code")
        pass
    return imports

def detect_js_imports_regex(code: str) -> Set[str]:
    """
    Uses regex to find potential module/file import targets in JavaScript/TypeScript.
    Returns a set of unique target strings.
    """
    targets = set()
    for m in IMPORT_RE_JS.finditer(code):
        # Group 1 is require('X'), Group 2 is import from 'X'
        t = m.group(1) or m.group(2)
        if t:
            # Often relative paths './component' or names 'react'
            targets.add(t)
    return targets

def build_graph_from_contexts(contexts: List[Dict[str, Any]], max_files: int = 40) -> Tuple[List[Dict], List[Dict]]:
    """
    Builds node and edge lists for visualization from ingested contexts.
    Uses AST parsing for Python import detection.
    """
    # Group contexts by file_path and calculate rank score
    files: Dict[str, Dict[str, Any]] = {}
    for c in contexts:
        fp = c['file_path']
        if fp not in files:
            # Store full content of first context for AST parsing
            files[fp] = {
                'file_path': fp,
                'language': c.get('language', 'text'),
                'content': c.get('content', ''),  # Need full content for AST
                'excerpt': c.get('excerpt', ''),
                'contexts_count': 0,
                'total_excerpt_len': 0
            }
        # If we encounter a later context chunk for the same file, append its content
        elif files[fp]['content'] and len(files[fp]['content']) < 20000:  # Limit appended content size
            files[fp]['content'] += "\n" + c.get('content', '')

        files[fp]['contexts_count'] += 1
        files[fp]['total_excerpt_len'] += len(c.get('excerpt', ''))

    # Rank files: prioritize by number of contexts, then total excerpt length
    ranked_files_list = sorted(
        files.values(),
        key=lambda x: (x['contexts_count'], x['total_excerpt_len']),
        reverse=True
    )[:max_files]

    # Create a map for quick lookup of included files
    file_map = {f['file_path']: f for f in ranked_files_list}

    # Create nodes for included files
    nodes = []
    for f in ranked_files_list:
        nodes.append({
            "id": f["file_path"],  # Use full path as unique ID
            "label": f["file_path"].split('/')[-1],  # Show only filename as label
            "title": f["excerpt"][:300] + "...",  # Tooltip hint
            "group": f.get("language", "file")  # Group by language for coloring
        })

    # Create edges based on language-specific import detection
    edges = []
    for f in ranked_files_list:
        content = f['content']  # Use the combined content
        lang = f['language']
        targets = set()

        # Use AST for Python files
        if lang == 'python':
            targets = detect_python_imports_ast(content)
            # Match Python module names to files
            for t in targets:
                module_name = t  # e.g., 'os', 'flask', 'app'
                for candidate_path in file_map.keys():
                    # Check if candidate matches Python module patterns
                    potential_paths = [
                        f"{module_name}.py",
                        f"{module_name}/__init__.py",
                        f"src/{module_name}.py",
                        f"src/{module_name}/__init__.py",
                        f"lib/{module_name}.py",
                        f"lib/{module_name}/__init__.py",
                        f"app/{module_name}.py",
                        f"app/{module_name}/__init__.py",
                    ]
                    # Check if the candidate_path ends with one of these possibilities
                    if any(candidate_path.endswith(p_path) for p_path in potential_paths):
                        if f['file_path'] != candidate_path:  # Avoid self-reference
                            edges.append({"from": f['file_path'], "to": candidate_path})

        # Use regex for JavaScript/TypeScript (keeping existing logic for now)
        elif lang in ('javascript', 'typescript'):
            targets = detect_js_imports_regex(content)
            # Handle relative JS paths
            for t in targets:
                if t.startswith('.'):
                    # Basic relative path resolution
                    base_dir = '/'.join(f['file_path'].split('/')[:-1])
                    target_path = os.path.normpath(os.path.join(base_dir, t))
                    # Check potential file extensions
                    possible_paths = [
                        target_path,
                        f"{target_path}.js", f"{target_path}.ts",
                        f"{target_path}.jsx", f"{target_path}.tsx",
                        f"{target_path}/index.js", f"{target_path}/index.ts"
                    ]
                    for p_path in possible_paths:
                        if p_path in file_map:
                            if f['file_path'] != p_path:
                                edges.append({"from": f['file_path'], "to": p_path})
                            break  # Found a match
                else:
                    # Handle non-relative imports
                    module_name = t
                    for candidate_path in file_map.keys():
                        if (candidate_path.endswith(f'/{module_name}.js') or
                            candidate_path.endswith(f'/{module_name}.ts')):
                            if f['file_path'] != candidate_path:
                                edges.append({"from": f['file_path'], "to": candidate_path})

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