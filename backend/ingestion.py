import base64
from . import gh_fetch
from . import chunker
from . import python_extractor
from . import js_extractor
from . import md_extractor
import os
import re
import streamlit as st
import hashlib

# --- Read settings from environment ---
MAX_FILE_SIZE = int(st.secrets.get("MAX_FILE_SIZE_BYTES", 200000))
# --- FIX: Read all from st.secrets for consistency ---
CHUNK_SIZE = int(st.secrets.get("CHUNK_SIZE", 3000))
CHUNK_OVERLAP = int(st.secrets.get("CHUNK_OVERLAP", 200))
MAX_FILES_TO_PROCESS = int(st.secrets.get("MAX_FILES_TO_PROCESS", 100))

# --- 3. File Selection Heuristics (Unchanged) ---
BLACKLIST_EXTENSIONS = (
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp', # Images
    '.pdf', '.epub', '.zip', '.gz', '.tar', '.rar', '.7z',   # Archives/Docs
    '.mp4', '.mov', '.avi', '.mp3', '.wav',                  # Media
    '.lock', '.log', '.sqlite', '.db',                       # Logs/DBs
    '.exe', '.dll', '.so', '.a', '.o',                       # Binaries
)

# blacklist paths
BLACKLIST_PATHS = (
    '.git/',
    'node_modules/',
    'dist/',
    'build/',
    'vendor/',
    '__pycache__/',
    '.venv/',
    'venv/',
)
PRIO_1_README_DOCS = (r'README(\..*)?$', r'docs\/')
PRIO_2_MANIFESTS = ('package.json', 'pyproject.toml', 'requirements.txt', 'setup.py', 'go.mod', 'pom.xml')
PRIO_3_CI_DOCKER = (r'\.github\/workflows\/', 'Dockerfile', r'docker-compose(\.yml|\.yaml)?$')
PRIO_4_SRC = ('src/', 'lib/', 'app/', r'packages\/[^\/]+\/src\/')
PRIO_5_TESTS = ('tests/', 'test/', 'spec/')
PRIO_6_CONTRIB = ('CONTRIBUTING.md', 'CHANGELOG.md', 'LICENSE')

# --- FIX: Moved Secret Detection to top level ---
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

def get_file_priority(path):
    # (This function is unchanged)
    path_lower = path.lower()

    #CRITICAL: Highest priority check is to 'exclude' sec
    if re.search(r'\.env(\.|$)', path_lower):
        return -1 
    for pattern in PRIO_1_README_DOCS:
        if re.search(pattern, path_lower):
            return 1
        
    if any(path_lower.endswith(f) for f in PRIO_2_MANIFESTS):
        return 2
    
    for pattern in PRIO_3_CI_DOCKER:
        if re.search(pattern, path_lower):
            return 3
        
    for pattern in PRIO_4_SRC:
        if path_lower.startswith(pattern):
            return 4
        
    for pattern in PRIO_5_TESTS:
        if path_lower.startswith(pattern):
            return 5
        
    if any(path_lower.endswith(f.lower()) for f in PRIO_6_CONTRIB):
        return 6
    
    return 99

# --- FIX: Removed old chunk_text function (we import it from chunker.py) ---

# --- 6. Context Object Creation (HEAVILY UPDATED) ---

def process_repository(owner, repo):
    """
    Main ingestion flow:
    1. Get repo tree
    2. Filter, prioritize, and sort files
    3. Fetch content and use file-type extractors
    4. Create context objects
    """
    print(f"Starting ingestion for {owner}/{repo}")
    
    # 1. Get full repo tree AND the commit SHA
    tree, commit_sha = gh_fetch.get_repo_tree(owner, repo)
    if not tree:
        print("Could not fetch repo tree.")
        return []

    # 2. Filter, prioritize, and sort files (Unchanged)
    files_to_process = []
    for item in tree:
        if item['type'] != 'blob':
            continue

        path = item['path']

        if item.get('size', 0) > MAX_FILE_SIZE:
            print(f"Skipping {path} (file size > {MAX_FILE_SIZE})")
            continue

        if path.lower().endswith(BLACKLIST_EXTENSIONS) or any(path.lower().startswith(p) for p in BLACKLIST_PATHS):
            continue

        priority = get_file_priority(path)

        if priority == -1:
            print(f"Skipping {path} (blacklisted by priority rule)")
            continue
        
        # Add valid file to the list
        files_to_process.append({'item': item, 'priority': priority})
            
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
          
        try:
            file_content = base64.b64decode(file_content_base64).decode('utf-8')
        except UnicodeDecodeError:
            print(f"Skipping {path} (not valid utf-8 text)")
            continue
            
        if contains_secrets(file_content):
            print(f"Skipping {path} (contains potential secrets)")
            continue
            
        # --- 4. NEW: FILE-TYPE ROUTER ---
        
        file_contexts = []
        
        if path.endswith('.py'):
            # --- Use the new Python extractor ---
            file_contexts = python_extractor.extract_python_contexts(
                file_content, path, repo_id, commit_sha
            )

            #-- Use the new JS/TS extractor ---
        elif path.endswith(('.js', '.ts')):
            file_contexts = js_extractor.extract_js_contexts(
                file_content, path, repo_id, commit_sha
            )

            #--- Use the new Markdown extractor ---
        elif path.lower().endswith(('.md', '.rst')):
            file_contexts = md_extractor.extract_markdown_sections(
                file_content, path, repo_id, commit_sha
            )
        
        else:
            # --- Use the old chunker as a FALLBACK ---
            chunks = chunker.chunk_text(file_content)
            
            # Determine language for highlighting
            language = "text"
            if path.lower().endswith(('.md', '.rst')): language = "markdown"
            elif path.lower().endswith('.js'): language = "javascript"
            elif path.lower().endswith('.ts'): language = "typescript"
            elif path.lower().endswith('.json'): language = "json"
            elif path.lower().endswith(('.yml', '.yaml')): language = "yaml"
            elif path.lower().endswith('.dockerfile') or 'dockerfile' in path.lower(): language = "dockerfile"

            for i, content_chunk in enumerate(chunks):
                # --- NEW: Create context object using the new schema ---
                checksum = hashlib.sha256(content_chunk.encode('utf-8')).hexdigest()
                ctx = {
                    "id": f"{repo_id}:{path}:chunk:{i}",
                    "repo_id": repo_id,
                    "file_path": path, # Standardize on file_path
                    "language": language,
                    "start_line": None, # We don't know line numbers for simple chunks
                    "end_line": None,
                    "chunk_index": i,
                    "excerpt": content_chunk[:400].strip() + "...",
                    "content": content_chunk,
                    "commit_sha": commit_sha,
                    "checksum": checksum,
                    "embedding": None
                }
                file_contexts.append(ctx)
        
        # 6. Add all contexts from this file to the main list
        all_context_objects.extend(file_contexts)
            
    print(f"Ingestion complete. Created {len(all_context_objects)} context objects from {len(files_to_process)} files.")
    return all_context_objects