import streamlit as st
import pandas as pd
import os
import glob
import random
import base64

# --- 1. CONFIGURATION & FICHIERS ---
st.set_page_config(page_title="Social Wall 2026", layout="wide", initial_sidebar_state="collapsed")

GALLERY_DIR = "galerie_images"
LOGO_FILE = "logo_entreprise.png"
MSG_FILE = "live_config.csv"

for d in [GALLERY_DIR]:
    if not os.path.exists(d): os.makedirs(d)

def get_b64(path):
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except: return ""
    return ""

def get_config():
    if os.path.exists(MSG_FILE):
        return pd.read_csv(MSG_FILE).iloc[0].to_dict()
    return {"texte": "✨ BIENVENUE AUX VOEUX 2026 ✨", "couleur": "#FFFFFF", "taille": 48}

# --- 2. LOGIQUE ACCÈS ---
params = st.query_params
est_admin = params.get("admin") == "true"

# --- 3. INTERFACE ADMIN (COMPLÈTE) ---
if est_admin:
    st.title("🛠️ Console Régie Master")
    
    config = get_config()
    
    t1, t2, t3 = st.tabs(["💬 Message Live", "🖼️ Logo & Photos", "🗑️ Nettoyage"])
    
    with t1:
        st.subheader("Personnalisation du titre")
        new_texte = st.text_input("Texte du message", config["texte"])
        new_couleur = st.color_picker("Couleur du texte", config["couleur"])
        new_taille = st.slider("Taille du texte", 20, 100, int(config["taille"]))
        
        if st.button("🚀 Publier les modifications"):
            pd.DataFrame([{"texte": new_texte, "couleur": new_couleur, "taille": new_taille}]).to_csv(MSG_FILE, index=False)
            st.success("Message mis à jour sur le Social Wall !")

    with t2:
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Logo Central")
            ul = st.file_uploader("Changer le logo", type=['png','jpg','jpeg'])
            if ul: 
                with open(LOGO_FILE, "wb") as f: f.write(ul.getbuffer())
                st.rerun()
            if os.path.exists(LOGO_FILE):
                st.image(LOGO_FILE, width=150, caption="Logo actuel")
        
        with col_b:
            st.subheader("Ajouter des photos")
            uf = st.file_uploader("Upload (plusieurs possibles)", type=['png','jpg','jpeg'], accept_multiple_files=True)
            if uf:
                for f in uf:
                    with open(os.path.join(GALLERY_DIR, f.name), "wb") as file: file.write(f.getbuffer())
                st.rerun()

    with t3:
        st.subheader("Gestion de la galerie")
        imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
        if imgs:
            cols = st.columns(5)
            for i, p in enumerate(imgs):
                with cols[i % 5]:
                    st.image(p, width=100)
                    if st.button(f"Supprimer", key=f"del_{i}"):
                        os.remove(p)
                        st.rerun()
            
            st.divider()
            if st.button("🔥 TOUT SUPPRIMER (Galerie)"):
                for f in imgs: os.remove(f)
                st.rerun()
        else:
            st.info("La galerie est vide.")

# --- 4. MODE LIVE (SOCIAL WALL) ---
else:
    config = get_config()
    logo_data = get_b64(LOGO_FILE)
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
    st.markdown(f"""
        <style>
            [data-testid="stHeader"], footer, header {{display:none !important;}}
            .stApp {{background-color: #050505 !important;}}
            
            .main-container {{
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background: #050505; z-index: 9999; overflow: hidden;
            }}

            .star {{
                position: absolute; background: white; border-radius: 50%;
                opacity: 0.5; animation: twinkle 3s infinite alternate;
            }}
            @keyframes twinkle {{ from {{ opacity: 0.2; }} to {{ opacity: 0.8; }} }}

            .welcome-title {{
                position: absolute; top: 7%; width: 100%; text-align: center;
                color: {config['couleur']}; font-family: sans-serif; font-size: {config['taille']}px; font-weight: bold;
                text-shadow: 0 0 20px {config['couleur']}99; z-index: 10001;
                animation: pulse-text 4s ease-in-out infinite;
            }}
            @keyframes pulse-text {{
                0% {{ transform: scale(1); opacity: 0.8; }}
                50% {{ transform: scale(1.02); opacity: 1; }}
                100% {{ transform: scale(1); opacity: 0.8; }}
            }}

            .center-point {{
                position: absolute; top: 58%; left: 50%;
                transform: translate(-50%, -50%);
                width: 180px; height: 180px;
                z-index: 10000;
            }

            .center-logo {{
                width: 180px; height: 180px; object-fit: contain;
                filter: drop-shadow(0 0 20px {config['couleur']}55);
            }}

            .orbit-photo {{
                position: absolute; top: 50%; left: 50%;
                width: 120px; height: 120px; margin-top: -60px; margin-left: -60px;
                border-radius: 50%; border: 3px solid white; object-fit: cover;
                box-shadow: 0 0 20px rgba(255,255,255,0.4);
                animation: orbit-animation 25s linear infinite;
            }

            @keyframes orbit-animation {{
                from {{ transform: rotate(0deg) translateX(240px) rotate(0deg); }}
                to {{ transform: rotate(360deg) translateX(240px) rotate(-360deg); }}
            }}
        </style>
    """, unsafe_allow_html=True)

    html_content = '<div class="main-container">'
    
    # Etoiles
    for _ in range(60):
        x, y = random.randint(0, 100), random.randint(0, 100)
        s = random.randint(1, 2)
        html_content += f'<div class="star" style="left:{x}vw; top:{y}vh; width:{s}px; height:{s}px;"></div>'

    html_content += f'<div class="welcome-title">{config["texte"]}</div>'
    
    html_content += '<div class="center-point">'
    if logo_data:
        html_content += f'<img src="data:image/png;base64,{logo_data}" class="center-logo">'
    
    if imgs:
        shuffled = imgs[-10:]
        for i, path in enumerate(shuffled):
            img_b64 = get_b64(path)
            delay = -(i * (25 / len(shuffled)))
            html_content += f'<img src="data:image/png;base64,{img_b64}" class="orbit-photo" style="animation-delay:{delay}s;">'
    
    html_content += '</div></div>'
    
    st.markdown(html_content, unsafe_allow_html=True)
