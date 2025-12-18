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
    current_pwd = open(PWD_FILE).read().strip() if os.path.exists(PWD_FILE) else "ADMIN_VOEUX_2026"
    with st.sidebar:
        input_pwd = st.text_input("Code Secret", type="password")
    
    if input_pwd != current_pwd:
        st.warning("Code requis dans la sidebar.")
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

# --- 4. MODE LIVE (SOCIAL WALL) ---
elif not mode_vote:
    config = {"texte": "✨ BIENVENUE ✨", "couleur": "#FFFFFF", "taille": 45}
    if os.path.exists(MSG_FILE): 
        try: config = pd.read_csv(MSG_FILE).iloc[0].to_dict()
        except: pass
    
    logo_b64 = get_b64(LOGO_FILE)
    img_list = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
    # QR Code
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO()
    qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    # Préparation des photos (limité à 8 pour la fluidité)
    photos_html = ""
    last_photos = img_list[-8:]
    for i, p_path in enumerate(last_photos):
        b64 = get_b64(p_path)
        if b64:
            delay = -(i * (20 / max(len(last_photos), 1)))
            photos_html += f'<img src="data:image/png;base64,{b64}" class="photo-bubble" style="animation-delay:{delay}s;">'

    # INJECTION DIRECTE SANS f-string POUR LE CSS (Évite les bugs d'accolades)
    st.markdown("""
    <style>
        /* Masquage des éléments Streamlit */
        header, footer, .stAppHeader, [data-testid="stHeader"] { visibility: hidden !important; }
        .stApp { background-color: #050505 !important; }

        /* Conteneur principal Social Wall */
        .planetarium {
            position: fixed;
            top: 0; left: 0;
            width: 100vw; height: 100vh;
            background: radial-gradient(circle at center, #1a1a1a 0%, #050505 100%);
            z-index: 999999;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }

        .wall-title {
            position: absolute; top: 10%;
            font-family: 'Segoe UI', sans-serif;
            font-weight: 800;
            text-align: center;
            z-index: 100;
        }

        .orbit-zone {
            position: relative;
            width: 1px; height: 1px;
            display: flex; justify-content: center; align-items: center;
        }

        .main-logo {
            width: 200px; height: 200px;
            object-fit: contain;
            z-index: 50;
        }

        .photo-bubble {
            position: absolute;
            width: 130px; height: 130px;
            border-radius: 50%;
            border: 3px solid white;
            object-fit: cover;
            box-shadow: 0 0 15px rgba(255,255,255,0.3);
            animation: moveOrbit 20s linear infinite;
        }

        @keyframes moveOrbit {
            from { transform: rotate(0deg) translateX(250px) rotate(0deg); }
            to { transform: rotate(360deg) translateX(250px) rotate(-360deg); }
        }

        .qr-anchor {
            position: fixed; bottom: 30px; right: 30px;
            background: white; padding: 10px; border-radius: 12px;
            text-align: center; z-index: 150;
        }
    </style>
    """, unsafe_allow_html=True)

    # Rendu du contenu avec les variables Python
    st.markdown(f"""
    <div class="planetarium">
        <div class="wall-title" style="color:{config['couleur']}; font-size:{config['taille']}px; text-shadow: 0 0 20px {config['couleur']}99;">
            {config['texte']}
        </div>
        
        <div class="orbit-zone">
            {"<img src='data:image/png;base64," + logo_b64 + "' class='main-logo'>" if logo_b64 else ""}
            {photos_html}
        </div>

        <div class="qr-anchor">
            <img src="data:image/png;base64,{qr_b64}" width="100"><br>
            <b style="color:black; font-family:sans-serif; font-size:10px;">SCANNEZ POUR VOTER</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    st.title("🗳️ Participation")
