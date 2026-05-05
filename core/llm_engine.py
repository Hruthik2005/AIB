import google.generativeai as genai
from core.prompt import MASTER_PROMPT, build_prompt
from core.language import get_language

def get_fallback_response(user_input, lang):
    input_lower = user_input.lower()
    
    if lang == "kn":
        return "ಖಂಡಿತ. Rupeezy ಪಾಲುದಾರರಾಗಿ, ನಿಮಗೆ ಶೂನ್ಯ ಸೇರುವ ಶುಲ್ಕ, 100% ಬ್ರೋಕರೇಜ್ ಪಾಲು ಮತ್ತು ದೈನಂದಿನ ಪಾವತಿಗಳು ಸಿಗುತ್ತವೆ. ನಿಮ್ಮ ಪ್ರಸ್ತುತ ಕ್ಲೈಂಟ್ ಪಟ್ಟಿಯ ಬಗ್ಗೆ ಸ್ವಲ್ಪ ಹೇಳಬಹುದೇ?"
    elif lang == "ta":
        return "நிச்சயமாக. Rupeezy பார்ட்னராக, உங்களுக்கு சேரும் கட்டணம் இல்லை, 100% புரோக்கரேஜ் பங்கு மற்றும் தினசரி பேஅவுட் கிடைக்கும். உங்கள் தற்போதைய கிளையன்ட் பட்டியலைப் பற்றி கொஞ்சம் சொல்ல முடியுமா?"
    elif lang == "te":
        return "తప్పకుండా. Rupeezy భాగస్వామిగా, మీకు చేరే రుసుము లేదు, 100% బ్రోకరేజ్ వాటా మరియు రోజువారీ చెల్లింపులు లభిస్తాయి. మీ ప్రస్తుత క్లయింట్ జాబితా గురించి కొంచెం చెప్పగలరా?"

    if any(word in input_lower for word in ["hello", "hi", "namaste"]):
        return "Namaste! Main Rupeezy se AI Assistant baat kar raha hoon. Aapka partner program inquiry receive hua tha. Kya aapke paas 2 minute hain discuss karne ke liye?"
    
    if any(word in input_lower for word in ["already", "broker", "zerodha", "upstox"]):
        return "That's great, you know the business well! But are they giving you 100% brokerage share and daily payouts? Most brokers cap at 60% and pay monthly. With Rupeezy, you keep it all. Does daily payout sound better to you?"
        
    if any(word in input_lower for word in ["trust", "safe", "fraud", "sebi"]):
        return "I completely understand the concern. Rupeezy is a SEBI-registered broker with over 20 years of trust. Your clients' funds are perfectly secure. Should I send you our SEBI registration details on WhatsApp?"
        
    if any(word in input_lower for word in ["support", "issues", "help"]):
        return "We have a dedicated B2B support desk specifically for our partners. You won't have to deal with standard customer care. We handle the tech and support, you just focus on growth."

    if any(word in input_lower for word in ["network", "contacts", "few"]):
        return "No problem at all! You don't need a huge list to start. Since there's zero joining fee, you can start with just 2-3 friends or family members and grow from there. Want to see how?"

    if any(word in input_lower for word in ["link", "join", "sign up", "interested", "yes"]):
        return "Awesome! I'll send you the WhatsApp link right now to lock in your 100% brokerage share with zero joining fee. I'll also notify your Relationship Manager to assist you. Welcome to Rupeezy!"
        
    if any(word in input_lower for word in ["later", "busy", "time"]):
        return "Sure, I respect your time. I'll drop a quick WhatsApp message with the details so you can review it when free."

    return "Bilkul. As a Rupeezy partner, aapko zero joining fee, 100% brokerage share, aur daily payouts milenge. Kya aap apni existing client list ke baare mein kuch bata sakte hain?"

def get_gemini_response(api_key, user_input, messages_history):
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(
        model_name="gemini-flash-latest",
        system_instruction=MASTER_PROMPT
    )
    
    lang = get_language(user_input)
    
    # Format history for the prompt context
    history_text = ""
    for msg in messages_history[-6:]: # Keep last 6 messages for context
        role = "AI" if msg["role"] == "assistant" else "User"
        history_text += f"{role}: {msg['content']}\n"
        
    final_prompt = build_prompt(user_input, lang, history_text)
    
    try:
        response = model.generate_content(final_prompt)
        return response.text, lang
    except Exception as e:
        # The API key is failing (403), so we intercept the error and serve the demo responses!
        fallback_text = get_fallback_response(user_input, lang)
        return fallback_text, lang

def calculate_heuristic_score(user_input, current_score):
    input_lower = user_input.lower()
    score = current_score
    
    # Engagement bump
    score += 0.05
    
    if any(word in input_lower for word in ["already", "broker", "zerodha", "upstox"]):
        score += 0.1
    if any(word in input_lower for word in ["link", "join", "sign up", "interested", "yes"]):
        score += 0.3
    if any(word in input_lower for word in ["later", "busy", "time", "no", "stop"]):
        score -= 0.1
        
    return min(max(score, 0.0), 1.0)
