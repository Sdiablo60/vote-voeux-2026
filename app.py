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
SETTINGS_FILE = "settings.csv"
LOCK_FILE = "vote_lock.txt"
LOGO_FILE = "logo_entreprise.png"

for d in [VOTES_DIR, GALLERY_DIR, SOUNDS_DIR]:
    if not os.path.exists(d): os.makedirs(d)

st.set_page_config(page_title="Régie Vote 2026", layout="wide")

# --- FONCTIONS ---
def jouer_son(nom_fichier):
    path = os.path.join(SOUNDS_DIR, nom_fichier)
    if os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            st.components.v1.html(f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', height=0)

def generer_qr(url):
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

def load_settings():
    if os.path.exists(SETTINGS_FILE): return pd.read_csv(SETTINGS_FILE).iloc[0].to_dict()
    return {"nb_choix": 3, "effet": "Ballons", "son": "Aucun"}

def load_videos():
    if os.path.exists(CONFIG_FILE): return pd.read_csv(CONFIG_FILE)['Video'].tolist()
    return ["BU PAX", "BU FRET", "BU BTOB", "DPMI (ateliers)", "Service RH", "Service Finances", "Service AO", "Service QSSE", "Service IT", "Direction Pôle"]

# --- LOGIQUE ---
settings = load_settings()
nb_requis = int(settings["nb_choix"])
est_admin = st.query_params.get("admin") == "true"

if os.path.exists(LOGO_FILE):
    st.image(Image.open(LOGO_FILE), width=150)

st.title("🎬 Élection Vidéo Vœux 2026")

# --- AFFICHAGE ---
if est_admin:
    tab_vote, tab_res, tab_admin = st.tabs(["🗳️ Espace Vote", "📊 Résultats", "🛠️ Console Admin"])
else:
    tab_vote = st.container()

with tab_vote:
    if est_admin:
        c_i, c_q = st.columns([2, 1])
        with c_q:
            st.write("📲 **Scannez pour voter**")
            st.image(generer_qr("https://vote-voeux-2026-6rueeu6wcdbxa878nepqgf.streamlit.app/"), width=180)
    
    if os.path.exists(LOCK_FILE):
        st.warning("🔒 Votes clos.")
    elif st.session_state.get("voted", False):
        st.success("✅ Vote enregistré !")
    else:
        with st.form("vote_form"):
            p1 = st.text_input("Prénom", key="p1")
            p2 = st.text_input("Pseudo", key="p2")
            vids = load_videos()
            choix = []
            for i in range(nb_requis):
                sel = st.selectbox(f"Choix n°{i+1}", [v for v in vids if v not in choix], key=f"s{i}")
                choix.append(sel)
            if st.form_submit_button("Voter"):
                if p1 and p2:
                    fn = os.path.join(VOTES_DIR, "votes_principale.csv")
                    df = pd.read_csv(fn) if os.path.exists(fn) else pd.DataFrame(columns=["Prenom", "Pseudo"] + [f"Top{j+1}" for j in range(nb_requis)])
                    pd.DataFrame([[p1, p2] + choix], columns=df.columns).to_csv(fn, mode='a', header=not os.path.exists(fn), index=False)
                    st.session_state["voted"] = True
                    st.rerun()

if est_admin:
    with tab_res:
        pwd_res = st.text_input("Mot de passe Résultats", type="password", key="pwd_res")
        if pwd_res == ADMIN_PASSWORD:
            st.subheader("Résultats en direct")
            fn = os.path.join(VOTES_DIR, "votes_principale.csv")
            if os.path.exists(fn):
                df_r = pd.read_csv(fn)
                st.write(f"Nombre de votes : {len(df_r)}")
                if st.button("📣 Célébrer"): st.balloons()
            else: st.info("Aucun vote.")

    with tab_admin:
        pwd_admin = st.text_input("Mot de passe Console Admin", type="password", key="pwd_admin")
        if pwd_admin == ADMIN_PASSWORD:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📁 Médias")
                u_logo = st.file_uploader("Logo
