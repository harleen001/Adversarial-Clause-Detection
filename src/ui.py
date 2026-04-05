import streamlit as st
import pdfplumber
from PIL import Image, ImageDraw
import plotly.graph_objects as go

# ==========================================
# 1. UI & BRANDING CONFIGURATION
# ==========================================
st.set_page_config(layout="wide", page_title="Legal Guard Elite", page_icon="⚖️")

def inject_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
        .main { background-color: #05070a; font-family: 'Inter', sans-serif; color: white; }
        .stApp { background-color: #05070a; }
        header, footer, #MainMenu { visibility: hidden; }
        
        .brand-header {
            background: linear-gradient(90deg, #1a1c23 0%, #05070a 100%);
            padding: 1.2rem 2rem; border-bottom: 1px solid #2d303d;
            border-radius: 0 0 15px 15px; margin-bottom: 2rem;
            display: flex; justify-content: space-between; align-items: center;
        }

        .risk-card {
            background: #11141b; border: 1px solid #2d303d; border-radius: 12px;
            padding: 20px; margin-bottom: 15px; border-left: 5px solid #ff4b4b;
        }
        
        .status-tag {
            background: rgba(255, 75, 75, 0.1); color: #ff4b4b; border: 1px solid #ff4b4b;
            padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700;
        }

        .progress-track { height: 4px; width: 100%; background: #1a1c23; border-radius: 2px; margin: 10px 0; }
        .progress-fill { height: 100%; background: #ff4b4b; border-radius: 2px; transition: width 0.6s ease; }
        </style>
        
        <div class="brand-header">
            <div>
                <h3 style='margin:0; font-weight:300;'>LEGAL<span style='color:#ff4b4b; font-weight:600;'>GUARD</span> ELITE</h3>
                <p style='margin:0; color:#8b8e98; font-size:11px;'>V6.0 | PRO-RISK SCORING & REBUTTAL ENGINE</p>
            </div>
            <div style='text-align:right;'>
                <p style='margin:0; font-size:13px;'><b>Harleen Singh</b></p>
                <p style='margin:0; color:#8b8e98; font-size:10px;'>GNDU JALANDHAR - FINAL YEAR PROJECT</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 2. LOGIC ENGINES (Visualization & Letters)
# ==========================================
def render_risk_chart(findings):
    """Generates a Plotly Radar Chart based on contract categories."""
    scores = {"Financial": 100, "Privacy": 100, "Career": 100, "Fairness": 100}
    for f in findings:
        if "Financial" in f['desc']: scores["Financial"] -= 25
        if "Unconscionable" in f['desc']: scores["Privacy"] -= 20
        if "Restraint" in f['desc']: scores["Career"] -= 30
        if "24/7" in f['desc']: scores["Fairness"] -= 15

    fig = go.Figure(data=go.Scatterpolar(
        r=[max(0, scores["Financial"]), max(0, scores["Privacy"]), max(0, scores["Career"]), max(0, scores["Fairness"])],
        theta=['Financial Risk', 'Privacy', 'Career Freedom', 'Fairness'],
        fill='toself', marker=dict(color='#ff4b4b')
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], color="#8b8e98"), bgcolor="rgba(0,0,0,0)"),
        showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white", size=10), height=300, margin=dict(l=50, r=50, t=30, b=30)
    )
    return fig

def get_protest_email(issue_title):
    """Drafts a professional rebuttal email citing Indian Law."""
    return f"""Subject: Discussion regarding '{issue_title}' Clause\n\nDear HR Team,\n\nI am reviewing the proposed agreement and have a concern regarding the clause related to {issue_title}.\n\nAccording to Section 27 of the Indian Contract Act, 1872, terms that impose an absolute restraint on an individual's right to work are generally considered legally unenforceable. \n\nCould we discuss modifying this to better align with current legal standards and industry norms?\n\nRegards,\n[Your Name]"""

class VisualMarkingEngine:
    @staticmethod
    def apply_marks(base_img, page_obj, text_context):
        overlay = Image.new("RGBA", base_img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        w_scale, h_scale = base_img.size[0]/page_obj.width, base_img.size[1]/page_obj.height
        targets = ["prohibited", "strictly", "penalty", "bond", "original", "24/7", "lakhs", "surveillance"]
        words = page_obj.extract_words()
        for w in words:
            if any(t in w['text'].lower() for t in targets) and w['text'].lower() in text_context.lower():
                coords = [w['x0']*w_scale, w['top']*h_scale, w['x1']*w_scale, w['bottom']*h_scale]
                draw.rectangle(coords, fill=(255, 75, 75, 45)) 
                draw.line([coords[0], coords[3]+3, coords[2], coords[3]+3], fill=(255, 75, 75, 255), width=3)
        return Image.alpha_composite(base_img.convert("RGBA"), overlay)

# ==========================================
# 3. MAIN APPLICATION
# ==========================================
def main():
    inject_styles()

    if 'audit_data' not in st.session_state: st.session_state.audit_data = []
    if 'issue_cursor' not in st.session_state: st.session_state.issue_cursor = 0
    if 'pdf_cache' not in st.session_state: st.session_state.pdf_cache = None

    uploaded_file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")

    if uploaded_file:
        if st.session_state.pdf_cache is None:
            with pdfplumber.open(uploaded_file) as pdf:
                st.session_state.pdf_cache = {
                    "pages": pdf.pages,
                    "imgs": [p.to_image(resolution=150).original for p in pdf.pages]
                }

        doc = st.session_state.pdf_cache
        col_viz, col_ctrl = st.columns([1.4, 1], gap="large")

        with col_ctrl:
            # --- 1. DASHBOARD AREA ---
            if st.session_state.audit_data:
                chart = render_risk_chart(st.session_state.audit_data)
                st.markdown("### 🛡️ Contract Health Profile")
                st.plotly_chart(chart, use_container_width=True, config={'displayModeBar': False})
                st.divider()

            if st.button("🚀 EXECUTE FULL AUDIT", use_container_width=True):
                findings = []
                for i, p in enumerate(doc["pages"]):
                    txt = p.extract_text() or ""
                    # Detection with expanded Legal Context
                    if any(k in txt.lower() for k in ["prohibited", "non-compete", "restricted"]):
                        findings.append({"page": i, "text": txt, "sev": 85, "title": "Restraint of Trade",
                            "desc": "<b>Legal Context:</b> Section 27 of <i>Indian Contract Act</i> makes agreements in restraint of trade void."})
                    if any(k in txt.lower() for k in ["penalty", "bond", "lakhs"]):
                        findings.append({"page": i, "text": txt, "sev": 95, "title": "Punitive Financial Penalty",
                            "desc": "<b>Legal Context:</b> Section 74 allows only 'reasonable compensation', not extortionate penal damages."})
                    if any(k in txt.lower() for k in ["original", "24/7", "surveillance"]):
                        findings.append({"page": i, "text": txt, "sev": 90, "title": "Unconscionable Terms",
                            "desc": "<b>Legal Context:</b> Holding original degrees or 24/7 monitoring violates labor rights and dignity."})
                st.session_state.audit_data = findings
                st.session_state.issue_cursor = 0
                st.rerun()

            # --- 2. ERROR NAVIGATOR ---
            if st.session_state.audit_data:
                idx = st.session_state.issue_cursor
                issue = st.session_state.audit_data[idx]
                st.markdown(f"""
                    <div class="risk-card">
                        <span class="status-tag">{issue['title'].upper()}</span>
                        <p style="font-size:0.9rem; color:#d1d1d1; margin-top:10px;">{issue['desc']}</p>
                    </div>
                """, unsafe_allow_html=True)

                # Action: Email Rebuttal
                with st.expander("📧 Generate Protest Email"):
                    email_body = get_protest_email(issue['title'])
                    st.text_area("Draft Rebuttal", email_body, height=180)
                    st.download_button("Download Email (.txt)", email_body, file_name="rebuttal.txt")

                b1, b2, b3 = st.columns([1, 1, 1])
                if b1.button("⬅️ PREV", disabled=(idx == 0)): st.session_state.issue_cursor -= 1; st.rerun()
                b2.markdown(f"<p style='text-align:center; padding-top:8px;'>{idx+1}/{len(st.session_state.audit_data)}</p>", unsafe_allow_html=True)
                if b3.button("NEXT ➡️", disabled=(idx == len(st.session_state.audit_data)-1)): st.session_state.issue_cursor += 1; st.rerun()
            else:
                st.info("Upload PDF and click 'Execute' to begin.")

        with col_viz:
            if st.session_state.audit_data:
                active = st.session_state.audit_data[st.session_state.issue_cursor]
                st.markdown(f"### 📄 Page {active['page'] + 1}")
                display_img = VisualMarkingEngine.apply_marks(doc["imgs"][active['page']], doc["pages"][active['page']], active['text'])
                st.image(display_img, use_container_width=True)
            elif st.session_state.pdf_cache:
                st.image(doc["imgs"][0], use_container_width=True, caption="Page 1 Preview")

if __name__ == "__main__":
    main()