import streamlit as st
import pandas as pd
import os
import base64
from PIL import Image
import altair as alt
from io import BytesIO
import qrcode

# --- CONFIGURATION ---
ADMIN_PASSWORD = "ADMIN_VOEUX_2026"
VOTES_DIR = "sessions_votes"
GALLERY_DIR = "galerie_images"
SOUNDS_DIR = "sons_admin"
CONFIG_FILE = "config_videos.csv"
LOCK_FILE = "vote_lock.txt"
LOGO_FILE = "logo_entreprise.png"

for d in [VOTES_DIR, GALLERY_DIR, SOUNDS_DIR]:
    if not os.path.exists(d): 
        os.makedirs(d)

st.set_page_config(page_title="Régie Vote 2026", layout="wide")

# --- FONCTIONS ---
def generer_qr(url):
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

def load_videos():
    if os.path.exists(CONFIG_FILE): 
        return pd.read_csv(CONFIG_FILE)['Video'].tolist()
    return ["BU PAX", "BU FRET", "BU BTOB", "DPMI (ateliers)", "Service RH", "Service Finances", "Service AO", "Service QSSE", "Service IT", "Direction Pôle"]

# --- LOGIQUE ---
est_admin = st.query_params.get("admin") == "true"
if os.path.exists(LOGO_FILE):
    st.image(Image.open(LOGO_FILE), width=150)

st.title("🎬 Élection Vidéo Vœux 2026")

if est_admin:
    tab_vote, tab_res, tab_admin = st.tabs(["🗳️ Espace Vote", "📊 Résultats", "🛠️ Console Admin"])
else:
    tab_vote = st.container()

with tab_vote:
    if est_admin:
        c_i, c_q = st.columns([2, 1])
        with c_q:
            st.write("📲 **Scannez pour voter**")
            url_fixe = "https://vote-voeux-2026-6rueeu6wcdbxa878nepqgf.streamlit.app/"
            st.image(generer_qr(url_fixe), width=180)
    
    if os.path.exists(LOCK_FILE):
        st.warning("🔒 Les votes sont clos.")
    elif st.session_state.get("voted", False):
        st.success("✅ Votre vote a bien été enregistré sur cet appareil.")
    else:
        with st.form("vote_form_final"):
            p1 = st.text_input("Prénom", key="p1")
            p2 = st.text_input("Pseudo", key="p2")
            vids = load_videos()
            choix = []
            
            for i in range(3):
                sel = st.selectbox(f"Choix n°{i+1}", [v for v in vids if v not in choix], index=None, placeholder="Sélectionnez une vidéo...", key=f"sel_v_{i}")
                if sel: choix.append(sel)
            
            if st.form_submit_button("Valider mon vote 🚀"):
                if p1 and p2 and len(choix) == 3:
                    fn = os.path.join(VOTES_DIR, "votes_principale.csv")
                    # LIGNE CORRIGÉE ICI
                    df = pd.read_csv(fn) if os.path.exists(fn) else pd.DataFrame(columns=["Prenom", "Pseudo", "Top1", "Top2", "Top3"])
                    
                    if p2.lower() in df['Pseudo'].str.lower().values:
                        st.warning("❌ Ce pseudo a déjà été utilisé.")
                    else:
                        new_row = pd.DataFrame([[p1, p2] + choix], columns=df.columns)
                        new_row.to_csv(fn, mode='a', header=not os.path.exists(fn), index=False)
                        st.session_state["voted"] = True
                        st.balloons()
                        st.rerun()
                else:
