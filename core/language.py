from langdetect import detect

def is_hinglish(text):
    hindi_words = ["hai", "kya", "nahi", "mera", "aap", "mujhe", "samajh", "paas"]
    english_words = ["the", "is", "broker", "account", "already", "network"]

    h = any(word in text.lower() for word in hindi_words)
    e = any(word in text.lower() for word in english_words)

    return h and e

def detect_lang(text):
    try:
        return detect(text)
    except:
        return "en"

def get_language(text):
    text_lower = text.lower()
    if "kannada" in text_lower:
        return "kn"
    if "tamil" in text_lower:
        return "ta"
    if "telugu" in text_lower:
        return "te"

    if is_hinglish(text):
        return "hinglish"

    lang = detect_lang(text)

    if lang == "hi":
        return "hindi"
    elif lang in ["ta", "te", "mr", "gu", "bn", "kn"]:
        return lang
    else:
        return "english"
