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
DEFAULT_PWD = "ADMIN_LIVE_MASTER"

if not os.path.exists(GALLERY_DIR): os.makedirs(GALLERY_DIR)
if not os.path.exists(PWD_FILE):
    with open(PWD_FILE, "w") as f: f.write(DEFAULT_PWD)

# --- STYLE CSS (SUPPRESSION TOTALE DU SCROLL) ---
st.markdown("""
    <style>
    /* Force le noir partout */
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: black !important;
        overflow: hidden !important;
        height: 100vh !important;
        width: 100vw !important;
    }

    /* Supprime les espacements internes de Streamlit qui créent le scroll */
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    
    [data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }

    #MainMenu, footer, [data-testid="stDecoration"] { 
        display: none !important; 
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
        st.title("Admin Wall")
        input_pwd = st.text_input("Code", type="password")
        if input_pwd == pwd_actuel:
            st.success("Connecté")
            config = get_config()
            new_txt = st.text_area("Message", config["texte"])
            new_clr = st.color_picker("Couleur", config["couleur"])
            new_siz = st.slider("Taille", 20, 150, int(config["taille"]))
            if st.button("Appliquer"):
                pd.DataFrame([{"texte": new_txt, "couleur": new_clr, "taille": new_siz}]).to_csv(MSG_FILE, index=False)
                st.rerun()
            ul = st.file_uploader("Logo", type=['png','jpg','jpeg'])
            if ul: 
                with open(LOGO_FILE, "wb") as f: f.write(ul.getbuffer())
                st.rerun()
            uf = st.file_uploader("Photos", type=['png','jpg','jpeg'], accept_multiple_files=True)
            if uf:
                for f in uf:
                    with open(os.path.join(GALLERY_DIR, f.name), "wb") as file: file.write(f.getbuffer())
                st.rerun()
        else: st.stop()
    
    st.markdown("<style>section.main { overflow: auto !important; }</style>", unsafe_allow_html=True) # Scroll autorisé en admin
    imgs = sorted(glob.glob(os.path.join(GALLERY_DIR, "*")), key=os.path.getmtime, reverse=True)
    cols = st.columns(6)
    for i, p in enumerate(imgs):
        with cols[i%6]:
            st.image(p, use_container_width=True)
            if st.button("🗑️", key=f"del_{i}"): os.remove(p); st.rerun()

# --- 4. MODE LIVE ---
elif not mode_vote:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=30000, key="wall_refresh")
    except: pass

    config = get_config()
    logo_b64 = get_b64(LOGO_FILE)
    img_list = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO()
    qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    photos_html = ""
    for i, img_path in enumerate(img_list[-15:]):
        b64 = get_b64(img_path)
        if b64:
            size = random.randint(140, 210)
            top = random.randint(5, 75)
            left = random.randint(5, 80)
            duration = random.uniform(6.0, 10.0)
            delay = random.uniform(0, 8)
            photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:{size}px; height:{size}px; top:{top}%; left:{left}%; animation-duration:{duration}s; animation-delay:-{delay}s;">'

    html_code = f"""
    <html>
    <head>
        <style>
            body, html {{ margin: 0; padding: 0; background: black; overflow: hidden; height: 100vh; width: 100vw; font-family: sans-serif; }}
            .wall {{ position: relative; width: 100vw; height: 100vh; background: black; }}
            .title {{ position: absolute; top: 2%; width: 100%; text-align: center; font-weight: bold; font-size: {config['taille']}px; color: {config['couleur']}; text-shadow: 0 0 20px {config['couleur']}aa; z-index: 100; }}
            .center-block {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); display: flex; flex-direction: column; align-items: center; gap: 8px; z-index: 1000; }}
            .logo {{ width: 220px; filter: drop-shadow(0 0 20px rgba(255,255,255,0.4)); }}
            .qr-zone {{ background: white; padding: 8px; border-radius: 12px; text-align: center; width: 95px; }}
            .photo {{ position: absolute; border-radius: 50%; border: 3px solid white; object-fit: cover; animation: floatAround linear infinite alternate; opacity: 0.9; }}
            @keyframes floatAround {{ 0% {{ transform: translate(0,0) rotate(0deg); }} 100% {{ transform: translate(60px, 80px) rotate(8deg); }} }}
        </style>
    </head>
    <body>
        <div class="wall">
            <div class="title">{config['texte']}</div>
            <div class="center-block">
                {"<img src='data:image/png;base64," + logo_b64 + "' class='logo'>" if logo_b64 else ""}
                <div class="qr-zone"><img src="data:image/png;base64,{qr_b64}" width="85"></div>
            </div>
            {photos_html}
        </div>
    </body>
    </html>
    """
    # Réduction de la hauteur à 98vh pour s'assurer que ça ne dépasse pas
    components.html(html_code, height=900, scrolling=False)

# --- 5. MODE VOTE ---
else:
    st.title("🗳️ Participez")
    uf = st.file_uploader("Prenez une photo ✨", type=['jpg', 'jpeg', 'png'])
    if uf:
        fname = f"img_{random.randint(1000,9999)}.jpg"
        with open(os.path.join(GALLERY_DIR, fname), "wb") as f: f.write(uf.getbuffer())
        st.success("Photo envoyée !")
