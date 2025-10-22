import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json

# --- Firestore Connection ---

@st.cache_resource
def get_firestore_client():
    """
    Connects to Firestore using Streamlit's secrets.
    Uses @st.cache_resource to only run this connection once.
    """
    # Get the credentials from st.secrets
    creds_json = st.secrets["firestore"]
    creds = service_account.Credentials.from_service_account_info(creds_json)
    db = firestore.Client(credentials=creds)
    return db

def get_repo_data_from_db(repo_name):
    """
    Fetches ingested data for a specific repo from Firestore.
    'repo_name' should be in 'owner/repo' format.
    """
    db = get_firestore_client()
    
    # We'll use the repo_name as the document ID
    # We replace '/' with '_' to create a valid Firestore doc ID
    doc_id = repo_name.replace("/", "_")
    doc_ref = db.collection("repo_contexts").document(doc_id)
    
    doc = doc_ref.get()
    if doc.exists:
        print(f"Found cached data for {repo_name} in Firestore.")
        return doc.to_dict().get("chunks", [])
    else:
        print(f"No cached data for {repo_name} in Firestore.")
        return None

def save_repo_data_to_db(repo_name, chunks):
    """
    Saves a list of ingested chunks to Firestore.
    'repo_name' is the doc ID, 'chunks' is the data.
    """
    if not chunks:
        print("No chunks to save.")
        return

    db = get_firestore_client()
    doc_id = repo_name.replace("/", "_")
    doc_ref = db.collection("repo_contexts").document(doc_id)
    
    # Firestore has a 1MB limit per document.
    # For a hackathon, we'll save it all in one go.
    # A safer production app would split this, but this is fine.
    data = {"chunks": chunks}
    
    try:
        doc_ref.set(data)
        print(f"Successfully saved {len(chunks)} chunks for {repo_name} to Firestore.")
    except Exception as e:
        print(f"Error saving to Firestore: {e}")
        st.error(f"Error saving to database. The repo might be too large: {e}")