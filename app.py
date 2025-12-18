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
    # On force la récupération des 10 dernières images
    valid_photos = []
    for p in img_list[-10:]:
        data = get_b64(p)
        if data: valid_photos.append(data)

    for i, b64 in enumerate(valid_photos):
        delay = -(i * (25 / max(len(valid_photos), 1)))
        photos_html += f'<img src="data:image/png;base64,{b64}" class="photo-node" style="animation-delay:{delay}s;">'

    # INJECTION CSS & HTML UNIQUE (STRATÉGIE OVERLAY TOTAL)
    st.markdown(f"""
    <style>
        /* Supprime toute trace d'interface Streamlit */
        header, footer, .stAppHeader, [data-testid="stHeader"] {{ display:none !important; visibility: hidden !important; }}
        
        /* Force le fond noir absolu sur l'application */
        .stApp {{ 
            background-color: #050505 !important; 
        }}

        /* Cache les conteneurs de widgets Streamlit qui créent le carré blanc */
        [data-testid="stVerticalBlock"] > div {{
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }}

        /* Le Mur Social qui recouvre TOUT */
        .wall-overlay {{ 
            position: fixed; 
            top: 0; left: 0; 
            width: 100vw; height: 100vh; 
            background: #050505; 
            z-index: 999999; 
            overflow: hidden;
            display: block !important;
        }}

        .star {{ position: absolute; background: white; border-radius: 50%; opacity: 0.5; animation: twi 3s infinite alternate; }}
        @keyframes twi {{ from {{ opacity: 0.2; }} to {{ opacity: 0.8; }} }}
        
        .title-wall {{ 
            position: absolute; top: 8%; width: 100%; text-align: center; 
            font-family: sans-serif; font-weight: bold; z-index: 1000001; 
            color: {config['couleur']}; font-size: {config['taille']}px; 
            text-shadow: 0 0 20px {config['couleur']};
            animation: pulse-text 4s infinite;
        }}
        @keyframes pulse-text {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.02); }} }}

        .orbit-container {{ 
            position: absolute; top: 58%; left: 50%; 
            transform: translate(-50%, -50%); 
            width: 1px; height: 1px; 
            z-index: 1000000; 
        }}

        .logo-main {{ 
            position: absolute; transform: translate(-50%, -50%); 
            width: 220px; height: 220px; object-fit: contain; 
            filter: drop-shadow(0 0 15px {config['couleur']}77); 
        }}

        .photo-node {{ 
            position: absolute; 
            width: 135px; height: 135px; 
            border-radius: 50%; 
            border: 3px solid white; 
            object-fit: cover; 
            box-shadow: 0 0 20px rgba(255,255,255,0.4); 
            animation: orbit-animation 25s linear infinite;
            display: block !important;
        }}

        @keyframes orbit-animation {{ 
            from {{ transform: rotate(0deg) translateX(270px) rotate(0deg); }} 
            to {{ transform: rotate(360deg) translateX(270px) rotate(-360deg); }} 
        }}

        .qr-box {{ 
            position: fixed; bottom: 30px; right: 30px; 
            background: white; padding: 10px; border-radius: 15px; 
            text-align: center; z-index: 1000002; 
        }}
    </style>
    
    <div class="wall-overlay">
        {stars_html}
        <div class="title-wall">{config['texte']}</div>
        <div class="orbit-container">
            {"<img src='data:image/png;base64," + logo_b64 + "' class='logo-main'>" if logo_b64 else ""}
            {photos_html}
        </div>
        <div class="qr-box">
            <img src="data:image/png;base64,{qr_b64}" width="105"><br>
            <b style="color:black; font-family:sans-serif; font-size:10px;">SCANNEZ POUR VOTER</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. MODE VOTE ---
else:
    st.title("🗳️ Participation")
    st.write("Interface mobile active.")
