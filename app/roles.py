import json
from pathlib import Path
import streamlit as st
from typing import List

# Define the path relative to this script's parent's parent (the project root)
SCRIPT_DIR = Path(__file__).resolve().parent
ROLES_FILE = SCRIPT_DIR.parent / "data" / "roles.json"

@st.cache_data(ttl=60) # Cache the roles file for 60 seconds
def get_user_roles(username: str) -> List[str]:
    """
    Fetches the role list for a given GitHub username from the local roles.json file.
    Defaults to ["student"] if user is not listed.
    """
    if not ROLES_FILE.exists():
        print(f"Warning: roles.json file not found at {ROLES_FILE}")
        return ["student"] # Default to student if file is missing
    
    try:
        d = json.loads(ROLES_FILE.read_text())
        # Return the user's roles, or default to ["student"] if they aren't in the file
        return d.get(username, ["student"])
    except Exception as e:
        print(f"Error reading or parsing roles.json: {e}")
        return ["student"] # Default to student on error
