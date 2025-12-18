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

st.set_page_config(page_title="Régie Master 2026", layout="wide")

# --- 2. FONCTIONS ---
def get_msg():
    if os.path.exists(MSG_FILE): return pd.read_csv(MSG_FILE).iloc[0].to_dict()
    return {"texte": "Bienvenue !", "couleur": "#FF4B4B", "taille": 50, "font": "sans-serif"}

def save_msg(t, c, s, f):
    pd.DataFrame([{"texte": t, "couleur": c, "taille": s, "font": f}]).to_csv(MSG_FILE, index=False)

def img_to_base64(img_path):
    try:
        if os.path.exists(img_path):
            with open(img_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except: return ""
    return ""

# --- 3. INITIALISATION ---
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

# --- 4. INTERFACE ADMIN ---
if est_admin:
    # On gère l'auth dans la sidebar
    with st.sidebar:
        st.header("🔑 Authentification")
        pwd_input = st.text_input("Saisir le Code Admin", type="password")
        real_pass = open(PASS_FILE).read().strip() if os.path.exists(PASS_FILE) else DEFAULT_PASSWORD
        auth_ok = (pwd_input == real_pass)

    if not auth_ok:
        st.title("🔐 En attente de connexion...")
        st.info("Veuillez saisir le code secret dans la barre latérale pour accéder aux commandes de la régie.")
    else:
        st.title("🛠️ Console Régie Master")
        t1, t2 = st.tabs(["✨ Message & Logo", "🖼️ Gestion Photos"])
        
        with t1:
            m = get_msg()
            with st.form("msg_form"):
                nt = st.text_area("Texte du message live", m["texte"])
                c1, c2, c3 = st.columns(3)
                nc = c1.color_picker("Couleur", m["couleur"])
                ns = c2.slider("Taille", 20, 120, int(m["taille"]))
                nf = c3.selectbox("Police", ["sans-serif", "serif", "cursive", "monospace"])
                if st.form_submit_button("Actualiser le Social Wall"):
                    save_msg(nt, nc, ns, nf); st.rerun()
            
            st.divider()
            if os.path.exists(LOGO_FILE):
                st.image(LOGO_FILE, width=150)
                if st.button("Supprimer ce logo"): os.remove(LOGO_FILE); st.rerun()
            else:
                ul = st.file_uploader("Ajouter le Logo Central", type=['png','jpg','jpeg'])
                if ul: Image.open(ul).save(LOGO_FILE); st.rerun()

        with t2:
            uf = st.file_uploader("Importer des photos", type=['png','jpg','jpeg'], accept_multiple_files=True)
            if uf:
                for f in uf: Image.open(f).save(os.path.join(GALLERY_DIR, f.name))
                st.success(f"{len(uf)} photos ajoutées"); st.rerun()
            
            st.divider()
            imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
            if imgs:
                cols = st.columns(5)
                for i, p in enumerate(imgs):
                    with cols[i%5]:
                        st.image(p, use_container_width=True)
                        if st.button("🗑️", key=f"del_{i}"): os.remove(p); st.rerun()

# --- 5. MODE LIVE (ORBITAL & ETOILES) ---
elif not mode_vote:
    msg = get_msg()
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    logo_b64 = img_to_base64(LOGO_FILE)

    # Génération des étoiles
    stars_html = "".join([f'<div style="position:absolute; left:{random.randint(0,100)}vw; top:{random.randint(0,100)}vh; width:{random.randint(1,3)}px; height:{random.randint(1,3)}px; background:white; border-radius:50%; opacity:0.6; animation: twinkle {random.randint(3,8)}s infinite alternate;"></div>' for _ in range(100)])

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
            position: absolute; top: 55%; left: 50%; transform: translate(-50%, -50%);
            width: 220px; height: 220px; z-index: 5; border-radius: 50%;
            box-shadow: 0 0 50px {msg['couleur']};
        }}
        .photo-orbit {{
            position: absolute; top: 50%; left: 47%; width: 130px; height: 130px;
            border-radius: 50%; border: 3px solid white; object-fit: cover;
            box-shadow: 0 0 15px rgba(255,255,255,0.5); animation: orbit var(--dur)s linear infinite;
        }}
        .qr-box {{
            position: fixed; bottom: 30px; right: 30px; background: white; padding: 12px;
            border-radius: 12px; text-align: center; z-index: 100; box-shadow: 0 10px 30px rgba(0,0,0,0.8);
        }}
        </style>
        <div class="stars-container">{stars_html}</div>
        <div class="welcome-msg">{msg['texte']}</div>
        {"<img src='data:image/png;base64," + logo_b64 + "' class='center-logo'>" if logo_b64 else ""}
    """, unsafe_allow_html=True)

    if imgs:
        for i, path in enumerate(imgs[-12:]):
            b64 = img_to_base64(path)
            st.markdown(f'<img src="data:image/png;base64,{b64}" class="photo-orbit" style="--dur:{20+(i*3)}s; animation-delay:-{i*4}s;">', unsafe_allow_html=True)

    # QR Code
    qr_url = f"https://{st.context.headers.get('Host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_img = base64.b64encode(qr_buf.getvalue()).decode()
    st.markdown(f'<div class="qr-box"><img src="data:image/png;base64,{qr_img}" width="110"><br><b style="color:black; font-size:12px;">SCANEZ POUR VOTER</b></div>', unsafe_allow_html=True)

    time.sleep(10); st.rerun()

# --- 6. MODE VOTE ---
else:
    st.title("🗳️ Vote & Présence")
    pseudo = st.text_input("Pseudo")
    if st.button("Valider"):
        st.success("Enregistré !"); st.balloons()
