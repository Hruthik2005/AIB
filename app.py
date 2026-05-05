import streamlit as st
import time
from core.llm_engine import get_gemini_response, calculate_heuristic_score
from gtts import gTTS
import speech_recognition as sr
import io
import os
from dotenv import load_dotenv
from deep_translator import GoogleTranslator

load_dotenv()

st.set_page_config(page_title="Rupeezy AI Agent", page_icon="🎙️", layout="wide")

# Inject Custom CSS for an "Amazing UI/UX"
st.markdown("""
<style>
    /* Clean Top Header */
    .header-container {
        display: flex;
        align-items: center;
        padding: 1rem 0 2rem 0;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 2rem;
    }
    .header-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f172a;
        margin-left: 10px;
    }
    
    /* Beautiful Chat Bubbles */
    [data-testid="stChatMessage"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* User Chat Bubble Style */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #f0fdf4 !important;
        border-color: #bbf7d0 !important;
    }
    
    /* Audio Component padding */
    [data-testid="stAudioInput"] {
        padding: 10px;
        border: 1px solid #e2e8f0;
        border-radius: 15px;
        background: #ffffff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# Application Header
st.markdown("""
<div class="header-container">
    <span style="font-size: 2rem;">🚀</span>
    <span class="header-title">Rupeezy Partner Conversion Agent</span>
</div>
""", unsafe_allow_html=True)

def generate_audio(text, lang):
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
        return None

# Sidebar - Dashboard/RM View
with st.sidebar:
    st.header("📊 RM Dashboard")
    st.markdown("Monitor live call intelligence.")
    
    if st.button("🔄 Reset Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.score = 0.0
        st.session_state.last_audio = None
        st.rerun()

    st.markdown("---")
    st.subheader("📈 Qualification Score")
    
    if "score" not in st.session_state:
        st.session_state.score = 0.0
        
    score_display = min(max(st.session_state.score, 0.0), 1.0)
    st.progress(score_display)

    if score_display >= 0.7:
        st.success(f"🔥 HOT ({score_display:.1f})\n\nReady for Handoff")
    elif score_display >= 0.4:
        st.warning(f"⚡ WARM ({score_display:.1f})\n\nSend WhatsApp Link")
    else:
        st.info(f"❄️ COLD ({score_display:.1f})\n\nNurture Pipeline")
        
    st.markdown("---")
    st.caption("🔒 Secured with Heuristic Fallback")

api_key = os.getenv("GEMINI_API_KEY")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.last_audio = None

# Display chat history in a container
chat_container = st.container()
with chat_container:
    if len(st.session_state.messages) == 0:
        st.markdown("<div style='text-align: center; color: #64748b; margin-top: 2rem;'>Start the conversation below...</div>", unsafe_allow_html=True)
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and "lang" in msg:
                st.markdown(f"**[{msg['lang'].upper()}]** {msg['content']}")
            else:
                st.markdown(msg["content"])

st.markdown("<br><br>", unsafe_allow_html=True)

# Interactive Section (Mic and Text)
col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("### 🎙️ Voice Input")
    
    audio_value = st.audio_input("Tap to speak", key="main_mic")

prompt = st.chat_input("Or type your message here...")

# Handle audio transcription
if audio_value is not None and audio_value != st.session_state.last_audio:
    st.session_state.last_audio = audio_value
    with st.spinner("Transcribing audio..."):
        r = sr.Recognizer()
        with sr.AudioFile(audio_value) as source:
            audio_data = r.record(source)
        prompt = None
        try:
            prompt = r.recognize_google(audio_data)
        except sr.UnknownValueError:
            st.error("⚠️ Audio unclear or silent. Please speak clearly or type your message.")
        except Exception as e:
            st.error(f"Speech recognition API error: {e}")

if prompt:
    translated_prompt = prompt
    try:
        translated_prompt = GoogleTranslator(source='auto', target='en').translate(prompt)
    except Exception:
        pass
        
    if translated_prompt and translated_prompt.strip().lower() != prompt.strip().lower():
        display_text = f"{prompt}\n\n*(English: {translated_prompt})*"
    else:
        display_text = prompt

    st.session_state.messages.append({"role": "user", "content": display_text})
    
    # Render user message
    with chat_container:
        with st.chat_message("user"):
            st.markdown(display_text)
        
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("*(Analyzing...)*")
            
            raw_response, detected_lang = get_gemini_response(api_key, prompt, st.session_state.messages)
            st.session_state.score = calculate_heuristic_score(prompt, st.session_state.score)
            
            full_response = raw_response
            message_placeholder.empty()
            message_placeholder.markdown(f"**[{detected_lang.upper()}]** {full_response}")
            
    st.session_state.messages.append({"role": "assistant", "content": full_response, "lang": detected_lang})
    
    audio_fp = generate_audio(full_response, detected_lang)
    if audio_fp:
        st.audio(audio_fp, format='audio/mp3', autoplay=True)

