import json
import os
import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import streamlit as st

# Define the log directory relative to this file
# (backend/logger.py -> backend/ -> RepoRover-AI/ -> data/logs)
try:
    SCRIPT_DIR = Path(__file__).resolve().parent.parent
    LOG_DIR = SCRIPT_DIR / "data" / "logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Logger initialized. Log directory set to: {LOG_DIR}")
except Exception as e:
    print(f"Warning: Could not create log directory at {LOG_DIR}. Error: {e}")
    LOG_DIR = None

def get_user_from_state() -> str:
    """Safely gets the user's login from session state."""
    if st.session_state.get('user'):
        return st.session_state['user'].get('login', 'unknown_user')
    return "anonymous"

def get_repo_from_state() -> str:
    """Safely gets the repo_id from session state."""
    return st.session_state.get('repo_id', 'N/A')

def log_event(event_type: str, data: Dict[str, Any]):
    """
    Writes a standardized event to its corresponding JSONL log file.
    Automatically enriches with timestamp, user, and repo.
    """
    if not LOG_DIR:
        print(f"Logging skipped (LOG_DIR not set): {event_type}")
        return

    try:
        # Enrich the log entry with standard info
        log_entry = {
            "event_id": f"{event_type}_{int(datetime.datetime.now().timestamp() * 1000)}",
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": event_type,
            "user_login": get_user_from_state(),
            "repo_id": get_repo_from_state(),
            "data": data # The specific event data
        }

        # Define the log file (e.g., data/logs/llm_calls.jsonl)
        log_filename = f"{event_type}_log.jsonl"
        log_filepath = LOG_DIR / log_filename

        # Append the JSON object as a new line
        with open(log_filepath, 'a', encoding='utf-8') as f:
            json.dump(log_entry, f, ensure_ascii=False)
            f.write('\n') # Newline for JSONL format
            
    except Exception as e:
        print(f"CRITICAL: Failed to write log event '{event_type}'. Error: {e}")
        print(f"Data: {data}")