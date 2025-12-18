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

# --- STYLE CSS (PURGE TOTALE DU BLANC) ---
st.markdown("""
    <style>
    /* On force le noir sur la racine absolue */
    :root { background-color: black !important; }
    
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: black !important;
        background: black !important;
        overflow: hidden !important;
        height: 100vh !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    .main .block-container { padding: 0 !important; }
    #MainMenu, footer, [data-testid="stDecoration"] { display: none !important; }
    
    /* On s'assure que l'iframe du mur occupe tout l'espace sans créer de scroll */
    iframe {
        border: none !important;
        width: 100vw !important;
        height: 100vh !important;
    }
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
    pwd = st.text_input("Code Master", type="password")
    if pwd == "ADMIN_LIVE_MASTER":
        st.success("Accès validé")
        config = get_config()
        t = st.text_input("Message", config["texte"])
        if st.button("Mettre à jour"):
            pd.DataFrame([{"texte": t, "couleur": "#FFFFFF", "taille": 50}]).to_csv(MSG_FILE, index=False)
            st.rerun()
        
        up = st.file_uploader("Ajouter Photos", accept_multiple_files=True)
        if up:
            for f in up:
                with open(os.path.join(GALLERY_DIR, f.name), "wb") as file: file.write(f.getbuffer())
            st.rerun()
        
        if st.button("🗑️ Vider la galerie"):
            for f in glob.glob(os.path.join(GALLERY_DIR, "*")): os.remove(f)
            st.rerun()
    else: st.stop()

# --- 4. MODE LIVE ---
elif not mode_vote:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=20000, key="wall_refresh")
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
            top, left = random.randint(5, 70), random.randint(5, 80)
            photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:{size}px; height:{size}px; top:{top}%; left:{left}%; animation-duration:{random.uniform(8,15)}s; animation-delay:-{random.uniform(0,10)}s;">'

    html_code = f"""
    <!DOCTYPE html>
    <html style="background: black;">
    <body style="margin: 0; padding: 0; background: black; overflow: hidden;">
        <style>
            .wall {{ position: relative; width: 100vw; height: 100vh; background: black; font-family: sans-serif; overflow: hidden; }}
            .title {{ position: absolute; top: 4%; width: 100%; text-align: center; color: white; font-size: {config['taille']}px; font-weight: bold; z-index: 100; text-shadow: 0 0 15px rgba(255,255,255,0.7); }}
            .center {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 1000; text-align: center; }}
            .logo {{ max-width: 240px; margin-bottom: 20px; filter: drop-shadow(0 0 10px white); }}
            .qr-box {{ background: white; padding: 10px; border-radius: 15px; display: inline-block; }}
            .photo {{ position: absolute; border-radius: 50%; border: 4px solid white; object-fit: cover; animation: float alternate infinite ease-in-out; opacity: 0.9; }}
            @keyframes float {{ from {{ transform: translate(0,0) rotate(0deg); }} to {{ transform: translate(50px, 70px) rotate(8deg); }} }}
        </style>
        <div class="wall">
            <div class="title">{config['texte']}</div>
            <div class="center">
                {f'<img src="data:image/png;base64,{logo_b64}" class="logo">' if logo_b64 else ''}
                <div class="qr-box">
                    <img src="data:image/png;base64,{qr_b64}" width="110">
                </div>
            </div>
            {photos_html}
        </div>
    </body>
    </html>
    """
    # Hauteur définie à 100vh via CSS pour éviter le scroll
    components.html(html_code, height=2000) # Hauteur virtuelle large mais bridée par le CSS

# --- 5. MODE VOTE ---
else:
    st.title("📸 Photo")
    f = st.file_uploader("Envoyer une photo", type=['jpg', 'jpeg', 'png'])
    if f:
        with open(os.path.join(GALLERY_DIR, f"img_{random.randint(1000,9999)}.jpg"), "wb") as out:
            out.write(f.getbuffer())
        st.success("Reçu !")
