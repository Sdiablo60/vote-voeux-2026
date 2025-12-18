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
    # --- MODE LIVE ---
    logo_data = get_b64(LOGO_FILE)
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
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

            .center-point {
                position: absolute; top: 60%; left: 50%;
                transform: translate(-50%, -50%);
                width: 250px; height: 250px;
                display: flex; justify-content: center; align-items: center;
            }

            .center-logo {
                width: 100%; height: 100%; object-fit: contain;
                z-index: 10000; filter: drop-shadow(0 0 20px rgba(255,255,255,0.3));
            }

            /* Conteneur de l'orbite pour éviter l'effet "trait" */
            .orbit-wrapper {
                position: absolute;
                width: 800px; height: 800px; /* Diamètre de l'orbite */
                animation: rotate-all 30s linear infinite;
                display: flex; justify-content: center; align-items: center;
            }

            @keyframes rotate-all {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }

            .photo-bubble {
                position: absolute;
                width: 160px; height: 160px;
                border-radius: 50%;
                border: 4px solid white;
                object-fit: cover;
                box-shadow: 0 0 25px rgba(255,255,255,0.5);
                /* On contre-pivote l'image pour qu'elle reste droite */
                animation: counter-rotate 30s linear infinite;
            }

            @keyframes counter-rotate {
                from { transform: rotate(0deg); }
                to { transform: rotate(-360deg); }
            }
        </style>
    """, unsafe_allow_html=True)

    html_content = '<div class="main-container">'
    
    # Étoiles
    for _ in range(70):
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
        display_imgs = imgs[-10:] # Max 10 photos pour la clarté
        for i, path in enumerate(display_imgs):
            img_b64 = get_b64(path)
            angle = (360 / len(display_imgs)) * i
            # On place chaque photo sur le bord du cercle de 800px (rayon 400px)
            html_content += f'''
                <div class="orbit-wrapper" style="transform: rotate({angle}deg);">
                    <img src="data:image/png;base64,{img_b64}" class="photo-bubble" style="top: 0;">
                </div>
            '''
    
    html_content += '</div></div>'
    
    st.markdown(html_content, unsafe_allow_html=True)
