import streamlit as st
import pandas as pd  # Correction ici : pandas au lieu de pd
import os
import glob
import random
import base64

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Social Wall 2026", layout="wide", initial_sidebar_state="collapsed")

GALLERY_DIR = "galerie_images"
LOGO_FILE = "logo_entreprise.png"
if not os.path.exists(GALLERY_DIR): os.makedirs(GALLERY_DIR)

def get_b64(path):
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except: return ""
    return ""

# --- 2. LOGIQUE ACCÈS ---
params = st.query_params
est_admin = params.get("admin") == "true"

if est_admin:
    st.title("🛠️ Console Régie")
    col1, col2 = st.columns(2)
    with col1:
        ul = st.file_uploader("Logo Central", type=['png','jpg','jpeg'])
        if ul: 
            with open(LOGO_FILE, "wb") as f: f.write(ul.getbuffer())
            st.success("Logo mis à jour")
    with col2:
        uf = st.file_uploader("Ajouter Photos", type=['png','jpg','jpeg'], accept_multiple_files=True)
        if uf:
            for f in uf:
                with open(os.path.join(GALLERY_DIR, f.name), "wb") as file: file.write(f.getbuffer())
            st.rerun()
    
    if st.button("🗑️ Vider la galerie"):
        for f in glob.glob(os.path.join(GALLERY_DIR, "*")): os.remove(f)
        st.rerun()

else:
    # --- 3. MODE LIVE ---
    logo_data = get_b64(LOGO_FILE)
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
    # CSS PUR
    st.markdown("""
        <style>
            [data-testid="stHeader"], footer, header {display:none !important;}
            .stApp {background-color: #050505 !important;}
            
            .main-container {
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background: #050505; z-index: 9999; overflow: hidden;
            }

            .star {
                position: absolute; background: white; border-radius: 50%;
                opacity: 0.5; animation: twinkle 3s infinite alternate;
            }
            @keyframes twinkle { from { opacity: 0.2; } to { opacity: 0.8; } }

            .welcome-title {
                position: absolute; top: 8%; width: 100%; text-align: center;
                color: white; font-family: sans-serif; font-size: 50px; font-weight: bold;
                text-shadow: 0 0 20px rgba(255,255,255,0.6); z-index: 10001;
                animation: pulse-text 4s ease-in-out infinite;
                padding: 0 20px;
            }
            @keyframes pulse-text {
                0% { transform: scale(1); opacity: 0.8; }
                50% { transform: scale(1.02); opacity: 1; }
                100% { transform: scale(1); opacity: 0.8; }
            }

            /* Centre abaissé à 65% pour libérer le haut */
            .center-point {
                position: absolute; top: 65%; left: 50%;
                transform: translate(-50%, -50%);
                width: 200px; height: 200px;
                z-index: 10000;
            }

            .center-logo {
                width: 200px; height: 200px; object-fit: contain;
                filter: drop-shadow(0 0 20px rgba(255,255,255,0.3));
            }

            .orbit-photo {
                position: absolute; top: 50%; left: 50%;
                width: 130px; height: 130px; margin-top: -65px; margin-left: -65px;
                border-radius: 50%; border: 3px solid white; object-fit: cover;
                box-shadow: 0 0 25px rgba(255,255,255,0.4);
                animation: orbit-animation 25s linear infinite;
            }

            /* Rayon resserré à 280px pour ne pas toucher le texte */
            @keyframes orbit-animation {
                from { transform: rotate(0deg) translateX(280px) rotate(0deg); }
                to { transform: rotate(360deg) translateX(280px) rotate(-360deg); }
            }
        </style>
    """, unsafe_allow_html=True)

    html_content = '<div class="main-container">'
    
    # Etoiles
    for _ in range(60):
        x, y = random.randint(0, 100), random.randint(0, 100)
        s = random.randint(1, 3)
        html_content += f'<div class="star" style="left:{x}vw; top:{y}vh; width:{s}px; height:{s}px;"></div>'

    html_content += '<div class="welcome-title">✨ BIENVENUE AUX VOEUX 2026 ✨</div>'
    
    # Centre
    html_content += '<div class="center-point">'
    if logo_data:
        html_content += f'<img src="data:image/png;base64,{logo_data}" class="center-logo">'
    
    # Photos
    if imgs:
        shuffled = imgs[-10:]
        for i, path in enumerate(shuffled):
            img_b64 = get_b64(path)
            delay = -(i * (25 / len(shuffled)))
            html_content += f'<img src="data:image/png;base64,{img_b64}" class="orbit-photo" style="animation-delay:{delay}s;">'
    
    html_content += '</div></div>'
    
    st.markdown(html_content, unsafe_allow_html=True)
