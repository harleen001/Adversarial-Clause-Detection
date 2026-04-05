import streamlit as st
import pdfplumber
from PIL import Image, ImageDraw
import plotly.graph_objects as go

# ==========================================
# 1. INDUSTRIAL UI CONFIGURATION
# ==========================================
st.set_page_config(layout="wide", page_title="Legal Guard Elite | Industry Pro", page_icon="⚖️")

def inject_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
        .main { background-color: #0b0e14; font-family: 'Inter', sans-serif; color: #e2e8f0; }
        .stApp { background-color: #0b0e14; }
        
        /* Modern Glassmorphism Cards */
        .comparison-container {
            display: flex; gap: 15px; margin-top: 15px;
        }
        .clause-box {
            flex: 1; padding: 15px; border-radius: 10px; font-size: 0.85rem; line-height: 1.4;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .box-red { background: rgba(239, 68, 68, 0.05); border-left: 4px solid #ef4444; }
        .box-green { background: rgba(16, 185, 129, 0.05); border-left: 4px solid #10b981; }
        
        .label { font-weight: 600; font-size: 0.7rem; text-transform: uppercase; margin-bottom: 8px; display: block; }
        .label-red { color: #ef4444; }
        .label-green { color: #10b981; }

        .brand-header {
            background: rgba(26, 28, 35, 0.8); backdrop-filter: blur(10px);
            padding: 1rem 2rem; border-bottom: 1px solid #2d303d;
            position: sticky; top: 0; z-index: 999; display: flex; justify-content: space-between;
        }
        </style>
        
        <div class="brand-header">
            <div>
                <h3 style='margin:0; letter-spacing:1px; font-weight:300;'>LEGAL<span style='color:#ef4444; font-weight:600;'>GUARD</span> PRO</h3>
                <p style='margin:0; color:#8b8e98; font-size:10px;'>ENTERPRISE ADVERSARIAL AUDIT ENGINE</p>
            </div>
            <div style='text-align:right;'>
                <p style='margin:0; font-size:12px; font-weight:600;'>Harleen Singh</p>
                <p style='margin:0; color:#8b8e98; font-size:9px;'>GNDU JALANDHAR | B.TECH FINAL YEAR</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 2. LEGAL COMPLIANCE ENGINE
# ==========================================
def get_compliant_version(issue_title):
    """Maps illegal clauses to industry-standard compliant versions."""
    suggestions = {
        "Restraint of Trade": "The Employee agrees not to join a direct competitor for a period of 6 months within the same city, provided the Company pays 50% of the last drawn salary during this period.",
        "Punitive Financial Penalty": "In the event of a breach, the Employee shall be liable only for actual, documented relocation or training expenses incurred by the company, capped at one month's basic salary.",
        "Unconscionable Terms": "The Company respects the Employee's right to privacy and work-life balance. Overtime is voluntary and original documents shall remain in the Employee's possession at all times."
    }
    return suggestions.get(issue_title, "Clause should be modified to be reasonable and mutual.")

# ==========================================
# 3. VISUALIZATION & CORE
# ==========================================
def render_risk_chart(findings):
    scores = {"Finance": 100, "Privacy": 100, "Career": 100, "Fairness": 100}
    for f in findings:
        if "Financial" in f['title']: scores["Finance"] -= 25
        if "Unconscionable" in f['title']: scores["Privacy"] -= 20
        if "Restraint" in f['title']: scores["Career"] -= 30
    
    fig = go.Figure(data=go.Scatterpolar(
        r=[max(0, s) for s in scores.values()],
        theta=list(scores.keys()), fill='toself', marker=dict(color='#ef4444')
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], color="#4b5563"), bgcolor="rgba(0,0,0,0)"),
        showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white", size=10), height=280, margin=dict(l=40, r=40, t=20, b=20)
    )
    return fig

# ==========================================
# 4. MAIN APP
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
        col_viz, col_ctrl = st.columns([1.3, 1], gap="large")

        with col_ctrl:
            if st.session_state.audit_data:
                st.plotly_chart(render_risk_chart(st.session_state.audit_data), use_container_width=True)
            
            if st.button("🔍 SCAN FOR INDUSTRIAL RISKS", use_container_width=True):
                findings = []
                for i, p in enumerate(doc["pages"]):
                    txt = p.extract_text() or ""
                    if any(k in txt.lower() for k in ["prohibited", "non-compete", "restricted"]):
                        findings.append({"page": i, "text": txt, "title": "Restraint of Trade", "raw": "Section 27 Violation: Absolute non-compete is void."})
                    if any(k in txt.lower() for k in ["penalty", "bond", "lakhs"]):
                        findings.append({"page": i, "text": txt, "title": "Punitive Financial Penalty", "raw": "Section 74 Violation: Penal damages are legally restricted."})
                    if any(k in txt.lower() for k in ["original", "24/7", "surveillance"]):
                        findings.append({"page": i, "text": txt, "title": "Unconscionable Terms", "raw": "Labor Rights Violation: Excessive monitoring or document seizure."})
                st.session_state.audit_data = findings
                st.session_state.issue_cursor = 0
                st.rerun()

            if st.session_state.audit_data:
                idx = st.session_state.issue_cursor
                issue = st.session_state.audit_data[idx]
                suggestion = get_compliant_version(issue['title'])

                # DUAL-PANE COMPARISON UI
                st.markdown(f"""
                    <div style="background:#1a1c23; padding:20px; border-radius:12px; border:1px solid #2d303d;">
                        <span style="color:#ef4444; font-weight:700; font-size:0.8rem;">ISSUE #{idx+1}: {issue['title']}</span>
                        <div class="comparison-container">
                            <div class="clause-box box-red">
                                <span class="label label-red">Adversarial Clause</span>
                                {issue['raw']}
                            </div>
                            <div class="clause-box box-green">
                                <span class="label label-green">Compliant Suggestion</span>
                                {suggestion}
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                # Action Controls
                st.markdown("<br>", unsafe_allow_html=True)
                b1, b2, b3 = st.columns([1,1,1])
                if b1.button("PREV", disabled=(idx==0)): st.session_state.issue_cursor -= 1; st.rerun()
                b2.markdown(f"<p style='text-align:center; margin-top:8px;'>{idx+1}/{len(st.session_state.audit_data)}</p>", unsafe_allow_html=True)
                if b3.button("NEXT", disabled=(idx==len(st.session_state.audit_data)-1)): st.session_state.issue_cursor += 1; st.rerun()
                
                with st.expander("📝 View Pro-Drafted Rebuttal"):
                    st.code(f"Dear HR,\nRegarding the {issue['title']} clause, I suggest adopting the following: \n\n'{suggestion}'\n\nThis aligns with Indian Contract Law.")
            else:
                st.info("Upload a document to generate a risk-vs-compliance report.")

        with col_viz:
            if st.session_state.audit_data:
                active = st.session_state.audit_data[st.session_state.issue_cursor]
                st.image(doc["imgs"][active['page']], use_container_width=True, caption=f"Audit View: Page {active['page']+1}")

if __name__ == "__main__":
    main()