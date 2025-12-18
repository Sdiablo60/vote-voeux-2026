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
PRESENCE_FILE = "presence_live.csv"
MSG_FILE = "live_message.csv"

for d in [VOTES_DIR, GALLERY_DIR]:
    if not os.path.exists(d): os.makedirs(d)

st.set_page_config(page_title="Social Wall 2026", layout="wide", initial_sidebar_state="collapsed")

# --- 2. FONCTIONS ---
def get_msg():
    if os.path.exists(MSG_FILE): return pd.read_csv(MSG_FILE).iloc[0].to_dict()
    return {"texte": "✨ Bienvenue à la Grande Soirée des Vœux 2026 !", 
            "couleur": "#FFFFFF", "taille": 45, "font": "sans-serif"}

def save_msg(t, c, s, f):
    pd.DataFrame([{"texte": t, "couleur": c, "taille": s, "font": f}]).to_csv(MSG_FILE, index=False)

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
    with st.sidebar:
        st.header("🔑 Authentification")
        pwd_input = st.text_input("Code Admin", type="password")
        real_pass = open(PASS_FILE).read().strip() if os.path.exists(PASS_FILE) else DEFAULT_PASSWORD
        auth_ok = (pwd_input == real_pass)

    if not auth_ok:
        st.title("🔐 En attente de connexion...")
    else:
        st.title("🛠️ Console Régie Master")
        t1, t2 = st.tabs(["✨ Message & Logo", "🖼️ Gestion Photos"])
        with t1:
            m = get_msg()
            with st.form("msg_form"):
                nt = st.text_area("Message d'accueil", m["texte"])
                c1, c2, c3 = st.columns(3)
                nc = c1.color_picker("Couleur", m["couleur"])
                ns = c2.slider("Taille", 20, 100, int(m["taille"]))
                nf = c3.selectbox("Police", ["sans-serif", "serif", "cursive", "monospace"])
                if st.form_submit_button("Mettre à jour"):
                    save_msg(nt, nc, ns, nf); st.rerun()
            if os.path.exists(LOGO_FILE):
                st.image(LOGO_FILE, width=150)
                if st.button("Supprimer logo"): os.remove(LOGO_FILE); st.rerun()
            else:
                ul = st.file_uploader("Logo Central", type=['png','jpg','jpeg'])
                if ul: Image.open(ul).save(LOGO_FILE); st.rerun()
        with t2:
            uf = st.file_uploader("Ajouter des photos", type=['png','jpg','jpeg'], accept_multiple_files=True)
            if uf:
                for f in uf: Image.open(f).save(os.path.join(GALLERY_DIR, f.name))
                st.rerun()
            imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
            cols = st.columns(5)
            for i, p in enumerate(imgs):
                with cols[i%5]:
                    st.image(p, use_container_width=True); st.button("🗑️", key=f"del_{i}", on_click=lambda p=p: os.remove(p))

# --- 5. MODE LIVE (SOCIAL WALL CORRIGÉ) ---
elif not mode_vote:
    msg = get_msg()
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    logo_b64 = img_to_base64(LOGO_FILE)

    stars_html = "".join([f'<div style="position:absolute; left:{random.randint(0,100)}vw; top:{random.randint(0,100)}vh; width:{random.randint(1,2)}px; height:{random.randint(1,2)}px; background:white; border-radius:50%; opacity:0.5; animation: twinkle {random.randint(2,5)}s infinite alternate;"></div>' for _ in range(120)])

    st.markdown(f"""
        <style>
        [data-testid="stSidebar"] {{ display: none; }}
        [data-testid="stHeader"] {{ display: none; }}
        .main {{ background-color: #050505; overflow: hidden; height: 100vh; width: 100vw; position: fixed; top:0; left:0; }}
        
        @keyframes twinkle {{ from {{ opacity: 0.1; }} to {{ opacity: 0.9; }} }}
        
        @keyframes pulse {{
            0% {{ opacity: 0.8; transform: scale(1); text-shadow: 0 0 10px {msg['couleur']}; }}
            50% {{ opacity: 1; transform: scale(1.05); text-shadow: 0 0 30px {msg['couleur']}; }}
            100% {{ opacity: 0.8; transform: scale(1); text-shadow: 0 0 10px {msg['couleur']}; }}
        }}
        
        /* CORRECTION ORBITE : Utilisation de rotate sur le parent et translation inverse sur l'image */
        @keyframes orbit {{
            from {{ transform: rotate(0deg) translateX(350px) rotate(0deg); }}
            to {{ transform: rotate(360deg) translateX(350px) rotate(-360deg); }}
        }}

        .welcome-container {{
            position: absolute; top: 8%; width: 100%; text-align: center; z-index: 20;
        }}
        .welcome-text {{
            color: {msg['couleur']}; font-size: {msg['taille']}px; font-family: {msg['font']};
            animation: pulse 4s ease-in-out infinite;
        }}

        .center-logo {{
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            width: 250px; z-index: 5; border-radius: 50%;
            filter: drop-shadow(0 0 40px {msg['couleur']}66);
        }}

        .photo-orbit {{
            position: absolute; top: 50%; left: 50%; 
            margin-top: -75px; margin-left: -75px; /* Centrage par rapport au centre du logo */
            width: 150px; height: 150px;
            border-radius: 50%; border: 3px solid white; object-fit: cover;
            box-shadow: 0 0 20px rgba(255,255,255,0.4); 
            animation: orbit var(--dur)s linear infinite;
        }}

        .qr-box {{
            position: fixed; bottom: 30px; right: 30px; background: white; padding: 10px;
            border-radius: 15px; text-align: center; z-index: 100;
        }}
        </style>
        
        <div class="stars-container">{stars_html}</div>
        <div class="welcome-container"><div class="welcome-text">{msg['texte']}</div></div>
        {"<img src='data:image/png;base64," + logo_b64 + "' class='center-logo'>" if logo_b64 else ""}
    """, unsafe_allow_html=True)

    if imgs:
        # On affiche les 12 dernières photos importées
        for i, path in enumerate(imgs[-12:]):
            b64 = img_to_base64(path)
            # On décale le départ de chaque photo pour qu'elles soient réparties sur le cercle
            delay = -(i * (25 / 12)) 
            st.markdown(f'<img src="data:image/png;base64,{b64}" class="photo-orbit" style="--dur:25s; animation-delay:{delay}s;">', unsafe_allow_html=True)

    # QR Code
    qr_url = f"https://{st.context.headers.get('Host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_img = base64.b64encode(qr_buf.getvalue()).decode()
    st.markdown(f'<div class="qr-box"><img src="data:image/png;base64,{qr_img}" width="100"><br><b style="color:black; font-size:10px;">VOTER ICI</b></div>', unsafe_allow_html=True)

    time.sleep(10); st.rerun()

else:
    st.title("🗳️ Vote & Présence")
