import re
from urllib.parse import urlparse

def parse_github_url(url):
    """
    Parses a GitHub URL to extract the owner and repo.
    Returns (owner, repo) or (None, None) if invalid.
    Supports:
    - https://github.com/owner/repo
    - https://github.com/owner/repo/tree/main
    - owner/repo
    """
    if not url:
        return None, None
        
    url = url.strip()

    # Case 1: Full URL (https://github.com/owner/repo)
    if url.startswith('http'):
        parts = urlparse(url).path.strip('/').split('/')
        if len(parts) >= 2 and parts[0] and parts[1]:
            return parts[0], parts[1]
            
    # Case 2: Short form (owner/repo)
    elif '/' in url:
        parts = url.split('/')
        if len(parts) >= 2 and parts[0] and parts[1]:
            return parts[0], parts[1]

    return None, None