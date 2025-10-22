import os

# Read chunking settings from environment variables
DEFAULT_CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 3000))
DEFAULT_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", 200))

def chunk_text(text: str, chunk_size=DEFAULT_CHUNK_SIZE, overlap=DEFAULT_OVERLAP):
    """
    Splits a text into overlapping chunks using a sliding window.
    Reads chunk_size and overlap from environment variables.
    """
    if not text:
        return []
    
    # Normalize line endings
    text = text.replace('\r\n', '\n') 
    
    chunks = []
    start = 0
    n = len(text)
    
    while start < n:
        # Calculate the end of the chunk
        end = min(start + chunk_size, n)
        
        # Append the chunk
        chunks.append(text[start:end])
        
        if end == n:
            break # We've reached the end of the text
        
        # Move the start position back by 'overlap'
        # max(0, ...) ensures we don't go before the start of the text
        start = max(0, end - overlap)
        
    return chunks