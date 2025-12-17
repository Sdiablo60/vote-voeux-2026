import streamlit as st
import pandas as pd
import os
from PIL import Image
import altair as alt
from io import BytesIO
import qrcode
import glob
import random
import time

# --- 1. CONFIGURATION ---
ADMIN_PASSWORD = "ADMIN_VOEUX_2026"
VOTES_DIR = "sessions_votes"
GALLERY_DIR = "galerie_images"
CONFIG_FILE = "config_videos.csv"
LOGO_FILE = "logo_entreprise.png"
SESSION_CONFIG = "current_session.txt"
PRESENCE_FILE = "presence_live.csv"
TITRE_FILE = "titre_config.txt"

for d in [VOTES_DIR, GALLERY_DIR]:
    if not os.path.exists(d): os.makedirs(d)

st.set_page_config(page_title="Régie Master 2026", layout="wide")

# --- 2. FONCTIONS ---
def get_current_session():
    if os.path.exists(SESSION_CONFIG):
        with open(SESSION_CONFIG, "r") as f: return f.read().strip()
    return "session_1"

def set_current_session(name):
    with open(SESSION_CONFIG, "w") as f: f.write(name)

def load_videos():
    if os.path.exists(CONFIG_FILE): 
        return pd.read_csv(CONFIG_FILE)['Video'].tolist()
    return ["BU PAX", "BU FRET", "BU BTOB", "DPMI (ateliers)", "Service RH", "Service Finances", "Service AO", "Service QSSE", "Service IT", "Direction Pôle"]

def save_videos(liste):
    pd.DataFrame(liste, columns=['Video']).to_csv(CONFIG_FILE, index=False)

# --- 3. LOGIQUE INITIALISATION ---
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"
current_session = get_current_session()

# Initialisation du verrou de vote dans le navigateur (Session State)
if "voted" not in st.session_state: 
    st.session_state["voted"] = False
if "editing_service" not in st.session_state: 
    st.session_state["editing_service"] = None

# --- 4. INTERFACE PUBLIC : SOCIAL WALL ---
if not est_admin and not mode_vote:
    col_l, col_r = st.columns([1, 2])
    with col_l:
        if os.path.exists(LOGO_FILE): st.image(Image.open(LOGO_FILE), width=200)
        st.write("## 📲 Scannez pour participer")
        qr_url = "https://vote-voeux-2026-6rueeu6wcdbxa878nepqgf.streamlit.app/?mode=vote"
        qr_buf = BytesIO()
        qrcode.make(qr_url).save(qr_buf, format="PNG")
        st.image(qr_buf.getvalue(), use_container_width=True)
    with col_r:
        st.markdown("<h1 style='text-align:center; color:#FF4B4B;'>Bienvenue ! 👋</h1>", unsafe_allow_html=True)
        if os.path.exists(PRESENCE_FILE):
            noms = pd.read_csv(PRESENCE_FILE)['Pseudo'].unique().tolist()
            nuage = "".join([f'<span style="font-size:{random.randint(20,50)}px; color:{random.choice(["#FF4B4B","#1f77b4","#2ca02c","#ff7f0e"])}; margin:15px; font-weight:bold; display:inline-block;">{n}</span>' for n in noms])
            st.markdown(f'<div style="background:rgba(255,255,255,0.05); padding:40px; border-radius:30px; text-align:center; min-height:400px;">{nuage}</div>', unsafe_allow_html=True)
    st.divider()
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    if imgs:
        cols = st.columns(6)
        for i, img in enumerate(imgs): cols[i%6].image(img, use_container_width=True)
    time.sleep(5); st.rerun()

# --- 5. INTERFACE MOBILE : MODE VOTE (AVEC ANTI-TRICHE) ---
elif mode_vote:
    st.title("🗳️ Vote Vœux 2026")
    
    # Vérification si le pseudo a déjà voté dans CETTE session précise
    fn_check = os.path.join(VOTES_DIR, f"{current_session}.csv")
    
    if st.session_state["voted"]:
        st.success(f"✅ Merci ! Votre vote pour la session '{current_session}' est bien enregistré.")
        st.info("Un seul vote autorisé par session.")
    else:
        pseudo = st.text_input("Votre Pseudo / Trigramme").strip()
        
        if pseudo and st.button("🚀 Rejoindre l'écran"):
            df_p = pd.read_csv(PRESENCE_FILE) if os.path.exists(PRESENCE_FILE) else pd.DataFrame(columns=["Pseudo"])
            if pseudo not in df_p['Pseudo'].values:
                pd.DataFrame([[pseudo]], columns=["Pseudo"]).to_csv(PRESENCE_FILE, mode='a', header=not os.path.exists(PRESENCE_FILE), index=False)
            st.toast("Regardez le grand écran !")

        st.write("---")
        vids = load_videos()
        s1 = st.segmented_control("Top 1 (5 pts)", vids, key="mv1")
        s2 = st.segmented_control("Top 2 (3 pts)", [v for v in vids if v != s1], key="mv2")
        s3 = st.segmented_control("Top 3 (1 pt)", [v for v in vids if v not in [s1, s2]], key="mv3")
        
        if st.button("Valider mon vote 🗳️", use_container_width=True):
            if not pseudo or not s1 or not s2 or not s3:
                st.error("⚠️ Pseudo + 3 choix requis")
            else:
                # Vérification croisée dans le fichier CSV de la session
                df_v = pd.read_csv(fn_check) if os.path.exists(fn_check) else pd.DataFrame(columns=["Pseudo"])
                
                if pseudo.lower() in df_v['Pseudo'].str.lower().values:
                    st.error(f"❌ Désolé, le pseudo '{pseudo}' a déjà voté pour cette session.")
                    st.session_state["voted"] = True # Verrouille l'interface
                else:
                    # Enregistrement du vote
                    new_v = pd.DataFrame([["", pseudo, s1, s2, s3]], columns=["Prenom", "Pseudo", "Top1", "Top2", "Top3"])
                    new_v.to_csv(fn_check, mode='a', header=not os.path.exists(fn_check), index=False)
                    st.session_state["voted"] = True
                    st.balloons(); time.sleep(1); st.rerun()

# --- 6. INTERFACE ADMIN ---
elif est_admin:
    # (Le reste du code admin reste inchangé pour garder toutes les fonctions)
    tab_res, tab_admin = st.tabs(["📊 Résultats", "🛠️ Configuration"])
    # ... (Code admin précédent)
