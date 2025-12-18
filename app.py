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
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
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
    with st.sidebar:
        input_pwd = st.text_input("Code Secret", type="password")
    
    if input_pwd != (open(PWD_FILE).read().strip() if os.path.exists(PWD_FILE) else "ADMIN_VOEUX_2026"):
        st.warning("Veuillez saisir le code dans la barre latérale.")
        st.stop() 

    config = get_config()
    t1, t2 = st.tabs(["💬 Configuration", "🖼️ Galerie"])
    with t1:
        col1, col2 = st.columns(2)
        txt = col1.text_area("Message", config["texte"])
        clr = col2.color_picker("Couleur", config["couleur"])
        siz = col2.slider("Taille", 20, 100, int(config["taille"]))
        if st.button("Enregistrer"):
            pd.DataFrame([{"texte": txt, "couleur": clr, "taille": siz}]).to_csv(MSG_FILE, index=False)
            st.rerun()
    with t2:
        c1, c2 = st.columns(2)
        ul = c1.file_uploader("Logo", type=['png','jpg'])
        if ul:
            with open(LOGO_FILE, "wb") as f: f.write(ul.getbuffer())
            st.rerun()
        uf = c2.file_uploader("Photos", type=['png','jpg'], accept_multiple_files=True)
        if uf:
            for f in uf:
                with open(os.path.join(GALLERY_DIR, f.name), "wb") as file: file.write(f.getbuffer())
            st.rerun()
        st.divider()
        imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
        cols = st.columns(6)
        for i, p in enumerate(imgs):
            with cols[i%6]:
                st.image(p)
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

    # Préparation des éléments
    stars_html = "".join([f'<div class="star" style="left:{random.randint(0,100)}vw; top:{random.randint(0,100)}vh; width:{random.randint(1,2)}px; height:{random.randint(1,2)}px;"></div>' for _ in range(50)])
    
    photos_html = ""
    valid_photos = [get_b64(p) for p in img_list[-12:] if get_b64(p)]
    for i, b64 in enumerate(valid_photos):
        delay = -(i * (25 / max(len(valid_photos), 1)))
        photos_html += f'<img src="data:image/png;base64,{b64}" class="photo-orbit" style="animation-delay:{delay}s;">'

    # INJECTION CSS (Version Corrigée pour l'affichage des images)
    st.markdown(f"""
    <style>
        /* Cache Streamlit mais autorise notre conteneur spécifique */
        [data-testid="stVerticalBlock"] > div:not(:last-child) {{ display: none !important; }}
        header, footer, .stAppHeader {{ display:none !important; }}
        .stApp {{ background-color: #050505 !important; overflow: hidden; }}
        
        .wall-final {{ 
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; 
            background: #050505; z-index: 9999; overflow: hidden;
            display: block !important;
        }}
        .star {{ position: absolute; background: white; border-radius: 50%; opacity: 0.5; animation: twi 3s infinite alternate; }}
        @keyframes twi {{ from {{ opacity: 0.2; }} to {{ opacity: 0.8; }} }}
        .msg {{ position: absolute; top: 8%; width: 100%; text-align: center; font-family: sans-serif; font-weight: bold; z-index: 10001; animation: pul 4s infinite; color: {config['couleur']}; font-size: {config['taille']}px; text-shadow: 0 0 20px {config['couleur']}; }}
        @keyframes pul {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.02); }} }}
        .hub {{ position: absolute; top: 58%; left: 50%; transform: translate(-50%, -50%); width: 1px; height: 1px; z-index: 10000; }}
        .logo {{ position: absolute; transform: translate(-50%, -50%); width: 200px; height: 200px; object-fit: contain; filter: drop-shadow(0 0 15px {config['couleur']}77); }}
        .photo-orbit {{ position: absolute; width: 130px; height: 130px; border-radius: 50%; border: 3px solid white; object-fit: cover; box-shadow: 0 0 20px rgba(255,255,255,0.4); animation: orb 25s linear infinite; display: block !important; }}
        @keyframes orb {{ from {{ transform: rotate(0deg) translateX(260px) rotate(0deg); }} to {{ transform: rotate(360deg) translateX(260px) rotate(-360deg); }} }}
        .qr {{ position: fixed; bottom: 30px; right: 30px; background: white; padding: 10px; border-radius: 15px; text-align: center; z-index: 10002; }}
    </style>
    
    <div class="wall-final">
        {stars_html}
        <div class="msg">{config['texte']}</div>
        <div class="hub">
            {"<img src='data:image/png;base64," + logo_b64 + "' class='logo'>" if logo_b64 else ""}
            {photos_html}
        </div>
        <div class="qr">
            <img src="data:image/png;base64,{qr_b64}" width="100"><br>
            <b style="color:black; font-family:sans-serif; font-size:10px;">SCANNEZ POUR VOTER</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. MODE VOTE ---
else:
    st.title("🗳️ Participation")
    st.write("Interface mobile active.")
