import streamlit as st
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

if not os.path.exists(GALLERY_DIR): os.makedirs(GALLERY_DIR)

# --- STYLE CSS CRITIQUE (ANTI-SCROLL & ANTI-FLASH) ---
st.markdown("""
    <style>
    /* Force le noir absolu sur toutes les couches de Streamlit */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .stApp {
        background-color: #000000 !important;
        overflow: hidden !important;
        height: 100vh !important;
        width: 100vw !important;
    }
    /* Supprime les marges qui créent le scroll */
    .main .block-container {
        padding: 0 !important;
        margin: 0 !important;
    }
    /* Masque les outils Streamlit */
    #MainMenu, footer, [data-testid="stDecoration"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

def get_b64(path):
    if os.path.exists(path):
        try:
            with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
        except: return None
    return None

def get_config():
    if os.path.exists(MSG_FILE):
        return pd.read_csv(MSG_FILE).iloc[0].to_dict()
    return {"texte": "✨ ENVOYEZ VOS PHOTOS ! ✨", "couleur": "#FFFFFF", "taille": 50}

params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

# --- 3. INTERFACE ADMIN ---
if est_admin:
    st.title("⚙️ Régie")
    pwd = st.text_input("Code", type="password")
    if pwd == "ADMIN_LIVE_MASTER":
        config = get_config()
        t = st.text_input("Message", config["texte"])
        if st.button("Enregistrer"):
            pd.DataFrame([{"texte": t, "couleur": "#FFFFFF", "taille": 50}]).to_csv(MSG_FILE, index=False)
            st.rerun()
        up = st.file_uploader("Photos", accept_multiple_files=True)
        if up:
            for f in up:
                with open(os.path.join(GALLERY_DIR, f.name), "wb") as file: file.write(f.getbuffer())
            st.rerun()
    else: st.stop()

# --- 4. MODE LIVE ---
elif not mode_vote:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=25000, key="wall_refresh")
    except: pass

    config = get_config()
    logo_b64 = get_b64(LOGO_FILE)
    img_list = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO()
    qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    photos_html = ""
    # On limite à 12 photos pour la fluidité
    for img_path in img_list[-12:]:
        b64 = get_b64(img_path)
        if b64:
            size = random.randint(160, 240)
            top, left = random.randint(5, 75), random.randint(5, 80)
            photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:{size}px; height:{size}px; top:{top}%; left:{left}%; animation-duration:{random.uniform(6,12)}s; animation-delay:-{random.uniform(0,10)}s;">'

    html_code = f"""
    <html>
    <head>
        <style>
            /* LE NOIR DOIT ÊTRE DÉFINI ICI AUSSI */
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body, html {{ background-color: black !important; overflow: hidden; height: 100vh; width: 100vw; font-family: sans-serif; }}
            
            .wall {{ position: relative; width: 100vw; height: 100vh; background: black; }}
            .title {{ position: absolute; top: 4%; width: 100%; text-align: center; color: white; font-size: {config['taille']}px; font-weight: bold; z-index: 100; text-shadow: 0 0 15px rgba(255,255,255,0.5); }}
            
            .center-zone {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 1000; text-align: center; }}
            .logo {{ width: 240px; margin-bottom: 15px; filter: drop-shadow(0 0 15px white); }}
            .qr-box {{ background: white; padding: 10px; border-radius: 15px; display: inline-block; box-shadow: 0 0 20px rgba(255,255,255,0.3); }}
            
            .photo {{ position: absolute; border-radius: 50%; border: 4px solid white; object-fit: cover; animation: float alternate infinite ease-in-out; opacity: 0.9; }}
            @keyframes float {{ from {{ transform: translate(0,0) rotate(0deg); }} to {{ transform: translate(70px, 90px) rotate(10deg); }} }}
        </style>
    </head>
    <body>
        <div class="wall">
            <div class="title">{config['texte']}</div>
            <div class="center-zone">
                {f'<img src="data:image/png;base64,{logo_b64}" class="logo">' if logo_b64 else ''}
                <div class="qr-box">
                    <img src="data:image/png;base64,{qr_b64}" width="110">
                    <div style="color:black; font-size:10px; font-weight:bold; margin-top:5px;">SCANNEZ MOI</div>
                </div>
            </div>
            {photos_html}
        </div>
    </body>
    </html>
    """
    # Le secret est ici : on utilise une hauteur fixe légèrement plus petite que 100vh
    components.html(html_code, height=900, scrolling=False)
