import json
import sys
from pathlib import Path

def replay_log(log_file_path: Path):
    """
    Loads a JSON log file and prints its key contents for reproducibility.
    """
    if not log_file_path.exists():
        print(f"Error: Log file not found at '{log_file_path}'")
        return

    print(f"--- 1. Loading Log File ---")
    print(f"{log_file_path.name}\n")

    try:
        data = json.loads(log_file_path.read_text(encoding='utf-8'))
        
        print("--- 2. Key Information ---")
        print(f"Repo ID:    {data.get('repo_id')}")
        print(f"Timestamp:  {data.get('timestamp')}")
        print(f"Status:     {data.get('status', 'N/A')}")
        
        # Determine log type (lesson, quiz, or explain)
        log_type = "Unknown"
        if "final_lesson_data" in data:
            log_type = "Lesson Log"
            final_data = data.get("final_lesson_data")
        elif "final_quiz_data" in data:
            log_type = "Quiz Log"
            final_data = data.get("final_quiz_data")
        elif "explanation_result" in data:
            log_type = "Explain Log"
            final_data = data.get("explanation_result")
        else:
            final_data = None
            
        print(f"Log Type:   {log_type}")
        print("\n--- 3. Context IDs Used in Prompt ---")
        context_ids = data.get('context_ids_used', [])
        for i, ctx_id in enumerate(context_ids):
            print(f"  {i+1}. {ctx_id}")
        
        print("\n--- 4. Final Parsed LLM Response (What the UI Rendered) ---")
        if final_data:
            print(json.dumps(final_data, indent=2, ensure_ascii=False))
        else:
            print("No final data was saved (e.g., generation failed).")

        # Optional: Print raw response from the last attempt
        if "llm_attempts" in data and data["llm_attempts"]:
             last_attempt = data["llm_attempts"][-1]
             print("\n--- 5. Raw LLM Response (Last Attempt) ---")
             print(last_attempt.get("raw_response", "Raw response not logged in this attempt."))

    except json.JSONDecodeError:
        print("Error: Could not parse the log file. It may be corrupted.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python replay_log.py <path_to_log_file>")
        print("\nExample:")
        print("  python replay_log.py data/lesson_logs/lesson_log_pallets_flask_20251025_055853.json")
    else:
        replay_log(Path(sys.argv[1]))