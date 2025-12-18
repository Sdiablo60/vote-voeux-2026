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
PWD_FILE = "admin_pwd.txt"

if not os.path.exists(GALLERY_DIR): os.makedirs(GALLERY_DIR)

# --- STYLE CSS ANTI-ÉCRAN NOIR ---
st.markdown("""
    <style>
    html, body, .stApp, [data-testid="stAppViewContainer"] {
        background-color: black !important;
        overflow: hidden !important;
    }
    .main .block-container { padding: 0 !important; }
    #MainMenu, footer, [data-testid="stHeader"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

def get_b64(path):
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

def get_config():
    if os.path.exists(MSG_FILE):
        return pd.read_csv(MSG_FILE).iloc[0].to_dict()
    return {"texte": "✨ EN ATTENTE DE PHOTOS ✨", "couleur": "#FFFFFF", "taille": 50}

params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

# --- 3. INTERFACE ADMIN ---
if est_admin:
    st.title("⚙️ Administration")
    pwd = st.text_input("Mot de passe", type="password")
    if pwd == "ADMIN_LIVE_MASTER":
        config = get_config()
        new_txt = st.text_input("Message", config["texte"])
        if st.button("Mettre à jour"):
            pd.DataFrame([{"texte": new_txt, "couleur": "#FFFFFF", "taille": 50}]).to_csv(MSG_FILE, index=False)
            st.rerun()
        
        up = st.file_uploader("Ajouter des photos", accept_multiple_files=True)
        if up:
            for f in up:
                with open(os.path.join(GALLERY_DIR, f.name), "wb") as file: file.write(f.getbuffer())
            st.rerun()
        
        imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
        for p in imgs:
            if st.button(f"Supprimer {os.path.basename(p)}"):
                os.remove(p)
                st.rerun()
    else: st.stop()

# --- 4. MODE LIVE ---
elif not mode_vote:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=30000, key="refresh")
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
            size, top, left = random.randint(150, 220), random.randint(10, 70), random.randint(10, 80)
            photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:{size}px; height:{size}px; top:{top}%; left:{left}%; animation-duration:{random.randint(5,10)}s;">'

    html_code = f"""
    <html>
    <head>
        <style>
            body {{ background: black; color: white; margin: 0; overflow: hidden; font-family: sans-serif; }}
            .wall {{ position: relative; width: 100vw; height: 100vh; }}
            .title {{ position: absolute; top: 5%; width: 100%; text-align: center; font-size: {config['taille']}px; z-index: 100; }}
            .center {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 1000; text-align: center; }}
            .qr {{ background: white; padding: 10px; border-radius: 10px; margin-top: 10px; display: inline-block; }}
            .photo {{ position: absolute; border-radius: 50%; border: 3px solid white; animation: move alternate infinite ease-in-out; }}
            @keyframes move {{ from {{ transform: translate(0,0); }} to {{ transform: translate(50px, 50px); }} }}
        </style>
    </head>
    <body>
        <div class="wall">
            <div class="title">{config['texte']}</div>
            <div class="center">
                {f'<img src="data:image/png;base64,{logo_b64}" width="200">' if logo_b64 else ''}
                <div class="qr"><img src="data:image/png;base64,{qr_b64}" width="100"><br><b style="color:black; font-size:10px;">PARTICIPER</b></div>
            </div>
            {photos_html}
        </div>
    </body>
    </html>
    """
    components.html(html_code, height=1000)

# --- 5. MODE VOTE ---
else:
    st.title("📸 Envoyez votre photo !")
    f = st.file_uploader("Prendre une photo", type=['jpg', 'png'])
    if f:
        with open(os.path.join(GALLERY_DIR, f"img_{random.randint(1,999)}.jpg"), "wb") as img_file:
            img_file.write(f.getbuffer())
        st.success("Reçu ! Regardez l'écran !")
