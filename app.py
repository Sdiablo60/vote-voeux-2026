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
st.set_page_config(page_title="Social Wall 2026", layout="wide", initial_sidebar_state="collapsed")

GALLERY_DIR = "galerie_images"
LOGO_FILE = "logo_entreprise.png"
MSG_FILE = "live_config.csv"
PWD_FILE = "admin_pwd.txt"
DEFAULT_PWD = "ADMIN_VOEUX_2026"

if not os.path.exists(GALLERY_DIR): os.makedirs(GALLERY_DIR)
if not os.path.exists(PWD_FILE):
    with open(PWD_FILE, "w") as f: f.write(DEFAULT_PWD)

# --- CSS POUR NETTOYER L'UPLOADER DE LOGO ---
# Ce bloc supprime "Drag and drop", la limite de taille et renomme le bouton
st.markdown("""
    <style>
    /* Masquer le texte "Drag and drop" et la limite de taille dans la sidebar */
    [data-testid="stSidebar"] section[data-testid="stFileUploadDropzone"] div div {
        display: none !important;
    }
    /* Supprimer la bordure et le fond gris du cadre d'upload pour qu'il soit transparent */
    [data-testid="stSidebar"] section[data-testid="stFileUploadDropzone"] {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
    }
    /* Modifier le texte du bouton "Browse files" */
    [data-testid="stSidebar"] button[kind="secondary"] div:before {
        content: "Importer un nouveau logo" !important;
    }
    [data-testid="stSidebar"] button[kind="secondary"] div {
        font-size: 0 !important;
    }
    [data-testid="stSidebar"] button[kind="secondary"] div:before {
        font-size: 16px !important;
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

# --- 2. LOGIQUE D'ACCÈS ---
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

# --- 3. INTERFACE ADMIN ---
if est_admin:
    with open(PWD_FILE, "r") as f:
        pwd_actuel = f.read().strip()

    with st.sidebar:
        # 1. LOGO EN PREMIER (VISUEL)
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, use_container_width=True)
        
        # 2. BOUTON D'IMPORTATION ÉPURÉ (SANS TEXTES PAR DÉFAUT)
        ul = st.file_uploader("", type=['png','jpg','jpeg'], key="logo_clean")
        if ul:
            with open(LOGO_FILE, "wb") as f: f.write(ul.getbuffer())
            st.rerun()

        st.divider()
        
        # 3. SÉCURITÉ
        st.header("🔑 Sécurité")
        input_pwd = st.text_input("Code Secret", type="password")
        
        if input_pwd == pwd_actuel:
            st.success("Déverrouillé")
            
            st.divider()
            st.header("💬 Message")
            config = get_config()
            new_txt = st.text_area("Texte", config["texte"])
            new_clr = st.color_picker("Couleur", config["couleur"])
            new_siz = st.slider("Taille", 20, 150, int(config["taille"]))
            if st.button("🚀 Appliquer"):
                pd.DataFrame([{"texte": new_txt, "couleur": new_clr, "taille": new_siz}]).to_csv(MSG_FILE, index=False)
                st.rerun()

            st.divider()
            st.header("📸 Photos")
            uf = st.file_uploader("Ajouter Photos", type=['png','jpg','jpeg'], accept_multiple_files=True)
            if uf:
                for f in uf:
                    with open(os.path.join(GALLERY_DIR, f.name), "wb") as file: file.write(f.getbuffer())
                st.rerun()

            st.divider()
            with st.expander("⚙️ Options"):
                new_pwd = st.text_input("Nouveau MDP", type="password")
                if st.button("💾 Sauver"):
                    with open(PWD_FILE, "w") as f: f.write(new_pwd); st.rerun()
                st.info(f"Défaut: {DEFAULT_PWD}")
                if st.button("♻️ Reset"):
                    with open(PWD_FILE, "w") as f: f.write(DEFAULT_PWD); st.rerun()
        else:
            st.stop()

    st.subheader("🗑️ Galerie Live")
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    cols = st.columns(6)
    for i, p in enumerate(imgs):
        with cols[i%6]:
            st.image(p, use_container_width=True)
            if st.button("Supprimer", key=f"del_{i}"):
                os.remove(p); st.rerun()

# --- 4. MODE LIVE (SOCIAL WALL) ---
elif not mode_vote:
    st.markdown("""<style>#MainMenu, header, footer {display: none !important;} .stApp {background:black !important;}</style>""", unsafe_allow_html=True)
    
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=30000, key="wall_refresh")
    except:
        st.fragment(run_every=30)(lambda: st.rerun())()

    config = get_config()
    logo_b64 = get_b64(LOGO_FILE)
    img_list = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO()
    qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    valid_photos = [get_b64(p) for p in img_list[-12:] if get_b64(p)]
    photos_html = "".join([f'<img src="data:image/png;base64,{b}" class="photo" style="animation-delay:{-(i*(30/max(len(valid_photos),1)))}s;">' for i, b in enumerate(valid_photos)])

    html_code = f"""
    <html>
    <head>
        <style>
            body, html {{ margin: 0; padding: 0; background-color: #050505; color: white; overflow: hidden; font-family: sans-serif; height: 100%; width: 100%; }}
            .wall {{ position: relative; width: 100vw; height: 100vh; overflow: hidden; }}
            .title {{ position: absolute; top: 0.5%; width: 100%; text-align: center; font-weight: bold; font-size: {config['taille']}px; color: {config['couleur']}; text-shadow: 0 0 25px {config['couleur']}; z-index: 100; }}
            .center-container {{ position: absolute; top: 38%; left: 50%; transform: translate(-50%, -50%); display: flex; align-items: center; justify-content: center; }}
            .logo {{ width: 170px; height: 170px; object-fit: contain; filter: drop-shadow(0 0 15px {config['couleur']}77); z-index: 10; }}
            .photo {{ position: absolute; width: 120px; height: 120px; border-radius: 50%; border: 3px solid white; object-fit: cover; box-shadow: 0 0 15px rgba(255,255,255,0.3); animation: orb 30s linear infinite; }}
            @keyframes orb {{ from {{ transform: rotate(0deg) translateX(230px) rotate(0deg); }} to {{ transform: rotate(360deg) translateX(230px) rotate(-360deg); }} }}
            .qr {{ position: absolute; bottom: 25px; right: 25px; background: white; padding: 10px; border-radius: 12px; text-align: center; color: black; z-index: 200; }}
        </style>
    </head>
    <body><div class="wall"><div class="title">{config['texte']}</div><div class="center-container">{"<img src='data:image/png;base64," + logo_b64 + "' class='logo'>" if logo_b64 else ""}{photos_html}</div><div class="qr"><img src="data:image/png;base64,{qr_b64}" width="95"><br><span style="font-size:10px; font-weight:bold;">SCANNEZ POUR PARTICIPER</span></div></div></body>
    </html>
    """
    components.html(html_code, height=980, scrolling=False)

# --- 5. MODE VOTE ---
else:
    st.title("🗳️ Participez")
    uf = st.file_uploader("Photo ✨", type=['jpg', 'jpeg', 'png'])
    if uf:
        with open(os.path.join(GALLERY_DIR, uf.name), "wb") as f: f.write(uf.getbuffer())
        st.success("Envoyé !")
