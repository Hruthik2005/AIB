from google import genai
from google.genai import types
from core.prompt import MASTER_PROMPT, build_prompt
from core.scoring import parse_llm_response
from core.logger import logger
import json
import time

def get_fallback_response():
    # Hardcoded fallback JSON if API completely fails
    return {
        "response": "Namaste! Main Rupeezy se AI Assistant baat kar raha hoon. Aapka partner program inquiry receive hua tha. Kya aapke paas 2 minute hain discuss karne ke liye?",
        "score": 0.2,
        "status": "Warm",
        "language": "hinglish"
    }

def get_gemini_response(api_key, user_input, messages_history, audio_bytes=None, audio_mime=None):
    start_time = time.time()
    try:
        client = genai.Client(api_key=api_key)
        
        # Log input type
        if audio_bytes:
            logger.info(f"Processing voice input ({len(audio_bytes)} bytes, {audio_mime})")
        else:
            logger.info(f"Processing text input: '{user_input[:50]}...'")

        # Format history for the prompt context
        history_text = ""
        for msg in messages_history[-6:]: # Keep last 6 messages for context
            role = "AI" if msg["role"] == "assistant" else "User"
            content = msg['content']
            if isinstance(content, dict):
                content = content.get('response', str(content))
            history_text += f"{role}: {content}\n"
            
        contents = []
        if audio_bytes:
            contents.append(types.Part.from_bytes(data=audio_bytes, mime_type=audio_mime))
            contents.append(f"User is speaking. Previous conversation history for context:\n{history_text}\n\nTranscribe the audio and respond according to the MASTER_PROMPT.")
        else:
            final_prompt = build_prompt(user_input, history_text)
            contents.append(final_prompt)
     
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=MASTER_PROMPT,
                response_mime_type="application/json"
            )
        )
        
        duration = time.time() - start_time
        logger.info(f"Gemini response received in {duration:.2f}s")
        logger.debug(f"Raw Response Text: {response.text}")
        
        result = parse_llm_response(response.text)
        logger.debug(f"Parsed LLM Result: {result}")
        return result
    except Exception as e:
        logger.error(f"Gemini API Error after {time.time() - start_time:.2f}s: {e}")
        return get_fallback_response()
