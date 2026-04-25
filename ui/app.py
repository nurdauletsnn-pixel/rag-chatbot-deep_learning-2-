# import streamlit as st
# import sys
# sys.path.append(".")

# from pipeline import RAGPipeline

# st.set_page_config(
#     page_title="FastAPI Docs Chatbot",
#     page_icon="⚡",
#     layout="wide"
# )

# st.title("⚡ FastAPI Documentation Chatbot")
# st.caption("RAG-powered chatbot | Knowledge base: FastAPI official docs | Model: Llama 3.3 70B via Groq")

# # Sidebar
# with st.sidebar:
#     st.header("⚙️ Settings")
#     top_k = st.slider("Retrieved chunks (top-k)", 3, 10, 5)
#     st.divider()
#     st.markdown("**Architecture:**")
#     st.markdown("- 📄 Ingestion: HTML + Markdown")
#     st.markdown("- ✂️ Chunking: Semantic splitting")
#     st.markdown("- 🔢 Embeddings: all-MiniLM-L6-v2")
#     st.markdown("- 🗄️ Vector DB: ChromaDB")
#     st.markdown("- 🤖 LLM: Llama 3.1 8B (Groq)")
#     st.divider()
#     if st.button("🗑️ Clear chat"):
#         st.session_state.messages = []
#         st.rerun()

# # Init pipeline (cached)
# @st.cache_resource
# def load_pipeline(top_k_value: int) -> RAGPipeline:
#     return RAGPipeline(top_k=top_k_value)

# @st.cache_resource
# def get_pipeline(top_k_value: int) -> RAGPipeline:
#     with st.spinner("Loading RAG pipeline..."):
#         return load_pipeline(top_k_value)

# rag = get_pipeline(top_k)

# # Chat history
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # Display history
# for msg in st.session_state.messages:
#     with st.chat_message(msg["role"]):
#         st.markdown(msg["content"])
#         if msg.get("sources"):
#             with st.expander("📎 Sources"):
#                 for src in msg["sources"]:
#                     st.markdown(f"- `{src}`")
#         if msg.get("cited_ids"):
#             st.caption("Citations: " + ", ".join(f"`{cid}`" for cid in msg["cited_ids"]))
#         if msg.get("chunks"):
#             with st.expander("🔍 Retrieved chunks"):
#                 for i, chunk in enumerate(msg["chunks"]):
#                     st.markdown(f"**Chunk {i+1}** | Score: `{chunk['score']:.3f}` | {chunk['metadata'].get('title','')}")
#                     st.code(chunk['text'][:300] + "...")

# # Input
# if prompt := st.chat_input("Ask anything about FastAPI..."):
#     # User message
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)
    
#     # Assistant response
#     with st.chat_message("assistant"):
#         with st.spinner("Retrieving and generating..."):
#             result = rag.ask(prompt)
        
#         answer = result["answer"]
        
#         if result["is_refusal"]:
#             st.warning("⚠️ " + answer)
#         else:
#             st.markdown(answer)
        
#         with st.expander("📎 Sources"):
#             for src in result["sources"]:
#                 st.markdown(f"- `{src}`")
#             if result.get("cited_ids"):
#                 st.markdown("**Citation IDs:** " + ", ".join(f"`{cid}`" for cid in result["cited_ids"]))
        
#         with st.expander("🔍 Retrieved chunks"):
#             for i, chunk in enumerate(result["chunks_used"]):
#                 st.markdown(f"**Chunk {i+1}** | Score: `{chunk['score']:.3f}` | {chunk['metadata'].get('title','')}")
#                 st.code(chunk['text'][:300] + "...")
    
#     st.session_state.messages.append({
#         "role": "assistant",
#         "content": answer,
#         "sources": result["sources"],
#         "cited_ids": result.get("cited_ids", []),
#         "chunks": result["chunks_used"]
#     })





import streamlit as st
import sys
sys.path.append(".")

from pipeline import RAGPipeline

st.set_page_config(
    page_title="FastAPI RAG Chatbot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── GLOBAL CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap');

/* ── PALETTE ── */
:root {
    --cyan:       #00e5ff;
    --cyan-dim:   #00b8cc;
    --cyan-glow:  rgba(0,229,255,0.18);
    --cyan-soft:  rgba(0,229,255,0.08);
    --amber:      #ffb300;
    --amber-soft: rgba(255,179,0,0.10);
    --red-soft:   rgba(255,80,80,0.10);
    --red:        #ff6b6b;

    --bg0:   #07090f;
    --bg1:   #0e1117;
    --bg2:   #141924;
    --bg3:   #1c2333;
    --bg4:   #242d42;

    --line:  rgba(255,255,255,0.06);
    --line2: rgba(0,229,255,0.22);

    --text0: #ffffff;
    --text1: #e2e8f5;
    --text2: #94a3b8;
    --text3: #546278;

    --mono:  'Fira Code', monospace;
    --sans:  'Plus Jakarta Sans', sans-serif;

    --r-sm:  8px;
    --r-md:  12px;
    --r-lg:  16px;
    --r-xl:  22px;
}

/* ── RESET ── */
html, body, [class*="css"] {
    background-color: var(--bg1) !important;
    color: var(--text1) !important;
    font-family: var(--sans) !important;
    font-size: 15px !important;
}
* { box-sizing: border-box; }
.stApp {
    background:
        radial-gradient(circle at 15% 0%, rgba(0,229,255,0.10), transparent 28%),
        radial-gradient(circle at 85% 12%, rgba(0,110,255,0.10), transparent 30%),
        linear-gradient(180deg, #080b13 0%, #0d111a 45%, #090c12 100%) !important;
    color: var(--text1) !important;
}

/* ── STREAMLIT CHROME ── */
#MainMenu, footer { visibility: hidden; }
[data-testid="stHeader"] {
    background: rgba(7, 9, 15, 0.72) !important;
    backdrop-filter: blur(10px);
}
[data-testid="stToolbar"] {
    right: 0.75rem !important;
}
[data-testid="collapsedControl"] {
    color: var(--text1) !important;
}
[data-testid="collapsedControl"] button,
[data-testid="stToolbar"] button {
    border-radius: 10px !important;
}
[data-testid="collapsedControl"] button:hover,
[data-testid="stToolbar"] button:hover {
    background: rgba(0,229,255,0.12) !important;
}
.block-container {
    padding: 5rem 3rem 5rem !important;
    max-width: 1080px !important;
}

/* ═══════════════════════════════════════
   SIDEBAR
═══════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: var(--bg0) !important;
    border-right: 1px solid var(--line) !important;
    padding-top: 0 !important;
}
[data-testid="stSidebar"] > div { padding: 1.5rem 1.25rem !important; }
[data-testid="stSidebar"] * { color: var(--text1) !important; }

/* Logo */
.sb-logo {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--line);
    margin-bottom: 1.75rem;
}
.sb-logo-icon {
    width: 42px; height: 42px;
    background: linear-gradient(135deg, #00e5ff 0%, #006eff 100%);
    border-radius: var(--r-md);
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
    box-shadow: 0 0 20px rgba(0,229,255,0.35);
    flex-shrink: 0;
}
.sb-logo-name {
    font-size: 17px;
    font-weight: 800;
    color: var(--text0) !important;
    letter-spacing: -0.02em;
    line-height: 1.1;
}
.sb-logo-tag {
    font-size: 11px;
    font-family: var(--mono);
    color: var(--cyan) !important;
    opacity: 0.8;
    margin-top: 2px;
}

/* Section label */
.sb-section {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--text3) !important;
    margin: 1.5rem 0 0.75rem;
}

/* Stack rows */
.sb-stack { display: flex; flex-direction: column; gap: 0; }
.sb-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 7px 0;
    border-bottom: 1px solid var(--line);
    font-size: 12.5px;
}
.sb-row:last-child { border-bottom: none; }
.sb-row-label { color: var(--text3) !important; font-size: 12px; }
.sb-row-val {
    font-family: var(--mono);
    font-size: 11.5px;
    color: var(--cyan) !important;
    background: var(--cyan-soft);
    padding: 2px 8px;
    border-radius: 20px;
    border: 1px solid rgba(0,229,255,0.15);
}

/* Topk display */
.topk-display {
    text-align: center;
    font-family: var(--mono);
    font-size: 28px;
    font-weight: 500;
    color: var(--cyan) !important;
    padding: 0.5rem 0 0.25rem;
    line-height: 1;
}
.topk-label {
    text-align: center;
    font-size: 11px;
    color: var(--text3) !important;
    margin-bottom: 0.5rem;
}

/* Slider */
[data-testid="stSlider"] > div > div > div > div {
    background: linear-gradient(90deg, #00e5ff, #006eff) !important;
}
[data-testid="stSlider"] label { display: none !important; }

/* Clear button */
[data-testid="stSidebar"] button {
    width: 100% !important;
    margin-top: 1.25rem !important;
    background: transparent !important;
    border: 1px solid var(--line2) !important;
    color: var(--cyan) !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    border-radius: var(--r-md) !important;
    padding: 0.6rem 1rem !important;
    font-family: var(--sans) !important;
    letter-spacing: 0.01em;
    transition: all 0.2s !important;
}
[data-testid="stSidebar"] button:hover {
    background: var(--cyan-glow) !important;
    box-shadow: 0 0 16px rgba(0,229,255,0.2) !important;
}

/* ═══════════════════════════════════════
   PAGE HEADER
═══════════════════════════════════════ */
.page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 1.15rem 1.25rem;
    margin-bottom: 1.75rem;
    background:
        linear-gradient(135deg, rgba(20,25,36,0.96), rgba(9,13,22,0.96)),
        radial-gradient(circle at top left, rgba(0,229,255,0.14), transparent 42%);
    border: 1px solid rgba(0,229,255,0.22);
    border-radius: 18px;
    box-shadow:
        0 18px 50px rgba(0,0,0,0.28),
        inset 0 1px 0 rgba(255,255,255,0.05);
}
.page-title {
    font-size: 30px;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #f8fbff !important;
    line-height: 1.15;
    text-shadow: 0 1px 18px rgba(0,0,0,0.35);
}
.page-title .hl {
    background: linear-gradient(90deg, #00e5ff 0%, #006eff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.page-meta {
    font-family: var(--mono);
    font-size: 12px;
    color: #9fb2c9 !important;
    margin-top: 5px;
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
}
.page-meta span { color: #b9c6d8 !important; }
.online-badge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: rgba(0,229,255,0.07);
    border: 1px solid var(--line2);
    border-radius: 30px;
    padding: 6px 14px 6px 10px;
    font-size: 12px;
    font-family: var(--mono);
    color: var(--cyan) !important;
    white-space: nowrap;
}
.pulse {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--cyan);
    box-shadow: 0 0 8px var(--cyan);
    animation: blink 2s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* ═══════════════════════════════════════
   WELCOME CARD
═══════════════════════════════════════ */
.welcome-wrap {
    display: flex;
    justify-content: center;
    margin: 3.5rem 0;
}
.welcome-card {
    background: var(--bg2);
    border: 1px solid var(--line);
    border-radius: var(--r-xl);
    padding: 2.5rem 2rem;
    text-align: center;
    max-width: 560px;
    width: 100%;
    position: relative;
    overflow: hidden;
}
.welcome-card::before {
    content: '';
    position: absolute;
    top: -60px; left: 50%;
    transform: translateX(-50%);
    width: 280px; height: 160px;
    background: radial-gradient(ellipse, rgba(0,229,255,0.12) 0%, transparent 70%);
    pointer-events: none;
}
.welcome-icon-wrap {
    width: 64px; height: 64px;
    background: linear-gradient(135deg, rgba(0,229,255,0.15), rgba(0,110,255,0.15));
    border: 1px solid var(--line2);
    border-radius: var(--r-lg);
    display: flex; align-items: center; justify-content: center;
    font-size: 30px;
    margin: 0 auto 1.25rem;
    box-shadow: 0 0 28px rgba(0,229,255,0.15);
}
.welcome-title {
    font-size: 22px;
    font-weight: 800;
    color: var(--text0);
    letter-spacing: -0.02em;
    margin-bottom: 0.6rem;
}
.welcome-desc {
    font-size: 14px;
    color: var(--text2);
    line-height: 1.7;
    margin-bottom: 1.75rem;
    max-width: 400px;
    margin-left: auto;
    margin-right: auto;
}
.examples-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text3);
    margin-bottom: 0.75rem;
    font-weight: 600;
}
.examples-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}
.ex-chip {
    background: var(--bg3);
    border: 1px solid var(--line);
    border-radius: var(--r-sm);
    padding: 9px 12px;
    font-size: 12.5px;
    color: var(--text2);
    font-family: var(--mono);
    text-align: left;
}

/* ═══════════════════════════════════════
   CHAT MESSAGES
═══════════════════════════════════════ */
[data-testid="stChatMessage"] {
    background: rgba(20,25,36,0.96) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: var(--r-lg) !important;
    padding: 1.1rem 1.4rem !important;
    margin-bottom: 0.9rem !important;
    box-shadow: 0 12px 30px rgba(0,0,0,0.18) !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]),
[data-testid="stChatMessage"]:has([aria-label="user avatar"]) {
    background: rgba(0,229,255,0.08) !important;
    border-color: rgba(0,229,255,0.22) !important;
}
[data-testid="stChatMessage"] p {
    font-size: 15px !important;
    line-height: 1.75 !important;
    color: #f1f5fb !important;
}
[data-testid="stChatMessage"] div,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] li {
    color: #e7edf7 !important;
}
[data-testid="stChatMessage"] strong { color: var(--text0) !important; }
[data-testid="stChatMessage"] code {
    background: var(--bg4) !important;
    color: var(--cyan) !important;
    border-radius: 4px !important;
    padding: 1px 5px !important;
    font-family: var(--mono) !important;
    font-size: 13px !important;
}

/* ═══════════════════════════════════════
   CHAT INPUT
═══════════════════════════════════════ */
[data-testid="stChatFloatingInputContainer"] {
    position: relative;
    background:
        radial-gradient(circle at 15% 0%, rgba(0,229,255,0.10), transparent 28%),
        radial-gradient(circle at 85% 12%, rgba(0,110,255,0.10), transparent 30%),
        linear-gradient(180deg, #080b13 0%, #0d111a 45%, #090c12 100%) !important;
    padding: 1.1rem 0 1.35rem !important;
}
[data-testid="stBottomBlockContainer"],
[data-testid="stBottom"] {
    background:
        radial-gradient(circle at 15% 0%, rgba(0,229,255,0.10), transparent 28%),
        radial-gradient(circle at 85% 12%, rgba(0,110,255,0.10), transparent 30%),
        linear-gradient(180deg, #080b13 0%, #0d111a 45%, #090c12 100%) !important;
}
[data-testid="stChatFloatingInputContainer"] > div {
    background: transparent !important;
}
[data-testid="stChatFloatingInputContainer"]::before {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(
        180deg,
        rgba(9, 12, 18, 0) 0%,
        rgba(9, 12, 18, 0.28) 20%,
        rgba(6, 9, 14, 0.82) 100%
    ) !important;
    pointer-events: none;
}
[data-testid="stChatInput"] {
    max-width: 980px;
    margin: 0 auto;
    position: relative;
    z-index: 1;
}
[data-testid="stChatInput"] > div {
    background:
        linear-gradient(145deg, rgba(11,16,26,0.96), rgba(17,24,39,0.98)) !important;
    border: 1px solid rgba(148,163,184,0.18) !important;
    border-radius: 24px !important;
    padding: 0.4rem 0.45rem 0.4rem 0.65rem !important;
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.04),
        0 16px 40px rgba(0,0,0,0.28),
        0 0 0 1px rgba(0,229,255,0.06) !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: rgba(0,229,255,0.42) !important;
    box-shadow:
        0 0 0 4px rgba(0,229,255,0.10),
        0 18px 44px rgba(0,0,0,0.34),
        0 0 26px rgba(0,229,255,0.12) !important;
}
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] textarea:focus,
[data-testid="stChatInput"] [contenteditable="true"],
[data-testid="stChatInput"] [data-baseweb="textarea"] textarea {
    background: #eef2f7 !important;
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
    font-size: 15px !important;
    font-family: var(--sans) !important;
    caret-color: var(--cyan) !important;
    border-radius: 16px !important;
    padding: 0.9rem 0.85rem !important;
    line-height: 1.5 !important;
    box-shadow: none !important;
}
[data-testid="stChatInput"] [data-baseweb="textarea"] {
    background: #eef2f7 !important;
    border-radius: 16px !important;
}
[data-testid="stChatInput"] [data-baseweb="textarea"] * {
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
}
[data-testid="stChatInput"] textarea::placeholder,
[data-testid="stChatInput"] [data-baseweb="textarea"] textarea::placeholder {
    color: #475569 !important;
    font-size: 14px !important;
}
[data-testid="stChatInput"] button {
    width: 44px !important;
    height: 44px !important;
    min-width: 44px !important;
    min-height: 44px !important;
    background: linear-gradient(135deg, #00d5ff, #007cf0) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 14px !important;
    color: #ffffff !important;
    box-shadow:
        0 10px 24px rgba(0,124,240,0.28),
        inset 0 1px 0 rgba(255,255,255,0.16) !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease !important;
}
[data-testid="stChatInput"] button:hover {
    transform: translateY(-1px);
    box-shadow:
        0 14px 28px rgba(0,124,240,0.32),
        inset 0 1px 0 rgba(255,255,255,0.18) !important;
}
[data-testid="stChatInput"] button svg {
    color: #ffffff !important;
    fill: #ffffff !important;
}
@media (max-width: 900px) {
    [data-testid="stChatFloatingInputContainer"] {
        padding: 0.85rem 0 1rem !important;
    }
    [data-testid="stChatInput"] {
        max-width: calc(100vw - 1.25rem);
    }
    [data-testid="stChatInput"] > div {
        border-radius: 20px !important;
        padding: 0.3rem 0.35rem 0.3rem 0.45rem !important;
    }
    [data-testid="stChatInput"] button {
        width: 40px !important;
        height: 40px !important;
        min-width: 40px !important;
        min-height: 40px !important;
        border-radius: 12px !important;
    }
}

/* ═══════════════════════════════════════
   EXPANDERS
═══════════════════════════════════════ */
[data-testid="stExpander"] {
    background: var(--bg3) !important;
    border: 1px solid var(--line) !important;
    border-radius: var(--r-md) !important;
    margin-top: 0.6rem !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary {
    font-size: 12.5px !important;
    font-weight: 600 !important;
    color: var(--text2) !important;
    font-family: var(--mono) !important;
    padding: 0.6rem 0.75rem !important;
    letter-spacing: 0.01em !important;
}
[data-testid="stExpander"] summary:hover { color: var(--cyan) !important; }
[data-testid="stExpander"] > div > div { padding: 0.5rem 0.75rem 0.75rem !important; }

/* ═══════════════════════════════════════
   CODE BLOCKS
═══════════════════════════════════════ */
pre, [data-testid="stCode"] pre {
    background: var(--bg0) !important;
    border: 1px solid var(--line) !important;
    border-radius: var(--r-sm) !important;
    font-family: var(--mono) !important;
    font-size: 12.5px !important;
    line-height: 1.6 !important;
    color: #cdd6f4 !important;
}

/* ═══════════════════════════════════════
   WARNING (REFUSAL)
═══════════════════════════════════════ */
[data-testid="stAlert"] {
    background: var(--amber-soft) !important;
    border: 1px solid rgba(255,179,0,0.3) !important;
    border-radius: var(--r-md) !important;
    color: #ffd060 !important;
    font-size: 14.5px !important;
}
[data-testid="stAlert"] p { color: #ffd060 !important; font-size: 14.5px !important; }

/* ═══════════════════════════════════════
   SOURCE PILLS
═══════════════════════════════════════ */
.src-wrap { display: flex; flex-wrap: wrap; gap: 6px; padding: 4px 0 6px; }
.src-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: var(--cyan-soft);
    border: 1px solid rgba(0,229,255,0.18);
    border-radius: 30px;
    padding: 3px 11px;
    font-family: var(--mono);
    font-size: 11.5px;
    color: var(--cyan);
    word-break: break-all;
}
.src-pill::before { content: '◆'; font-size: 8px; opacity: 0.6; }

/* ═══════════════════════════════════════
   CHUNK CARDS
═══════════════════════════════════════ */
.chunk-card {
    background: var(--bg0);
    border: 1px solid var(--line);
    border-left: 3px solid var(--cyan);
    border-radius: var(--r-sm);
    padding: 0.85rem 1rem;
    margin-bottom: 0.6rem;
}
.chunk-meta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 0.55rem;
}
.chunk-num {
    font-family: var(--mono);
    font-size: 11px;
    font-weight: 500;
    color: var(--text3);
    background: var(--bg3);
    padding: 2px 8px;
    border-radius: 20px;
}
.chunk-score {
    font-family: var(--mono);
    font-size: 12px;
    font-weight: 500;
    color: var(--cyan);
    background: var(--cyan-soft);
    padding: 2px 9px;
    border-radius: 20px;
    border: 1px solid rgba(0,229,255,0.15);
}
.chunk-title {
    font-size: 12.5px;
    font-weight: 600;
    color: var(--text1);
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.chunk-text {
    font-family: var(--mono);
    font-size: 12px;
    line-height: 1.65;
    color: var(--text2);
    white-space: pre-wrap;
    word-break: break-word;
    border-top: 1px solid var(--line);
    padding-top: 0.55rem;
}

/* ═══════════════════════════════════════
   CITATION LINE
═══════════════════════════════════════ */
.cite-line {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    align-items: center;
    margin-top: 0.4rem;
}
.cite-label {
    font-size: 11px;
    font-family: var(--mono);
    color: var(--text3);
    margin-right: 2px;
}
.cite-id {
    font-family: var(--mono);
    font-size: 11px;
    color: var(--amber);
    background: var(--amber-soft);
    border: 1px solid rgba(255,179,0,0.2);
    border-radius: 20px;
    padding: 1px 8px;
}

/* Spinner / divider */
[data-testid="stSpinner"] > div { border-top-color: var(--cyan) !important; }
[data-testid="stSpinner"] p { color: var(--text2) !important; font-size: 13px !important; }
hr { border-color: var(--line) !important; margin: 0.75rem 0 !important; }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────
def render_sources(sources: list, cited_ids: list = None):
    pills = "".join(f'<span class="src-pill">{s}</span>' for s in sources)
    st.markdown(f'<div class="src-wrap">{pills}</div>', unsafe_allow_html=True)
    if cited_ids:
        ids_html = "".join(f'<span class="cite-id">{c}</span>' for c in cited_ids)
        st.markdown(
            f'<div class="cite-line"><span class="cite-label">citation ids</span>{ids_html}</div>',
            unsafe_allow_html=True
        )

def render_chunks(chunks: list):
    for i, chunk in enumerate(chunks):
        title = chunk["metadata"].get("title", "—")
        score = chunk["score"]
        text  = chunk["text"][:300].replace("<", "&lt;").replace(">", "&gt;")
        st.markdown(f"""
        <div class="chunk-card">
            <div class="chunk-meta">
                <span class="chunk-num">#{i+1}</span>
                <span class="chunk-score">↑ {score:.3f}</span>
                <span class="chunk-title">{title}</span>
            </div>
            <div class="chunk-text">{text}…</div>
        </div>
        """, unsafe_allow_html=True)


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-logo">
        <div class="sb-logo-icon">⚡</div>
        <div>
            <div class="sb-logo-name">FastAPI RAG</div>
            <div class="sb-logo-tag">v1.0 · llama-3.3-70b</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-section">Retrieval</div>', unsafe_allow_html=True)
    top_k = st.slider("top_k", 3, 10, 5, label_visibility="collapsed")
    st.markdown(
        f'<div class="topk-display">{top_k}</div>'
        f'<div class="topk-label">chunks retrieved per query</div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="sb-section">Stack</div>', unsafe_allow_html=True)
    rows = [
        ("Ingestion",  "HTML + Markdown"),
        ("Chunking",   "Semantic"),
        ("Embeddings", "MiniLM-L6-v2"),
        ("Vector DB",  "ChromaDB"),
        ("LLM",        "Llama 3.3 70B"),
        ("Inference",  "Groq API"),
    ]
    html_rows = "".join(
        f'<div class="sb-row"><span class="sb-row-label">{k}</span>'
        f'<span class="sb-row-val">{v}</span></div>'
        for k, v in rows
    )
    st.markdown(f'<div class="sb-stack">{html_rows}</div>', unsafe_allow_html=True)

    if st.button("⟳  Clear conversation"):
        st.session_state.messages = []
        st.rerun()


# ── PIPELINE ──────────────────────────────────────────────────────────────────
@st.cache_resource
def load_pipeline(k: int) -> RAGPipeline:
    return RAGPipeline(top_k=k)

with st.spinner("Loading RAG pipeline…"):
    rag = load_pipeline(top_k)


# ── STATE ─────────────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []


# ── PAGE HEADER ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <div>
        <div class="page-title">FastAPI <span class="hl">Docs</span> Chatbot</div>
        <div class="page-meta">
            <span>RAG Pipeline</span> ·
            <span>ChromaDB</span> ·
            <span>Groq · Llama 3.3 70B</span>
        </div>
    </div>
    <div class="online-badge">
        <div class="pulse"></div>
        model online
    </div>
</div>
""", unsafe_allow_html=True)


# ── WELCOME SCREEN ────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-wrap">
      <div class="welcome-card">
        <div class="welcome-icon-wrap">⚡</div>
        <div class="welcome-title">Ask about FastAPI</div>
        <div class="welcome-desc">
          Grounded answers from the official FastAPI documentation.<br>
          Every claim is cited — zero hallucinations.
        </div>
        <div class="examples-label">Try asking</div>
        <div class="examples-grid">
          <div class="ex-chip">How do I define a path parameter?</div>
          <div class="ex-chip">What does Depends() do?</div>
          <div class="ex-chip">How to enable CORS?</div>
          <div class="ex-chip">Deploy FastAPI with Docker?</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── CHAT HISTORY ──────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("is_refusal"):
            st.warning("⚠️ " + msg["content"])
        else:
            st.markdown(msg["content"])

        if msg.get("sources"):
            with st.expander(f"◆ sources  ({len(msg['sources'])})"):
                render_sources(msg["sources"], msg.get("cited_ids"))

        if msg.get("chunks"):
            with st.expander(f"◈ retrieved chunks  ({len(msg['chunks'])})"):
                render_chunks(msg["chunks"])


# ── CHAT INPUT ────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask anything about FastAPI…"):

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving · Generating…"):
            result = rag.ask(prompt)

        answer     = result["answer"]
        is_refusal = result.get("is_refusal", False)
        sources    = result.get("sources", [])
        cited_ids  = result.get("cited_ids", [])
        chunks     = result.get("chunks_used", [])

        if is_refusal:
            st.warning("⚠️ " + answer)
        else:
            st.markdown(answer)

        if sources:
            with st.expander(f"◆ sources  ({len(sources)})"):
                render_sources(sources, cited_ids)

        if chunks:
            with st.expander(f"◈ retrieved chunks  ({len(chunks)})"):
                render_chunks(chunks)

    st.session_state.messages.append({
        "role":       "assistant",
        "content":    answer,
        "is_refusal": is_refusal,
        "sources":    sources,
        "cited_ids":  cited_ids,
        "chunks":     chunks,
    })
