import ast
import hashlib
import streamlit as st
from . import chunker

# --- Read BOTH sets of chunking rules from st.secrets ---
PROSE_CHUNK_SIZE = int(st.secrets.get("CHUNK_SIZE", 3000))
PROSE_CHUNK_OVERLAP = int(st.secrets.get("CHUNK_OVERLAP", 200))
CODE_CHUNK_SIZE = int(st.secrets.get("CODE_CHUNK_SIZE", 1200))
CODE_CHUNK_OVERLAP = int(st.secrets.get("CODE_CHUNK_OVERLAP", 100))


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
        # Check if docstring is too long (it's prose)
        if len(module_doc) > PROSE_CHUNK_SIZE:
            # Chunk it using prose settings
            doc_chunks = chunker.chunk_text(module_doc, PROSE_CHUNK_SIZE, PROSE_CHUNK_OVERLAP)
            for i, chunk in enumerate(doc_chunks):
                contexts.append({
                    "id": f"{repo_id}:{file_path}:module:{i}",
                    "repo_id": repo_id, "file_path": file_path, "language": "python",
                    "start_line": 1, "end_line": module_doc.count("\n")+1, # Line numbers are approximate
                    "chunk_index": i, "excerpt": chunk[:400].strip(), "content": chunk,
                    "commit_sha": commit_sha, "checksum": hashlib.sha256(chunk.encode('utf-8')).hexdigest(),
                    "embedding": None
                })
        else:
            # Keep it as one context
            contexts.append({
                "id": f"{repo_id}:{file_path}:module:0",
                "repo_id": repo_id, "file_path": file_path, "language": "python",
                "start_line": 1, "end_line": module_doc.count("\n")+1,
                "chunk_index": 0, "excerpt": module_doc[:400].strip(), "content": module_doc,
                "commit_sha": commit_sha, "checksum": hashlib.sha256(module_doc.encode('utf-8')).hexdigest(),
                "embedding": None
            })

    # function and class nodes
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = getattr(node, 'lineno', None)
            end = getattr(node, 'end_lineno', None)
            block = ast.get_source_segment(text, node)
            if not block: continue
            
            # Check if code block is too long
            if len(block) > CODE_CHUNK_SIZE:
                # Chunk it using code settings
                code_chunks = chunker.chunk_text(block, CODE_CHUNK_SIZE, CODE_CHUNK_OVERLAP)
                for i, chunk in enumerate(code_chunks):
                    contexts.append({
                        "id": f"{repo_id}:{file_path}:{node.name}:{start}:{i}",
                        "repo_id": repo_id, "file_path": file_path, "language": "python",
                        "start_line": start, "end_line": end, # Line numbers for whole block
                        "chunk_index": i, "excerpt": chunk[:400].strip(), "content": chunk,
                        "commit_sha": commit_sha, "checksum": hashlib.sha256(chunk.encode('utf-8')).hexdigest(),
                        "embedding": None
                    })
            else:
                # Keep it as one context
                contexts.append({
                    "id": f"{repo_id}:{file_path}:{node.name}:{start}:0",
                    "repo_id": repo_id, "file_path": file_path, "language": "python",
                    "start_line": start, "end_line": end,
                    "chunk_index": 0, "excerpt": block[:400].strip(), "content": block,
                    "commit_sha": commit_sha, "checksum": hashlib.sha256(block.encode('utf-8')).hexdigest(),
                    "embedding": None
                })
    return contexts