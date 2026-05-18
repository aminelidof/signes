import streamlit as st
import cv2
from ultralytics import YOLO
import numpy as np
import time
from gtts import gTTS
import base64
import io
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURATION PRESTIGE (App6) ---
st.set_page_config(page_title="ArabiSign AI Ultimate Pro", layout="wide", initial_sidebar_state="expanded")

# --- DICTIONNAIRE DE CONVERSION ---
AR_MAP = {
    "ALIF": "أ", "BAA": "ب", "TA": "ت", "THA": "ث", "JEEM": "ج", "HAA": "ح", "KHAA": "خ",
    "DELL": "د", "DHELL": "ذ", "RAA": "ر", "ZAY": "ز", "SEEN": "س", "SHEEN": "ش", "SAD": "ص",
    "DAD": "ض", "TAA": "ط", "DHAA": "ظ", "AYN": "ع", "GHAYN": "غ", "FAA": "ف", "QAAF": "ق",
    "KAAF": "ك", "LAAM": "ل", "MEEM": "م", "NOON": "ن", "HA": "هـ", "WAW": "و", "YA": "ي"
}

# --- DESIGN "MERVEILLE" FUSIONNÉ (App5 + App6) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: white; }
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 20px;
    }
    .big-letter-ar { font-size: 100px; font-weight: 800; color: #38bdf8; text-align: center; margin: 0; text-shadow: 0 0 20px rgba(56, 189, 248, 0.5); }
    .transcription-area {
        background: rgba(0, 0, 0, 0.4);
        border-radius: 15px;
        padding: 20px;
        font-size: 40px;
        color: #10b981;
        direction: rtl;
        text-align: right;
        min-height: 120px;
        border: 1px dashed #10b981;
    }
    /* Style Bouton PDF App5 */
    .pdf-btn {
        width: 100%;
        background-color: #38bdf8;
        border: none;
        color: white;
        padding: 12px;
        border-radius: 8px;
        cursor: pointer;
        font-weight: bold;
        transition: 0.3s;
    }
    .pdf-btn:hover { background-color: #0ea5e9; shadow: 0 4px 15px rgba(56, 189, 248, 0.4); }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIQUE EXPORT PDF SÉCURISÉE (Optimisée de App5) ---
def create_pdf_download_link(history_en):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Rapport ArabiSign AI - Traduction", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Date de session: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
        pdf.ln(10)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Sequence de signes detectes:", ln=True)
        pdf.set_font("Arial", size=12)
        
        text_content = " -> ".join(history_en)
        pdf.multi_cell(0, 10, txt=text_content)
        
        # Encodage en base64 pour injection HTML (Méthode App5)
        pdf_output = pdf.output(dest='S').encode('latin-1', errors='replace')
        b64_pdf = base64.b64encode(pdf_output).decode()
        
        return f'''
            <a href="data:application/pdf;base64,{b64_pdf}" download="rapport_arabisign.pdf" style="text-decoration:none;">
                <button class="pdf-btn">📥 TÉLÉCHARGER LE RAPPORT (PDF)</button>
            </a>
        '''
    except Exception as e:
        return f"<p style='color:red;'>Erreur PDF: {str(e)}</p>"

def speak_async(text):
    try:
        tts = gTTS(text=text, lang='ar')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        st.markdown(f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
    except: pass

# --- INITIALISATION ---
@st.cache_resource
def load_yolo_model():
    return YOLO('best.pt')

model = load_yolo_model()

if "history_en" not in st.session_state: st.session_state.history_en = []
if "history_ar" not in st.session_state: st.session_state.history_ar = []
if "last_sign" not in st.session_state: st.session_state.last_sign = None

# --- UI SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3843/3843032.png", width=80)
    st.title("Control Center")
    cam_id = st.selectbox("Source Vidéo", [0, 1], format_func=lambda x: "Caméra Interne" if x==0 else "Caméra USB")
    conf_level = st.slider("Seuil de Confiance", 0.1, 1.0, 0.45)
    
    if st.button("🗑️ Réinitialiser la Session"):
        st.session_state.history_en = []
        st.session_state.history_ar = []
        st.session_state.last_sign = None
        st.rerun()

    st.write("---")
    # Placeholder pour le bouton PDF dynamique (évite le lag de la page entière)
    pdf_placeholder = st.empty()

# --- UI PRINCIPALE ---
st.markdown("<h1 style='text-align: center; color: white;'>✨ ARABISIGN <span style='color: #38bdf8;'>ULTIMATE PRO</span></h1>", unsafe_allow_html=True)

col_vid, col_data = st.columns([1.6, 1])

with col_vid:
    video_placeholder = st.empty()

with col_data:
    # Signe Actuel
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<p style="color:#38bdf8; font-weight:bold; margin-bottom:5px;">🎯 DÉTECTION EN DIRECT</p>', unsafe_allow_html=True)
    res_ar_display = st.empty()
    res_en_display = st.empty()
    st.markdown('</div>', unsafe_allow_html=True)

    # Transcription
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<p style="color:#10b981; font-weight:bold; margin-bottom:5px;">📜 TRANSCRIPTION CONTINUE (AR)</p>', unsafe_allow_html=True)
    trans_ar_display = st.empty()
    st.markdown('</div>', unsafe_allow_html=True)

# --- BOUCLE DE TRAITEMENT TEMPS RÉEL ---
cap = cv2.VideoCapture(cam_id)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

while True:
    ret, frame = cap.read()
    if not ret: break

    frame = cv2.flip(frame, 1)
    results = model(frame, conf=conf_level, verbose=False)
    
    # Affichage vidéo
    video_placeholder.image(results[0].plot(), channels="BGR", use_container_width=True)

    if len(results[0].boxes) > 0:
        label_en = model.names[int(results[0].boxes[0].cls[0])]
        label_ar = AR_MAP.get(label_en, "؟")
        
        # Mise à jour visuelle des volets de droite
        res_ar_display.markdown(f'<p class="big-letter-ar">{label_ar}</p>', unsafe_allow_html=True)
        res_en_display.markdown(f'<p style="text-align:center; color:white; font-size:1.2rem;">{label_en}</p>', unsafe_allow_html=True)

        # Nouvelle détection
        if label_en != st.session_state.last_sign:
            st.session_state.history_en.append(label_en)
            st.session_state.history_ar.append(label_ar)
            
            # Limiter pour la mémoire
            if len(st.session_state.history_en) > 30:
                st.session_state.history_en.pop(0)
                st.session_state.history_ar.pop(0)
            
            # Mise à jour instantanée du bouton PDF dans la sidebar
            pdf_html = create_pdf_download_link(st.session_state.history_en)
            pdf_placeholder.markdown(pdf_html, unsafe_allow_html=True)
            
            # Audio
            speak_async(label_en)
            st.session_state.last_sign = label_en
    else:
        res_ar_display.markdown('<p style="text-align:center; color:gray; font-size:2rem; padding:20px;">...</p>', unsafe_allow_html=True)
        res_en_display.empty()

    # Mise à jour de la transcription (RTL)
    full_ar_text = " ".join(st.session_state.history_ar)
    trans_ar_display.markdown(f'<div class="transcription-area">{full_ar_text if full_ar_text else "..."}</div>', unsafe_allow_html=True)

    time.sleep(0.01)
