import streamlit as st
import pandas as pd
import os
import glob
import random
import base64
import qrcode
from io import BytesIO

# --- CONFIGURATION ---
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

# --- LOGIQUE ---
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

# --- INTERFACE ADMIN ---
if est_admin:
    st.title("🛠️ Console Régie Master")
    pwd_actuel = open(PWD_FILE).read().strip() if os.path.exists(PWD_FILE) else "ADMIN_VOEUX_2026"
    with st.sidebar:
        input_pwd = st.text_input("Code Secret", type="password")
    if input_pwd != pwd_actuel:
        st.warning("Code requis.")
        st.stop()

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
        cols = st.columns(6)
        for i, p in enumerate(imgs):
            with cols[i%6]:
                st.image(p)
                if st.button("🗑️", key=f"del_{i}"): os.remove(p); st.rerun()

# --- MODE LIVE (SOCIAL WALL) ---
elif not mode_vote:
    config = {"texte": "✨ BIENVENUE ✨", "couleur": "#FFFFFF", "taille": 45}
    if os.path.exists(MSG_FILE):
        try: config = pd.read_csv(MSG_FILE).iloc[0].to_dict()
        except: pass
    
    logo_b64 = get_b64(LOGO_FILE)
    img_list = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO()
    qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    # Génération des étoiles
    stars_html = "".join([f'<div class="star" style="top:{random.randint(0,100)}vh; left:{random.randint(0,100)}vw; width:{random.randint(1,3)}px; height:{random.randint(1,3)}px; animation-delay:{random.random()*3}s;"></div>' for _ in range(80)])
    
    # Génération des photos
    photos_html = ""
    valid_photos = [get_b64(p) for p in img_list[-10:] if get_b64(p)]
    for i, b64 in enumerate(valid_photos):
        delay = -(i * (25 / max(len(valid_photos), 1)))
        photos_html += f'<img src="data:image/png;base64,{b64}" class="photo-bubble" style="animation-delay:{delay}s;">'

    # INJECTION CSS & HTML (CORRECTION CADRE BLANC)
    st.markdown(f"""
    <style>
        /* Supprime les marges de Streamlit et force le noir */
        [data-testid="stAppViewContainer"], .stApp {{
            background-color: #050505 !important;
            padding: 0 !important;
        }}
        header, footer, [data-testid="stHeader"] {{ display: none !important; }}

        .wall-container {{
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background-color: #050505; z-index: 9999; overflow: hidden;
        }}

        .star {{
            position: absolute; background: white; border-radius: 50%;
            opacity: 0.3; animation: twinkle 2s infinite alternate;
        }}
        @keyframes twinkle {{ from {{ opacity: 0.1; }} to {{ opacity: 0.8; }} }}

        .title-text {{
            position: absolute; top: 8%; width: 100%; text-align: center;
            font-family: sans-serif; font-weight: bold; z-index: 100;
            color: {config['couleur']}; font-size: {config['taille']}px;
            text-shadow: 0 0 20px {config['couleur']}aa;
        }}

        .center-hub {{
            position: absolute; top: 55%; left: 50%;
            transform: translate(-50%, -50%); width: 1px; height: 1px;
        }}

        .logo-img {{
            position: absolute; transform: translate(-50%, -50%);
            width: 200px; height: 200px; object-fit: contain;
            filter: drop-shadow(0 0 15px {config['couleur']}55);
        }}

        .photo-bubble {{
            position: absolute; width: 130px; height: 130px;
            border-radius: 50%; border: 3px solid white; object-fit: cover;
            box-shadow: 0 0 15px rgba(255,255,255,0.3);
            animation: orbitAnim 25s linear infinite;
        }

        @keyframes orbitAnim {{
            from {{ transform: rotate(0deg) translateX(260px) rotate(0deg); }}
            to {{ transform: rotate(360deg) translateX(260px) rotate(-360deg); }}
        }}

        .qr-anchor {{
            position: fixed; bottom: 30px; right: 30px;
            background: white; padding: 10px; border-radius: 12px;
            text-align: center; z-index: 200;
        }}
    </style>

    <div class="wall-container">
        {stars_html}
        <div class="title-text">{config['texte']}</div>
        <div class="center-hub">
            {"<img src='data:image/png;base64," + logo_b64 + "' class='logo-img'>" if logo_b64 else ""}
            {photos_html}
        </div>
        <div class="qr-anchor">
            <img src="data:image/png;base64,{qr_b64}" width="100"><br>
            <b style="color:black; font-family:sans-serif; font-size:10px;">SCANEZ POUR VOTER</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    st.title("🗳️ Participation")
