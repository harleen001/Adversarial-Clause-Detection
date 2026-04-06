import streamlit as st
import pdfplumber
from PIL import Image, ImageDraw
import plotly.graph_objects as go

# ==========================================
# 1. PAGE CONFIG & STYLING
# ==========================================
st.set_page_config(layout="wide", page_title="Adversarial Clause Detection", page_icon="⚖️")

def inject_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
        .main { background-color: #0b0e14; font-family: 'Inter', sans-serif; color: #e2e8f0; }
        .stApp { background-color: #0b0e14; }
        
        .comparison-container { display: flex; flex-wrap: wrap; gap: 15px; margin-top: 15px; }
        .clause-box {
            flex: 1; min-width: 280px; padding: 15px; border-radius: 10px; 
            font-size: 0.85rem; border: 1px solid rgba(255,255,255,0.1);
        }
        .box-red { background: rgba(239, 68, 68, 0.05); border-left: 4px solid #ef4444; }
        .box-green { background: rgba(16, 185, 129, 0.05); border-left: 4px solid #10b981; }
        
        @media (max-width: 768px) {
            .brand-header { flex-direction: column; text-align: center; gap: 10px; }
            .comparison-container { flex-direction: column; }
        }

        .brand-header {
            background: rgba(26, 28, 35, 0.9); backdrop-filter: blur(12px);
            padding: 1rem 2rem; border-bottom: 1px solid #2d303d;
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 20px;
        }
        </style>
        
        <div class="brand-header">
            <div>
                <h3 style='margin:0; letter-spacing:1px; font-weight:300;'>ADVERSIAL <span style='color:#ef4444; font-weight:600;'>CLAUSE</span> DETECTION</h3>
                <p style='margin:0; color:#8b8e98; font-size:10px;'>V1.0 | RAG-AUGMENTED NEGOTIATION SUITE</p>
            </div>
            <div style='text-align:right;'>
                <p style='margin:0; font-size:12px; font-weight:600;'>Harleen Singh</p>
                <p style='margin:0; color:#8b8e98; font-size:9px;'>GNDU JALANDHAR | FINAL YEAR PROJECT</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 2. LOGIC ENGINES (RAG & DRAWING)
# ==========================================
def get_legal_precedent(issue_title):
    db = {
        "Restraint of Trade": "Niranjan Shankar Golikari v. Century Spinning & Mfg. Co. (AIR 1967 SC 1098). The Supreme Court ruled post-employment restrictions are void under Section 27.",
        "Punitive Financial Penalty": "Fateh Chand v. Balkishan Das (1964). Section 74 limits damages to 'reasonable compensation' for actual loss.",
        "Unconscionable Terms": "Central Inland Water Transport Corp v. Brojo Nath Ganguly (1986). Terms that are grossly unfair to an employee are void."
    }
    return db.get(issue_title, "Consult Section 27 of the Indian Contract Act.")

def draw_highlights(page_obj, base_img, search_keywords):
    """Draws professional, high-precision red underlines and faints glows."""
    draw = ImageDraw.Draw(base_img)
    # Extracting words with spatial coordinates [cite: 10]
    words = page_obj.extract_words()
    
    for word in words:
        if any(k in word['text'].lower() for k in search_keywords):
            # 1. THE UNDERLINE: Positioned 2 pixels below the text baseline
            # Coordinates: [x0, y_position, x1, y_position]
            line_y = word['bottom'] + 2 
            draw.line([word['x0'], line_y, word['x1'], line_y], fill="#ef4444", width=3)
            
            # 2. THE GLOW: A semi-transparent box that makes the word 'pop'
            # (R, G, B, Alpha) -> Alpha 40 is very faint
            glow_shape = [word['x0'], word['top'], word['x1'], word['bottom']]
            draw.rectangle(glow_shape, fill=(239, 68, 68, 40)) 
            
    return base_img

def render_negotiation_gauge(issue_title):
    difficulty = {"Restraint of Trade": 40, "Punitive Financial Penalty": 85, "Unconscionable Terms": 90}
    val = difficulty.get(issue_title, 50)
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = val,
        title = {'text': "Negotiation Ease (%)", 'font': {'size': 12, 'color': 'white'}},
        gauge = {'axis': {'range': [0, 100], 'tickcolor': "white"},
                 'bar': {'color': "#10b981" if val > 50 else "#ef4444"}}))
    fig.update_layout(height=180, paper_bgcolor='rgba(0,0,0,0)', font={'color': "white", 'size': 10}, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def get_protest_email(issue_title):
    return f"""Subject: Regarding proposed '{issue_title}' clause\n\nDear HR Team,\n\nI am reviewing the proposed agreement. I have a concern regarding the '{issue_title}' provision, as it seems to conflict with Section 27/74 of the Indian Contract Act. \n\nSpecifically, legal precedents like Niranjan Shankar Golikari v. Century Spinning suggest such restrictions are often unenforceable. Could we modify this to align with standard industry practices?\n\nBest regards,\n[Your Name]"""

# ==========================================
# 3. MAIN APPLICATION
# ==========================================
def main():
    inject_styles()
    
    # Session State Initialization
    if 'audit_data' not in st.session_state: st.session_state.audit_data = []
    if 'issue_cursor' not in st.session_state: st.session_state.issue_cursor = 0
    if 'pdf_cache' not in st.session_state: st.session_state.pdf_cache = None

    uploaded_file = st.file_uploader("Upload PDF Contract", type="pdf", label_visibility="collapsed")

    if uploaded_file:
        if st.session_state.pdf_cache is None:
            with pdfplumber.open(uploaded_file) as pdf:
                # Cache raw pages and base images for performance
                st.session_state.pdf_cache = {
                    "pages": pdf.pages,
                    "imgs": [p.to_image(resolution=150).original for p in pdf.pages]
                }

        doc = st.session_state.pdf_cache
        col_viz, col_ctrl = st.columns([1.2, 1], gap="medium")

        with col_ctrl:
            if st.button("🚀 EXECUTE RAG-POWERED AUDIT", use_container_width=True):
                findings = []
                keywords_map = {
                    "Restraint of Trade": ["prohibited", "non-compete", "restriction", "exclusivity"],
                    "Punitive Financial Penalty": ["penalty", "bond", "repay", "liquidated", "cost"],
                    "Unconscionable Terms": ["original", "24/7", "indemnity", "unilateral"]
                }
                
                for i, p in enumerate(doc["pages"]):
                    txt = p.extract_text() or ""
                    for title, keys in keywords_map.items():
                        if any(k in txt.lower() for k in keys):
                            # Create a fresh copy of the page image and draw highlights
                            base_img_copy = doc["imgs"][i].copy()
                            marked_img = draw_highlights(p, base_img_copy, keys)
                            
                            findings.append({
                                "page": i, 
                                "title": title, 
                                "raw": f"Detected potential {title} issue on Page {i+1}.",
                                "viz": marked_img
                            })
                
                st.session_state.audit_data = findings
                st.session_state.issue_cursor = 0
                st.rerun()

            if st.session_state.audit_data:
                idx = st.session_state.issue_cursor
                issue = st.session_state.audit_data[idx]
                
                # Gauge Chart
                st.plotly_chart(render_negotiation_gauge(issue['title']), use_container_width=True)
                
                # Dual-Pane Comparison
                st.markdown(f"""
                    <div style="background:#1a1c23; padding:15px; border-radius:10px; border:1px solid #2d303d;">
                        <span style="color:#ef4444; font-weight:700; font-size:0.75rem;">AUDIT HIT #{idx+1}</span>
                        <div class="comparison-container">
                            <div class="clause-box box-red">
                                <span style="color:#ef4444; font-size:0.6rem; font-weight:700;">CLAUSE IMPACT</span><br>
                                {issue['raw']}
                            </div>
                            <div class="clause-box box-green">
                                <span style="color:#10b981; font-size:0.6rem; font-weight:700;">LEGAL RAG INSIGHT</span><br>
                                <i>{get_legal_precedent(issue['title'])}</i>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                # Email Generator
                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("📧 DRAFT PROTEST EMAIL"):
                    email_body = get_protest_email(issue['title'])
                    st.text_area("Draft Rebuttal", email_body, height=180)
                    st.download_button("Download Email (.txt)", email_body, file_name=f"rebuttal_{idx}.txt", key=f"dl_{idx}")

                # Navigation Controls
                st.markdown("<br>", unsafe_allow_html=True)
                b1, b2, b3 = st.columns([1,1,1])
                if b1.button("PREV", disabled=(idx==0), use_container_width=True): 
                    st.session_state.issue_cursor -= 1
                    st.rerun()
                b2.markdown(f"<p style='text-align:center; margin-top:8px;'>{idx+1}/{len(st.session_state.audit_data)}</p>", unsafe_allow_html=True)
                if b3.button("NEXT", disabled=(idx==len(st.session_state.audit_data)-1), use_container_width=True): 
                    st.session_state.issue_cursor += 1
                    st.rerun()
            else:
                st.info("System Ready. Please upload a PDF contract to begin the audit.")

        with col_viz:
            if st.session_state.audit_data:
                active_issue = st.session_state.audit_data[st.session_state.issue_cursor]
                # Render the image with PIL-painted highlights
                st.image(active_issue['viz'], use_container_width=True, caption=f"Page {active_issue['page']+1} - Visual Audit")
            elif st.session_state.pdf_cache:
                # If no audit run yet, show the first page
                st.image(st.session_state.pdf_cache["imgs"][0], use_container_width=True, caption="Document Preview")

if __name__ == "__main__":
    main()