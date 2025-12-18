import streamlit as st
import pandas as pd
import os
import glob
import random
import base64
import qrcode
from io import BytesIO
import streamlit.components.v1 as components

# --- CONFIGURATION ---
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

# --- LOGIQUE ---
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

if est_admin:
    st.title("🛠️ Console Régie Master")
    pwd_actuel = open(PWD_FILE).read().strip() if os.path.exists(PWD_FILE) else "ADMIN_VOEUX_2026"
    with st.sidebar:
        input_pwd = st.text_input("Code Secret", type="password")
    if input_pwd != pwd_actuel:
        st.warning("Code requis.")
        st.stop()

    if os.path.exists(MSG_FILE): config = pd.read_csv(MSG_FILE).iloc[0].to_dict()
    else: config = {"texte": "✨ BIENVENUE ✨", "couleur": "#FFFFFF", "taille": 45}
    
    t1, t2 = st.tabs(["💬 Config", "🖼️ Médias"])
    with t1:
        txt = st.text_area("Message", config["texte"])
        clr = st.color_picker("Couleur", config["couleur"])
        siz = st.slider("Taille", 20, 100, int(config["taille"]))
        if st.button("🚀 Enregistrer"):
            pd.DataFrame([{"texte": txt, "couleur": clr, "taille": siz}]).to_csv(MSG_FILE, index=False)
            st.rerun()
    with t2:
        ul = st.file_uploader("Logo", type=['png','jpg','jpeg'])
        if ul:
            with open(LOGO_FILE, "wb") as f: f.write(ul.getbuffer())
            st.rerun()
        uf = st.file_uploader("Photos", type=['png','jpg','jpeg'], accept_multiple_files=True)
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

elif not mode_vote:
    if os.path.exists(MSG_FILE): config = pd.read_csv(MSG_FILE).iloc[0].to_dict()
    else: config = {"texte": "✨ BIENVENUE ✨", "couleur": "#FFFFFF", "taille": 45}
    
    logo_b64 = get_b64(LOGO_FILE)
    img_list = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO()
    qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    stars_html = "".join([f'<div class="star" style="top:{random.randint(0,100)}%; left:{random.randint(0,100)}%; width:2px; height:2px; animation-delay:{random.random()*3}s;"></div>' for _ in range(70)])
    
    valid_photos = [get_b64(p) for p in img_list[-12:] if get_b64(p)]
    photos_html = "".join([f'<img src="data:image/png;base64,{b}" class="photo" style="animation-delay:{-(i*(30/max(len(valid_photos),1)))}s;">' for i, b in enumerate(valid_photos)])

    html_code = f"""
    <html>
    <head>
        <style>
            body, html {{ margin: 0; padding: 0; background-color: #050505; color: white; overflow: hidden; font-family: sans-serif; height: 100%; width: 100%; }}
            .wall {{ position: relative; width: 100vw; height: 100vh; overflow: hidden; }}
            .star {{ position: absolute; background: white; border-radius: 50%; opacity: 0.3; animation: twi 2s infinite alternate; }}
            @keyframes twi {{ from {{ opacity: 0.1; }} to {{ opacity: 0.8; }} }}
            
            .title {{ position: absolute; top: 1%; width: 100%; text-align: center; font-weight: bold; font-size: {config['taille']}px; color: {config['couleur']}; text-shadow: 0 0 25px {config['couleur']}; z-index: 100; }}
            
            /* CENTRE REMONTÉ À 42% */
            .center-container {{ position: absolute; top: 42%; left: 50%; transform: translate(-50%, -50%); display: flex; align-items: center; justify-content: center; }}
            
            .logo {{ width: 190px; height: 190px; object-fit: contain; filter: drop-shadow(0 0 20px {config['couleur']}66); z-index: 10; }}
            
            .photo {{ position: absolute; width: 135px; height: 135px; border-radius: 50%; border: 3px solid white; object-fit: cover; box-shadow: 0 0 20px rgba(255,255,255,0.4); animation: orb 30s linear infinite; }}
            
            /* RAYON AJUSTÉ À 260px POUR ÉVITER LES COUPURES */
            @keyframes orb {{ 
                from {{ transform: rotate(0deg) translateX(260px) rotate(0deg); }} 
                to {{ transform: rotate(360deg) translateX(260px) rotate(-360deg); }} 
            }}
            
            .qr {{ position: absolute; bottom: 25px; right: 25px; background: white; padding: 10px; border-radius: 12px; text-align: center; color: black; z-index: 200; box-shadow: 0 0 15px rgba(255,255,255,0.2); }}
        </style>
    </head>
    <body>
        <div class="wall">
            {stars_html}
            <div class="title">{config['texte']}</div>
            <div class="center-container">
                {"<img src='data:image/png;base64," + logo_b64 + "' class='logo'>" if logo_b64 else ""}
                {photos_html}
            </div>
            <div class="qr">
                <img src="data:image/png;base64,{qr_b64}" width="95"><br>
                <span style="font-size:10px; font-weight:bold;">SCANNEZ POUR VOTER</span>
            </div>
        </div>
    </body>
    </html>
    """
    
    st.markdown("""
        <style>
            [data-testid="stHeader"], footer {display:none !important;}
            .stApp {background:black !important; overflow: hidden !important;}
            iframe {border: none !important;}
            .block-container {padding: 0 !important; max-width: 100% !important;}
        </style>
    """, unsafe_allow_html=True)
    
    components.html(html_code, height=980, scrolling=False)

else:
    st.title("🗳️ Participation")
