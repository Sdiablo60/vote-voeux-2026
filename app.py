import streamlit as st
import pandas as pd
import os
import base64
from PIL import Image
import altair as alt
from io import BytesIO
import qrcode

# --- CONFIGURATION DES RÉPERTOIRES ---
ADMIN_PASSWORD = "ADMIN_VOEUX_2026"
VOTES_DIR = "sessions_votes"
GALLERY_DIR = "galerie_images"
SOUNDS_DIR = "sons_admin"
CONFIG_FILE = "config_videos.csv"
LOCK_FILE = "vote_lock.txt"
LOGO_FILE = "logo_entreprise.png"

# Création des dossiers si nécessaires
for d in [VOTES_DIR, GALLERY_DIR, SOUNDS_DIR]:
    if not os.path.exists(d): 
        os.makedirs(d)

st.set_page_config(page_title="Régie Vote 2026", layout="wide")

# --- FONCTIONS TECHNIQUES ---
def generer_qr(url):
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

def load_videos():
    if os.path.exists(CONFIG_FILE): 
        return pd.read_csv(CONFIG_FILE)['Video'].tolist()
    return ["BU PAX", "BU FRET", "BU BTOB", "DPMI (ateliers)", "Service RH", "Service Finances", "Service AO", "Service QSSE", "Service IT", "Direction Pôle"]

# --- LOGIQUE D'AFFICHAGE ---
est_admin = st.query_params.get("admin") == "true"

if os.path.exists(LOGO_FILE):
    st.image(Image.open(LOGO_FILE), width=150)

st.title("🎬 Élection Vidéo Vœux 2026")

# --- STRUCTURE DES ONGLETS ---
if est_admin:
    tab_vote, tab_res, tab_admin = st.tabs(["🗳️ Espace Vote", "📊 Résultats", "🛠️ Console Admin"])
else:
    tab_vote = st.container()

# --- 1. ONGLET VOTE ---
with tab_vote:
    if est_admin:
        col_txt, col_qr = st.columns([2, 1])
        with col_qr:
            st.write("📲 **Scannez pour voter**")
            url_fixe = "https://vote-voeux-2026-6rueeu6wcdbxa878nepqgf.streamlit.app/"
            st.image(generer_qr(url_fixe), width=180)
    
    if os.path.exists(LOCK_FILE):
        st.warning("🔒 Les votes sont clos. Merci de votre participation !")
    elif st.session_state.get("voted", False):
        st.success("✅ Votre vote a bien été enregistré sur cet appareil.")
    else:
        with st.form("vote_form_final"):
            p1 = st.text_input("Prénom", key="input_prenom")
            p2 = st.text_input("Pseudo", key
