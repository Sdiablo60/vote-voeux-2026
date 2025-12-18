import streamlit as st
import pandas as pd
import os
from PIL import Image
from io import BytesIO
import qrcode
import glob
import random
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
    return {"texte": "✨ Bienvenue à la Grande Soirée des Vœux 2026 !", "couleur": "#FFFFFF", "taille": 45}

def img_to_base64(img_path):
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

# --- 3. LOGIQUE D'ACCÈS ---
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

# --- 4. INTERFACE ADMIN ---
if est_admin:
    st.title("🛠️ Console Régie")
    pwd_input = st.sidebar.text_input("Code Admin", type="password")
    if pwd_input == (open(PASS_FILE).read().strip() if os.path.exists(PASS_FILE) else DEFAULT_PASSWORD):
        t1, t2 = st.tabs(["✨ Configuration", "🖼️ Photos"])
        with t1:
            m = get_msg()
            nt = st.text_area("Message", m["texte"])
            nc = st.color_picker("Couleur", m["couleur"])
            ns = st.slider("Taille", 20, 100, int(m["taille"]))
            if st.button("Mettre à jour"):
                pd.DataFrame([{"texte": nt, "couleur": nc, "taille": ns}]).to_csv(MSG_FILE, index=False)
                st.rerun()
            ul = st.file_uploader("Logo Central", type=['png','jpg'])
            if ul: Image.open(ul).save(LOGO_FILE); st.rerun()
        with t2:
            uf = st.file_uploader("Ajouter des photos", type=['png','jpg','jpeg'], accept_multiple_files=True)
            if uf:
                for f in uf: Image.open(f).save(os.path.join(GALLERY_DIR, f.name))
                st.rerun()
            imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
            cols = st.columns(4)
            for i, p in enumerate(imgs):
                with cols[i%4]:
                    st.image(p, width=100)
                    if st.button("Supprimer", key=f"del_{i}"): os.remove(p); st.rerun()
    else:
        st.info("Veuillez entrer le code dans la barre latérale.")

# --- 5. MODE LIVE ---
elif not mode_vote:
    msg = get_msg()
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    logo_b64 = img_to_base64(LOGO_FILE)
    
    qr_url = f"https://{st.context.headers.get('Host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO()
    qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    # Génération du HTML dynamique
    stars_html = "".join([f'<div class="star" style="left:{random.randint(0,100)}vw; top:{random.randint(0,100)}vh; animation-duration:{random.randint(3,6)}s;"></div>' for _ in range(60)])
    photos_html = ""
    if imgs:
        shuffled = imgs[-10:]
        for i, path in enumerate(shuffled):
            p_b64 = img_to_base64(path)
            delay = -(i * (20 / len(shuffled)))
            photos_html += f'<img src="data:image/png;base64,{p_b64}" class="photo-orbit" style="animation-delay:{delay}s;">'

    # INJECTION DU CSS PUR (SANS VARIABLES PYTHON POUR ÉVITER LES ERREURS)
    st.markdown(r"""
    <style>
        /* Masquage radical de Streamlit */
        header, footer, .stAppHeader, [data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
        .stApp { background-color: #050505 !important; }
        
        .live-container {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: #050505; z-index: 9999; overflow: hidden;
            color: white; margin: 0; padding: 0;
        }
        .star { position: absolute; width: 2px; height: 2px; background: white; border-radius: 50%; animation: twinkle infinite alternate; }
        @keyframes twinkle { from { opacity: 0.1; } to { opacity: 0.8; } }
        
        .welcome-msg {
            position: absolute; top: 10%; width: 100%; text-align: center;
            font-weight: bold; font-family: sans-serif; z-index: 10001;
            animation: pulse 4s ease-in-out infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); opacity: 0.8; }
            50% { transform: scale(1.02); opacity: 1; }
            100% { transform: scale(1); opacity: 0.8; }
        }
        .logo-center {
            position: absolute; top: 55%; left: 50%; transform: translate(-50%, -50%);
            width: 220px; height: 220px; object-fit: contain; z-index: 10000;
        }
        .photo-orbit {
            position: absolute; top: 55%; left: 50%; width: 140px; height: 140px;
            margin-top: -70px; margin-left: -70px; border-radius: 50%;
            border: 3px solid white; object-fit: cover;
            animation: orbit 20s linear infinite; z-index: 9999;
        }
        @keyframes orbit {
            from { transform: rotate(0deg) translateX(min(32vw, 350px)) rotate(0deg); }
            to { transform: rotate(360deg) translateX(min(32vw, 350px)) rotate(-360deg); }
        }
        .qr-zone { position: fixed; bottom: 30px; right: 30px; background: white; padding: 10px; border-radius: 12px; text-align: center; z-index: 10002; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

    # AFFICHAGE DU CONTENU (INJECTION DES VARIABLES VIA STYLE INLINE)
    st.markdown(f"""
    <div class="live-container">
        {stars_html}
        <div class="welcome-msg" style="color:{msg['couleur']}; font-size:{msg['taille']}px; text-shadow: 0 0 20px {msg['couleur']};">
            {msg['texte']}
        </div>
        {"<img src='data:image/png;base64," + logo_b64 + "' class='logo-center' style='filter: drop-shadow(0 0 30px "+msg['couleur']+"88);'>" if logo_b64 else ""}
        {photos_html}
        <div class="qr-zone">
            <img src="data:image/png;base64,{qr_b64}" width="100"><br>
            <span style="font-size:12px; font-weight:bold; font-family:sans-serif;">SCANNEZ POUR VOTER</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    st.title("🗳️ Vote & Présence")
