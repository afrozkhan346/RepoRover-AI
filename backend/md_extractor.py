import re
import hashlib
import streamlit as st
from . import chunker

# --- 2. Read PROSE chunking rules ---
PROSE_CHUNK_SIZE = int(st.secrets.get("CHUNK_SIZE", 3000))
PROSE_CHUNK_OVERLAP = int(st.secrets.get("CHUNK_OVERLAP", 200))


def extract_markdown_sections(text, file_path, repo_id, priority, commit_sha=None):
    # ... (The regex logic to split 'parts' and 'sections' is unchanged) ...
    parts = re.split(r'(^#{1,6}\s.*?$)', text, flags=re.MULTILINE)
    sections = []

    title = "Introduction"
    buf = parts[0]

    for i in range(1, len(parts), 2):
        if buf.strip():
            sections.append((title.strip(), buf.strip()))
        title = parts[i].strip()
        buf = parts[i+1]
    if buf.strip():
        sections.append((title.strip(), buf.strip()))

    contexts = []
    
    # --- 3. Update the loop to conditionally chunk ---
    for i, (title, body) in enumerate(sections):
        ctx_text = f"{title}\n\n{body}"
        
        # Check if the section is too long
        if len(ctx_text) > PROSE_CHUNK_SIZE:
            # Chunk it using prose settings
            md_chunks = chunker.chunk_text(ctx_text, PROSE_CHUNK_SIZE, PROSE_CHUNK_OVERLAP)
            for j, chunk in enumerate(md_chunks):
                contexts.append({
                    "id": f"{repo_id}:{file_path}:section:{i}:{j}",
                    "repo_id": repo_id, "file_path": file_path, "language": "markdown",
                    "start_line": None, "end_line": None,
                    "chunk_index": j, "excerpt": chunk[:400].strip() + "...", "content": chunk,
                    "commit_sha": commit_sha, "checksum": hashlib.sha256(chunk.encode('utf-8')).hexdigest(),
                    "embedding": None,
                    "priority": priority
                })
        else:
            # Keep it as one context
            contexts.append({
                "id": f"{repo_id}:{file_path}:section:{i}:0",
                "repo_id": repo_id, "file_path": file_path, "language": "markdown",
                "start_line": None, "end_line": None,
                "chunk_index": 0, "excerpt": ctx_text[:400].strip() + "...", "content": ctx_text,
                "commit_sha": commit_sha, "checksum": hashlib.sha256(ctx_text.encode('utf-8')).hexdigest(),
                "embedding": None,
                "priority": priority
            })
    return contexts