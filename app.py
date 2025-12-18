import streamlit as st
import pd as pd # Alias court pour éviter les erreurs
import pandas as pd
import os
import glob
import random
import base64
import qrcode
from io import BytesIO
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Social Wall Pro", layout="wide", initial_sidebar_state="collapsed")

GALLERY_DIR = "galerie_images"
LOGO_FILE = "logo_entreprise.png"
MSG_FILE = "live_config.csv"
PWD_FILE = "admin_pwd.txt"
DEFAULT_PWD = "ADMIN_LIVE_MASTER"

if not os.path.exists(GALLERY_DIR): os.makedirs(GALLERY_DIR)
if not os.path.exists(PWD_FILE):
    with open(PWD_FILE, "w") as f: f.write(DEFAULT_PWD)

# --- STYLE CSS RADICAL (BLOQUE LE SCROLL) ---
st.markdown("""
    <style>
    /* Supprime tout scroll possible sur Streamlit */
    #MainMenu, header, footer {display: none !important;}
    [data-testid="stHeader"] {display:none !important;}
    
    /* Bloque le scroll vertical et horizontal sur toutes les couches */
    html, body, [data-testid="stAppViewContainer"], .main, .block-container {
        overflow: hidden !important;
        height: 100vh !important;
        width: 100vw !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Titre Tableau de Bord */
    .sidebar-title {
        text-align: center;
        font-size: 24px;
        font-weight: 900;
        background: linear-gradient(45deg, #ff00cc, #3333ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding-top: 10px;
        margin-bottom: 20px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* Welcome Badge */
    .welcome-header {
        position: fixed;
        top: 20px;
        right: 30px;
        padding: 12px 28px;
        background: rgba(0, 0, 0, 0.85);
        border-radius: 50px;
        border: 2px solid #ff00cc;
        z-index: 9999;
    }
    </style>
""", unsafe_allow_html=True)

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
    return {"texte": "✨ BIENVENUE ✨", "couleur": "#FFFFFF", "taille": 50}

params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

# --- 3. INTERFACE ADMIN ---
if est_admin:
    with open(PWD_FILE, "r") as f: pwd_actuel = f.read().strip()
    with st.sidebar:
        st.markdown('<p class="sidebar-title">Tableau de Bord</p>', unsafe_allow_html=True)
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, use_container_width=True)
        st.divider()
        input_pwd = st.text_input("Code Secret", type="password")
        if input_pwd == pwd_actuel:
            st.markdown('<div class="welcome-header"><span style="color:white;font-weight:bold;">🚀 Bienvenue sur votre Espace de Gestion</span></div>', unsafe_allow_html=True)
            # Paramètres logo, message, photos... (Code identique précédent)
            ul = st.file_uploader("Changer Logo", type=['png','jpg','jpeg'], key="logo_clean")
            if ul: 
                with open(LOGO_FILE, "wb") as f: f.write(ul.getbuffer())
                st.rerun()
            # ... (Ajoutez ici les autres sliders et boutons si besoin)
        else:
            st.stop()
    
    st.subheader("🗑️ Gestion du Flux")
    imgs = sorted(glob.glob(os.path.join(GALLERY_DIR, "*")), key=os.path.getmtime, reverse=True)
    cols = st.columns(6)
    for i, p in enumerate(imgs):
        with cols[i%6]:
            st.image(p, use_container_width=True)
            if st.button("🗑️", key=f"del_{i}"): os.remove(p); st.rerun()

# --- 4. MODE LIVE (SOCIAL WALL) ---
elif not mode_vote:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=20000, key="wall_refresh")
    except: pass

    config = get_config()
    logo_b64 = get_b64(LOGO_FILE)
    img_list = sorted(glob.glob(os.path.join(GALLERY_DIR, "*")), key=os.path.getmtime)
    
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO()
    qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    valid_photos = [get_b64(p) for p in img_list[-15:] if get_b64(p)]
    photos_html = "".join([f'<img src="data:image/png;base64,{b}" class="photo" style="animation-delay:{-(i*(30/max(len(valid_photos),1)))}s;">' for i, b in enumerate(valid_photos)])

    html_code = f"""
    <html>
    <head>
        <style>
            body, html {{ margin: 0; padding: 0; background: #050505; color: white; overflow: hidden !important; height: 100vh; width: 100vw; }}
            .wall {{ position: relative; width: 100vw; height: 100vh; overflow: hidden !important; }}
            .title {{ position: absolute; top: 2%; width: 100%; text-align: center; font-weight: bold; font-size: {config['taille']}px; color: {config['couleur']}; text-shadow: 0 0 25px {config['couleur']}; z-index: 100; }}
            .center-container {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); display: flex; align-items: center; justify-content: center; }}
            .logo {{ width: 220px; height: 220px; object-fit: contain; z-index: 10; filter: drop-shadow(0 0 15px rgba(255,255,255,0.2)); }}
            .photo {{ position: absolute; width: 160px; height: 160px; border-radius: 50%; border: 4px solid white; object-fit: cover; animation: orb 40s linear infinite; }}
            @keyframes orb {{ from {{ transform: rotate(0deg) translateX(320px) rotate(0deg); }} to {{ transform: rotate(360deg) translateX(320px) rotate(-360deg); }} }}
            
            /* FORCE QR CODE EN HAUT A DROITE */
            .qr-fixed {{ 
                position: fixed !important; 
                top: 20px !important; 
                right: 20px !important; 
                background: white !important; 
                padding: 10px !important; 
                border-radius: 15px !important; 
                text-align: center !important; 
                color: black !important; 
                z-index: 9999 !important; 
                width: 120px !important;
                box-shadow: 0 0 20px rgba(255,255,255,0.3) !important;
            }}
        </style>
    </head>
    <body>
        <div class="wall">
            <div class="qr-fixed">
                <img src="data:image/png;base64,{qr_b64}" width="100">
                <div style="font-size:10px; font-weight:bold; margin-top:5px;">SCANNEZ ICI</div>
            </div>
            <div class="title">{config['texte']}</div>
            <div class="center-container">
                {"<img src='data:image/png;base64," + logo_b64 + "' class='logo'>" if logo_b64 else ""}
                {photos_html}
            </div>
        </div>
    </body>
    </html>
    """
    # Augmentation de la hauteur pour couvrir tout l'écran
    components.html(html_code, height=1200, scrolling=False)

# --- 5. MODE VOTE ---
else:
    st.title("🗳️ Participez")
    uf = st.file_uploader("Prenez une photo ✨", type=['jpg', 'jpeg', 'png'])
    if uf:
        fname = f"img_{random.randint(1000,9999)}.jpg"
        with open(os.path.join(GALLERY_DIR, fname), "wb") as f: f.write(uf.getbuffer())
        st.success("Envoyé !")
