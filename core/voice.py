import io
from gtts import gTTS

def generate_audio(text: str, lang: str = "en") -> io.BytesIO | None:
    """
    Generates TTS audio from text.
    Handles language mapping and outputs a BytesIO stream for Streamlit playback.
    """
    mapping = {
        "english": "en",
        "hindi": "hi",
        "hinglish": "hi",
        "ta": "ta",
        "te": "te",
        "mr": "mr",
        "gu": "gu",
        "bn": "bn",
        "kn": "kn"
    }
    tts_lang = mapping.get(lang.lower(), "en")
    
    try:
        tts = gTTS(text=text, lang=tts_lang, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception as e:
        print(f"TTS Error: {e}")
        return None
