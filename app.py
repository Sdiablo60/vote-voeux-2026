import streamlit as st
import pandas as pd
import os
from PIL import Image
from io import BytesIO
import qrcode
import glob
import random
import time
import base64

# --- 1. CONFIGURATION ---
DEFAULT_PASSWORD = "ADMIN_VOEUX_2026"
PASS_FILE = "pass_config.txt"
VOTES_DIR = "sessions_votes"
GALLERY_DIR = "galerie_images"
LOGO_FILE = "logo_entreprise.png"
MSG_FILE = "live_message.csv"

for d in [VOTES_DIR, GALLERY_DIR]:
    if not os.path.exists(d): os.makedirs(d)

st.set_page_config(page_title="Social Wall 2026", layout="wide", initial_sidebar_state="collapsed")

# --- 2. FONCTIONS ---
def get_msg():
    if os.path.exists(MSG_FILE): return pd.read_csv(MSG_FILE).iloc[0].to_dict()
    return {"texte": "✨ Bienvenue à la Grande Soirée des Vœux 2026 !", "couleur": "#FFFFFF", "taille": 45, "font": "sans-serif"}

def img_to_base64(img_path):
    try:
        if os.path.exists(img_path):
            with open(img_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except: return ""
    return ""

# --- 3. LOGIQUE D'ACCÈS ---
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

# --- 4. INTERFACE ADMIN ---
if est_admin:
    st.title("🛠️ Console Régie Master")
    pwd_input = st.sidebar.text_input("Code Admin", type="password")
    if pwd_input == (open(PASS_FILE).read().strip() if os.path.exists(PASS_FILE) else DEFAULT_PASSWORD):
        t1, t2 = st.tabs(["✨ Configuration", "🖼️ Photos"])
        with t1:
            m = get_msg()
            nt = st.text_area("Message", m["texte"])
            nc = st.color_picker("Couleur", m["couleur"])
            ns = st.slider("Taille", 20, 100, int(m["taille"]))
            if st.button("Mettre à jour"):
                pd.DataFrame([{"texte": nt, "couleur": nc, "taille": ns, "font": "sans-serif"}]).to_csv(MSG_FILE, index=False)
                st.rerun()
            ul = st.file_uploader("Logo Central", type=['png','jpg'])
            if ul: Image.open(ul).save(LOGO_FILE); st.rerun()
        with t2:
            uf = st.file_uploader("Ajouter des photos", type=['png','jpg'], accept_multiple_files=True)
            if uf:
                for f in uf: Image.open(f).save(os.path.join(GALLERY_DIR, f.name))
                st.rerun()
            imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
            for i, p in enumerate(imgs):
                if st.button(f"Supprimer {i}", key=f"del_{i}"): os.remove(p); st.rerun()

# --- 5. MODE LIVE (TOTALEMENT INDÉPENDANT) ---
elif not mode_vote:
    msg = get_msg()
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    logo_b64 = img_to_base64(LOGO_FILE)
    
    # Préparation du HTML des photos
    photos_html = ""
    if imgs:
        shuffled = imgs[-12:] # 12 dernières
        for i, path in enumerate(shuffled):
            b64 = img_to_base64(path)
            delay = -(i * (30 / len(shuffled)))
            photos_html += f'<img src="data:image/png;base64,{b64}" class="photo-orbit" style="animation-delay:{delay}s;">'

    # Préparation des étoiles
    stars_html = "".join([f'<div class="star" style="left:{random.randint(0,100)}vw; top:{random.randint(0,100)}vh; animation-duration:{random.randint(3,7)}s; animation-delay:{random.randint(0,5)}s;"></div>' for _ in range(100)])

    # QR Code
    qr_url = f"https://{st.context.headers.get('Host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    # STYLE & HTML FINAL (Injection directe pour éviter les contraintes de layout)
    st.markdown(f"""
        <style>
        /* On cache tout Streamlit */
        [data-testid="stSidebar"], [data-testid="stHeader"], .stApp {{ display: none; }}
        
        body {{ background-color: #050505; margin: 0; padding: 0; overflow: hidden; }}

        .wall-wrapper {{
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background-color: #050505; z-index: 9999; font-family: sans-serif;
        }}

        /* Etoiles */
        .star {{
            position: absolute; width: 2px; height: 2px; background: white; 
            border-radius: 50%; opacity: 0.3; animation: twinkle infinite alternate;
        }}
        @keyframes twinkle {{ from {{ opacity: 0.1; }} to {{ opacity: 0.8; }} }}

        /* Message accueil avec Pulsation */
        .welcome {{
            position: absolute; top: 10%; width: 100%; text-align: center;
            color: {msg['couleur']}; font-size: {msg['taille']}px; font-weight: bold;
            animation: pulse 4s ease-in-out infinite; z-index: 100;
        }}
        @keyframes pulse {{
            0% {{ transform: scale(1); text-shadow: 0 0 10px {msg['couleur']}55; }}
            50% {{ transform: scale(1.05); text-shadow: 0 0 30px {msg['couleur']}; }}
            100% {{ transform: scale(1); text-shadow: 0 0 10px {msg['couleur']}55; }}
        }}

        /* Logo Central */
        .logo {{
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            width: 250px; height: 250px; border-radius: 50%; z-index: 50;
            filter: drop-shadow(0 0 30px {msg['couleur']}88); object-fit: contain;
        }}

        /* Orbite */
        .photo-orbit {{
            position: absolute; top: 50%; left: 50%; width: 150px; height: 150px;
            margin-top: -75px; margin-left: -75px; border-radius: 50%;
            border: 3px solid white; object-fit: cover;
            animation: orbit 30s linear infinite; z-index: 40;
            box-shadow: 0 0 20px rgba(255,255,255,0.3);
        }}
        @keyframes orbit {{
            from {{ transform: rotate(0deg) translateX(min(30vw, 380px)) rotate(0deg); }}
            to {{ transform: rotate(360deg) translateX(min(30vw, 380px)) rotate(-360deg); }}
        }}

        /* QR Code */
        .qr {{
            position: fixed; bottom: 30px; right: 30px; background: white;
            padding: 10px; border-radius: 15px; text-align: center; z-index: 200;
        }}
        </style>

        <div class="wall-wrapper">
            {stars_html}
            <div class="welcome">{msg['texte']}</div>
            {"<img src='data:image/png;base64," + logo_b64 + "' class='logo'>" if logo_b64 else ""}
            {photos_html}
            <div class="qr">
                <img src="data:image/png;base64,{qr_b64}" width="110"><br>
                <b style="color:black; font-size:12px;">SCANNEZ POUR VOTER</b>
            </div>
        </div>
    """, unsafe_allow_html=True)

    time.sleep(10); st.rerun()

else:
    st.title("🗳️ Vote & Présence")
