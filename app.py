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
st.set_page_config(page_title="Social Wall", layout="wide", initial_sidebar_state="collapsed")

GALLERY_DIR = "galerie_images"
LOGO_FILE = "logo_entreprise.png"
MSG_FILE = "live_config.csv"

# Sécurité : création du dossier
if not os.path.exists(GALLERY_DIR):
    os.makedirs(GALLERY_DIR)

# --- STYLE CSS (FORÇAGE DU NOIR SANS SCROLL) ---
st.markdown("""
    <style>
    /* On élimine tout ce qui n'est pas le mur */
    [data-testid="stHeader"], [data-testid="stDecoration"], footer, #MainMenu {display: none !important;}
    
    html, body, .stApp, [data-testid="stAppViewContainer"] {
        background-color: black !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
        height: 100vh !important;
    }
    .main .block-container { padding: 0 !important; }
    
    /* On force l'iframe à être invisible en cas de scroll */
    iframe { border: none !important; overflow: hidden !important; }
    </style>
""", unsafe_allow_html=True)

def get_b64(path):
    """Récupère l'image en base64 avec gestion d'erreur"""
    if os.path.exists(path) and os.path.getsize(path) > 0:
        try:
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except:
            return None
    return None

# --- 2. LOGIQUE D'ACCÈS ---
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

# --- 3. INTERFACE ADMIN ---
if est_admin:
    st.title("🛠 Administration")
    if st.text_input("Code Secret", type="password") == "ADMIN_LIVE_MASTER":
        st.success("Accès autorisé")
        # Upload Logo
        ul = st.file_uploader("Changer le Logo Central", type=['png', 'jpg'])
        if ul:
            with open(LOGO_FILE, "wb") as f: f.write(ul.getbuffer())
            st.rerun()
        # Upload Photos
        up = st.file_uploader("Ajouter des Photos", accept_multiple_files=True)
        if up:
            for f in up:
                with open(os.path.join(GALLERY_DIR, f.name), "wb") as file: file.write(f.getbuffer())
            st.rerun()
        # Nettoyage
        if st.button("Tout supprimer"):
            for f in glob.glob(os.path.join(GALLERY_DIR, "*")): os.remove(f)
            st.rerun()
    else: st.stop()

# --- 4. MODE LIVE (MUR) ---
elif not mode_vote:
    # Auto-refresh
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=20000, key="wall_refresh")
    except: pass

    # Données
    logo_b64 = get_b64(LOGO_FILE)
    img_list = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO()
    qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    # Génération HTML des photos
    photos_html = ""
    for img_path in img_list[-15:]:
        b64 = get_b64(img_path)
        if b64:
            size = random.randint(160, 240)
            top, left = random.randint(5, 75), random.randint(5, 85)
            # Animation rapide demandée
            duration = random.uniform(5, 10)
            photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:{size}px; height:{size}px; top:{top}%; left:{left}%; animation-duration:{duration}s;">'

    # Code HTML pur
    html_code = f"""
    <!DOCTYPE html>
    <html style="background: black; overflow: hidden;">
    <body style="margin: 0; padding: 0; background: black; overflow: hidden; font-family: sans-serif;">
        <style>
            .container {{ position: relative; width: 100vw; height: 100vh; overflow: hidden; }}
            .center {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 1000; text-align: center; }}
            .logo {{ width: 250px; filter: drop-shadow(0 0 15px rgba(255,255,255,0.5)); margin-bottom: 10px; }}
            .qr {{ background: white; padding: 10px; border-radius: 12px; display: inline-block; box-shadow: 0 0 20px rgba(255,255,255,0.3); }}
            .photo {{ position: absolute; border-radius: 50%; border: 4px solid white; object-fit: cover; animation: move alternate infinite linear; opacity: 0.9; }}
            @keyframes move {{ from {{ transform: translate(0,0); }} to {{ transform: translate(100px, 100px); }} }}
        </style>
        <div class="container">
            <div class="center">
                {f'<img src="data:image/png;base64,{logo_b64}" class="logo">' if logo_b64 else '<div style="color:white; font-weight:bold; font-size:40px;">BIENVENUE</div>'}
                <div class="qr">
                    <img src="data:image/png;base64,{qr_b64}" width="110">
                </div>
            </div>
            {photos_html}
        </div>
    </body>
    </html>
    """
    components.html(html_code, height=1000, scrolling=False)

# --- 5. MODE VOTE ---
else:
    st.title("📸 Envoyez votre photo !")
    f = st.file_uploader("Choisissez une image", type=['jpg', 'jpeg', 'png'])
    if f:
        with open(os.path.join(GALLERY_DIR, f"img_{random.randint(1,9999)}.jpg"), "wb") as out:
            out.write(f.getbuffer())
        st.success("C'est envoyé !")
