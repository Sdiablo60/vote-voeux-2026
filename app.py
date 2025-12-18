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
PWD_FILE = "admin_pwd.txt" # Pour stocker le mot de passe personnalisé

for d in [GALLERY_DIR]:
    if not os.path.exists(d): os.makedirs(d)

# Fonctions utilitaires
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
        
        if input_pwd == current_pwd:
            st.success("Accès Autorisé")
            st.divider()
            st.header("⚙️ Paramètres Avancés")
            
            # 1. Changement de mot de passe
            new_pwd = st.text_input("Nouveau mot de passe", type="password")
            if st.button("Modifier le code"):
                with open(PWD_FILE, "w") as f: f.write(new_pwd)
                st.success("Code modifié !")
                st.rerun()
            
            st.divider()
            # 2. Réinitialisation complète
            if st.button("🚨 RESET TOTAL (Galerie + Logo)"):
                for f in glob.glob(os.path.join(GALLERY_DIR, "*")): os.remove(f)
                if os.path.exists(LOGO_FILE): os.remove(LOGO_FILE)
                st.warning("Système réinitialisé")
                st.rerun()
        else:
            st.error("Code requis")

    if input_pwd == current_pwd:
        config = get_config()
        t1, t2 = st.tabs(["💬 Message & Design", "🖼️ Médias (Logo/Photos)"])
        
        with t1:
            col_text, col_style = st.columns(2)
            with col_text:
                new_texte = st.text_area("Texte du message", config["texte"])
            with col_style:
                new_couleur = st.color_picker("Couleur", config["couleur"])
                new_taille = st.slider("Taille (px)", 20, 100, int(config["taille"]))
            
            if st.button("🚀 Mettre à jour le Mur"):
                pd.DataFrame([{"texte": new_texte, "couleur": new_couleur, "taille": new_taille}]).to_csv(MSG_FILE, index=False)
                st.rerun()

        with t2:
            st.subheader("Logo & Photos")
            col_up1, col_up2 = st.columns(2)
            with col_up1:
                ul = st.file_uploader("Logo Central (PNG/JPG)", type=['png','jpg','jpeg'])
                if ul: 
                    with open(LOGO_FILE, "wb") as f: f.write(ul.getbuffer())
                    st.rerun()
            with col_up2:
                uf = st.file_uploader("Ajouter des photos", type=['png','jpg','jpeg'], accept_multiple_files=True)
                if uf:
                    for f in uf:
                        with open(os.path.join(GALLERY_DIR, f.name), "wb") as file: file.write(f.getbuffer())
                    st.rerun()
            
            st.divider()
            # Prévisualisation et suppression individuelle
            imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
            if imgs:
                st.write(f"Photos en ligne : {len(imgs)}")
                cols = st.columns(6)
                for i, p in enumerate(imgs):
                    with cols[i % 6]:
                        st.image(p, use_container_width=True)
                        if st.button("🗑️", key=f"del_{i}"):
                            os.remove(p)
                            st.rerun()
    else:
        st.info("Saisissez le code dans la barre latérale pour déverrouiller les outils.")

# --- 3. MODE VOTE & LIVE ---
elif mode_vote:
    st.title("🗳️ Interface Invité")
    # (Interface de vote simplifiée)
else:
    # --- SOCIAL WALL CODE ---
    config = get_config()
    logo_data = get_b64(LOGO_FILE)
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
    # QR Code dynamique
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_img = qrcode.make(qr_url)
    buf = BytesIO()
    qr_img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    # HTML/CSS Injection
    st.markdown(f"""
        <style>
            [data-testid="stHeader"], footer, header {{ display:none !important; }}
            .stApp {{ background-color: #050505 !important; }}
            .main-container {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; overflow: hidden; }}
            .star {{ position: absolute; background: white; border-radius: 50%; opacity: 0.5; animation: twinkle 3s infinite alternate; }}
            @keyframes twinkle {{ from {{ opacity: 0.2; }} to {{ opacity: 0.8; }} }}
            .welcome-title {{ position: absolute; top: 7%; width: 100%; text-align: center; color: {config['couleur']}; font-family: sans-serif; font-size: {config['taille']}px; font-weight: bold; text-shadow: 0 0 20px {config['couleur']}99; animation: pulse-text 4s ease-in-out infinite; }}
            @keyframes pulse-text {{ 0% {{ transform: scale(1); opacity: 0.8; }} 50% {{ transform: scale(1.02); opacity: 1; }} 100% {{ transform: scale(1); opacity: 0.8; }} }}
            .center-point {{ position: absolute; top: 58%; left: 50%; transform: translate(-50%, -50%); width: 180px; height: 180px; }}
            .center-logo {{ width: 180px; height: 180px; object-fit: contain; filter: drop-shadow(0 0 20px {config['couleur']}55); }}
            .orbit-photo {{ position: absolute; top: 50%; left: 50%; width: 120px; height: 120px; margin-top: -60px; margin-left: -60px; border-radius: 50%; border: 3px solid white; object-fit: cover; box-shadow: 0 0 20px rgba(255,255,255,0.4); animation: orbit-animation 25s linear infinite; }}
            @keyframes orbit-animation {{ from {{ transform: rotate(0deg) translateX(240px) rotate(0deg); }} to {{ transform: rotate(360deg) translateX(240px) rotate(-360deg); }} }}
            .qr-container {{ position: fixed; bottom: 30px; right: 30px; background: white; padding: 10px; border-radius: 15px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
        </style>
        <div class="main-container">
            {"".join([f'<div class="star" style="left:{random.randint(0,100)}vw; top:{random.randint(0,100)}vh; width:{random.randint(1,2)}px; height:{random.randint(1,2)}px;"></div>' for _ in range(60)])}
            <div class="welcome-title">{config['texte']}</div>
            <div class="center-point">
                {"<img src='data:image/png;base64," + logo_data + "' class='center-logo'>" if logo_data else ""}
                {"".join([f'<img src="data:image/png;base64,{get_b64(p)}" class="orbit-photo" style="animation-delay:{-(i*(25/min(len(imgs),10)))}s;">' for i, p in enumerate(imgs[-10:])])}
            </div>
            <div class="qr-container">
                <img src="data:image/png;base64,{qr_b64}" width="100"><br>
                <b style="color:black; font-family:sans-serif; font-size:10px;">SCANNEZ POUR VOTER</b>
            </div>
        </div>
    """, unsafe_allow_html=True)
