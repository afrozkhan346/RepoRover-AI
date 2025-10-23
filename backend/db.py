import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account

# --- Firestore Connection ---

@st.cache_resource
def get_firestore_client():
    """
    Connects to Firestore using Streamlit's secrets.
    Uses @st.cache_resource to only run this connection once.
    """
    creds_json = st.secrets["firestore"]
    creds = service_account.Credentials.from_service_account_info(creds_json)
    db = firestore.Client(credentials=creds)
    return db

def get_repo_data_from_db(repo_name):
    """
    Fetches all ingested chunks for a repo from its 'chunks' subcollection.
    """
    db = get_firestore_client()
    doc_id = repo_name.replace("/", "_")
    
    # Reference the 'chunks' subcollection
    chunks_ref = db.collection("repo_contexts").document(doc_id).collection("chunks")
    
    # Get all documents from the subcollection
    docs = chunks_ref.stream()
    
    chunks_list = [doc.to_dict() for doc in docs]
    
    if chunks_list:
        print(f"Found {len(chunks_list)} cached chunks for {repo_name} in Firestore.")
        return chunks_list
    else:
        print(f"No cached data for {repo_name} in Firestore.")
        return None

def save_repo_data_to_db(repo_name, chunks):
    """
    Saves a list of ingested chunks to Firestore using batched writes.
    Each chunk becomes a separate document in a 'chunks' subcollection.
    """
    if not chunks:
        print("No chunks to save.")
        return

    db = get_firestore_client()
    doc_id = repo_name.replace("/", "_")
    
    # Get a reference to the main repo document
    repo_doc_ref = db.collection("repo_contexts").document(doc_id)
    
    # Get a reference to the 'chunks' subcollection
    chunks_collection_ref = repo_doc_ref.collection("chunks")
    
    # Initialize a batch
    batch = db.batch()
    
    # Set a small metadata document just to show the repo exists
    batch.set(repo_doc_ref, {"repo_name": repo_name, "chunk_count": len(chunks)})
    
    # Firestore batches are limited by size (10MB) and ops (500).
    # We use a smaller op limit (250) to stay safely under the 10MB size limit.
    for i, chunk in enumerate(chunks):
        # Create a unique ID for each chunk document
        chunk_doc_id = f"chunk_{i:04d}" 
        chunk_doc_ref = chunks_collection_ref.document(chunk_doc_id)
        
        # Add the set operation to the batch
        batch.set(chunk_doc_ref, chunk)
        
        # --- THIS IS THE FIX ---
        # Commit every 100 chunks and start a new batch.
        if (i + 1) % 100 == 0:
            print(f"Committing batch of {i+1} chunks...")
            batch.commit()
            batch = db.batch() # Start a new batch
            
            # Re-add the repo doc set to the new batch (it's safe to set multiple times)
            batch.set(repo_doc_ref, {"repo_name": repo_name, "chunk_count": len(chunks)})


    # Commit any remaining chunks in the last batch
    try:
        batch.commit()
        print(f"Successfully saved {len(chunks)} chunks for {repo_name} to Firestore.")
    except Exception as e:
        print(f"Error committing final batch to Firestore: {e}")
        st.error(f"Error saving to database: {e}")