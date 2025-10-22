import re
import hashlib

def extract_markdown_sections(text, file_path, repo_id, commit_sha=None):
    """
    Splits a Markdown file into sections based on headings (#, ##, etc.).
    Each section becomes a separate context.
    """
    
    # split on headings (lines starting with 1-6 #)
    parts = re.split(r'(^#{1,6}\s.*?$)', text, flags=re.MULTILINE)
    sections = []
    
    # The first part is the "Introduction" (text before the first heading)
    title = "Introduction"
    buf = parts[0]
    
    # Process the rest of the parts, which come in (heading, content) pairs
    for i in range(1, len(parts), 2):
        # Flush the previous section
        if buf.strip():
            sections.append((title.strip(), buf.strip()))
        
        # Start the new section
        title = parts[i].strip()
        buf = parts[i+1] # The content after the heading
        
    # Add the final section
    if buf.strip():
        sections.append((title.strip(), buf.strip()))

    contexts = []
    for i, (title, body) in enumerate(sections):
        ctx_text = f"{title}\n\n{body}" # Re-combine title and body for the content
        checksum = hashlib.sha256(ctx_text.encode('utf-8')).hexdigest()
        
        contexts.append({
            "id": f"{repo_id}:{file_path}:section:{i}",
            "repo_id": repo_id,
            "file_path": file_path,
            "language": "markdown",
            "start_line": None, # Line numbers are hard to track with this regex
            "end_line": None,
            "chunk_index": i,
            "excerpt": ctx_text[:400].strip() + "...",
            "content": ctx_text,
            "commit_sha": commit_sha,
            "checksum": checksum,
            "embedding": None # Added to match your schema
        })
    return contexts