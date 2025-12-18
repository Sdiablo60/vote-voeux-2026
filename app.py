import streamlit as st
import pandas as pd
import os
import glob
import random
import base64
import qrcode
from io import BytesIO

# --- 1. CONFIGURATION & FICHIERS ---
st.set_page_config(page_title="Social Wall 2026", layout="wide", initial_sidebar_state="collapsed")

GALLERY_DIR = "galerie_images"
LOGO_FILE = "logo_entreprise.png"
MSG_FILE = "live_config.csv"

if not os.path.exists(GALLERY_DIR): os.makedirs(GALLERY_DIR)

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
mode_vote = params.get("mode") == "vote"

# --- 3. INTERFACE ADMIN ---
if est_admin:
    st.title("🛠️ Console Régie Master")
    config = get_config()
    
    t1, t2, t3 = st.tabs(["💬 Message Live", "🖼️ Logo & Photos", "🗑️ Nettoyage"])
    
    with t1:
        st.subheader("Personnalisation du titre")
        new_texte = st.text_input("Texte du message", config["texte"])
        new_couleur = st.color_picker("Couleur du texte", config["couleur"])
        new_taille = st.slider("Taille du texte (px)", 20, 100, int(config["taille"]))
        
        if st.button("🚀 Publier les modifications"):
            pd.DataFrame([{"texte": new_texte, "couleur": new_couleur, "taille": new_taille}]).to_csv(MSG_FILE, index=False)
            st.success("Message mis à jour !")
            st.rerun()

    with t2:
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Logo Central")
            ul = st.file_uploader("Changer le logo", type=['png','jpg','jpeg'])
            if ul: 
                with open(LOGO_FILE, "wb") as f: f.write(ul.getbuffer())
                st.rerun()
            if os.path.exists(LOGO_FILE):
                st.image(LOGO_FILE, width=150)
        
        with col_b:
            st.subheader("Ajouter des photos")
            uf = st.file_uploader("Upload photos", type=['png','jpg','jpeg'], accept_multiple_files=True)
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
                    st.image(p, use_container_width=True)
                    if st.button(f"Supprimer", key=f"del_{i}"):
                        os.remove(p)
                        st.rerun()

# --- 4. MODE VOTE (POUR LES INVITÉS) ---
elif mode_vote:
    st.title("🗳️ Vote & Participation")
    st.write("Bienvenue sur l'interface de vote.")
    pseudo = st.text_input("Votre prénom / pseudo")
    if st.button("Valider ma présence"):
        st.balloons()
        st.success(f"Merci {pseudo}, vous allez apparaître sur l'écran !")

# --- 5. MODE LIVE (SOCIAL WALL) ---
else:
    config = get_config()
    logo_data = get_b64(LOGO_FILE)
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
    # Génération du QR Code
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_img = qrcode.make(qr_url)
    buf = BytesIO()
    qr_img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    # Étoiles et Photos
    stars_html = "".join([f'<div class="star" style="left:{random.randint(0,100)}vw; top:{random.randint(0,100)}vh; width:{random.randint(1,2)}px; height:{random.randint(1,2)}px;"></div>' for _ in range(60)])
    
    photos_html = ""
    if imgs:
        shuffled = imgs[-10:]
        for i, path in enumerate(shuffled):
            img_b64 = get_b64(path)
            delay = -(i * (25 / len(shuffled)))
            photos_html += f'<img src="data:image/png;base64,{img_b64}" class="orbit-photo" style="animation-delay:{delay}s;">'

    # INJECTION CSS
    st.markdown(f"""
        <style>
            [data-testid="stHeader"], footer, header {{ display:none !important; }}
            .stApp {{ background-color: #050505 !important; }}
            
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
                width: 180px; height: 180px; z-index: 10000;
            }}

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
            }}

            @keyframes orbit-animation {{
                from {{ transform: rotate(0deg) translateX(240px) rotate(0deg); }}
                to {{ transform: rotate(360deg) translateX(240px) rotate(-360deg); }}
            }}

            .qr-container {{
                position: fixed; bottom: 30px; right: 30px;
                background: white; padding: 10px; border-radius: 15px;
                text-align: center; z-index: 10005;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            }}
        </style>
        
        <div class="main-container">
            {stars_html}
            <div class="welcome-title">{config['texte']}</div>
            <div class="center-point">
                {"<img src='data:image/png;base64," + logo_data + "' class='center-logo'>" if logo_data else ""}
                {photos_html}
            </div>
            <div class="qr-container">
                <img src="data:image/png;base64,{qr_b64}" width="110"><br>
                <b style="color:black; font-family:sans-serif; font-size:12px;">SCANEZ POUR VOTER</b>
            </div>
        </div>
    """, unsafe_allow_html=True)
