import ast
import hashlib

def extract_python_contexts(text, file_path, repo_id, commit_sha=None):
    """
    Extracts module docstring, functions, and classes from Python code
    using an Abstract Syntax Tree (AST).
    """
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        print(f"Skipping {file_path}, invalid Python syntax: {e}")
        return []
        
    contexts = []

    # Module docstring
    module_doc = ast.get_docstring(tree)
    if module_doc:
        ctx = {
            "id": f"{repo_id}:{file_path}:module:0",
            "repo_id": repo_id,
            "file_path": file_path,
            "language": "python",
            "start_line": 1,
            "end_line": module_doc.count("\n")+1,
            "chunk_index": 0,
            "excerpt": module_doc[:400].strip(),
            "content": module_doc,
            "commit_sha": commit_sha,
            "checksum": hashlib.sha256(module_doc.encode('utf-8')).hexdigest(),
            "embedding": None
        }
        contexts.append(ctx)

    # function and class nodes
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = getattr(node, 'lineno', None)
            end = getattr(node, 'end_lineno', None)
            
            # Extract source lines (requires original text)
            block = ast.get_source_segment(text, node)
            
            if not block:
                # Fallback for nodes without a direct source segment
                lines = text.splitlines()
                if start and end:
                    block = "\n".join(lines[start-1:end])
                else:
                    block = node.name # Last resort

            if not block:
                continue # Skip if we couldn't get content

            # If the block is long, you will chunk later (see chunker)
            ctx = {
                "id": f"{repo_id}:{file_path}:{node.name}:{start}",
                "repo_id": repo_id,
                "file_path": file_path,
                "language": "python",
                "start_line": start,
                "end_line": end or start,
                "chunk_index": 0,
                "excerpt": block[:400].strip(),
                "content": block,
                "commit_sha": commit_sha,
                "checksum": hashlib.sha256(block.encode('utf-8')).hexdigest(),
                "embedding": None
            }
            contexts.append(ctx)
    return contexts