import json

def parse_llm_response(text: str) -> dict:
    """
    Parses the JSON response from the LLM.
    Handles potential markdown formatting (```json ... ```) and errors.
    """
    try:
        # Strip markdown formatting if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].strip()
            
        return json.loads(text)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        # Fallback dictionary if JSON parsing completely fails
        return {
            "response": text,
            "score": 0.1,
            "status": "Cold",
            "language": "en"
        }
