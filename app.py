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

# État de la sidebar : Seule l'admin la voit ouverte
st.set_page_config(
    page_title="Social Wall 2026", 
    layout="wide", 
    initial_sidebar_state="expanded" if est_admin else "collapsed"
)

GALLERY_DIR = "galerie_images"
LOGO_FILE = "logo_entreprise.png"
MSG_FILE = "live_config.csv"
PWD_FILE = "admin_pwd.txt"

if not os.path.exists(GALLERY_DIR): os.makedirs(GALLERY_DIR)

def get_b64(path):
    try:
        if os.path.exists(path):
            with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return ""
    return ""

def get_config():
    if os.path.exists(MSG_FILE): return pd.read_csv(MSG_FILE).iloc[0].to_dict()
    return {"texte": "✨ BIENVENUE ✨", "couleur": "#FFFFFF", "taille": 48}

def get_admin_pwd():
    if os.path.exists(PWD_FILE):
        with open(PWD_FILE, "r") as f: return f.read().strip()
    return "ADMIN_VOEUX_2026"

# --- 2. INTERFACE ADMIN (CONSOLE RÉGIE) ---
if est_admin:
    st.title("🛠️ Console Régie Master")
    current_pwd = get_admin_pwd()
    
    # --- BARRE LATÉRALE STRICTE ---
    with st.sidebar:
        st.header("🔑 Accès")
        input_pwd = st.text_input("Saisir le Code Admin", type="password")
        
        # On vérifie si le mot de passe est correct
        auth_valide = (input_pwd == current_pwd)
        
        if auth_valide:
            st.success("Accès Autorisé")
            st.divider()
            st.header("⚙️ Paramètres Avancés")
            new_pwd = st.text_input("Changer le mot de passe", type="password")
            if st.button("Enregistrer nouveau code"):
                with open(PWD_FILE, "w") as f: f.write(new_pwd)
                st.success("Code modifié !")
            
            if st.button("🚨 RÉINITIALISATION TOTALE"):
                for f in glob.glob(os.path.join(GALLERY_DIR, "*")): os.remove(f)
                if os.path.exists(LOGO_FILE): os.remove(LOGO_FILE)
                st.rerun()
        else:
            if input_pwd: st.error("Code incorrect")

    # --- CORPS DE LA PAGE (Masqué si pas d'auth) ---
    if auth_valide:
        config = get_config()
        t1, t2 = st.tabs(["💬 Message & Design", "🖼️ Médias (Logo/Photos)"])
        
        with t1:
            c1, c2 = st.columns(2)
            new_texte = c1.text_area("Texte du message", config["texte"])
            new_couleur = c2.color_picker("Couleur du texte", config["couleur"])
            new_taille = c2.slider("Taille (px)", 20, 100, int(config["taille"]))
            if st.button("🚀 Mettre à jour le Mur"):
                pd.DataFrame([{"texte": new_texte, "couleur": new_couleur, "taille": new_taille}]).to_csv(MSG_FILE, index=False)
                st.rerun()

        with t2:
            c1, c2 = st.columns(2)
            ul = c1.file_uploader("Upload Logo Central", type=['png','jpg','jpeg'])
            if ul: 
                with open(LOGO_FILE, "wb") as f: f.write(ul.getbuffer())
                st.rerun()
            uf = c2.file_uploader("Upload Photos Galerie", type=['png','jpg','jpeg'], accept_multiple_files=True)
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
    else:
        st.info("Veuillez entrer le code admin dans la barre latérale pour afficher les réglages.")

# --- 3. MODE LIVE (SOCIAL WALL) ---
elif not mode_vote:
    config = get_config()
    logo_data = get_b64(LOGO_FILE)
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
    # QR Code
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_img = qrcode.make(qr_url)
    buf = BytesIO()
    qr_img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    # CSS DANS UN BLOC SÉPARÉ (SANS AUCUNE VARIABLE) POUR ÉVITER LE BUG DU CARRÉ BLANC
    st.markdown("""
        <style>
            [data-testid="stHeader"], footer, header { display:none !important; }
            .stApp { background-color: #050505 !important; }
            .main-wall { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: #050505; z-index: 999; overflow: hidden; }
            .star { position: absolute; background: white; border-radius: 50%; opacity: 0.5; animation: twinkle 3s infinite alternate; }
            @keyframes twinkle { from { opacity: 0.2; } to { opacity: 0.8; } }
            .title-wall { position: absolute; top: 8%; width: 100%; text-align: center; font-family: sans-serif; font-weight: bold; z-index: 1001; animation: pulse 4s infinite; }
            @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.03); } }
            .orbit-center { position: absolute; top: 58%; left: 50%; transform: translate(-50%, -50%); width: 1px; height: 1px; z-index: 1000; }
            .logo-wall { position: absolute; transform: translate(-50%, -50%); width: 220px; height: 220px; object-fit: contain; }
            .photo-node { position: absolute; width: 130px; height: 130px; border-radius: 50%; border: 3px solid white; object-fit: cover; box-shadow: 0 0 20px rgba(255,255,255,0.4); animation: orbit-loop 25s linear infinite; }
            @keyframes orbit-loop { from { transform: rotate(0deg) translateX(260px) rotate(0deg); } to { transform: rotate(360deg) translateX(260px) rotate(-360deg); } }
            .qr-wall { position: fixed; bottom: 30px; right: 30px; background: white; padding: 10px; border-radius: 15px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.5); z-index: 1002; }
        </style>
    """, unsafe_allow_html=True)

    # GÉNÉRATION DU CONTENU
    stars_html = "".join([f'<div class="star" style="left:{random.randint(0,100)}vw; top:{random.randint(0,100)}vh; width:{random.randint(1,2)}px; height:{random.randint(1,2)}px;"></div>' for _ in range(60)])
    photos_html = "".join([f'<img src="data:image/png;base64,{get_b64(p)}" class="photo-node" style="animation-delay:{-(i*(25/max(len(imgs),1)))}s;">' for i, p in enumerate(imgs[-10:])])
    
    st.markdown(f"""
        <div class="main-wall">
            {stars_html}
            <div class="title-wall" style="color:{config['couleur']}; font-size:{config['taille']}px; text-shadow: 0 0 20px {config['couleur']};">
                {config['texte']}
            </div>
            <div class="orbit-center">
                {"<img src='data:image/png;base64," + logo_data + "' class='logo-wall' style='filter:drop-shadow(0 0 15px "+config['couleur']+"77);'>" if logo_data else ""}
                {photos_html}
            </div>
            <div class="qr-wall">
                <img src="data:image/png;base64,{qr_b64}" width="100"><br>
                <b style="color:black; font-family:sans-serif; font-size:10px;">SCANNEZ POUR VOTER</b>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 4. MODE VOTE ---
else:
    st.title("🗳️ Participation")
    st.write("Bienvenue sur l'interface mobile !")
