import streamlit as st
import pandas as pd
import os
import glob
import random
import base64
from io import BytesIO

# --- CONFIGURATION DE BASE ---
st.set_page_config(page_title="Social Wall 2026", layout="wide", initial_sidebar_state="collapsed")

# Dossiers
GALLERY_DIR = "galerie_images"
LOGO_FILE = "logo_entreprise.png"
if not os.path.exists(GALLERY_DIR): os.makedirs(GALLERY_DIR)

# --- FONCTION SECURISEE ---
def get_b64(path):
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except: return ""
    return ""

# --- LOGIQUE ADMIN OU LIVE ---
params = st.query_params
est_admin = params.get("admin") == "true"

if est_admin:
    st.title("🛠️ Console Régie")
    # Simplification extrême de l'admin pour tester la stabilité
    ul = st.file_uploader("Ajouter Logo (PNG/JPG)", type=['png','jpg','jpeg'])
    if ul: 
        with open(LOGO_FILE, "wb") as f: f.write(ul.getbuffer())
        st.success("Logo mis à jour")
    
    uf = st.file_uploader("Ajouter Photos", type=['png','jpg','jpeg'], accept_multiple_files=True)
    if uf:
        for f in uf:
            with open(os.path.join(GALLERY_DIR, f.name), "wb") as file: file.write(f.getbuffer())
        st.rerun()

else:
    # --- MODE LIVE TOTALEMENT SIMPLIFIÉ ---
    logo_data = get_b64(LOGO_FILE)
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
    # CSS Injecté sans f-string pour éviter l'erreur de "double accolade"
    st.markdown("""
        <style>
            /* Cache l'interface Streamlit */
            [data-testid="stHeader"], footer, header {display:none !important;}
            .stApp {background-color: #050505 !important;}
            
            .main-container {
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background: #050505; z-index: 9999; overflow: hidden;
                display: flex; justify-content: center; align-items: center;
            }

            .welcome-title {
                position: absolute; top: 10%; width: 100%; text-align: center;
                color: white; font-family: sans-serif; font-size: 50px; font-weight: bold;
                text-shadow: 0 0 20px rgba(255,255,255,0.5); z-index: 10001;
            }

            .center-logo {
                width: 250px; height: 250px; object-fit: contain; z-index: 10000;
            }

            .orbit-photo {
                position: absolute; width: 150px; height: 150px;
                border-radius: 50%; border: 3px solid white; object-fit: cover;
                animation: orbit-move 20s linear infinite; z-index: 9998;
            }

            @keyframes orbit-move {
                from { transform: rotate(0deg) translateX(350px) rotate(0deg); }
                to { transform: rotate(360deg) translateX(350px) rotate(-360deg); }
            }
        </style>
    """, unsafe_allow_html=True)

    # Construction du HTML manuel (plus robuste que les f-strings complexes)
    html_content = '<div class="main-container">'
    html_content += '<div class="welcome-title">✨ BIENVENUE AUX VOEUX 2026 ✨</div>'
    
    if logo_data:
        html_content += f'<img src="data:image/png;base64,{logo_data}" class="center-logo">'
    
    if imgs:
        for i, path in enumerate(imgs[-10:]):
            img_b64 = get_b64(path)
            delay = -(i * 2)
            html_content += f'<img src="data:image/png;base64,{img_b64}" class="orbit-photo" style="animation-delay:{delay}s;">'
    
    html_content += '</div>'
    
    st.markdown(html_content, unsafe_allow_html=True)

    # Rafraîchissement lent pour éviter les plantages (toutes les 20 sec)
    # On n'utilise pas st.rerun ici pour éviter l'erreur de boucle
