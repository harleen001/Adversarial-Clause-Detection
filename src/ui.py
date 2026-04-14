import streamlit as st
import pdfplumber
from PIL import Image, ImageDraw
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# 1. PAGE CONFIG & STYLING
# ==========================================
st.set_page_config(layout="wide", page_title="Legal Guard Pro", page_icon="⚖️")

def inject_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&display=swap');

        * { font-family: 'DM Sans', sans-serif !important; }

        .main, .stApp {
            background-color: #f5f0e8 !important;
            color: #1a1a1a !important;
        }

        #MainMenu, footer, header { visibility: hidden; }

        .block-container {
            padding-top: 1rem !important;
            max-width: 1300px !important;
        }

        /* --- FILE UPLOADER CLEANUP (THE FIX) --- */
        
        /* 1. Hide the browse button completely (since you have a custom label) */
        [data-testid="stFileUploader"] section button {
            display: none !important;
        }

        /* 2. Hide the redundant 'upload' text that appears next to the button */
        [data-testid="stFileUploader"] section div {
            font-size: 0px !important;
            color: transparent !important;
        }

        /* 3. Hide the small '200MB per file' helper text if it's causing the overlap */
        [data-testid="stFileUploader"] small {
            display: none !important;
        }

        /* 4. Restore visibility ONLY for the Drag and Drop text if needed, 
           or just keep it clean as a box */
        [data-testid="stFileUploader"] section::before {
            content: "Drop your contract PDF here";
            font-size: 1rem;
            color: #1a1a1a;
            display: block;
            margin-bottom: 10px;
        }

        /* --- REST OF YOUR STYLES --- */
        .brand-header {
            background: #1a1a1a;
            padding: 1rem 2rem;
            border-radius: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }
        .brand-header h3 { margin: 0; color: #f5f0e8; font-weight: 300; font-size: 1.1rem; letter-spacing: 2px; }
        .brand-header .accent { color: #e8b931; font-weight: 700; }
        .brand-header .meta { margin: 0; color: #8b8e98; font-size: 9px; letter-spacing: 1px; }
        .brand-header .user-info { text-align: right; }
        .brand-header .user-name { margin: 0; font-size: 12px; font-weight: 600; color: #f5f0e8; }
        .brand-header .user-sub { margin: 0; color: #8b8e98; font-size: 9px; }

        /* Greeting */
        .greeting-section {
            margin-bottom: 28px;
        }
        .greeting-section h1 {
            font-size: 2rem; font-weight: 700; color: #1a1a1a; margin: 0 0 4px 0;
        }
        .greeting-section p {
            font-size: 0.95rem; color: #6b6b6b; margin: 0;
        }

        /* Cards */
        .dash-card {
            background: #ffffff;
            border-radius: 16px;
            padding: 20px 24px;
            margin-bottom: 16px;
            border: 1px solid rgba(0,0,0,0.06);
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .dash-card-dark {
            background: #1a1a1a;
            border-radius: 16px;
            padding: 20px 24px;
            margin-bottom: 16px;
            color: #f5f0e8;
        }
        .card-title {
            font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
            letter-spacing: 1.5px; color: #999; margin-bottom: 10px;
        }

        /* Issue cards */
        .issue-card {
            background: #fff;
            border-radius: 14px;
            padding: 18px 22px;
            margin-bottom: 12px;
            border-left: 4px solid #e74c3c;
            border: 1px solid rgba(0,0,0,0.06);
            border-left: 4px solid #e74c3c;
        }
        .issue-card.safe {
            border-left: 4px solid #2ecc71;
        }
        .issue-card b { color: #1a1a1a; font-size: 0.85rem; }
        .issue-card p { color: #555; font-size: 0.8rem; margin: 6px 0 0 0; line-height: 1.5; }

        /* Insight pill */
        .insight-pill {
            background: linear-gradient(135deg, #fdf6e3 0%, #fceabb 100%);
            border-radius: 14px;
            padding: 18px 22px;
            margin-bottom: 12px;
            border: 1px solid rgba(200,170,80,0.2);
        }
        .insight-pill b { color: #8a6d00; font-size: 0.75rem; letter-spacing: 1px; }
        .insight-pill p { color: #5a4e00; font-size: 0.82rem; margin: 8px 0 0 0; font-style: italic; line-height: 1.5; }

        /* Stats row */
        .stat-box {
            text-align: center; padding: 16px;
            background: #fff; border-radius: 14px;
            border: 1px solid rgba(0,0,0,0.06);
        }
        .stat-box .num { font-size: 1.8rem; font-weight: 700; color: #1a1a1a; }
        .stat-box .label { font-size: 0.7rem; color: #999; text-transform: uppercase; letter-spacing: 1px; }

        /* Navigation buttons */
        .stButton > button {
            background: #1a1a1a !important;
            color: #f5f0e8 !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.5rem 1.5rem !important;
            font-weight: 500 !important;
            font-size: 0.85rem !important;
            letter-spacing: 0.5px !important;
            transition: all 0.2s !important;
        }
        .stButton > button:hover {
            background: #333 !important;
            transform: translateY(-1px) !important;
        }

        /* File uploader */
        .stFileUploader {
            background: #fff !important;
            border-radius: 16px !important;
            border: 2px dashed rgba(0,0,0,0.12) !important;
            padding: 20px !important;
        }
        .stFileUploader label { color: #1a1a1a !important; }

        /* Plotly chart background fix */
        .js-plotly-plot .plotly .main-svg { border-radius: 14px; }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #ccc; border-radius: 3px; }

        /* Input styling */
        .stTextInput input {
            background: #fff !important;
            border: 1px solid rgba(0,0,0,0.1) !important;
            border-radius: 12px !important;
            color: #1a1a1a !important;
            font-size: 1rem !important;
            padding: 12px 16px !important;
        }

        /* Dialog / popup styling */
        div[data-testid="stForm"] {
            background: #fff;
            border-radius: 20px;
            padding: 2rem;
            border: 1px solid rgba(0,0,0,0.06);
        }

        .welcome-box {
            text-align: center;
            padding: 60px 40px;
        }
        .welcome-box h2 {
            font-size: 1.6rem; font-weight: 700; color: #1a1a1a; margin-bottom: 8px;
        }
        .welcome-box p {
            color: #888; font-size: 0.9rem; margin-bottom: 24px;
        }
        .welcome-box .emoji { font-size: 3rem; margin-bottom: 16px; }
        
                /* Force hide the redundant label and internal 'upload' text overflow */
div[data-testid="stFileUploader"] section div[role="button"] + div {
    display: none !important;
}

/* Optional: Clean up the 'Browse files' button text if it's still overlapping */
div[data-testid="stFileUploader"] label {
    display: none !important;
}
        </style>
    """, unsafe_allow_html=True)


def render_header():
    st.markdown("""
        <div class="brand-header">
            <div>
                <h3>LEGAL GUARD <span class="accent">PRO</span></h3>
                <p class="meta">V1.0 · RAG-AUGMENTED AUDIT ENGINE</p>
            </div>
            <div class="user-info">
                <p class="user-name">Harleen Singh</p>
                <p class="user-sub">GNDU JALANDHAR · 2026</p>
            </div>
        </div>
    """, unsafe_allow_html=True)


def get_greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


# ==========================================
# 2. CORE LOGIC
# ==========================================
def get_legal_precedent(issue_title):
    db = {
        "Restraint of Trade": "Niranjan Shankar Golikari v. Century Spinning (1967). Post-employment restrictions are void under Section 27.",
        "Punitive Financial Penalty": "Fateh Chand v. Balkishan Das (1964). Damages limited to 'reasonable compensation'.",
        "Unconscionable Terms": "Central Inland Water Transport (1986). Grossly unfair terms are unenforceable."
    }
    return db.get(issue_title, "Refer to Section 27 of the Indian Contract Act.")


def draw_precise_underline(page_obj, base_img, search_keywords):
    draw = ImageDraw.Draw(base_img)
    pdf_width = float(page_obj.width)
    img_width = float(base_img.width)
    scale = img_width / pdf_width
    words = page_obj.extract_words()
    for word in words:
        if any(k in word['text'].lower() for k in search_keywords):
            x0 = float(word['x0']) * scale
            x1 = float(word['x1']) * scale
            y_base = float(word['bottom']) * scale + 2
            draw.line([x0, y_base, x1, y_base], fill="#e74c3c", width=3)
    return base_img


def render_gauge(issue_title):
    difficulty = {"Restraint of Trade": 40, "Punitive Financial Penalty": 85, "Unconscionable Terms": 90}
    val = difficulty.get(issue_title, 50)
    color = "#2ecc71" if val < 50 else "#e8b931" if val < 75 else "#e74c3c"
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=val,
        title={'text': f"Risk Level", 'font': {'size': 13, 'color': '#1a1a1a'}},
        number={'font': {'color': '#1a1a1a', 'size': 36}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': '#ccc'},
            'bar': {'color': color, 'thickness': 0.3},
            'bgcolor': '#f0ebe0',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 40], 'color': 'rgba(46,204,113,0.1)'},
                {'range': [40, 75], 'color': 'rgba(232,185,49,0.1)'},
                {'range': [75, 100], 'color': 'rgba(231,76,60,0.1)'}
            ],
        }
    ))
    fig.update_layout(
        height=200,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#1a1a1a"},
        margin=dict(t=50, b=10, l=30, r=30)
    )
    return fig


# ==========================================
# 3. MAIN APP
# ==========================================
def main():
    inject_styles()

    # --- Name popup / onboarding ---
    if 'username' not in st.session_state:
        st.session_state.username = None

    if not st.session_state.username:
        col_spacer1, col_form, col_spacer2 = st.columns([1, 1.5, 1])
        with col_form:
            st.markdown("""
                <div class="welcome-box">
                    <div class="emoji">⚖️</div>
                    <h2>Who's auditing clauses today?</h2>
                    <p>Enter your name to get started with Legal Guard Pro</p>
                </div>
            """, unsafe_allow_html=True)
            with st.form("name_form"):
                name = st.text_input("Your name", placeholder="e.g. Harleen Singh", label_visibility="collapsed")
                submitted = st.form_submit_button("Let's go →", use_container_width=True)
                if submitted and name.strip():
                    st.session_state.username = name.strip()
                    st.rerun()
        return

    # --- Main Dashboard ---
    if 'audit_hits' not in st.session_state:
        st.session_state.audit_hits = []
    if 'idx' not in st.session_state:
        st.session_state.idx = 0

    render_header()

    # Greeting
    greeting = get_greeting()
    st.markdown(f"""
        <div class="greeting-section">
            <h1>{greeting}, {st.session_state.username} 👋</h1>
            <p>Let's review your legal documents for adversarial clauses today.</p>
        </div>
    """, unsafe_allow_html=True)

    # Upload section
    # Upload section - label is collapsed to prevent the double text overlay
    file = st.file_uploader("Drop your contract PDF here", type="pdf", label_visibility="hidden")

    if file:
        with pdfplumber.open(file) as pdf:
            pages = pdf.pages
            raw_imgs = [p.to_image(resolution=150).original for p in pages]

        c_left, c_right = st.columns([1.3, 1], gap="large")

        with c_right:
            # Run audit button
            if st.button("🔍  Run Clause Audit", use_container_width=True):
                hits = []
                rules = {
                    "Restraint of Trade": ["24/7", "availability", "github", "open-source", "prohibited"],
                    "Punitive Financial Penalty": ["penalty", "bond", "repay"],
                    "Unconscionable Terms": ["reassign", "manual labor", "security"]
                }
                for i, p in enumerate(pages):
                    text = p.extract_text().lower() if p.extract_text() else ""
                    for title, keys in rules.items():
                        if any(k in text for k in keys):
                            marked_img = draw_precise_underline(p, raw_imgs[i].copy(), keys)
                            hits.append({"title": title, "img": marked_img, "pg": i + 1})
                st.session_state.audit_hits = hits
                st.session_state.idx = 0
                st.rerun()

            if st.session_state.audit_hits:
                curr = st.session_state.audit_hits[st.session_state.idx]

                # Stats row
                total = len(st.session_state.audit_hits)
                st.markdown(f"""
                    <div style="display:flex; gap:12px; margin-bottom:16px;">
                        <div class="stat-box" style="flex:1;">
                            <div class="num" style="color:#e74c3c;">{total}</div>
                            <div class="label">Issues Found</div>
                        </div>
                        <div class="stat-box" style="flex:1;">
                            <div class="num">{len(pages)}</div>
                            <div class="label">Pages Scanned</div>
                        </div>
                        <div class="stat-box" style="flex:1;">
                            <div class="num">Pg {curr['pg']}</div>
                            <div class="label">Current</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                # Gauge
                st.plotly_chart(render_gauge(curr['title']), use_container_width=True)

                # Issue detail
                st.markdown(f"""
                    <div class="issue-card">
                        <b>⚠️ {curr['title']}</b>
                        <p>Detected on <b>Page {curr['pg']}</b> — This clause may be legally unenforceable or exploitative.</p>
                    </div>
                """, unsafe_allow_html=True)

                # Legal insight
                st.markdown(f"""
                    <div class="insight-pill">
                        <b>📚 LEGAL PRECEDENT</b>
                        <p>{get_legal_precedent(curr['title'])}</p>
                    </div>
                """, unsafe_allow_html=True)

                # Navigation
                n1, n2, n3 = st.columns([1, 1, 1])
                if n1.button("← Prev") and st.session_state.idx > 0:
                    st.session_state.idx -= 1
                    st.rerun()
                n2.markdown(f"<div style='text-align:center; padding-top:8px; font-weight:600; color:#1a1a1a;'>{st.session_state.idx + 1} / {total}</div>", unsafe_allow_html=True)
                if n3.button("Next →") and st.session_state.idx < total - 1:
                    st.session_state.idx += 1
                    st.rerun()
            else:
                # Empty state
                st.markdown("""
                    <div class="dash-card" style="text-align:center; padding:40px;">
                        <p style="font-size:2rem; margin-bottom:8px;">🔍</p>
                        <p style="color:#999; font-size:0.9rem;">Hit <b>Run Clause Audit</b> to scan for adversarial clauses</p>
                    </div>
                """, unsafe_allow_html=True)

        with c_left:
            # Document preview card
            st.markdown('<div class="card-title">📄 Document Preview</div>', unsafe_allow_html=True)
            if st.session_state.audit_hits:
                st.image(st.session_state.audit_hits[st.session_state.idx]['img'], use_container_width=True)
            else:
                st.image(raw_imgs[0], use_container_width=True)
    else:
        # No file uploaded — show empty dashboard state
        st.markdown("""
            <div class="dash-card" style="text-align:center; padding:60px 40px;">
                <p style="font-size:3rem; margin-bottom:12px;">📄</p>
                <h3 style="color:#1a1a1a; font-weight:600; margin-bottom:8px;">Drop your contract here</h3>
                <p style="color:#888; font-size:0.9rem;">Upload a PDF to begin scanning for adversarial clauses</p>
            </div>
        """, unsafe_allow_html=True)

        # Feature cards
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""
                <div class="dash-card">
                    <p style="font-size:1.5rem; margin-bottom:8px;">🔍</p>
                    <b style="font-size:0.85rem;">Clause Detection</b>
                    <p style="color:#888; font-size:0.78rem; margin-top:6px;">Automatically flags restraint of trade, penalties & unconscionable terms</p>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("""
                <div class="dash-card">
                    <p style="font-size:1.5rem; margin-bottom:8px;">📚</p>
                    <b style="font-size:0.85rem;">Legal Precedents</b>
                    <p style="color:#888; font-size:0.78rem; margin-top:6px;">RAG-powered insights citing landmark Indian Supreme Court cases</p>
                </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown("""
                <div class="dash-card">
                    <p style="font-size:1.5rem; margin-bottom:8px;">📊</p>
                    <b style="font-size:0.85rem;">Risk Scoring</b>
                    <p style="color:#888; font-size:0.78rem; margin-top:6px;">Visual risk gauges showing enforceability difficulty per clause</p>
                </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
