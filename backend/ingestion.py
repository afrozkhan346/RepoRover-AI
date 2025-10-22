import base64
from . import gh_fetch

# --- 3. File Selection Heuristics ---

# Files to explicitly ignore (binaries, locks, common noise)
BLACKLIST_EXTENSIONS = (
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp', # Images
    '.pdf', '.epub', '.zip', '.gz', '.tar', '.rar', '.7z',   # Archives/Docs
    '.mp4', '.mov', '.avi', '.mp3', '.wav',                  # Media
    '.lock', '.log', '.sqlite', '.db',                       # Logs/DBs
    '.exe', '.dll', '.so', '.a', '.o',                       # Binaries
)

# Paths to explicitly ignore
BLACKLIST_PATHS = (
    '.git/',
    'node_modules/',
    'dist/',
    'build/',
    '__pycache__/',
    '.venv/',
    'venv/',
)

# Files to prioritize (e.g., for lessons)
PRIORITY_FILES = (
    'README.md',
    'package.json',
    'requirements.txt',
    'pyproject.toml',
    'go.mod',
    'pom.xml',
    'docker-compose.yml',
    'Dockerfile',
)

def filter_file_list(tree_list):
    """
    Filters the full file tree from GitHub to get a list of
    relevant files to fetch and process.
    """
    files_to_fetch = []
    for item in tree_list:
        if item['type'] != 'blob': # 'blob' means file
            continue
        
        path = item['path']
        
        # Check against blacklists
        if path.endswith(BLACKLIST_EXTENSIONS) or any(path.startswith(p) for p in BLACKLIST_PATHS):
            continue
        
        # Add to list
        files_to_fetch.append(item)
    
    return files_to_fetch

# --- 5. Chunking ---

def chunk_text(text, chunk_size=3000, overlap=200):
    """
    Splits a large text into smaller chunks with overlap.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
        if start >= len(text):
            break
    return chunks

# --- 6. Context Object Creation ---

def process_repository(owner, repo):
    """
    Main ingestion flow:
    1. Get repo tree
    2. Filter for relevant files
    3. Fetch content for each file
    4. Chunk content
    5. Create context objects
    """
    print(f"Starting ingestion for {owner}/{repo}")
    
    # 1. Get full repo tree
    tree = gh_fetch.get_repo_tree(owner, repo)
    if not tree:
        print("Could not fetch repo tree.")
        return []

    # 2. Filter for relevant files
    files_to_process = filter_file_list(tree)
    print(f"Found {len(files_to_process)} files to process.")
    
    all_context_objects = []
    repo_id = f"{owner}/{repo}"
    
    for file_item in files_to_process:
        path = file_item['path']
        sha = file_item['sha']
        
        # 3. Fetch file content
        file_content_base64 = gh_fetch.get_file_blob(owner, repo, sha)
        if not file_content_base64:
            print(f"Skipping {path} (could not fetch content)")
            continue
            
        # Decode content
        try:
            file_content = base64.b64decode(file_content_base64).decode('utf-8')
        except UnicodeDecodeError:
            print(f"Skipping {path} (not valid utf-8 text)")
            continue
            
        # 4. Chunk content
        chunks = chunk_text(file_content)
        
        # 5. Create context objects
        for i, content_chunk in enumerate(chunks):
            obj = {
                "id": f"{repo_id}:{path}:{i}",
                "repo_id": repo_id,
                "path": path,
                "excerpt": content_chunk[:150] + "...", # Short preview
                "chunk_index": i,
                "content": content_chunk,
                "priority": 1 if path in PRIORITY_FILES else 2
            }
            all_context_objects.append(obj)
            
    print(f"Ingestion complete. Created {len(all_context_objects)} context objects.")
    return all_context_objects