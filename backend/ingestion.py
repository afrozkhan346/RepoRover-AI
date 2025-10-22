import base64
from . import gh_fetch
from . import chunker
import os
import re
import streamlit as st

# --- Read settings from environment ---
MAX_FILE_SIZE = int(st.secrets.get("MAX_FILE_SIZE_BYTES", 200000))
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 3000))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", 200))
MAX_FILES_TO_PROCESS = int(st.secrets.get("MAX_FILES_TO_PROCESS", 100))

# --- 3. File Selection Heuristics ---

# Blacklist extensions (unchanged)
BLACKLIST_EXTENSIONS = (
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp', # Images
    '.pdf', '.epub', '.zip', '.gz', '.tar', '.rar', '.7z',   # Archives/Docs
    '.mp4', '.mov', '.avi', '.mp3', '.wav',                  # Media
    '.lock', '.log', '.sqlite', '.db',                       # Logs/DBs
    '.exe', '.dll', '.so', '.a', '.o',                       # Binaries
)

# Blacklist paths (updated from your list)
BLACKLIST_PATHS = (
    '.git/',
    'node_modules/',
    'dist/',
    'build/',
    'vendor/', # <-- Added from your list
    '__pycache__/',
    '.venv/',
    'venv/',
)

# --- NEW: Priority Lists (from your plan) ---
# We'll check these in order. Regex is used for flexibility.
# Note: 'docs/' is in Prio 1 AND Prio 6, we'll keep it in Prio 1.
PRIO_1_README_DOCS = (r'README(\..*)?$', r'docs\/') # Matches README, README.md, docs/
PRIO_2_MANIFESTS = ('package.json', 'pyproject.toml', 'requirements.txt', 'setup.py', 'go.mod', 'pom.xml')
PRIO_3_CI_DOCKER = (r'\.github\/workflows\/', 'Dockerfile', r'docker-compose(\.yml|\.yaml)?$')
PRIO_4_SRC = ('src/', 'lib/', 'app/', r'packages\/[^\/]+\/src\/') # [^/]+ means any folder name
PRIO_5_TESTS = ('tests/', 'test/', 'spec/')
PRIO_6_CONTRIB = ('CONTRIBUTING.md', 'CHANGELOG.md', 'LICENSE')

def get_file_priority(path):
    """
    Assigns a priority score to a file path based on heuristics.
    Lower number = higher priority.
    Returns -1 if the file should be explicitly blacklisted.
    """
    path_lower = path.lower()

    # CRITICAL: Highest priority check is to *exclude* secrets
    if re.search(r'\.env(\.|$)', path_lower):
        return -1 # -1 means blacklist

    # Prio 1
    for pattern in PRIO_1_README_DOCS:
        if re.search(pattern, path_lower):
            return 1
    
    # Prio 2
    if any(path_lower.endswith(f) for f in PRIO_2_MANIFESTS):
        return 2

    # Prio 3
    for pattern in PRIO_3_CI_DOCKER:
        if re.search(pattern, path_lower):
            return 3
    
    # Prio 4
    for pattern in PRIO_4_SRC:
        if path_lower.startswith(pattern):
            return 4
            
    # Prio 5
    for pattern in PRIO_5_TESTS:
        if path_lower.startswith(pattern):
            return 5
    
    # Prio 6
    if any(path_lower.endswith(f.lower()) for f in PRIO_6_CONTRIB):
        return 6

    # Default priority for any other text file
    return 99

# --- REMOVED: filter_file_list() function is no longer needed ---

# --- 5. Chunking (unchanged) ---
def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
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

# --- 6. Context Object Creation (HEAVILY UPDATED) ---

def process_repository(owner, repo):
    """
    Main ingestion flow:
    1. Get repo tree
    2. Filter, prioritize, and sort files
    3. Fetch content for each file (up to MAX_FILES_TO_PROCESS)
    4. Chunk content
    5. Create context objects
    """
    print(f"Starting ingestion for {owner}/{repo}")
    
    # 1. Get full repo tree
    tree = gh_fetch.get_repo_tree(owner, repo)
    if not tree:
        print("Could not fetch repo tree.")
        return []

    # 2. Filter, prioritize, and sort files
    files_to_process = []
    for item in tree:
        if item['type'] != 'blob': # Skip directories
            continue
        
        path = item['path']
        
        # --- Run Blacklist Checks ---
        if item.get('size', 0) > MAX_FILE_SIZE:
            print(f"Skipping {path} (file size > {MAX_FILE_SIZE})")
            continue
        
        if path.lower().endswith(BLACKLIST_EXTENSIONS) or any(path.lower().startswith(p) for p in BLACKLIST_PATHS):
            continue
        
        # --- Get Priority ---
        priority = get_file_priority(path)
        
        if priority == -1: # Blacklisted by priority function (e.g., .env)
            print(f"Skipping {path} (blacklisted by priority rule)")
            continue

        # Add valid file to our list
        files_to_process.append({'item': item, 'priority': priority})

        # --- NEW: Secret Detection Logic ---

        # We compile the regex patterns once for efficiency
        SECRET_PATTERNS_COMPILED = [
            re.compile(r'AKIA[0-9A-Z]{16}'),                      # AWS Key
            re.compile(r'AIza[0-9A-Za-z-_]{35}'),                 # Google API Key
            re.compile(r'-----BEGIN PRIVATE KEY-----'),          # PEM Private Key
            re.compile(r'SECRET\s*=', re.IGNORECASE),            # SECRET =
            re.compile(r'API_KEY\s*=', re.IGNORECASE),           # API_KEY =
            re.compile(r'password\s*[:=]', re.IGNORECASE)        # password: or password=
        ]

        def contains_secrets(content):
            """
            Checks if a string contains common secret patterns.
            Returns True if a secret is found, False otherwise.
            """
            for pattern in SECRET_PATTERNS_COMPILED:
                if pattern.search(content):
                    return True
            return False
            
    # --- Sort by priority (lower is better) ---
    # As a tie-breaker, sort by size (descending) to get larger source files first
    files_to_process.sort(key=lambda x: (x['priority'], -x['item'].get('size', 0)))
    
    print(f"Found {len(files_to_process)} valid files. Processing top {MAX_FILES_TO_PROCESS}...")
    
    # --- Truncate to MAX_FILES_TO_PROCESS ---
    if len(files_to_process) > MAX_FILES_TO_PROCESS:
        files_to_process = files_to_process[:MAX_FILES_TO_PROCESS]
        
    all_context_objects = []
    repo_id = f"{owner}/{repo}"
    
    # 3. Fetch content for each file in the sorted list
    for file_info in files_to_process:
        item = file_info['item']
        priority = file_info['priority']
        path = item['path']
        sha = item['sha']
        
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

        # --- 
        # --- ADD THIS CHECK ---
        # ---
        if contains_secrets(file_content):
            print(f"Skipping {path} (contains potential secrets)")
            continue # Skip this file entirely
        # ---
        # --- END OF NEW CHECK ---
        # ---
            
        # 4. Chunk content
        chunks = chunk_text(file_content)
        
        # 5. Create context objects
        for i, content_chunk in enumerate(chunks):
            obj = {
                "id": f"{repo_id}:{path}:{i}",
                "repo_id": repo_id,
                "path": path,
                "excerpt": content_chunk[:150] + "...",
                "chunk_index": i,
                "content": content_chunk,
                "priority": priority, # <-- Store the priority!
            }
            all_context_objects.append(obj)
            
    print(f"Ingestion complete. Created {len(all_context_objects)} context objects from {len(files_to_process)} files.")
    return all_context_objects