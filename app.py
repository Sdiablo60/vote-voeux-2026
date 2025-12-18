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

# --- STYLE CSS RADICAL (TUE LE SCROLL) ---
st.markdown("""
    <style>
    /* 1. Bloque le scroll sur tous les niveaux de Streamlit */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .stApp {
        background-color: #000000 !important;
        overflow: hidden !important;
        height: 100vh !important;
        width: 100vw !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* 2. Supprime spécifiquement le padding blanc/gris en haut */
    .main .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        max-width: 100% !important;
    }

    /* 3. Masque la barre de défilement même si elle veut apparaître */
    ::-webkit-scrollbar {
        display: none !important;
    }

    #MainMenu, footer, [data-testid="stDecoration"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

def get_b64(path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        try:
            with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
        except: return None
    return None

def get_config():
    if os.path.exists(MSG_FILE):
        try: return pd.read_csv(MSG_FILE).iloc[0].to_dict()
        except: pass
    return {"texte": "✨ ENVOYEZ VOS PHOTOS ! ✨", "couleur": "#FFFFFF", "taille": 50}

params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

# --- 3. INTERFACE ADMIN ---
if est_admin:
    st.markdown("<style>html, body, .stApp { overflow: auto !important; }</style>", unsafe_allow_html=True)
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
    for img_path in img_list[-15:]:
        b64 = get_b64(img_path)
        if b64:
            size = random.randint(150, 230)
            top, left = random.randint(5, 75), random.randint(5, 80)
            photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:{size}px; height:{size}px; top:{top}%; left:{left}%; animation-duration:{random.uniform(7,12)}s; animation-delay:-{random.uniform(0,10)}s;">'

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body, html {{ 
                background-color: black !important; 
                overflow: hidden !important; 
                height: 100vh; 
                width: 100vw; 
                font-family: sans-serif; 
            }}
            .wall {{ position: relative; width: 100vw; height: 100vh; background: black; }}
            .title {{ position: absolute; top: 4%; width: 100%; text-align: center; color: white; font-size: {config['taille']}px; font-weight: bold; z-index: 100; text-shadow: 0 0 15px rgba(255,255,255,0.7); }}
            .center-zone {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 1000; text-align: center; display: flex; flex-direction: column; align-items: center; }}
            .logo {{ max-width: 250px; margin-bottom: 20px; filter: drop-shadow(0 0 10px white); }}
            .qr-box {{ background: white; padding: 12px; border-radius: 15px; display: inline-block; box-shadow: 0 0 30px rgba(255,255,255,0.4); }}
            .photo {{ position: absolute; border-radius: 50%; border: 4px solid white; object-fit: cover; animation: float alternate infinite ease-in-out; opacity: 0.9; }}
            @keyframes float {{ from {{ transform: translate(0,0) rotate(0deg); }} to {{ transform: translate(60px, 80px) rotate(8deg); }} }}
        </style>
    </head>
    <body>
        <div class="wall">
            <div class="title">{config['texte']}</div>
            <div class="center-zone">
                {f'<img src="data:image/png;base64,{logo_b64}" class="logo">' if logo_b64 else ''}
                <div class="qr-box">
                    <img src="data:image/png;base64,{qr_b64}" width="120">
                    <p style="color:black; font-size:11px; font-weight:bold; margin-top:5px;">PARTICIPER</p>
                </div>
            </div>
            {photos_html}
        </div>
    </body>
    </html>
    """
    # Le secret : on utilise calc(100vh - 5px) pour être sûr que le conteneur ne déborde jamais
    components.html(html_code, height=None, scrolling=False)
    
    # CSS pour forcer le composant iframe à prendre toute la place
    st.markdown("""
        <style>
        iframe {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw !important;
            height: 100vh !important;
            border: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 5. MODE VOTE ---
else:
    st.title("📸 Envoyez votre photo")
    f = st.file_uploader("Prendre une photo", type=['jpg', 'jpeg', 'png'])
    if f:
        with open(os.path.join(GALLERY_DIR, f"img_{random.randint(1000,9999)}.jpg"), "wb") as out:
            out.write(f.getbuffer())
        st.success("C'est envoyé !")
