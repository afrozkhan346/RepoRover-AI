import streamlit as st
import google.generativeai as genai
import time
from google.api_core import exceptions # Keep this import

# --- Gemini API Setup ---
API_KEY = st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found...")

genai.configure(api_key=API_KEY)
EMBEDDING_MODEL = "models/text-embedding-004"
BATCH_SIZE = 100
MAX_RETRIES = 3 # Keep this

def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generates embeddings for a list of texts in batches with retry logic.
    """
    all_embeddings = []
    
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i+BATCH_SIZE]
        print(f"Embedding batch {i//BATCH_SIZE + 1}/{len(texts)//BATCH_SIZE + 1}...")
        
        # --- ADD RETRY LOGIC BACK ---
        retries = 0
        while retries < MAX_RETRIES:
            try:
                result = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=batch,
                    task_type="RETRIEVAL_DOCUMENT"
                )
                all_embeddings.extend(result['embedding'])
                break # Success! Exit the retry loop
                
            except exceptions.DeadlineExceeded as e:
                retries += 1
                print(f"Gemini API timeout (Attempt {retries}/{MAX_RETRIES}). Retrying in 5 seconds...")
                time.sleep(5) # Wait before retrying
            except Exception as e:
                print(f"Error embedding batch: {e}")
                all_embeddings.extend([None] * len(batch)) # Add None for failed items
                break # Don't retry on other errors

        # Check if we exhausted retries after the loop
        if retries == MAX_RETRIES:
            print(f"Failed to embed batch after {MAX_RETRIES} attempts. Skipping.")
            all_embeddings.extend([None] * len(batch)) # Mark batch as failed
            
    return all_embeddings

# --- Function to embed a single query (Keep this as it was) ---
def generate_embedding_query(query: str) -> list[float] | None:
    """Generates an embedding for a single query string with retry logic."""
    retries = 0
    while retries < MAX_RETRIES:
        try:
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=query,
                task_type="RETRIEVAL_QUERY" # Use QUERY type here
            )
            return result['embedding']
        except exceptions.DeadlineExceeded as e:
            retries += 1
            print(f"Query Embedding Timeout (Attempt {retries}/{MAX_RETRIES}). Retrying...")
            time.sleep(5)
        except Exception as e:
            print(f"Error embedding query: {e}")
            return None # Return None on other errors
    
    print(f"Failed to embed query after {MAX_RETRIES} attempts.")
    return None