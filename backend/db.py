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
    Saves a list of ingested chunks to Firestore using smaller batched writes.
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
    
    # Use a smaller batch size (50 instead of 100) to stay well under limits
    BATCH_SIZE = 50
    total_saved = 0
    current_batch = db.batch()
    
    try:
        # Set repo metadata first
        current_batch.set(repo_doc_ref, {
            "repo_name": repo_name, 
            "chunk_count": len(chunks),
            "last_updated": firestore.SERVER_TIMESTAMP
        })

        for i, chunk in enumerate(chunks):
            # Create a unique ID for each chunk document
            chunk_doc_id = f"chunk_{i:04d}" 
            chunk_doc_ref = chunks_collection_ref.document(chunk_doc_id)
            
            # Add the set operation to the batch
            current_batch.set(chunk_doc_ref, chunk)
            
            # Commit when batch reaches size limit or on last chunk
            if (i + 1) % BATCH_SIZE == 0 or i == len(chunks) - 1:
                print(f"Committing batch {total_saved//BATCH_SIZE + 1} ({total_saved + 1}-{i + 1} of {len(chunks)} chunks)...")
                current_batch.commit()
                total_saved = i + 1
                
                # Start a new batch if there are more chunks
                if i < len(chunks) - 1:
                    current_batch = db.batch()
                    # Re-add repo metadata to ensure consistency
                    current_batch.set(repo_doc_ref, {
                        "repo_name": repo_name, 
                        "chunk_count": len(chunks),
                        "last_updated": firestore.SERVER_TIMESTAMP
                    })

        print(f"✅ Successfully saved all {len(chunks)} chunks for {repo_name} to Firestore.")
        return True

    except Exception as e:
        print(f"❌ Error saving to Firestore: {e}")
        st.error(f"Database error: {str(e)}")
        # Attempt to save what we can
        if total_saved > 0:
            print(f"Partial save: {total_saved} of {len(chunks)} chunks were saved.")
            # Update metadata to reflect partial save
            try:
                repo_doc_ref.set({
                    "repo_name": repo_name,
                    "chunk_count": total_saved,
                    "last_updated": firestore.SERVER_TIMESTAMP,
                    "partial_save": True,
                    "total_chunks": len(chunks)
                })
            except Exception as metadata_e:
                print(f"Failed to update metadata after partial save: {metadata_e}")
        return False