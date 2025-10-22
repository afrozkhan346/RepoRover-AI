import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- THIS IS THE KEY PART ---
# It looks for the API key in your .env.local file
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    # This error stops the app if the key is missing
    raise ValueError("GEMINI_API_KEY not found. Please set it in your .env.local file.")

genai.configure(api_key=API_KEY)

# Set up the model
generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", # Using a common, reliable model
    generation_config=generation_config,
    safety_settings=safety_settings
)

def get_gemini_response(prompt_text):
    """
    Sends a prompt to the Gemini API and returns the text response.
    """
    try:
        prompt_parts = [prompt_text]
        response = model.generate_content(prompt_parts)
        return response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Error: Could not get a response from the AI."

def stream_gemini_response(prompt_text):
    """
    Sends a prompt to the Gemini API and yields the response chunks.
    This is useful for st.write_stream in Streamlit.
    """
    try:
        prompt_parts = [prompt_text]
        response_stream = model.generate_content(prompt_parts, stream=True)
        for chunk in response_stream:
            yield chunk.text
    except Exception as e:
        print(f"Error streaming Gemini API: {e}")
        yield "Error: Could not get a streaming response from the AI."