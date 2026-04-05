import streamlit as st
import pdfplumber
from PIL import Image, ImageDraw, ImageOps
import io
from app import LegalAI

# 1. HIGH-END UI CONFIGURATION
st.set_page_config(layout="wide", page_title="Legal Guard AI | Professional Audit", page_icon="⚖️")

# 2. PROFESSIONAL CSS INJECTION (The "Non-Streamlit" Look)
st.markdown("""
    <style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #05070a; }
    
    /* Header Styling */
    .main-header {
        background: linear-gradient(90deg, #1a1c23 0%, #05070a 100%);
        padding: 2rem; border-bottom: 1px solid #2d303d; margin-bottom: 2rem; border-radius: 0 0 20px 20px;
    }
    
    /* Custom Card Styling */
    .legal-card {
        background: #11141b; border: 1px solid #2d303d; border-radius: 12px;
        padding: 20px; margin-bottom: 15px; transition: all 0.3s ease;
    }
    .legal-card:hover { border-color: #4a9eff; box-shadow: 0 4px 20px rgba(0,0,0,0.4); }
    
    /* Severity Indicators */
    .status-badge {
        padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
    }
    .status-critical { background: rgba(255, 75, 75, 0.1); color: #ff4b4b; border: 1px solid #ff4b4b; }
    .status-warning { background: rgba(255, 165, 0, 0.1); color: #ffa500; border: 1px solid #ffa500; }
    
    /* Hide Streamlit Native Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    
    <div class="main-header">
        <h1 style='color: white; margin: 0;'>⚖️ Legal Guard <span style='color: #4a9eff; font-weight: 300;'>AI</span></h1>
        <p style='color: #8b8e98; margin-top: 5px;'>Enterprise-Grade Adversarial Clause Detection for Indian Labor Law</p>
    </div>
    """, unsafe_allow_html=True)

# 3. CORE LOGIC & STATE
if 'selected_idx' not in st.session_state: st.session_state.selected_idx = None
if 'results' not in st.session_state: st.session_state.results = []

@st.cache_resource
def get_ai():
    try: return LegalAI()
    except: return None

ai = get_ai()

# 4. SIDEBAR (UTILITIES)
with st.sidebar:
    st.markdown("### 🛠️ Audit Controls")
    scan_limit = st.slider("Analysis Depth", 1, 15, 5)
    st.markdown("---")
    st.markdown("🚀 **Project Status**: Final Build (v2.0)")
    st.markdown(f"👤 **Lead Dev**: Harleen Singh")
    st.markdown("🎓 **Affiliation**: GNDU Jalandhar")

# 5. UPLOAD & PROCESSING
file = st.file_uploader("", type="pdf", label_visibility="collapsed")

if file:
    if 'data' not in st.session_state:
        with st.spinner("Initializing Deep Scan..."):
            with pdfplumber.open(file) as pdf:
                imgs, pgs, txt = [], [], ""
                for p in pdf.pages:
                    txt += p.extract_text() or ""
                    pgs.append(p)
                    imgs.append(p.to_image(resolution=150).original.convert("RGBA"))
                st.session_state.data = {"imgs": imgs, "pgs": pgs, "txt": txt}

    doc = st.session_state.data
    left, right = st.columns([1.3, 1], gap="large")

    with right:
        st.markdown("### 📊 AI Analysis Report")
        if st.button("🔍 Execute Full Document Audit", use_container_width=True):
            blocks = [b.strip() for b in doc["txt"].split('\n\n') if len(b.strip()) > 50]
            st.session_state.results = []
            for i, b in enumerate(blocks[:scan_limit]):
                verdict = ai.analyze_clause(b)
                crit = any(k in verdict.lower() for k in ["illegal", "void", "unconstitutional", "violation"])
                st.session_state.results.append({"id": i, "text": b, "verdict": verdict, "crit": crit})

        # Render Results as Professional UI Cards
        for r in st.session_state.results:
            badge_class = "status-critical" if r['crit'] else "status-warning"
            badge_text = "Critical Risk" if r['crit'] else "Review Required"
            
            with st.container():
                st.markdown(f"""
                    <div class="legal-card">
                        <span class="status-badge {badge_class}">{badge_text}</span>
                        <p style="margin-top:15px; color:#e0e0e0; font-size:0.95rem;">{r['verdict']}</p>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"🎯 View in Document", key=f"view_{r['id']}", use_container_width=True):
                    st.session_state.selected_idx = r['id']

    with left:
        st.markdown("### 📄 Interactive Preview")
        # --- PRO HIGHLIGHTER (Alpha Blending) ---
        base_img = doc["imgs"][0].copy() # Page 1 for Demo
        overlay = Image.new("RGBA", base_img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Scaling
        w_ratio = base_img.size[0] / float(doc["pgs"][0].width)
        h_ratio = base_img.size[1] / float(doc["pgs"][0].height)

        if st.session_state.selected_idx is not None:
            # Smart Highlight Logic: Find core identifiers in the text
            current_words = doc["pgs"][0].extract_words()
            for w in current_words:
                # Highlight logic targets section headers and risk keywords
                if any(k in w['text'].lower() for k in ["section", "8", "12", "4", "penalty", "bond"]):
                    coords = [w['x0']*w_ratio, w['top']*h_ratio, w['x1']*w_ratio, w['bottom']*h_ratio]
                    # Draw a glowy, professional highlighter box
                    draw.rectangle(coords, fill=(255, 75, 75, 50), outline=(255, 75, 75, 180), width=2)

        final_view = Image.alpha_composite(base_img, overlay)
        st.image(final_view, use_container_width=True)

else:
    # Minimalist Empty State
    st.markdown("""
        <div style="text-align:center; padding: 100px; border: 2px dashed #2d303d; border-radius: 20px;">
            <h2 style="color:#4a9eff;">Ready for Audit</h2>
            <p style="color:#8b8e98;">Upload a legal contract (PDF) to begin high-speed adversarial clause detection.</p>
        </div>
    """, unsafe_allow_html=True)