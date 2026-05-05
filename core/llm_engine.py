import google.generativeai as genai
from core.prompt import MASTER_PROMPT, build_prompt
from core.scoring import parse_llm_response
import json

def get_fallback_response():
    # Hardcoded fallback JSON if API completely fails
    return {
        "response": "Namaste! Main Rupeezy se AI Assistant baat kar raha hoon. Aapka partner program inquiry receive hua tha. Kya aapke paas 2 minute hain discuss karne ke liye?",
        "score": 0.2,
        "status": "Warm",
        "language": "hinglish"
    }

def get_gemini_response(api_key, user_input, messages_history):
    genai.configure(api_key=api_key)
    
    # We enforce JSON output using generation_config
    model = genai.GenerativeModel(
        model_name="gemini-flash-latest",
        system_instruction=MASTER_PROMPT,
        generation_config={"response_mime_type": "application/json"}
    )
    
    # Format history for the prompt context
    history_text = ""
    for msg in messages_history[-6:]: # Keep last 6 messages for context
        role = "AI" if msg["role"] == "assistant" else "User"
        # If assistant message is a dict, get response
        content = msg['content']
        if isinstance(content, dict):
            content = content.get('response', str(content))
        history_text += f"{role}: {content}\n"
        
    final_prompt = build_prompt(user_input, history_text)
    
    try:
        response = model.generate_content(final_prompt)
        return parse_llm_response(response.text)
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return get_fallback_response()
