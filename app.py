import streamlit as st
import pandas as pd
import os
import glob
import random
import base64
import qrcode
from io import BytesIO

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Social Wall 2026", layout="wide", initial_sidebar_state="collapsed")

GALLERY_DIR = "galerie_images"
LOGO_FILE = "logo_entreprise.png"
MSG_FILE = "live_config.csv"
PWD_FILE = "admin_pwd.txt"

if not os.path.exists(GALLERY_DIR): os.makedirs(GALLERY_DIR)

def get_b64(path):
    try:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None
    return None

# --- 2. LOGIQUE ---
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

# --- 3. INTERFACE ADMIN ---
if est_admin:
    st.title("🛠️ Console Régie Master")
    with st.sidebar:
        input_pwd = st.text_input("Code Secret", type="password")
    
    if input_pwd != (open(PWD_FILE).read().strip() if os.path.exists(PWD_FILE) else "ADMIN_VOEUX_2026"):
        st.warning("Veuillez saisir le code dans la barre latérale.")
        st.stop() 

    # (Code Admin inchangé pour gagner de la place, il fonctionne bien)
    config = {"texte": "✨ BIENVENUE ✨", "couleur": "#FFFFFF", "taille": 45}
    if os.path.exists(MSG_FILE): config = pd.read_csv(MSG_FILE).iloc[0].to_dict()
    
    t1, t2 = st.tabs(["💬 Config", "🖼️ Galerie"])
    with t1:
        txt = st.text_area("Message", config["texte"])
        clr = st.color_picker("Couleur", config["couleur"])
        siz = st.slider("Taille", 20, 100, int(config["taille"]))
        if st.button("Enregistrer"):
            pd.DataFrame([{"texte": txt, "couleur": clr, "taille": siz}]).to_csv(MSG_FILE, index=False)
            st.rerun()
    with t2:
        ul = st.file_uploader("Logo", type=['png','jpg'])
        if ul:
            with open(LOGO_FILE, "wb") as f: f.write(ul.getbuffer())
            st.rerun()
        uf = st.file_uploader("Photos", type=['png','jpg'], accept_multiple_files=True)
        if uf:
            for f in uf:
                with open(os.path.join(GALLERY_DIR, f.name), "wb") as file: file.write(f.getbuffer())
            st.rerun()
        imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
        for i, p in enumerate(imgs):
            if st.button(f"Supprimer {i}", key=f"del_{i}"): os.remove(p); st.rerun()

# --- 4. MODE LIVE (SOCIAL WALL) ---
elif not mode_vote:
    config = {"texte": "✨ BIENVENUE ✨", "couleur": "#FFFFFF", "taille": 45}
    if os.path.exists(MSG_FILE): config = pd.read_csv(MSG_FILE).iloc[0].to_dict()
    
    logo_b64 = get_b64(LOGO_FILE)
    img_list = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
    # QR Code
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO()
    qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    # Nettoyage CSS Radical
    st.markdown(f"""
    <style>
        /* 1. CACHE TOUT STREAMLIT SANS EXCEPTION */
        [data-testid="stAppViewContainer"], [data-testid="stHeader"], footer, .stAppHeader {{
            background-color: #050505 !important;
        }}
        
        /* 2. CIBLE LE CARRÉ BLANC (Cache les conteneurs de texte Streamlit) */
        .stMarkdown, .element-container, [data-testid="stVerticalBlock"] > div {{
            display: none !important;
            height: 0px !important;
            margin: 0 !important;
            padding: 0 !important;
        }}

        /* 3. NOTRE MUR (Force l'affichage) */
        #mon-wall-final {{
            display: block !important;
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: #050505; z-index: 2147483647; /* Z-index maximum possible */
            overflow: hidden;
        }}

        .star {{ position: absolute; background: white; border-radius: 50%; opacity: 0.5; }}
        .welcome-msg {{
            position: absolute; top: 10%; width: 100%; text-align: center;
            font-family: sans-serif; font-weight: bold;
            color: {config['couleur']}; font-size: {config['taille']}px;
            text-shadow: 0 0 20px {config['couleur']};
        }}
        .center-hub {{ position: absolute; top: 55%; left: 50%; transform: translate(-50%, -50%); }}
        .logo-img {{ width: 200px; height: 200px; object-fit: contain; }}
        .orbit-img {{
            position: absolute; width: 130px; height: 130px; border-radius: 50%;
            border: 3px solid white; object-fit: cover;
            animation: move-orbit 25s linear infinite;
        }}
        @keyframes move-orbit {{
            from {{ transform: rotate(0deg) translateX(260px) rotate(0deg); }}
            to {{ transform: rotate(360deg) translateX(260px) rotate(-360deg); }}
        }}
        .qr-area {{ position: fixed; bottom: 30px; right: 30px; background: white; padding: 10px; border-radius: 12px; text-align: center; }}
    </style>

    <div id="mon-wall-final">
        {"".join([f'<div class="star" style="left:{random.randint(0,100)}vw; top:{random.randint(0,100)}vh; width:2px; height:2px;"></div>' for _ in range(50)])}
        <div class="welcome-msg">{config['texte']}</div>
        <div class="center-hub">
            {"<img src='data:image/png;base64," + logo_b64 + "' class='logo-img'>" if logo_b64 else ""}
            {"".join([f'<img src="data:image/png;base64,{get_b64(p)}" class="orbit-img" style="animation-delay:{-(i*(25/max(len(img_list),1)))}s;">' for i, p in enumerate(img_list[-10:]) if get_b64(p)])}
        </div>
        <div class="qr-area">
            <img src="data:image/png;base64,{qr_b64}" width="100"><br>
            <b style="color:black; font-family:sans-serif; font-size:10px;">SCANNEZ POUR VOTER</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    st.title("🗳️ Participation")
