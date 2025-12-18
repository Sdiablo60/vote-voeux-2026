import streamlit as st
import pandas as pd
import os
import glob
import random
import base64
import qrcode
from io import BytesIO

# --- 1. CONFIGURATION & ÉTAT ---
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

sidebar_state = "expanded" if est_admin else "collapsed"
st.set_page_config(page_title="Social Wall 2026", layout="wide", initial_sidebar_state=sidebar_state)

GALLERY_DIR = "galerie_images"
LOGO_FILE = "logo_entreprise.png"
MSG_FILE = "live_config.csv"
PWD_FILE = "admin_pwd.txt"

for d in [GALLERY_DIR]:
    if not os.path.exists(d): os.makedirs(d)

def get_b64(path):
    try:
        if os.path.exists(path):
            with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return ""
    return ""

def get_config():
    if os.path.exists(MSG_FILE): return pd.read_csv(MSG_FILE).iloc[0].to_dict()
    return {"texte": "✨ BIENVENUE AUX VOEUX 2026 ✨", "couleur": "#FFFFFF", "taille": 48}

def get_admin_pwd():
    if os.path.exists(PWD_FILE):
        with open(PWD_FILE, "r") as f: return f.read().strip()
    return "ADMIN_VOEUX_2026"

# --- 2. INTERFACE ADMIN ---
if est_admin:
    st.title("🛠️ Console Régie Master")
    current_pwd = get_admin_pwd()
    
    with st.sidebar:
        st.header("🔑 Contrôle Accès")
        input_pwd = st.text_input("Code Admin", type="password")
        
        auth = (input_pwd == current_pwd)
        
        if auth:
            st.success("Accès Autorisé")
            st.divider()
            st.header("⚙️ Paramètres Avancés")
            new_pwd = st.text_input("Nouveau mot de passe", type="password")
            if st.button("Modifier le code"):
                with open(PWD_FILE, "w") as f: f.write(new_pwd)
                st.rerun()
            if st.button("🚨 RESET TOTAL"):
                for f in glob.glob(os.path.join(GALLERY_DIR, "*")): os.remove(f)
                if os.path.exists(LOGO_FILE): os.remove(LOGO_FILE)
                st.rerun()
        else:
            st.warning("Veuillez vous connecter")

    if auth:
        config = get_config()
        t1, t2 = st.tabs(["💬 Message & Design", "🖼️ Médias"])
        
        with t1:
            col_text, col_style = st.columns(2)
            new_texte = col_text.text_area("Texte du message", config["texte"])
            new_couleur = col_style.color_picker("Couleur", config["couleur"])
            new_taille = col_style.slider("Taille (px)", 20, 100, int(config["taille"]))
            if st.button("🚀 Mettre à jour le Mur"):
                pd.DataFrame([{"texte": new_texte, "couleur": new_couleur, "taille": new_taille}]).to_csv(MSG_FILE, index=False)
                st.rerun()

        with t2:
            c1, c2 = st.columns(2)
            ul = c1.file_uploader("Logo Central", type=['png','jpg','jpeg'])
            if ul: 
                with open(LOGO_FILE, "wb") as f: f.write(ul.getbuffer())
                st.rerun()
            uf = c2.file_uploader("Ajouter des photos", type=['png','jpg','jpeg'], accept_multiple_files=True)
            if uf:
                for f in uf:
                    with open(os.path.join(GALLERY_DIR, f.name), "wb") as file: file.write(f.getbuffer())
                st.rerun()
            
            st.divider()
            imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
            if imgs:
                cols = st.columns(6)
                for i, p in enumerate(imgs):
                    with cols[i % 6]:
                        st.image(p, use_container_width=True)
                        if st.button("🗑️", key=f"del_{i}"):
                            os.remove(p)
                            st.rerun()

# --- 3. MODE LIVE (SOCIAL WALL) ---
elif not mode_vote:
    config = get_config()
    logo_data = get_b64(LOGO_FILE)
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_img = qrcode.make(qr_url)
    buf = BytesIO()
    qr_img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    # --- INJECTION CSS SÉCURISÉE (SANS F-STRING POUR ÉVITER LE CARRÉ BLANC) ---
    st.markdown("""
        <style>
            [data-testid="stHeader"], footer, header { display:none !important; }
            .stApp { background-color: #050505 !important; }
            .main-container { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; overflow: hidden; background: #050505; }
            .star { position: absolute; background: white; border-radius: 50%; opacity: 0.5; animation: twinkle 3s infinite alternate; }
            @keyframes twinkle { from { opacity: 0.2; } to { opacity: 0.8; } }
            .welcome-title { position: absolute; top: 7%; width: 100%; text-align: center; font-family: sans-serif; font-weight: bold; animation: pulse-text 4s ease-in-out infinite; }
            @keyframes pulse-text { 0% { transform: scale(1); opacity: 0.8; } 50% { transform: scale(1.02); opacity: 1; } 100% { transform: scale(1); opacity: 0.8; } }
            .center-point { position: absolute; top: 58%; left: 50%; transform: translate(-50%, -50%); width: 1px; height: 1px; }
            .center-logo { position: absolute; transform: translate(-50%, -50%); width: 200px; height: 200px; object-fit: contain; }
            .photo-orbit { position: absolute; width: 120px; height: 120px; border-radius: 50%; border: 3px solid white; object-fit: cover; box-shadow: 0 0 20px rgba(255,255,255,0.4); animation: orbit-animation 25s linear infinite; }
            @keyframes orbit-animation { from { transform: rotate(0deg) translateX(240px) rotate(0deg); } to { transform: rotate(360deg) translateX(240px) rotate(-360deg); } }
            .qr-container { position: fixed; bottom: 30px; right: 30px; background: white; padding: 10px; border-radius: 15px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        </style>
    """, unsafe_allow_html=True)

    # --- CONTENU DYNAMIQUE ---
    stars = "".join([f'<div class="star" style="left:{random.randint(0,100)}vw; top:{random.randint(0,100)}vh; width:{random.randint(1,2)}px; height:{random.randint(1,2)}px;"></div>' for _ in range(60)])
    photos = "".join([f'<img src="data:image/png;base64,{get_b64(p)}" class="photo-orbit" style="animation-delay:{-(i*(25/max(len(imgs),1))) if imgs else 0}s;">' for i, p in enumerate(imgs[-10:])])
    
    st.markdown(f"""
        <div class="main-container">
            {stars}
            <div class="welcome-title" style="color:{config['couleur']}; font-size:{config['taille']}px; text-shadow:0 0 20px {config['couleur']};">{config['texte']}</div>
            <div class="center-point">
                {"<img src='data:image/png;base64," + logo_data + "' class='center-logo' style='filter:drop-shadow(0 0 20px "+config['couleur']+"55);'>" if logo_data else ""}
                {photos}
            </div>
            <div class="qr-container">
                <img src="data:image/png;base64,{qr_b64}" width="100"><br>
                <b style="color:black; font-family:sans-serif; font-size:10px;">SCANNEZ POUR VOTER</b>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 4. MODE VOTE ---
else:
    st.title("🗳️ Participation")
    st.write("Bienvenue !")
