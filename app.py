import streamlit as st
import time
from core.llm_engine import get_gemini_response
from core.voice import generate_audio
from core.logger import logger
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Rupeezy AI Agent", page_icon="🎤", layout="centered")

# ───────────────────────────────────────────────
# SESSION STATE INIT
# ───────────────────────────────────────────────
if "messages" not in st.session_state:
    logger.info("New session started")
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hi! I'm calling from Rupeezy regarding our partner program. Can I quickly explain how you can earn 100% brokerage?",
            "language": "en",
        }
    ]
if "status" not in st.session_state:
    st.session_state.status = "Cold"
if "score" not in st.session_state:
    st.session_state.score = 0.0
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None
if "processing_state" not in st.session_state:
    st.session_state.processing_state = "Idle"

# ───────────────────────────────────────────────
# COMPUTED VALUES
# ───────────────────────────────────────────────
confidence_pct = int(st.session_state.score * 100)
elapsed = int(time.time() - st.session_state.start_time)
mins, secs = divmod(elapsed, 60)
timer_str = f"{mins:02d}:{secs:02d}"

status_map = {
    "Hot": ("🔥", "#dc2626", "#fef2f2", "#fecaca"),
    "Warm": ("⚡", "#d97706", "#fffbeb", "#fde68a"),
    "Cold": ("❄️", "#16a34a", "#f0fdf4", "#bbf7d0"),
}
s_icon, s_color, s_bg, s_border = status_map.get(
    st.session_state.status, ("❄️", "#16a34a", "#f0fdf4", "#bbf7d0")
)

state_label = "✨ Ready to listen"
if st.session_state.processing_state == "Thinking":
    state_label = "🤖 AI is thinking…"
elif st.session_state.processing_state == "Speaking":
    state_label = "🔊 Speaking…"

# ───────────────────────────────────────────────
# CSS — styling only, NO layout tricks
# ───────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Global ── */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif !important;
    background: #f7f8fa !important;
}
#MainMenu, header, footer { display:none !important; }
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1rem !important;
    max-width: 820px !important;
}

/* ── Top bar (rendered via native columns) ── */
div[data-testid="stHorizontalBlock"]:first-of-type {
    background: #ffffff;
    border-radius: 14px;
    padding: 12px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    border: 1px solid #f0f0f0;
    margin-bottom: 10px !important;
}

/* ── Chat card ── */
.chat-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 28px 24px 20px 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    border: 1px solid #f0f0f0;
    min-height: 55vh;
    max-height: 55vh;
    overflow-y: auto;
    margin-bottom: 14px;
}

/* ── Chat bubbles ── */
.msg-row { display:flex; margin-bottom:14px; }
.msg-row.user { justify-content:flex-end; }
.msg-row.ai   { justify-content:flex-start; }

.bubble {
    max-width: 72%;
    padding: 13px 18px;
    border-radius: 18px;
    font-size: 0.97rem;
    line-height: 1.55;
    animation: pop .25s ease-out;
}
@keyframes pop {
    from { opacity:0; transform:translateY(8px); }
    to   { opacity:1; transform:translateY(0); }
}

.bubble.user {
    background: #dbeafe;
    color: #1e3a8a;
    border-bottom-right-radius: 4px;
}
.bubble.ai {
    background: #f3f4f6;
    color: #1f2937;
    border-bottom-left-radius: 4px;
}

/* ── Typing dots ── */
.typing { display:inline-flex; gap:4px; align-items:center; }
.typing span {
    width:6px; height:6px; border-radius:50%;
    background:#9ca3af;
    animation: blink 1.4s infinite both;
}
.typing span:nth-child(2) { animation-delay:.16s; }
.typing span:nth-child(3) { animation-delay:.32s; }
@keyframes blink {
    0%,80%,100% { opacity:.3; transform:scale(.85); }
    40% { opacity:1; transform:scale(1); }
}

/* ── Status pill ── */
.state-pill {
    text-align: center;
    font-size: 0.88rem;
    font-weight: 600;
    color: #6b7280;
    margin-bottom: 10px;
}

/* ── Mic area ── */
[data-testid="stAudioInput"] {
    border-radius: 40px !important;
    border: 2px solid #bfdbfe !important;
    box-shadow: 0 6px 24px rgba(59,130,246,.18) !important;
    transition: box-shadow .2s, transform .2s;
}
[data-testid="stAudioInput"]:hover {
    box-shadow: 0 10px 30px rgba(59,130,246,.28) !important;
    transform: translateY(-1px);
}

/* ── Bottom buttons ── */
[data-testid="stButton"] > button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 6px 0 !important;
}

/* ── Metric overrides to look like badges ── */
[data-testid="stMetric"] {
    background: transparent !important;
    padding: 0 !important;
}
[data-testid="stMetricValue"] {
    font-size: 1rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: .5px !important;
    color: #9ca3af !important;
}

/* ── Suppression of default Streamlit errors/toasts ── */
div[data-testid="stNotification"], 
div[data-testid="stException"], 
.stException, 
.stAlert, 
[data-testid="stToast"] {
    display: none !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ───────────────────────────────────────────────
# 1 · TOP BAR  (native Streamlit columns)
# ───────────────────────────────────────────────
t1, t2, t3, t4 = st.columns([3, 1.2, 1.2, 1])
with t1:
    st.markdown(
        "<span style='font-size:1.15rem;font-weight:700;color:#111827;'>🎤 Rupeezy AI Agent</span>",
        unsafe_allow_html=True,
    )
with t2:
    st.markdown(
        f"<span style='background:{s_bg};color:{s_color};border:1px solid {s_border};"
        f"padding:4px 10px;border-radius:8px;font-size:.82rem;font-weight:600;'>"
        f"{s_icon} {st.session_state.status}</span>",
        unsafe_allow_html=True,
    )
with t3:
    st.markdown(
        f"<span style='background:#f8fafc;color:#475569;border:1px solid #e2e8f0;"
        f"padding:4px 10px;border-radius:8px;font-size:.82rem;font-weight:600;'>"
        f"💯 {confidence_pct}%</span>",
        unsafe_allow_html=True,
    )
with t4:
    st.markdown(
        f"<span style='background:#f8fafc;color:#475569;border:1px solid #e2e8f0;"
        f"padding:4px 10px;border-radius:8px;font-size:.82rem;font-weight:600;'>"
        f"⏱ {timer_str}</span>",
        unsafe_allow_html=True,
    )

# ───────────────────────────────────────────────
# 2 · CHAT CARD  (scrollable conversation)
# ───────────────────────────────────────────────
chat_html = ""
for msg in st.session_state.messages:
    if msg["role"] == "user":
        chat_html += (
            f'<div class="msg-row user"><div class="bubble user">{msg["content"]}</div></div>'
        )
    else:
        chat_html += (
            f'<div class="msg-row ai"><div class="bubble ai">🤖 {msg["content"]}</div></div>'
        )

# Typing indicator
if st.session_state.processing_state == "Thinking":
    chat_html += (
        '<div class="msg-row ai"><div class="bubble ai">'
        '🤖 <span class="typing"><span></span><span></span><span></span></span>'
        "</div></div>"
    )

# Invisible anchor for auto-scroll
chat_html += '<div id="chat-bottom"></div>'

st.markdown(
    f"""
<div class="chat-card" id="chat-scroll-container">
{chat_html}
</div>
<script>
var c = document.getElementById('chat-scroll-container');
if(c) c.scrollTop = c.scrollHeight;
</script>
""",
    unsafe_allow_html=True,
)

# ───────────────────────────────────────────────
# 2.5 · PLAY PENDING AUDIO (survives rerun)
# ───────────────────────────────────────────────
if "pending_audio" in st.session_state and st.session_state.pending_audio is not None:
    st.audio(st.session_state.pending_audio, format="audio/mp3", autoplay=True)
    st.session_state.pending_audio = None

# ───────────────────────────────────────────────
# 3 · STATUS PILL
# ───────────────────────────────────────────────
st.markdown(f'<div class="state-pill">{state_label}</div>', unsafe_allow_html=True)

# ───────────────────────────────────────────────
# 4 · MIC INPUT  (hero, centered)
# ───────────────────────────────────────────────
mic_pad_l, mic_col, mic_pad_r = st.columns([1, 2, 1])
with mic_col:
    audio_value = st.audio_input("🎤 Tap to speak", label_visibility="collapsed", key="main_mic")

# ───────────────────────────────────────────────
# 5 · CALL CONTROLS
# ───────────────────────────────────────────────
_pad1, btn_end, btn_restart, _pad2 = st.columns([1.5, 1, 1, 1.5])
with btn_end:
    if st.button("🔴 End Call", use_container_width=True):
        logger.info(f"Call ended manually. Final Status: {st.session_state.status}, Score: {st.session_state.score}")
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi! I'm calling from Rupeezy regarding our partner program. Can I quickly explain how you can earn 100% brokerage?",
                "language": "en",
            }
        ]
        st.session_state.score = 0.0
        st.session_state.status = "Cold"
        st.session_state.start_time = time.time()
        st.session_state.processing_state = "Idle"
        st.session_state.last_audio = None
        st.rerun()
with btn_restart:
    if st.button("🔄 Restart", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi! I'm calling from Rupeezy regarding our partner program. Can I quickly explain how you can earn 100% brokerage?",
                "language": "en",
            }
        ]
        st.session_state.score = 0.0
        st.session_state.status = "Cold"
        st.session_state.start_time = time.time()
        st.session_state.processing_state = "Idle"
        st.session_state.last_audio = None
        st.rerun()

# ───────────────────────────────────────────────
# 6 · TEXT INPUT (chat_input — always at bottom)
# ───────────────────────────────────────────────
typed_prompt = st.chat_input("Or type your message here…")

# ───────────────────────────────────────────────
# 7 · BACKEND LOGIC (Optimized Multimodal)
# ───────────────────────────────────────────────
api_key = os.getenv("GEMINI_API_KEY")

prompt = None
audio_bytes = None
audio_mime = None

# ── Voice path ──
if audio_value:
    current_audio_bytes = audio_value.getvalue()
    audio_hash = hashlib.md5(current_audio_bytes).hexdigest()
    
    if audio_hash != st.session_state.get("last_audio_hash"):
        logger.debug("New audio input detected via hash")
        st.session_state.last_audio_hash = audio_hash
        audio_bytes = current_audio_bytes
        audio_mime = audio_value.type

# ── Text path ──
if typed_prompt:
    prompt = typed_prompt

# ── Processing ──
if prompt or audio_bytes:
    try:
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})

        st.session_state.processing_state = "Thinking"
        
        llm_json = get_gemini_response(
            api_key, 
            prompt, 
            st.session_state.messages, 
            audio_bytes=audio_bytes, 
            audio_mime=audio_mime
        )

        transcript = llm_json.get("user_transcript")
        ai_response_text = llm_json.get("response", "I'm sorry, I encountered an error.")
        detected_lang = llm_json.get("language", "en")
        
        try:
            st.session_state.score = float(llm_json.get("score", 0.0))
        except (ValueError, TypeError):
            st.session_state.score = 0.0
            
        old_status = st.session_state.status
        st.session_state.status = llm_json.get("status", "Warm")
        if old_status != st.session_state.status:
            logger.info(f"Lead status changed from {old_status} to {st.session_state.status}")

        # If it was audio, add the transcribed user message to history
        if audio_bytes and transcript:
            logger.info(f"Audio Transcript: '{transcript}'")
            st.session_state.messages.append({"role": "user", "content": f"🎤 {transcript}"})

        logger.info(f"AI Response: '{ai_response_text[:50]}...' Status: {st.session_state.status}, Score: {st.session_state.score}")
        st.session_state.messages.append(
            {"role": "assistant", "content": ai_response_text, "language": detected_lang}
        )

        st.session_state.processing_state = "Idle"

        audio_fp = generate_audio(ai_response_text, detected_lang)
        if audio_fp:
            st.session_state.pending_audio = audio_fp

        st.rerun()
    except Exception as e:
        logger.error(f"Global Backend Error: {e}", exc_info=True)
        st.session_state.processing_state = "Idle"
        st.rerun()

