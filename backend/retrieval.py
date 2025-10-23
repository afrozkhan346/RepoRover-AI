import math
from . import embeddings # Import embeddings module

# --- This function is correct ---
def cosine_sim(a: list[float], b: list[float]) -> float:
    """
    Calculates the cosine similarity between two embedding vectors.
    """
    if not a or not b:
        return 0.0
        
    dot = sum(x*y for x,y in zip(a,b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(y*y for y in b))
    
    denominator = (na * nb + 1e-12) # Add epsilon for numerical stability
    if denominator == 0:
        return 0.0
        
    return dot / denominator

# --- ADD THIS FUNCTION BACK ---
def find_relevant_contexts(query: str, contexts: list[dict], top_k: int = 6) -> list[dict]:
    """
    Finds the top_k most relevant contexts from a list based on cosine similarity
    with the query embedding.
    """
    if not contexts:
        return []

    # 1. Generate embedding for the user's query
    query_embedding = embeddings.generate_embedding_query(query)
    if not query_embedding:
        print("Could not generate embedding for the query.")
        return []

    # 2. Calculate similarity for each context
    contexts_with_similarity = []
    for ctx in contexts:
        ctx_embedding = ctx.get('embedding')
        # Only compare if embedding exists and is not None
        if ctx_embedding: 
            similarity = cosine_sim(query_embedding, ctx_embedding)
            contexts_with_similarity.append((similarity, ctx))

    # 3. Sort by similarity (highest first)
    contexts_with_similarity.sort(key=lambda x: x[0], reverse=True)

    # 4. Return the top_k contexts (just the dictionary part)
    top_contexts = [ctx for similarity, ctx in contexts_with_similarity[:top_k]]
    
    print(f"Found {len(top_contexts)} relevant contexts for query.")
    return top_contexts