import io
import asyncio
import edge_tts
import time
from core.logger import logger

def generate_audio(text: str, lang: str = "en") -> io.BytesIO | None:
    """
    Generates TTS audio from text.
    Handles language mapping and outputs a BytesIO stream for Streamlit playback.
    """
    start_time = time.time()
    mapping = {
        "english": "en-IN-NeerjaNeural",
        "en": "en-IN-NeerjaNeural",
        "hindi": "hi-IN-SwaraNeural",
        "hi": "hi-IN-SwaraNeural",
        "hinglish": "hi-IN-SwaraNeural",
        "tamil": "ta-IN-PallaviNeural",
        "ta": "ta-IN-PallaviNeural",
        "telugu": "te-IN-ShrutiNeural",
        "te": "te-IN-ShrutiNeural",
        "marathi": "mr-IN-AarohiNeural",
        "mr": "mr-IN-AarohiNeural",
        "gujarati": "gu-IN-DhwaniNeural",
        "gu": "gu-IN-DhwaniNeural",
        "bengali": "bn-IN-TanishaaNeural",
        "bn": "bn-IN-TanishaaNeural",
        "kannada": "kn-IN-SapnaNeural",
        "kn": "kn-IN-SapnaNeural",
    }
    voice = mapping.get(lang.lower(), "en-IN-NeerjaNeural")

    async def _generate():
        communicate = edge_tts.Communicate(text, voice)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data

    try:
        logger.info(f"Generating TTS for language: {lang} (voice: {voice})")
        audio_bytes = asyncio.run(_generate())
        duration = time.time() - start_time
        logger.info(f"TTS generated successfully in {duration:.2f}s ({len(audio_bytes)} bytes)")
        fp = io.BytesIO(audio_bytes)
        fp.seek(0)
        return fp
    except Exception as e:
        logger.error(f"TTS Error after {time.time() - start_time:.2f}s: {e}")
        return None
