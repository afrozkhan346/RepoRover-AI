import requests
import streamlit as st
import base64
import os
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# --- GitHub API Helpers ---

def _get_github_headers():
    """Returns headers for GitHub API requests, including auth if available."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers

@st.cache_data(ttl=600)
def get_repo_details(owner, repo):
    """Gets main repository details, including the default branch."""
    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    response = requests.get(api_url, headers=_get_github_headers())
    response.raise_for_status()
    return response.json()

@st.cache_data(ttl=600)
def get_repo_tree(owner, repo):
    """
    Fetches the full, recursive file tree for the default branch.
    This is much more efficient than walking the 'contents' endpoint.
    """
    # 1. Get default branch name
    try:
        repo_details = get_repo_details(owner, repo)
        default_branch = repo_details.get('default_branch')
        if not default_branch:
            return None
    except Exception as e:
        print(f"Error getting repo details: {e}")
        return None

    # 2. Get the tree
    api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=true"
    
    try:
        response = requests.get(api_url, headers=_get_github_headers())
        response.raise_for_status()
        tree_data = response.json()
        
        if tree_data.get('truncated'):
            st.warning("Repository is too large! File list is truncated.")
            
        return tree_data.get('tree', []) # Return the list of file objects
    except Exception as e:
        print(f"Error getting repo tree: {e}")
        st.error(f"Failed to fetch repository tree. Rate limit exceeded? Error: {e}")
        return None

@st.cache_data(ttl=600)
def get_file_blob(owner, repo, file_sha):
    """
    Fetches a single file's content (blob) using its SHA.
    Returns the base64-encoded content.
    """
    api_url = f"https://api.github.com/repos/{owner}/{repo}/git/blobs/{file_sha}"
    try:
        response = requests.get(api_url, headers=_get_github_headers())
        response.raise_for_status()
        return response.json().get('content') # This is base64 encoded
    except Exception as e:
        print(f"Error fetching blob {file_sha}: {e}")
        return None

# (You can keep get_readme or remove it, as the tree/blob flow is more complete)
@st.cache_data(ttl=600)
def get_readme(owner, repo):
    # ... (existing function) ...
    pass