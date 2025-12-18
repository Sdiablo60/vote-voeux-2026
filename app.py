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

st.set_page_config(page_title="Social Wall Starlight", layout="wide")

# --- 2. FONCTIONS DE GESTION ---
def get_msg():
    if os.path.exists(MSG_FILE): return pd.read_csv(MSG_FILE).iloc[0].to_dict()
    return {"texte": "Bienvenue !", "couleur": "#FF4B4B", "taille": 50, "font": "sans-serif"}

def save_msg(t, c, s, f):
    pd.DataFrame([{"texte": t, "couleur": c, "taille": s, "font": f}]).to_csv(MSG_FILE, index=False)

def img_to_base64(img_path):
    try:
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

# --- 3. LOGIQUE ADMIN ---
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

if est_admin:
    st.title("🛠️ Régie Social Wall")
    pwd = st.sidebar.text_input("Code Admin", type="password")
    if pwd == (open(PASS_FILE).read().strip() if os.path.exists(PASS_FILE) else DEFAULT_PASSWORD):
        t1, t2 = st.tabs(["✨ Message & Logo", "🖼️ Photos"])
        with t1:
            m = get_msg()
            nt = st.text_area("Texte du message", m["texte"])
            nc = st.color_picker("Couleur", m["couleur"])
            ns = st.slider("Taille (px)", 20, 100, int(m["taille"]))
            nf = st.selectbox("Police", ["sans-serif", "serif", "cursive", "monospace"], index=0)
            if st.button("Enregistrer Message"): save_msg(nt, nc, ns, nf); st.rerun()
            st.divider()
            ul = st.file_uploader("Importer Logo Central", type=['png','jpg'])
            if ul: Image.open(ul).save(LOGO_FILE); st.rerun()
            if os.path.exists(LOGO_FILE):
                if st.button("Supprimer Logo"): os.remove(LOGO_FILE); st.rerun()
        with t2:
            uf = st.file_uploader("Ajouter Photos", type=['png','jpg','jpeg'], accept_multiple_files=True)
            if uf:
                for f in uf: Image.open(f).save(os.path.join(GALLERY_DIR, f.name))
                st.rerun()
            st.divider()
            imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
            for i, p in enumerate(imgs):
                col1, col2 = st.columns([0.8, 0.2])
                col1.image(p, width=100)
                if col2.button(f"Supprimer", key=f"del_{i}"): os.remove(p); st.rerun()

# --- 4. MODE LIVE (ORBITAL STELLAIRE) ---
elif not mode_vote:
    msg = get_msg()
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    logo_b64 = img_to_base64(LOGO_FILE)

    # Génération du fond étoilé
    stars_html = ""
    for _ in range(80):
        x, y = random.randint(0, 100), random.randint(0, 100)
        size = random.randint(1, 3)
        dur = random.randint(3, 8)
        stars_html += f'<div style="position:absolute; left:{x}vw; top:{y}vh; width:{size}px; height:{size}px; background:white; border-radius:50%; opacity:0.6; animation: twinkle {dur}s infinite alternate;"></div>'

    st.markdown(f"""
        <style>
        [data-testid="stSidebar"] {{display: none;}}
        .main {{background-color: #050505; overflow: hidden; height: 100vh; position: relative;}}
        
        @keyframes twinkle {{ from {{opacity: 0.2;}} to {{opacity: 1;}} }}
        @keyframes orbit {{
            from {{ transform: rotate(0deg) translateX(320px) rotate(0deg); }}
            to {{ transform: rotate(360deg) translateX(320px) rotate(-360deg); }}
        }}

        .welcome-msg {{
            position: absolute; top: 40px; width: 100%; text-align: center;
            color: {msg['couleur']}; font-size: {msg['taille']}px; font-family: {msg['font']};
            z-index: 10; text-shadow: 0 0 20px {msg['couleur']};
        }}

        .center-logo {{
            position: absolute; top: 55%; left: 50%;
            transform: translate(-50%, -50%);
            width: 220px; height: 220px; z-index: 5;
            border-radius: 50%; object-fit: contain;
            box-shadow: 0 0 60px {msg['couleur']};
        }}

        .photo-orbit {{
            position: absolute; top: 50%; left: 47%;
            width: 130px; height: 130px;
            border-radius: 50%; border: 3px solid white;
            object-fit: cover;
            box-shadow: 0 0 20px rgba(255,255,255,0.6);
            animation: orbit var(--dur)s linear infinite;
        }}

        .qr-box {{
            position: fixed; bottom: 30px; right: 30px;
            background: white; padding: 12px; border-radius: 12px; text-align: center;
            z-index: 100; box-shadow: 0 10px 30px rgba(0,0,0,0.8);
        }}
        </style>
        
        <div class="stars-container">{stars_html}</div>
        <div class="welcome-msg">{msg['texte']}</div>
        {"<img src='data:image/png;base64," + logo_b64 + "' class='center-logo'>" if logo_b64 else ""}
    """, unsafe_allow_html=True)

    if imgs:
        # On affiche max 12 photos pour la performance
        for i, path in enumerate(imgs[-12:]):
            b64 = img_to_base64(path)
            duration = 20 + (i * 4)
            delay = -(i * 5)
            st.markdown(f"""
                <img src="data:image/png;base64,{b64}" class="photo-orbit" 
                style="--dur:{duration}; animation-delay:{delay}s;">
            """, unsafe_allow_html=True)

    # QR CODE
    qr_url = f"https://{st.context.headers.get('Host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_img = base64.b64encode(qr_buf.getvalue()).decode()
    st.markdown(f"""
        <div class="qr-box">
            <img src="data:image/png;base64,{qr_img}" width="110"><br>
            <b style="color:black; font-size:12px; font-family:sans-serif;">SCANNEZ POUR VOTER</b>
        </div>
    """, unsafe_allow_html=True)

    time.sleep(10); st.rerun()

# --- 5. MODE VOTE ---
else:
    st.title("🗳️ Participation Live")
    pseudo = st.text_input("Votre Pseudo")
    if st.button("Valider"):
        st.success("C'est fait ! Regardez l'écran."); st.balloons()
