import re
import hashlib

# Regex patterns (from your plan)
FUNC_PATTERN = re.compile(r'(?:function\s+([a-zA-Z0-9_$]+)\s*\(|([a-zA-Z0-9_$]+)\s*=\s*function\s*\(|([a-zA-Z0-9_$]+)\s*:\s*function\s*\()')
EXPORT_FN = re.compile(r'export\s+(?:default\s+)?function\s+([a-zA-Z0-9_$]+)\s*\(')

def extract_js_contexts(text, file_path, repo_id, priority, commit_sha=None):
    contexts = []
    lines = text.splitlines()
    
    # --- IMPROVEMENT: Set language based on file extension ---
    language = "typescript" if file_path.endswith(".ts") else "javascript"

    # Naive: find function keyword lines and take next N lines
    for i, line in enumerate(lines):
        if 'function ' in line or '=>' in line:
            # Capture a block of lines
            start = max(0, i-2) # Include a couple lines before
            end = min(len(lines), i+40) # Grab a 40-line block
            block = "\n".join(lines[start:end])
            
            name_match = FUNC_PATTERN.search(line) or EXPORT_FN.search(line)
            
            # --- FIX: Find the first non-None capture group for the name ---
            name = next((g for g in name_match.groups() if g), f'anon_{i}') if name_match else f'anon_{i}'
            
            ctx = {
                "id": f"{repo_id}:{file_path}:{name}:{start+1}",
                "repo_id": repo_id,
                "file_path": file_path,
                "language": language,
                "start_line": start+1,
                "end_line": end,
                "chunk_index": 0,
                "excerpt": block[:300].strip() + "...",
                "content": block,
                "commit_sha": commit_sha,
                "checksum": hashlib.sha256(block.encode('utf-8')).hexdigest(),
                "embedding": None,
                "priority": priority
            }
            contexts.append(ctx)
            
    # Fallback: if no functions, add whole file as single context
    if not contexts:
        block = text[:20000] # Limit to 20k chars
        contexts.append({
            "id": f"{repo_id}:{file_path}:0",
            "repo_id": repo_id,
            "file_path": file_path,
            "language": language,
            "start_line": 1,
            "end_line": len(lines),
            "chunk_index": 0,
            "excerpt": block[:300].strip() + "...",
            "content": block,
            "commit_sha": commit_sha,
            "checksum": hashlib.sha256(block.encode('utf-8')).hexdigest(),
            "embedding": None,
            "priority": priority
        })
    return contexts