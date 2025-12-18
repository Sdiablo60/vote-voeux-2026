import streamlit as st
import pandas as pd
import os
import glob
import random
import base64

# --- CONFIGURATION ---
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

# --- LOGIQUE ---
params = st.query_params
est_admin = params.get("admin") == "true"

if est_admin:
    st.title("🛠️ Console Régie")
    ul = st.file_uploader("Logo Central", type=['png','jpg','jpeg'])
    if ul: 
        with open(LOGO_FILE, "wb") as f: f.write(ul.getbuffer())
        st.success("Logo mis à jour")
    
    uf = st.file_uploader("Ajouter Photos", type=['png','jpg','jpeg'], accept_multiple_files=True)
    if uf:
        for f in uf:
            with open(os.path.join(GALLERY_DIR, f.name), "wb") as file: file.write(f.getbuffer())
        st.rerun()
    
    if st.button("Vider la galerie"):
        for f in glob.glob(os.path.join(GALLERY_DIR, "*")): os.remove(f)
        st.rerun()

else:
    # --- MODE LIVE ---
    logo_data = get_b64(LOGO_FILE)
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
    # CSS Sécurisé
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
                color: white; font-family: sans-serif; font-size: 55px; font-weight: bold;
                text-shadow: 0 0 20px rgba(255,255,255,0.6); z-index: 10001;
                animation: pulse-text 4s ease-in-out infinite;
            }
            @keyframes pulse-text {
                0% { transform: scale(1); opacity: 0.8; }
                50% { transform: scale(1.03); opacity: 1; }
                100% { transform: scale(1); opacity: 0.8; }
            }

            /* Positionnement du centre de l'orbite à 60% du haut */
            .center-point {
                position: absolute; top: 60%; left: 50%;
                transform: translate(-50%, -50%);
                width: 1px; height: 1px; z-index: 10000;
            }

            .center-logo {
                position: absolute; top: 0; left: 0;
                transform: translate(-50%, -50%);
                width: 250px; height: 250px; object-fit: contain;
            }

            .orbit-photo {
                position: absolute; top: 0; left: 0;
                width: 150px; height: 150px; margin-top: -75px; margin-left: -75px;
                border-radius: 50%; border: 3px solid white; object-fit: cover;
                box-shadow: 0 0 20px rgba(255,255,255,0.4);
                animation: orbit-move 25s linear infinite;
            }

            @keyframes orbit-move {
                from { transform: rotate(0deg) translateX(380px) rotate(0deg); }
                to { transform: rotate(360deg) translateX(380px) rotate(-360deg); }
            }
        </style>
    """, unsafe_allow_html=True)

    # Construction HTML
    html_content = '<div class="main-container">'
    
    # Étoiles (60 étoiles)
    for _ in range(60):
        x, y = random.randint(0, 100), random.randint(0, 100)
        s = random.randint(1, 3)
        html_content += f'<div class="star" style="left:{x}vw; top:{y}vh; width:{s}px; height:{s}px;"></div>'

    html_content += '<div class="welcome-title">✨ BIENVENUE AUX VOEUX 2026 ✨</div>'
    
    # Point central (Logo + Photos)
    html_content += '<div class="center-point">'
    if logo_data:
        html_content += f'<img src="data:image/png;base64,{logo_data}" class="center-logo">'
    
    if imgs:
        shuffled = imgs[-12:] # 12 dernières photos
        for i, path in enumerate(shuffled):
            img_b64 = get_b64(path)
            delay = -(i * (25 / len(shuffled)))
            html_content += f'<img src="data:image/png;base64,{img_b64}" class="orbit-photo" style="animation-delay:{delay}s;">'
    
    html_content += '</div></div>' # Fermeture center-point et main-container
    
    st.markdown(html_content, unsafe_allow_html=True)
