# delete_firestore_doc.py
import sys
from google.cloud import firestore
from google.oauth2 import service_account

# --- CONFIGURATION ---
# IMPORTANT: Replace with the actual path to your service account key file
SERVICE_ACCOUNT_FILE = "gen-lang-client-0753746276-f31ca33fa93d.json"

# The name of the repo document you want to delete (e.g., "pallets_flask")
REPO_DOC_ID_TO_DELETE = "pallets_flask" 
# --- END CONFIGURATION ---

BATCH_SIZE = 100 # Delete in batches of 100

def delete_collection(coll_ref, batch_size):
    """Recursively deletes documents in a collection in batches."""
    docs = coll_ref.limit(batch_size).stream()
    deleted = 0

    for doc in docs:
        print(f"Deleting doc {doc.id} => {doc.to_dict()}")
        doc.reference.delete()
        deleted += 1

    if deleted >= batch_size:
        return delete_collection(coll_ref, batch_size) # Recurse if more docs exist

def main(repo_doc_id):
    try:
        # Initialize Firestore client
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
        db = firestore.Client(credentials=creds)
        print("Firestore client initialized.")

        # Get reference to the main document and its subcollection
        doc_ref = db.collection("repo_contexts").document(repo_doc_id)
        chunks_coll_ref = doc_ref.collection("chunks")

        # Delete the subcollection first
        print(f"\n--- Deleting 'chunks' subcollection for {repo_doc_id} ---")
        delete_collection(chunks_coll_ref, BATCH_SIZE)
        print("--- Subcollection deletion complete. ---")

        # Delete the main document
        print(f"\n--- Deleting main document {repo_doc_id} ---")
        doc_ref.delete()
        print("--- Main document deleted. ---")

        print("\nDeletion finished successfully.")

    except FileNotFoundError:
        print(f"ERROR: Service account file not found at '{SERVICE_ACCOUNT_FILE}'.")
        print("Please ensure the file exists and the path is correct.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        doc_id = sys.argv[1] # Allow passing doc ID via command line
    else:
        doc_id = REPO_DOC_ID_TO_DELETE # Use the default from config

    print(f"Attempting to delete document '{doc_id}' and its 'chunks' subcollection.")
    main(doc_id)