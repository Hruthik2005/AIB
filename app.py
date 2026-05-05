import streamlit as st
import time
from core.llm_engine import get_gemini_response
from core.voice import generate_audio
import speech_recognition as sr
import os
from dotenv import load_dotenv
from deep_translator import GoogleTranslator

load_dotenv()

st.set_page_config(page_title="Rupeezy AI Agent", page_icon="🎙️", layout="centered")

# Premium UI/UX CSS Overhaul
st.markdown("""
<style>
    /* Global Reset & White Theme */
    body, .stApp {
        background-color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu, header, footer {visibility: hidden;}

    /* Top Bar Header */
    .top-bar {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        z-index: 1000;
        padding: 15px 30px;
        border-bottom: 1px solid #f1f5f9;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .top-bar-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #0f172a;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .badges-container {
        display: flex;
        gap: 15px;
        align-items: center;
    }
    .status-badge {
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .badge-hot { background: #fef2f2; color: #ef4444; border: 1px solid #fca5a5; }
    .badge-warm { background: #fefce8; color: #eab308; border: 1px solid #fde047; }
    .badge-cold { background: #f0fdf4; color: #22c55e; border: 1px solid #86efac; }
    
    .timer-badge { background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }
    
    /* Main Chat Container */
    .chat-wrapper {
        padding-top: 80px;
        padding-bottom: 150px;
        max-width: 800px;
        margin: 0 auto;
    }

    /* Message Bubbles */
    .chat-bubble {
        max-width: 75%;
        padding: 14px 20px;
        border-radius: 20px;
        margin-bottom: 20px;
        line-height: 1.5;
        font-size: 1rem;
        position: relative;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        animation: fadeIn 0.3s ease-out forwards;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .user-bubble {
        background: linear-gradient(135deg, #2563eb, #3b82f6);
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }
    
    .ai-bubble {
        background: #f8fafc;
        color: #1e293b;
        margin-right: auto;
        border: 1px solid #e2e8f0;
        border-bottom-left-radius: 4px;
    }
    
    .lang-indicator {
        font-size: 0.7rem;
        text-transform: uppercase;
        opacity: 0.7;
        margin-bottom: 5px;
        font-weight: 600;
        letter-spacing: 1px;
    }

    /* Floating Mic Area */
    .bottom-mic-container {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background: linear-gradient(to top, #ffffff 60%, rgba(255,255,255,0));
        padding: 30px 0;
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
        gap: 20px;
    }
    
    /* Overriding Streamlit Audio Input to look like a floating mic */
    [data-testid="stAudioInput"] {
        width: 300px !important;
        margin: 0 auto;
        border-radius: 30px;
        background: white;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    [data-testid="stAudioInput"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    }
    
    /* Control Buttons */
    .control-btn {
        padding: 10px 20px;
        border-radius: 20px;
        font-weight: 600;
        cursor: pointer;
        border: none;
        transition: all 0.2s ease;
    }
    .end-call-btn { background: #fee2e2; color: #dc2626; border: 1px solid #fecaca; }
    .end-call-btn:hover { background: #fca5a5; }
    
    /* Typing indicator */
    .typing-indicator {
        display: inline-flex;
        gap: 4px;
        padding: 10px;
        background: #f1f5f9;
        border-radius: 20px;
        margin-bottom: 20px;
    }
    .typing-dot {
        width: 6px;
        height: 6px;
        background: #94a3b8;
        border-radius: 50%;
        animation: typing 1.4s infinite ease-in-out both;
    }
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    @keyframes typing {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1); }
    }
    
</style>
""", unsafe_allow_html=True)

# State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "status" not in st.session_state:
    st.session_state.status = "Cold"
if "score" not in st.session_state:
    st.session_state.score = 0.0
if "call_active" not in st.session_state:
    st.session_state.call_active = False
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None
if "processing_state" not in st.session_state:
    st.session_state.processing_state = "Idle"

# Determine badges
status_class = f"badge-{st.session_state.status.lower()}"
confidence_pct = int(st.session_state.score * 100)
elapsed_time = int(time.time() - st.session_state.start_time)
mins, secs = divmod(elapsed_time, 60)
timer_str = f"{mins:02d}:{secs:02d}"

# Render Top Bar
st.markdown(f"""
<div class="top-bar">
    <div class="top-bar-title">🎙️ Rupeezy AI Agent</div>
    <div class="badges-container">
        <div class="status-badge {status_class}">🔥 {st.session_state.status}</div>
        <div class="status-badge timer-badge">💯 {confidence_pct}% AI Confidence</div>
        <div class="status-badge timer-badge">⏱️ {timer_str}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Main Chat Container
st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)

if not st.session_state.call_active and len(st.session_state.messages) == 0:
    st.markdown("""
        <div style="text-align: center; color: #64748b; margin-top: 100px;">
            <h3>Start the conversation</h3>
            <p>Tap the microphone below to begin the pitch.</p>
        </div>
    """, unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"""
        <div class="chat-bubble user-bubble">
            {msg["content"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        lang_indicator = msg.get("language", "en").upper()
        st.markdown(f"""
        <div class="chat-bubble ai-bubble">
            <div class="lang-indicator">🌐 {lang_indicator}</div>
            {msg["content"]}
        </div>
        """, unsafe_allow_html=True)

if st.session_state.processing_state == "Thinking":
    st.markdown("""
        <div class="typing-indicator">
            <div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>
        </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Bottom Floating Mic Area
st.markdown('<div class="bottom-mic-container">', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    audio_value = st.audio_input("Speak to AI", key="main_mic")
with col3:
    if st.button("🔴 End Call", use_container_width=True):
        st.session_state.call_active = False
        st.session_state.messages = []
        st.session_state.score = 0.0
        st.session_state.status = "Cold"
        st.session_state.start_time = time.time()
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

api_key = os.getenv("GEMINI_API_KEY")

# Process Audio Input
if audio_value is not None and audio_value != st.session_state.last_audio:
    st.session_state.call_active = True
    st.session_state.last_audio = audio_value
    st.session_state.processing_state = "Thinking"
    
    # Transcribe
    r = sr.Recognizer()
    with sr.AudioFile(audio_value) as source:
        audio_data = r.record(source)
    prompt = None
    try:
        # en-IN helps significantly with Hinglish/Tanglish STT phonetic recognition
        prompt = r.recognize_google(audio_data, language="en-IN")
    except sr.UnknownValueError:
        st.error("⚠️ Audio unclear or silent.")
        st.session_state.processing_state = "Idle"
        st.rerun()
    except Exception as e:
        st.error(f"STT Error: {e}")
        st.session_state.processing_state = "Idle"
        st.rerun()

    if prompt:
        translated_prompt = prompt
        try:
            translated_prompt = GoogleTranslator(source='auto', target='en').translate(prompt)
        except Exception:
            pass
            
        display_text = prompt
        if translated_prompt and translated_prompt.strip().lower() != prompt.strip().lower():
            display_text += f"<br><small style='opacity:0.8'>*(English: {translated_prompt})*</small>"

        st.session_state.messages.append({"role": "user", "content": display_text})
        
        # We need to trigger a rerun here to show user message AND thinking indicator
        # but Streamlit reruns stop execution. So we process LLM immediately, but UI won't show thinking dot 
        # for LLM wait unless we do a trick.
        
        llm_json = get_gemini_response(api_key, prompt, st.session_state.messages)
        
        # Extract from JSON
        ai_response_text = llm_json.get("response", "I'm sorry, I encountered an error.")
        detected_lang = llm_json.get("language", "en")
        st.session_state.score = float(llm_json.get("score", 0.0))
        st.session_state.status = llm_json.get("status", "Warm")
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": ai_response_text, 
            "language": detected_lang
        })
        
        st.session_state.processing_state = "Idle"
        
        audio_fp = generate_audio(ai_response_text, detected_lang)
        if audio_fp:
            st.audio(audio_fp, format='audio/mp3', autoplay=True)
            
        st.rerun()

