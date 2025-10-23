import os
import google.generativeai as genai
import streamlit as st
import time # Ensure time is imported for sleep

# --- API Key Setup ---
API_KEY = st.secrets.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found...")
genai.configure(api_key=API_KEY)

# --- Default Generation Config ---
# Lowered default temp, max tokens kept high for flexibility
generation_config = {
    "temperature": 0.2, # Default, can be overridden
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 8192, # Kept high, adjust if needed
}

# --- Default Safety Settings ---
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# --- Model Selection Logic ---
def get_available_model_name():
    """Gets a suitable model name, preferring 'gemini-pro-latest'."""
    try:
        print("Listing available Gemini models...")
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        print(f"Models supporting generateContent: {available_models}")

        # Prioritize specific known good models
        preferred_models = ["models/gemini-pro-latest", "models/gemini-1.0-pro", "models/gemini-pro"]
        for pref_model in preferred_models:
            if pref_model in available_models:
                print(f"Using preferred model: {pref_model}")
                return pref_model

        # Fallback to the first available gemini model if preferred aren't found
        gemini_models = [m for m in available_models if "gemini" in m]
        if gemini_models:
            fallback_model = gemini_models[0]
            print(f"Preferred models not found. Using fallback: {fallback_model}")
            return fallback_model

        # If absolutely no Gemini models supporting generateContent are found
        raise ValueError("No suitable Gemini models found supporting generateContent.")

    except Exception as e:
        print(f"Error listing or selecting models: {e}. Falling back to 'gemini-pro-latest'.")
        # Fall back to the most likely stable name if listing fails
        return "models/gemini-pro-latest"

# --- Initialize the Model Globally ---
# Determine the model name once when the script loads
_MODEL_NAME = get_available_model_name()
model = genai.GenerativeModel(
    model_name=_MODEL_NAME,
    generation_config=generation_config, # Use default config here
    safety_settings=safety_settings
)
print(f"Initialized Gemini client with model: {_MODEL_NAME}")


# --- Generation Functions ---
def get_gemini_response(prompt_text: str, temperature: float = 0.1) -> str:
    """
    Sends a prompt to the Gemini API (non-streaming) and returns the text response.
    Includes retry logic and safety checks.
    """
    MAX_RETRIES = 2
    for attempt in range(MAX_RETRIES):
        try:
            # Override temperature for this specific call
            current_generation_config = {
                 **generation_config, # Start with defaults
                 "temperature": temperature # Override temperature
            }

            response = model.generate_content(
                [prompt_text], # Content needs to be in a list
                generation_config=current_generation_config,
                safety_settings=safety_settings # Pass safety settings here too
            )

            # Deeper check for valid response and text
            if not response:
                raise ValueError("API returned an empty response object.")
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                print(f"Response blocked due to: {response.prompt_feedback.block_reason}")
                return f"Error: Response blocked by safety filters ({response.prompt_feedback.block_reason})."
            # Access text safely using parts
            if not response.parts:
                 raise ValueError("Response object has no 'parts'.")
            text = response.parts[0].text
            if text is None: # Check for None explicitly
                 raise ValueError("Response part contains 'None' instead of text.")

            return text.strip()

        except Exception as e:
            error_details = f"{type(e).__name__}: {str(e)}"
            print(f"Gemini API call attempt {attempt + 1} failed: {error_details}")
            if attempt < MAX_RETRIES - 1:
                print("Retrying in 2 seconds...")
                time.sleep(2) # Short delay before retry
            else:
                final_error_msg = f"Error: Could not get a response from the AI (model: {_MODEL_NAME}) after {MAX_RETRIES} attempts. Details: {error_details}"
                print(final_error_msg)
                return final_error_msg # Return the error message to the UI

    # Should not be reached, but added for safety
    return f"Error: Unexpected issue in get_gemini_response after retries."


def stream_gemini_response(prompt_text: str, temperature: float = 0.1):
    """
    Sends a prompt to the Gemini API and yields response chunks for streaming.
    Includes safety checks.
    """
    try:
        # Override temperature for this specific call
        current_generation_config = {
            **generation_config,
            "temperature": temperature
        }

        response_stream = model.generate_content(
            [prompt_text],
            stream=True,
            generation_config=current_generation_config,
            safety_settings=safety_settings
        )

        if not response_stream:
            yield "Error: Received empty stream from Gemini API."
            return

        for chunk in response_stream:
            # Check for blocks in each chunk
            if chunk.prompt_feedback and chunk.prompt_feedback.block_reason:
                yield f"\nError: Response stream blocked by safety filters ({chunk.prompt_feedback.block_reason})."
                break # Stop streaming if blocked
            # Yield text safely using parts
            if chunk.parts:
                yield chunk.parts[0].text
            # It's normal for some chunks not to have text (e.g., metadata chunks)

    except Exception as e:
        error_details = f"{type(e).__name__}: {str(e)}"
        error_msg = f"\nError: Could not stream response from AI (model: {_MODEL_NAME}). Details: {error_details}"
        print(error_msg)
        yield error_msg