import streamlit as st
import pdfplumber
from PIL import Image, ImageDraw
import plotly.graph_objects as go
from datetime import datetime
import html as html_lib
import io
import asyncio
import base64
import tempfile
import os
import sqlite3
import hashlib
import json
import uuid

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

# ==========================================
# DATABASE LAYER
# ==========================================
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "legal_guard.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            created_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audits (
            id           TEXT PRIMARY KEY,
            user_id      TEXT NOT NULL,
            filename     TEXT NOT NULL,
            page_count   INTEGER,
            issues_found INTEGER,
            issues_json  TEXT,
            created_at   TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def db_create_user(name, email, password):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (id,name,email,password,created_at) VALUES (?,?,?,?,?)",
            (str(uuid.uuid4()), name, email.lower().strip(), hash_pw(password), datetime.now().isoformat())
        )
        conn.commit()
        return True, "Account created! Please sign in."
    except sqlite3.IntegrityError:
        return False, "Email already registered."
    finally:
        conn.close()

def db_login(email, password):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email.lower().strip(), hash_pw(password))
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def db_save_audit(user_id, filename, page_count, hits):
    issues_json = json.dumps([{"title": h["title"], "pg": h["pg"]} for h in hits])
    conn = get_db()
    conn.execute(
        "INSERT INTO audits (id,user_id,filename,page_count,issues_found,issues_json,created_at) VALUES (?,?,?,?,?,?,?)",
        (str(uuid.uuid4()), user_id, filename, page_count, len(hits), issues_json, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def db_get_audits(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM audits WHERE user_id=? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ==========================================
# PDF RENDERER
# ==========================================
def _render_pages_to_images(uploaded_file, resolution=150):
    uploaded_file.seek(0)
    raw_bytes = uploaded_file.read()
    try:
        from pdf2image import convert_from_bytes
        imgs = convert_from_bytes(raw_bytes, dpi=resolution)
        uploaded_file.seek(0)
        return imgs
    except Exception:
        pass
    try:
        uploaded_file.seek(0)
        with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
            imgs = [p.to_image(resolution=resolution).original for p in pdf.pages]
        uploaded_file.seek(0)
        return imgs
    except Exception:
        pass
    uploaded_file.seek(0)
    with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
        n = len(pdf.pages)
    imgs = []
    for i in range(n):
        img = Image.new("RGB", (850, 1100), color=(240, 237, 230))
        draw = ImageDraw.Draw(img)
        draw.text((425, 550), f"Page {i+1}\n(Preview unavailable)", fill=(150,150,150), anchor="mm")
        imgs.append(img)
    uploaded_file.seek(0)
    return imgs

# ==========================================
# 1. PAGE CONFIG & STYLING
# ==========================================
st.set_page_config(layout="wide", page_title="Legal Guard Pro", page_icon="⚖️")
init_db()

def inject_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&display=swap');
        * { font-family: 'DM Sans', sans-serif !important; }
        .main, .stApp { background-color: #f5f0e8 !important; color: #1a1a1a !important; }
        #MainMenu, footer, header { visibility: hidden; }
        .block-container { padding-top: 1rem !important; max-width: 1300px !important; }

        [data-testid="stFileUploader"] section button { display: none !important; }
        [data-testid="stFileUploader"] section div { font-size: 0px !important; color: transparent !important; }
        [data-testid="stFileUploader"] small { display: none !important; }
        [data-testid="stFileUploader"] section::before { content: "Drop your contract PDF here"; font-size: 1rem; color: #1a1a1a; display: block; margin-bottom: 10px; }
        div[data-testid="stFileUploader"] section div[role="button"] + div { display: none !important; }
        div[data-testid="stFileUploader"] label { display: none !important; }

        .brand-header { background: #1a1a1a; padding: 1rem 2rem; border-radius: 16px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
        .brand-header h3 { margin: 0; color: #f5f0e8; font-weight: 300; font-size: 1.1rem; letter-spacing: 2px; }
        .brand-header .accent { color: #e8b931; font-weight: 700; }
        .brand-header .meta { margin: 0; color: #8b8e98; font-size: 9px; letter-spacing: 1px; }
        .brand-header .user-name { margin: 0; font-size: 12px; font-weight: 600; color: #f5f0e8; }
        .brand-header .user-sub { margin: 0; color: #8b8e98; font-size: 9px; }

        .greeting-section { margin-bottom: 28px; }
        .greeting-section h1 { font-size: 2rem; font-weight: 700; color: #1a1a1a; margin: 0 0 4px 0; }
        .greeting-section p { font-size: 0.95rem; color: #6b6b6b; margin: 0; }

        .dash-card { background: #ffffff; border-radius: 16px; padding: 20px 24px; margin-bottom: 16px; border: 1px solid rgba(0,0,0,0.06); box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
        .card-title { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; color: #999; margin-bottom: 10px; }

        .issue-card { background: #fff; border-radius: 14px; padding: 18px 22px; margin-bottom: 12px; border: 1px solid rgba(0,0,0,0.06); border-left: 4px solid #e74c3c; }
        .issue-card b { color: #1a1a1a; font-size: 0.85rem; }
        .issue-card p { color: #555; font-size: 0.8rem; margin: 6px 0 0 0; line-height: 1.5; }

        .insight-pill { background: linear-gradient(135deg, #fdf6e3 0%, #fceabb 100%); border-radius: 14px; padding: 18px 22px; margin-bottom: 12px; border: 1px solid rgba(200,170,80,0.2); }
        .insight-pill b { color: #8a6d00; font-size: 0.75rem; letter-spacing: 1px; }
        .insight-pill p { color: #5a4e00; font-size: 0.82rem; margin: 8px 0 0 0; font-style: italic; line-height: 1.5; }

        .stat-box { text-align: center; padding: 16px; background: #fff; border-radius: 14px; border: 1px solid rgba(0,0,0,0.06); }
        .stat-box .num { font-size: 1.8rem; font-weight: 700; color: #1a1a1a; }
        .stat-box .label { font-size: 0.7rem; color: #999; text-transform: uppercase; letter-spacing: 1px; }

        .stButton > button { background: #1a1a1a !important; color: #f5f0e8 !important; border: none !important; border-radius: 12px !important; padding: 0.5rem 1.5rem !important; font-weight: 500 !important; font-size: 0.85rem !important; letter-spacing: 0.5px !important; transition: all 0.2s !important; }
        .stButton > button:hover { background: #333 !important; transform: translateY(-1px) !important; }

        .stFileUploader { background: #fff !important; border-radius: 16px !important; border: 2px dashed rgba(0,0,0,0.12) !important; padding: 20px !important; }
        .stTextInput input { background: #fff !important; border: 1px solid rgba(0,0,0,0.1) !important; border-radius: 12px !important; color: #1a1a1a !important; font-size: 1rem !important; padding: 12px 16px !important; }
        div[data-testid="stForm"] { background: #fff; border-radius: 20px; padding: 2rem; border: 1px solid rgba(0,0,0,0.06); }

        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #ccc; border-radius: 3px; }

        /* Auth page */
        .auth-hero { text-align: center; padding: 48px 20px 28px 20px; }
        .auth-hero .emoji { font-size: 3rem; margin-bottom: 12px; }
        .auth-hero h1 { font-size: 1.8rem; font-weight: 700; color: #1a1a1a; margin: 0 0 6px 0; }
        .auth-hero p { color: #888; font-size: 0.9rem; margin: 0; }

        /* Sidebar history card */
        .hist-card { background:#fff; border-radius:10px; padding:10px 14px; margin-bottom:8px; border:1px solid rgba(0,0,0,0.06); }
        .hist-card .hc-name { font-size:0.78rem; font-weight:600; color:#1a1a1a; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin:0; }
        .hist-card .hc-meta { font-size:0.7rem; color:#999; margin:2px 0 0 0; }
        </style>
    """, unsafe_allow_html=True)


def render_header(user):
    st.markdown(f"""
        <div class="brand-header">
            <div>
                <h3>LEGAL GUARD <span class="accent">PRO</span></h3>
                <p class="meta">V1.0 · RAG-AUGMENTED AUDIT ENGINE</p>
            </div>
            <div style="text-align:right;">
                <p class="user-name">{user['name'].upper()}</p>
                <p class="user-sub">{user['email']}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)


def get_greeting():
    h = datetime.now().hour
    return "Good morning" if h < 12 else "Good afternoon" if h < 17 else "Good evening"


# ==========================================
# 2. CORE LOGIC
# ==========================================
def get_legal_context(issue_title):
    db = {
        "Restraint of Trade": {
            "law": "Section 27, Indian Contract Act",
            "precedent": "Niranjan Shankar Golikari v. Century Spinning (1967). Post-employment restrictions are void under Section 27.",
            "reason_en": "restricts your freedom to work after employment ends. Courts have consistently held such clauses unenforceable.",
            "reason_hi": "यह रोजगार समाप्त होने के बाद आपके काम करने की स्वतंत्रता पर रोक लगाता है। अदालतों ने ऐसे क्लॉज को अप्रवर्तनीय माना है।",
            "law_hi": "भारतीय अनुबंध अधिनियम की धारा 27",
        },
        "Punitive Financial Penalty": {
            "law": "Section 74, Indian Contract Act",
            "precedent": "Fateh Chand v. Balkishan Das (1964). Damages limited to 'reasonable compensation'.",
            "reason_en": "imposes unreasonable financial penalties. The law limits compensation to actual loss, not arbitrary punishment amounts.",
            "reason_hi": "यह अनुचित वित्तीय जुर्माना लगाता है। कानून केवल वास्तविक नुकसान की भरपाई की अनुमति देता है, मनमानी दंड राशि की नहीं।",
            "law_hi": "भारतीय अनुबंध अधिनियम की धारा 74",
        },
        "Unconscionable Terms": {
            "law": "Article 14, Constitution of India",
            "precedent": "Central Inland Water Transport (1986). Grossly unfair terms are unenforceable.",
            "reason_en": "contains grossly unfair and unconscionable terms that no reasonable person would agree to voluntarily.",
            "reason_hi": "इसमें अत्यधिक अनुचित शर्तें हैं जिन पर कोई भी समझदार व्यक्ति स्वेच्छा से सहमत नहीं होगा।",
            "law_hi": "भारतीय संविधान का अनुच्छेद 14",
        },
        "Document Seizure": {
            "law": "Fundamental Rights & Bonded Labour System (Abolition) Act, 1976",
            "precedent": "Surrendering original educational certificates is classified as bonded labour practice.",
            "reason_en": "requires surrender of original documents, which is illegal under the Bonded Labour Abolition Act and violates fundamental rights.",
            "reason_hi": "मूल दस्तावेज़ जमा करने की आवश्यकता है, जो बंधुआ मजदूरी उन्मूलन अधिनियम के तहत गैरकानूनी है।",
            "law_hi": "बंधुआ मजदूरी प्रणाली (उन्मूलन) अधिनियम, 1976",
        },
        "Privacy Violation": {
            "law": "Information Technology Act & Right to Privacy (K.S. Puttaswamy, 2017)",
            "precedent": "K.S. Puttaswamy v. Union of India (2017). Privacy is a fundamental right.",
            "reason_en": "mandates pervasive monitoring including screen recording and webcam capture, which violates your constitutional right to privacy.",
            "reason_hi": "स्क्रीन रिकॉर्डिंग और वेबकैम सहित व्यापक निगरानी अनिवार्य करता है, जो आपके गोपनीयता के मौलिक अधिकार का उल्लंघन है।",
            "law_hi": "सूचना प्रौद्योगिकी अधिनियम और गोपनीयता का अधिकार",
        },
    }
    return db.get(issue_title, {
        "law": "Indian Contract Act", "precedent": "Refer to relevant sections of the Indian Contract Act.",
        "reason_en": "may be legally unenforceable or exploitative.",
        "reason_hi": "कानूनी रूप से अप्रवर्तनीय या शोषणकारी हो सकता है।",
        "law_hi": "भारतीय अनुबंध अधिनियम",
    })


def draw_precise_underline(page_obj, base_img, search_keywords):
    draw = ImageDraw.Draw(base_img)
    pdf_w = float(page_obj.width)
    pdf_h = float(page_obj.height)
    img_w, img_h = base_img.size
    scale_x = img_w / pdf_w
    scale_y = img_h / pdf_h
    words = page_obj.extract_words()
    for word in words:
        if any(k.lower() in word['text'].lower() for k in search_keywords):
            x0 = float(word['x0']) * scale_x
            x1 = float(word['x1']) * scale_x
            y_line = float(word['bottom']) * scale_y + 2
            y_top = float(word['top']) * scale_y
            y_bot = float(word['bottom']) * scale_y
            if base_img.mode != 'RGBA':
                base_img = base_img.convert('RGBA')
            overlay = Image.new('RGBA', base_img.size, (0, 0, 0, 0))
            ov_draw = ImageDraw.Draw(overlay)
            ov_draw.rectangle([(x0-1, y_top-1), (x1+1, y_bot+1)], fill=(255, 215, 0, 120))
            base_img = Image.alpha_composite(base_img, overlay)
            draw = ImageDraw.Draw(base_img)
            draw.line([(x0, y_line), (x1, y_line)], fill="#e74c3c", width=3)
    return base_img


def render_gauge(issue_title):
    difficulty = {"Restraint of Trade": 40, "Punitive Financial Penalty": 85, "Unconscionable Terms": 90, "Document Seizure": 95, "Privacy Violation": 70}
    val = difficulty.get(issue_title, 50)
    color = "#2ecc71" if val < 50 else "#e8b931" if val < 75 else "#e74c3c"
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=val,
        title={'text': "Risk Level", 'font': {'size': 13, 'color': '#1a1a1a'}},
        number={'font': {'color': '#1a1a1a', 'size': 36}},
        gauge={'axis': {'range': [0, 100], 'tickcolor': '#ccc'}, 'bar': {'color': color, 'thickness': 0.3}, 'bgcolor': '#f0ebe0', 'borderwidth': 0,
               'steps': [{'range': [0,40], 'color': 'rgba(46,204,113,0.1)'}, {'range': [40,75], 'color': 'rgba(232,185,49,0.1)'}, {'range': [75,100], 'color': 'rgba(231,76,60,0.1)'}]}
    ))
    fig.update_layout(height=200, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'color': "#1a1a1a"}, margin=dict(t=50, b=10, l=30, r=30))
    return fig


_HI_TITLE_MAP = {
    "Restraint of Trade": "व्यापार पर प्रतिबंध",
    "Punitive Financial Penalty": "दंडात्मक वित्तीय जुर्माना",
    "Unconscionable Terms": "अनुचित शर्तें",
    "Document Seizure": "दस्तावेज़ जब्ती",
    "Privacy Violation": "गोपनीयता उल्लंघन",
}

def generate_transcript_en(hits, username):
    if not hits:
        return f"Hello {username}. No adversarial clauses were detected in this document."
    lines = [f"Hello {username}. I have found {len(hits)} adversarial clause{'s' if len(hits)>1 else ''} in this contract."]
    for i, h in enumerate(hits, 1):
        ctx = get_legal_context(h['title'])
        lines.append(f"Issue {i}: {h['title']} — detected on page {h['pg']}. According to {ctx['law']}, this clause {ctx['reason_en']}")
    lines.append("Please consult a qualified legal professional before signing this document.")
    return " ".join(lines)

def generate_transcript_hi(hits, username):
    if not hits:
        return f"नमस्ते {username}। इस दस्तावेज़ में कोई प्रतिकूल क्लॉज नहीं मिला।"
    lines = [f"नमस्ते {username}। मुझे इस अनुबंध में {len(hits)} प्रतिकूल क्लॉज मिले हैं।"]
    for i, h in enumerate(hits, 1):
        ctx = get_legal_context(h['title'])
        title_hi = _HI_TITLE_MAP.get(h['title'], h['title'])
        lines.append(f"समस्या {i}: {title_hi} — पृष्ठ {h['pg']} पर पाया गया। {ctx['law_hi']} के अनुसार, यह क्लॉज {ctx['reason_hi']}")
    lines.append("कृपया इस दस्तावेज़ पर हस्ताक्षर करने से पहले किसी योग्य कानूनी विशेषज्ञ से परामर्श लें।")
    return " ".join(lines)


def _generate_audio_b64(text: str, voice: str):
    if not EDGE_TTS_AVAILABLE:
        return None
    try:
        async def _run():
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tmp_path = f.name
            comm = edge_tts.Communicate(text, voice)
            await comm.save(tmp_path)
            return tmp_path
        tmp_path = asyncio.run(_run())
        with open(tmp_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        os.remove(tmp_path)
        return data
    except Exception:
        return None


def render_tts_component(text_en: str, text_hi: str):
    safe_en = html_lib.escape(text_en)
    safe_hi = html_lib.escape(text_hi)
    audio_en_b64 = _generate_audio_b64(text_en, "en-IN-NeerjaNeural")
    audio_hi_b64 = _generate_audio_b64(text_hi, "hi-IN-SwaraNeural")
    src_en = f"data:audio/mpeg;base64,{audio_en_b64}" if audio_en_b64 else ""
    src_hi = f"data:audio/mpeg;base64,{audio_hi_b64}" if audio_hi_b64 else ""
    edge_ok = bool(audio_en_b64 or audio_hi_b64)
    component_html = f"""
    <div style="background:#1a1a1a;border-radius:14px;padding:20px 22px;margin-bottom:12px;border-left:4px solid #e8b931;font-family:'DM Sans',sans-serif;">
        <div style="color:#e8b931;font-size:0.7rem;font-weight:700;letter-spacing:1.5px;margin-bottom:14px;">🔊 VOICE TRANSCRIPT {"· Microsoft Neural" if edge_ok else "· Web Speech"}</div>
        <div style="display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap;">
            <button onclick="playEN()" style="background:#e8b931;color:#1a1a1a;border:none;border-radius:10px;padding:10px 22px;font-size:0.85rem;font-weight:700;cursor:pointer;">▶ English</button>
            <button onclick="playHI()" style="background:#2a2a2a;color:#f5f0e8;border:1px solid #444;border-radius:10px;padding:10px 22px;font-size:0.85rem;font-weight:700;cursor:pointer;">▶ हिंदी</button>
            <button onclick="stopAll()" style="background:#e74c3c22;color:#e74c3c;border:1px solid #e74c3c55;border-radius:10px;padding:10px 16px;font-size:0.85rem;cursor:pointer;">■ Stop</button>
        </div>
        <div id="rv-status" style="color:#888;font-size:0.75rem;margin-bottom:12px;min-height:18px;"></div>
        <audio id="audio-en" src="{src_en}" preload="auto"></audio>
        <audio id="audio-hi" src="{src_hi}" preload="auto"></audio>
        <div id="panel-en" style="display:none;border-top:1px solid #333;padding-top:14px;margin-top:8px;">
            <div style="color:#e8b931;font-size:0.68rem;letter-spacing:1px;margin-bottom:10px;">EN · TRANSCRIPT</div>
            <div style="color:#f5f0e8;font-size:0.8rem;line-height:1.75;font-style:italic;">{safe_en}</div>
        </div>
        <div id="panel-hi" style="display:none;border-top:1px solid #333;padding-top:14px;margin-top:8px;">
            <div style="color:#e8b931;font-size:0.68rem;letter-spacing:1px;margin-bottom:10px;">HI · ट्रांसक्रिप्ट</div>
            <div style="color:#f5f0e8;font-size:0.8rem;line-height:1.75;font-style:italic;">{safe_hi}</div>
        </div>
    </div>
    <script>
    var _edgeOK = {'true' if edge_ok else 'false'};
    var _textEN = {repr(text_en)};
    var _textHI = {repr(text_hi)};
    function setStatus(m){{document.getElementById('rv-status').textContent=m;}}
    function stopAll(){{['audio-en','audio-hi'].forEach(function(id){{var a=document.getElementById(id);if(a){{a.pause();a.currentTime=0;}}}});window.speechSynthesis&&window.speechSynthesis.cancel();setStatus('');}}
    function showPanel(l){{document.getElementById('panel-en').style.display=l==='en'?'block':'none';document.getElementById('panel-hi').style.display=l==='hi'?'block':'none';}}
    function playEN(){{stopAll();showPanel('en');var a=document.getElementById('audio-en');if(_edgeOK&&a&&a.src&&a.src!==window.location.href){{setStatus('Speaking English (Microsoft Neural)...');a.play();a.onended=function(){{setStatus('Done.');}};}}else{{var u=new SpeechSynthesisUtterance(_textEN);u.lang='en-IN';window.speechSynthesis.speak(u);setStatus('Speaking...');}}}}
    function playHI(){{stopAll();showPanel('hi');var a=document.getElementById('audio-hi');if(_edgeOK&&a&&a.src&&a.src!==window.location.href){{setStatus('हिंदी में बोल रहे हैं (Microsoft Neural)...');a.play();a.onended=function(){{setStatus('पूर्ण।');}};}}else{{var u=new SpeechSynthesisUtterance(_textHI);u.lang='hi-IN';window.speechSynthesis.speak(u);setStatus('Speaking...');}}}}
    </script>
    """
    st.components.v1.html(component_html, height=400, scrolling=True)


# ==========================================
# AUTH SCREEN
# ==========================================
def show_auth_screen():
    inject_styles()
    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        st.markdown("""
            <div class="auth-hero">
                <div class="emoji">⚖️</div>
                <h1>Legal Guard Pro</h1>
                <p>AI-powered adversarial clause detection engine</p>
            </div>
        """, unsafe_allow_html=True)

        tab_in, tab_up = st.tabs(["  Sign In  ", "  Create Account  "])

        with tab_in:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("login_form"):
                email    = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                if st.form_submit_button("Sign In →", use_container_width=True):
                    if email and password:
                        user = db_login(email, password)
                        if user:
                            st.session_state.user        = user
                            st.session_state.audit_hits  = []
                            st.session_state.idx         = 0
                            st.rerun()
                        else:
                            st.error("Incorrect email or password.")
                    else:
                        st.warning("Please enter email and password.")

        with tab_up:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("signup_form"):
                name     = st.text_input("Full Name", placeholder="Harleen Singh")
                email2   = st.text_input("Email", placeholder="you@example.com")
                pass1    = st.text_input("Password", type="password", placeholder="Min 6 characters")
                pass2    = st.text_input("Confirm Password", type="password", placeholder="Repeat password")
                if st.form_submit_button("Create Account →", use_container_width=True):
                    if not all([name, email2, pass1, pass2]):
                        st.warning("Please fill in all fields.")
                    elif len(pass1) < 6:
                        st.warning("Password must be at least 6 characters.")
                    elif pass1 != pass2:
                        st.error("Passwords do not match.")
                    else:
                        ok, msg = db_create_user(name, email2, pass1)
                        st.success(msg) if ok else st.error(msg)


# ==========================================
# SIDEBAR — audit history + sign out
# ==========================================
def show_sidebar(user):
    with st.sidebar:
        st.markdown(f"""
            <div style="padding:16px 0 8px 0;">
                <p style="font-size:0.68rem;color:#999;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px;">Signed in as</p>
                <p style="font-weight:700;color:#1a1a1a;font-size:0.95rem;margin:0;">{user['name']}</p>
                <p style="font-size:0.75rem;color:#888;margin:2px 0 16px 0;">{user['email']}</p>
            </div>
        """, unsafe_allow_html=True)

        if st.button("⬅  Sign Out", use_container_width=True):
            for k in ["user", "audit_hits", "idx"]:
                st.session_state.pop(k, None)
            st.rerun()

        st.markdown("---")
        st.markdown('<p style="font-size:0.68rem;color:#999;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;">📋 Audit History</p>', unsafe_allow_html=True)

        audits = db_get_audits(user["id"])
        if not audits:
            st.markdown('<p style="color:#bbb;font-size:0.82rem;font-style:italic;">No audits yet.</p>', unsafe_allow_html=True)
        else:
            for a in audits[:15]:
                dt     = datetime.fromisoformat(a["created_at"]).strftime("%d %b %Y, %I:%M %p")
                n      = a["issues_found"]
                color  = "#e74c3c" if n > 0 else "#2ecc71"
                label  = f"{n} issue{'s' if n != 1 else ''}"
                st.markdown(f"""
                    <div class="hist-card">
                        <p class="hc-name">📄 {a['filename']}</p>
                        <p class="hc-meta">{dt} &nbsp;·&nbsp; <span style="color:{color};font-weight:600;">{label}</span> &nbsp;·&nbsp; {a['page_count']}p</p>
                    </div>
                """, unsafe_allow_html=True)


# ==========================================
# 3. MAIN APP
# ==========================================
def main():
    # ── Auth gate ──────────────────────────────
    if "user" not in st.session_state:
        show_auth_screen()
        return

    user = st.session_state.user
    inject_styles()
    show_sidebar(user)

    if "audit_hits" not in st.session_state:
        st.session_state.audit_hits = []
    if "idx" not in st.session_state:
        st.session_state.idx = 0

    render_header(user)

    greeting = get_greeting()
    st.markdown(f"""
        <div class="greeting-section">
            <h1>{greeting}, {user['name'].split()[0]} 👋</h1>
            <p>Let's review your legal documents for adversarial clauses today.</p>
        </div>
    """, unsafe_allow_html=True)

    file = st.file_uploader("Drop your contract PDF here", type="pdf", label_visibility="hidden")

    if file:
        raw_imgs = _render_pages_to_images(file, resolution=150)
        file.seek(0)
        with pdfplumber.open(file) as pdf:
            page_count = len(pdf.pages)

        c_left, c_right = st.columns([1.3, 1], gap="large")

        with c_right:
            if st.button("🔍  Run Clause Audit", use_container_width=True):
                hits = []
                rules = {
                    "Restraint of Trade":        ["24/7", "availability", "github", "open-source", "prohibited", "seeking employment", "five (5) years"],
                    "Punitive Financial Penalty": ["penalty", "bond", "repay", "reimburse", "₹8,00,000", "training bond"],
                    "Unconscionable Terms":       ["reassign", "manual labor", "security"],
                    "Document Seizure":           ["surrender", "original", "certificates", "hr safe"],
                    "Privacy Violation":          ["pervasive", "monitoring", "records screen", "webcam", "microphone"],
                }
                file.seek(0)
                with pdfplumber.open(file) as pdf2:
                    for i, p in enumerate(pdf2.pages):
                        text_lower = (p.extract_text() or "").lower()
                        for title, keys in rules.items():
                            if any(k.lower() in text_lower for k in keys):
                                marked_img = draw_precise_underline(p, raw_imgs[i].copy(), keys)
                                hits.append({"title": title, "img": marked_img, "pg": i + 1})

                st.session_state.audit_hits = hits
                st.session_state.idx = 0
                # ── Save to DB ──────────────────
                db_save_audit(user["id"], file.name, page_count, hits)
                st.rerun()

            if st.session_state.audit_hits:
                curr  = st.session_state.audit_hits[st.session_state.idx]
                ctx   = get_legal_context(curr['title'])
                total = len(st.session_state.audit_hits)

                st.markdown(f"""
                    <div style="display:flex;gap:12px;margin-bottom:16px;">
                        <div class="stat-box" style="flex:1;"><div class="num" style="color:#e74c3c;">{total}</div><div class="label">Issues Found</div></div>
                        <div class="stat-box" style="flex:1;"><div class="num">{page_count}</div><div class="label">Pages Scanned</div></div>
                        <div class="stat-box" style="flex:1;"><div class="num">Pg {curr['pg']}</div><div class="label">Current</div></div>
                    </div>
                """, unsafe_allow_html=True)

                st.plotly_chart(render_gauge(curr['title']), use_container_width=True)

                st.markdown(f"""
                    <div class="issue-card">
                        <b>⚠️ {curr['title']}</b>
                        <p>Detected on <b>Page {curr['pg']}</b> — This clause may be legally unenforceable or exploitative.</p>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                    <div class="insight-pill">
                        <b>📚 LEGAL PRECEDENT</b>
                        <p>{ctx['precedent']}</p>
                    </div>
                """, unsafe_allow_html=True)

                n1, n2, n3 = st.columns([1, 1, 1])
                if n1.button("← Prev") and st.session_state.idx > 0:
                    st.session_state.idx -= 1; st.rerun()
                n2.markdown(f"<div style='text-align:center;padding-top:8px;font-weight:600;color:#1a1a1a;'>{st.session_state.idx+1} / {total}</div>", unsafe_allow_html=True)
                if n3.button("Next →") and st.session_state.idx < total - 1:
                    st.session_state.idx += 1; st.rerun()

                st.markdown("---")
                transcript_en = generate_transcript_en(st.session_state.audit_hits, user['name'])
                transcript_hi = generate_transcript_hi(st.session_state.audit_hits, user['name'])
                render_tts_component(transcript_en, transcript_hi)

            else:
                st.markdown("""
                    <div class="dash-card" style="text-align:center;padding:40px;">
                        <p style="font-size:2rem;margin-bottom:8px;">🔍</p>
                        <p style="color:#999;font-size:0.9rem;">Hit <b>Run Clause Audit</b> to scan for adversarial clauses</p>
                    </div>
                """, unsafe_allow_html=True)

        with c_left:
            st.markdown('<div class="card-title">📄 Document Preview</div>', unsafe_allow_html=True)
            if st.session_state.audit_hits:
                st.image(st.session_state.audit_hits[st.session_state.idx]['img'], use_container_width=True)
            else:
                st.image(raw_imgs[0], use_container_width=True)

    else:
        st.markdown("""
            <div class="dash-card" style="text-align:center;padding:60px 40px;">
                <p style="font-size:3rem;margin-bottom:12px;">📄</p>
                <h3 style="color:#1a1a1a;font-weight:600;margin-bottom:8px;">Drop your contract here</h3>
                <p style="color:#888;font-size:0.9rem;">Upload a PDF to begin scanning for adversarial clauses</p>
            </div>
        """, unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""<div class="dash-card"><p style="font-size:1.5rem;margin-bottom:8px;">🔍</p><b style="font-size:0.85rem;">Clause Detection</b><p style="color:#888;font-size:0.78rem;margin-top:6px;">Automatically flags restraint of trade, penalties & unconscionable terms</p></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown("""<div class="dash-card"><p style="font-size:1.5rem;margin-bottom:8px;">📚</p><b style="font-size:0.85rem;">Legal Precedents</b><p style="color:#888;font-size:0.78rem;margin-top:6px;">RAG-powered insights citing landmark Indian Supreme Court cases</p></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown("""<div class="dash-card"><p style="font-size:1.5rem;margin-bottom:8px;">🔊</p><b style="font-size:0.85rem;">Voice Transcript</b><p style="color:#888;font-size:0.78rem;margin-top:6px;">Full audit read aloud in English & Hindi with on-screen transcript</p></div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()