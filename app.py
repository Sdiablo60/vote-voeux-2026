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

def get_config():
    if os.path.exists(MSG_FILE):
        try: return pd.read_csv(MSG_FILE).iloc[0].to_dict()
        except: pass
    return {"texte": "✨ BIENVENUE ✨", "couleur": "#FFFFFF", "taille": 45}

# --- 2. LOGIQUE ---
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

# --- 3. INTERFACE ADMIN ---
if est_admin:
    st.title("🛠️ Console Régie Master")
    pwd_actuel = open(PWD_FILE).read().strip() if os.path.exists(PWD_FILE) else "ADMIN_VOEUX_2026"
    with st.sidebar:
        input_pwd = st.text_input("Code Secret", type="password")
    if input_pwd != pwd_actuel:
        st.warning("Veuillez saisir le code dans la barre latérale.")
        st.stop() 

    config = get_config()
    t1, t2 = st.tabs(["💬 Configuration", "🖼️ Galerie"])
    with t1:
        col1, col2 = st.columns(2)
        txt = col1.text_area("Message", config["texte"])
        clr = col2.color_picker("Couleur", config["couleur"])
        siz = col2.slider("Taille", 20, 100, int(config["taille"]))
        if st.button("🚀 Enregistrer"):
            pd.DataFrame([{"texte": txt, "couleur": clr, "taille": siz}]).to_csv(MSG_FILE, index=False)
            st.rerun()
    with t2:
        c1, c2 = st.columns(2)
        ul = c1.file_uploader("Logo", type=['png','jpg','jpeg'])
        if ul:
            with open(LOGO_FILE, "wb") as f: f.write(ul.getbuffer())
            st.rerun()
        uf = c2.file_uploader("Photos", type=['png','jpg','jpeg'], accept_multiple_files=True)
        if uf:
            for f in uf:
                with open(os.path.join(GALLERY_DIR, f.name), "wb") as file: file.write(f.getbuffer())
            st.rerun()
        imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
        cols = st.columns(6)
        for i, p in enumerate(imgs):
            with cols[i%6]:
                st.image(p, use_container_width=True)
                if st.button("🗑️", key=f"del_{i}"):
                    os.remove(p); st.rerun()

# --- 4. MODE LIVE (SOCIAL WALL) ---
elif not mode_vote:
    config = get_config()
    logo_b64 = get_b64(LOGO_FILE)
    img_list = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO()
    qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    stars_html = "".join([f'<div class="st" style="top:{random.randint(0,100)}vh; left:{random.randint(0,100)}vw; width:2px; height:2px; animation-delay:{random.random()*3}s;"></div>' for _ in range(50)])
    
    valid_photos = [get_b64(p) for p in img_list[-10:] if get_b64(p)]
    photos_html = "".join([f'<img src="data:image/png;base64,{b}" class="ph" style="animation-delay:{-(i*(25/max(len(valid_photos),1)))}s;">' for i, b in enumerate(valid_photos)])

    # INJECTION CSS ULTIME
    st.markdown(f"""
    <style>
        /* 1. ON TUE TOUT L'AFFICHAGE STREAMLIT PAR DÉFAUT */
        header, footer, [data-testid="stHeader"], [data-testid="stStatusWidget"] {{
            display: none !important;
        }}
        
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stVerticalBlock"] > div {{
            background-color: #050505 !important;
            border: none !important;
            box-shadow: none !important;
        }}

        /* 2. LE CALQUE MAITRE QUI COUVRE LE CARRÉ BLANC */
        .black-hole {{
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background-color: #050505; z-index: 9999999; overflow: hidden;
            display: flex; align-items: center; justify-content: center;
        }}

        .st {{ position: absolute; background: white; border-radius: 50%; opacity: 0.3; animation: sw 2s infinite alternate; }}
        @keyframes sw {{ from {{ opacity: 0.1; }} to {{ opacity: 0.8; }} }}

        .tit {{ 
            position: absolute; top: 8%; width: 100%; text-align: center;
            font-family: sans-serif; font-weight: bold; z-index: 10000001;
            color: {config['couleur']}; font-size: {config['taille']}px;
            text-shadow: 0 0 20px {config['couleur']};
        }}

        .orb-hub {{ position: relative; width: 1px; height: 1px; z-index: 10000000; }}
        
        .lg {{ 
            position: absolute; transform: translate(-50%, -50%);
            width: 220px; height: 220px; object-fit: contain;
            filter: drop-shadow(0 0 15px {config['couleur']}77);
        }}

        .ph {{ 
            position: absolute; width: 130px; height: 130px; border-radius: 50%;
            border: 3px solid white; object-fit: cover; box-shadow: 0 0 15px rgba(255,255,255,0.3);
            animation: moveOrb 25s linear infinite;
        }}

        @keyframes moveOrb {{
            from {{ transform: rotate(0deg) translateX(275px) rotate(0deg); }}
            to {{ transform: rotate(360deg) translateX(275px) rotate(-360deg); }}
        }}

        .qrc {{ 
            position: fixed; bottom: 30px; right: 30px; background: white;
            padding: 10px; border-radius: 12px; text-align: center; z-index: 10000002;
        }}
    </style>

    <div class="black-hole">
        {stars_html}
        <div class="tit">{config['texte']}</div>
        <div class="orb-hub">
            {"<img src='data:image/png;base64," + logo_b64 + "' class='lg'>" if logo_b64 else ""}
            {photos_html}
        </div>
        <div class="qrc">
            <img src="data:image/png;base64,{qr_b64}" width="100"><br>
            <b style="color:black; font-family:sans-serif; font-size:10px;">SCANNEZ POUR VOTER</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.title("🗳️ Participation")
