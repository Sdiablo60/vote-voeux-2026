import streamlit as st

# --- 0. PRIORITÉ ABSOLUE : FORCER LE NOIR AVANT TOUT ---
st.markdown("""
    <style>
    :root { background-color: #000000 !important; }
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #000000 !important;
        background: #000000 !important;
    }
    </style>
""", unsafe_allow_html=True)

import pandas as pd  # Correction ici : pandas as pd
import os
import glob
import random
import base64
import qrcode
from io import BytesIO
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Social Wall", layout="wide", initial_sidebar_state="collapsed")

GALLERY_DIR = "galerie_images"
LOGO_FILE = "logo_entreprise.png"
if not os.path.exists(GALLERY_DIR): os.makedirs(GALLERY_DIR)

# --- 2. STYLE CSS COMPLET ---
st.markdown("""
    <style>
    [data-testid="stHeader"], footer, #MainMenu, [data-testid="stDecoration"] { display: none !important; }
    
    html, body, [data-testid="stAppViewContainer"], .stApp {
        overflow: hidden !important;
        height: 100vh !important;
        width: 100vw !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    iframe {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        border: none !important;
        background-color: #000000 !important;
        z-index: 9999;
    }
    .main .block-container { padding: 0 !important; }
    </style>
""", unsafe_allow_html=True)

def get_b64(path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        try:
            with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
        except: return None
    return None

params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

# --- 3. INTERFACE ADMIN ---
if est_admin:
    st.markdown("<style>html, body, .stApp { overflow: auto !important; position: relative !important; color: white !important; }</style>", unsafe_allow_html=True)
    st.title("⚙️ Administration")
    if st.text_input("Code Secret", type="password") == "ADMIN_LIVE_MASTER":
        st.success("Accès autorisé")
        ul = st.file_uploader("Charger le Logo", type=['png', 'jpg'])
        if ul:
            with open(LOGO_FILE, "wb") as f: f.write(ul.getbuffer())
            st.rerun()
        up = st.file_uploader("Ajouter des Photos", accept_multiple_files=True)
        if up:
            for f in up:
                with open(os.path.join(GALLERY_DIR, f.name), "wb") as file: file.write(f.getbuffer())
            st.rerun()
    else: st.stop()

# --- 4. MODE LIVE (MUR) ---
elif not mode_vote:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=25000, key="wall_refresh")
    except: pass

    logo_b64 = get_b64(LOGO_FILE)
    img_list = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
    # URL dynamique pour le QR Code
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO()
    qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    photos_html = ""
    for img_path in img_list[-15:]:
        b64 = get_b64(img_path)
        if b64:
            size = random.randint(160, 240)
            top, left = random.randint(5, 75), random.randint(5, 85)
            duration = random.uniform(6, 12)
            photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:{size}px; height:{size}px; top:{top}%; left:{left}%; animation-duration:{duration}s;">'

    html_code = f"""
    <!DOCTYPE html>
    <html style="background: black;">
    <body style="margin: 0; padding: 0; background: black; overflow: hidden; height: 100vh; width: 100vw; opacity: 0; animation: fadeIn 1.5s forwards;">
        <style>
            @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
            .container {{ position: relative; width: 100vw; height: 100vh; background: black; overflow: hidden; }}
            
            .center-stack {{ 
                position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                z-index: 1000; display: flex; flex-direction: column; align-items: center; gap: 20px; 
            }}
            .logo {{ max-width: 260px; filter: drop-shadow(0 0 15px white); }}
            .qr-box {{ background: white; padding: 12px; border-radius: 15px; text-align: center; box-shadow: 0 0 30px rgba(255,255,255,0.4); }}
            
            .photo {{ position: absolute; border-radius: 50%; border: 4px solid white; object-fit: cover; animation: move alternate infinite ease-in-out; opacity: 0.9; }}
            @keyframes move {{ from {{ transform: translate(0,0) rotate(0deg); }} to {{ transform: translate(60px, 90px) rotate(10deg); }} }}
        </style>
        <div class="container">
            <div class="center-stack">
                {f'<img src="data:image/png;base64,{logo_b64}" class="logo">' if logo_b64 else '<div style="color:white; font-size:40px; font-weight:bold;">SOCIAL WALL</div>'}
                <div class="qr-box">
                    <img src="data:image/png;base64,{qr_b64}" width="120">
                    <p style="color:black; font-size:10px; font-weight:bold; margin-top:5px; font-family:sans-serif;">SCANNEZ MOI</p>
                </div>
            </div>
            {photos_html}
        </div>
    </body>
    </html>
    """
    components.html(html_code)

# --- 5. MODE VOTE ---
else:
    st.markdown("<style>html, body, .stApp { background-color: #111 !important; color: white !important; overflow: auto !important; }</style>", unsafe_allow_html=True)
    st.title("📸 Envoyez votre photo")
    f = st.file_uploader("Image", type=['jpg', 'jpeg', 'png'])
    if f:
        with open(os.path.join(GALLERY_DIR, f"img_{random.randint(1,9999)}.jpg"), "wb") as out:
            out.write(f.getbuffer())
        st.success("C'est envoyé !")
