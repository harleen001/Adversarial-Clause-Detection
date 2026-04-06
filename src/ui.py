import streamlit as st
import pdfplumber
from PIL import Image, ImageDraw
import plotly.graph_objects as go

# ==========================================
# 1. PAGE CONFIG & STYLING
# ==========================================
st.set_page_config(layout="wide", page_title="Legal Guard Pro", page_icon="⚖️")

def inject_styles():
    st.markdown("""
        <style>
        .main { background-color: #0b0e14; color: #e2e8f0; }
        .stApp { background-color: #0b0e14; }
        .brand-header {
            background: rgba(26, 28, 35, 0.9); padding: 1rem 2rem; 
            border-bottom: 1px solid #2d303d; display: flex; 
            justify-content: space-between; align-items: center; margin-bottom: 20px;
        }
        .clause-box {
            padding: 15px; border-radius: 10px; font-size: 0.85rem; 
            border: 1px solid rgba(255,255,255,0.1); margin-bottom: 10px;
        }
        .box-red { background: rgba(239, 68, 68, 0.05); border-left: 4px solid #ef4444; }
        .box-green { background: rgba(16, 185, 129, 0.05); border-left: 4px solid #10b981; }
        </style>
        <div class="brand-header">
            <div>
                <h3 style='margin:0; font-weight:300;'>LEGAL GUARD <span style='color:#ef4444; font-weight:600;'>PRO</span></h3>
                <p style='margin:0; color:#8b8e98; font-size:10px;'>V1.0 | RAG-AUGMENTED AUDIT</p>
            </div>
            <div style='text-align:right;'>
                <p style='margin:0; font-size:12px; font-weight:600;'>Harleen Singh</p>
                <p style='margin:0; color:#8b8e98; font-size:9px;'>GNDU JALANDHAR | 2026</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 2. CORE LOGIC: SCALED UNDERLINING
# ==========================================
def get_legal_precedent(issue_title):
    db = {
        "Restraint of Trade": "Niranjan Shankar Golikari v. Century Spinning (1967). Post-employment restrictions are void under Section 27.",
        "Punitive Financial Penalty": "Fateh Chand v. Balkishan Das (1964). Damages limited to 'reasonable compensation'.",
        "Unconscionable Terms": "Central Inland Water Transport (1986). Grossly unfair terms are unenforceable."
    }
    return db.get(issue_title, "Refer to Section 27 of the Indian Contract Act.")

def draw_precise_underline(page_obj, base_img, search_keywords):
    """Draws scaled red underlines to match image resolution exactly."""
    draw = ImageDraw.Draw(base_img)
    
    # Calculate scaling factor
    pdf_width = float(page_obj.width)
    img_width = float(base_img.width)
    scale = img_width / pdf_width
    
    words = page_obj.extract_words()
    for word in words:
        if any(k in word['text'].lower() for k in search_keywords):
            # Scale the PDF coordinates to match the image pixel space
            x0 = float(word['x0']) * scale
            x1 = float(word['x1']) * scale
            y_base = float(word['bottom']) * scale + 2 # Minor offset below baseline
            
            # Draw a single clean red line
            draw.line([x0, y_base, x1, y_base], fill="#ef4444", width=3)
    return base_img

def render_gauge(issue_title):
    difficulty = {"Restraint of Trade": 40, "Punitive Financial Penalty": 85, "Unconscionable Terms": 90}
    val = difficulty.get(issue_title, 50)
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = val,
        title = {'text': f"Ease: {issue_title}", 'font': {'size': 14, 'color': 'white'}},
        gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#ef4444"}}))
    fig.update_layout(height=200, paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, margin=dict(t=40, b=10))
    return fig

# ==========================================
# 3. INTERFACE & SESSION SYNC
# ==========================================
def main():
    inject_styles()
    if 'audit_hits' not in st.session_state: st.session_state.audit_hits = []
    if 'idx' not in st.session_state: st.session_state.idx = 0

    file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")

    if file:
        with pdfplumber.open(file) as pdf:
            pages = pdf.pages
            # Generate raw images at a fixed resolution for consistent scaling
            raw_imgs = [p.to_image(resolution=150).original for p in pages]

        c_left, c_right = st.columns([1.2, 1], gap="large")

        with c_right:
            if st.button("🚀 RUN SYNCED AUDIT", use_container_width=True):
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
                            # Sync: Pass current keywords and clean image copy
                            marked_img = draw_precise_underline(p, raw_imgs[i].copy(), keys)
                            hits.append({"title": title, "img": marked_img, "pg": i+1})
                
                st.session_state.audit_hits = hits
                st.session_state.idx = 0
                st.rerun()

            if st.session_state.audit_hits:
                curr = st.session_state.audit_hits[st.session_state.idx]
                
                # Update Gauge and Insights to match current highlighted issue
                st.plotly_chart(render_gauge(curr['title']), use_container_width=True)
                
                st.markdown(f"""
                    <div class="clause-box box-red">
                        <b>CLAUSE IMPACT</b><br>Detected {curr['title']} on Page {curr['pg']}.
                    </div>
                    <div class="clause-box box-green">
                        <b>LEGAL RAG INSIGHT</b><br><i>{get_legal_precedent(curr['title'])}</i>
                    </div>
                """, unsafe_allow_html=True)

                # Navigation
                n1, n2, n3 = st.columns([1,1,1])
                if n1.button("PREV") and st.session_state.idx > 0:
                    st.session_state.idx -= 1
                    st.rerun()
                n2.write(f"**{st.session_state.idx + 1} / {len(st.session_state.audit_hits)}**")
                if n3.button("NEXT") and st.session_state.idx < len(st.session_state.audit_hits)-1:
                    st.session_state.idx += 1
                    st.rerun()

        with c_left:
            if st.session_state.audit_hits:
                # Synchronized display of the current hit
                st.image(st.session_state.audit_hits[st.session_state.idx]['img'], use_container_width=True)
            else:
                st.image(raw_imgs[0], use_container_width=True)

if __name__ == "__main__":
    main()