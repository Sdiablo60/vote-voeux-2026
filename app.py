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
DEFAULT_PASSWORD = "ADMIN_VOEUX_2026"
PASS_FILE = "pass_config.txt"
VOTES_DIR = "sessions_votes"
GALLERY_DIR = "galerie_images"
CONFIG_FILE = "config_videos.csv"
LOGO_FILE = "logo_entreprise.png"
SESSION_CONFIG = "current_session.txt"
PRESENCE_FILE = "presence_live.csv"

for d in [VOTES_DIR, GALLERY_DIR]:
    if not os.path.exists(d): os.makedirs(d)

st.set_page_config(page_title="Régie Master 2026", layout="wide")

# --- 2. FONCTIONS DE GESTION ---
def get_admin_password():
    if os.path.exists(PASS_FILE):
        with open(PASS_FILE, "r", encoding="utf-8") as f: return f.read().strip()
    return DEFAULT_PASSWORD

def set_admin_password(new_pass):
    with open(PASS_FILE, "w", encoding="utf-8") as f: f.write(new_pass)

def get_current_session():
    if os.path.exists(SESSION_CONFIG):
        with open(SESSION_CONFIG, "r", encoding="utf-8") as f: return f.read().strip()
    return "session_1"

def set_current_session(name):
    with open(SESSION_CONFIG, "w", encoding="utf-8") as f: f.write(name)

def load_videos():
    if os.path.exists(CONFIG_FILE): 
        return pd.read_csv(CONFIG_FILE)['Video'].tolist()
    return ["BU PAX", "BU FRET", "BU BTOB", "DPMI (ateliers)", "Service RH", "Service Finances", "Service AO", "Service QSSE", "Service IT", "Direction Pôle"]

def save_videos(liste):
    pd.DataFrame(liste, columns=['Video']).to_csv(CONFIG_FILE, index=False)

def get_stats():
    nb_p = 0
    if os.path.exists(PRESENCE_FILE):
        nb_p = len(pd.read_csv(PRESENCE_FILE)['Pseudo'].unique())
    curr = get_current_session()
    path_v = os.path.join(VOTES_DIR, f"{curr}.csv")
    nb_v = len(pd.read_csv(path_v)) if os.path.exists(path_v) else 0
    return nb_p, nb_v

# --- 3. INITIALISATION DES VARIABLES ---
admin_pass = get_admin_password()
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"
current_session = get_current_session()

if "auth_ok" not in st.session_state: st.session_state["auth_ok"] = False
if "voted" not in st.session_state: st.session_state["voted"] = False

# --- 4. MODE ADMIN (REGIE) ---
if est_admin:
    st.title("🛠️ Console de Régie")
    nb_p, nb_v = get_stats()
    
    with st.sidebar:
        st.header("🔑 Authentification")
        if not st.session_state["auth_ok"]:
            pwd_input = st.text_input("Code Admin", type="password")
            if pwd_input == admin_pass:
                st.session_state["auth_ok"] = True
                st.rerun()
        else:
            st.success("✅ Accès Autorisé")
            st.metric("👥 Participants", nb_p)
            st.metric("📥 Votes", nb_v)
            st.divider()
            st.subheader("📡 Session")
            st.info(f"Active : {current_session}")
            ns = st.text_input("Changer session", key="new_s")
            if st.button("🚀 Lancer"):
                set_current_session(ns)
                st.rerun()
            st.divider()
            with st.expander("**SECURITE**"):
                np = st.text_input("Nouveau code", type="password")
                if st.button("Modifier"): set_admin_password(np); st.rerun()
            with st.expander("**REINITIALISATION**"):
                st.info("Mémoire : ADMIN_***_**26")
                if st.button("RESET USINE"):
                    if os.path.exists(PASS_FILE): os.remove(PASS_FILE)
                    st.rerun()

    if st.session_state["auth_ok"]:
        t1, t2, t3 = st.tabs(["📊 Résultats", "📝 Services", "🖼️ Galerie"])
        with t1:
            all_f = glob.glob(os.path.join(VOTES_DIR, "*.csv"))
            if all_f:
                df = pd.concat([pd.read_csv(f) for f in all_f])
                # Calcul simplifié pour l'exemple
                st.write("Graphique des scores...")
                st.download_button("Export CSV", df.to_csv(), "votes.csv")
        with t2:
            vids = load_videos()
            new_v = st.text_input("Nouveau service")
            if st.button("Ajouter"): vids.append(new_v); save_videos(vids); st.rerun()
            for v in vids: st.write(f"• {v}")
        with t3:
            u = st.file_uploader("Images", accept_multiple_files=True)
            if u:
                for f in u: Image.open(f).save(os.path.join(GALLERY_DIR, f.name))
                st.rerun()

# --- 5. MODE PARTICIPANT (VOTE MOBILE) ---
elif mode_vote:
    st.title("🗳️ Vote Vœux 2026")
    if st.session_state["voted"]:
        st.success("✅ Merci ! Vote enregistré.")
    else:
        pseudo = st.text_input("Pseudo / Trigramme")
        if pseudo and st.button("🚀 Rejoindre l'écran"):
            df_p = pd.read_csv(PRESENCE_FILE) if os.path.exists(PRESENCE_FILE) else pd.DataFrame(columns=["Pseudo"])
            if pseudo not in df_p['Pseudo'].values:
                pd.DataFrame([[pseudo]], columns=["Pseudo"]).to_csv(PRESENCE_FILE, mode='a', header=not os.path.exists(PRESENCE_FILE), index=False)
            st.toast("Regardez le grand écran !")
        
        st.divider()
        vids = load_videos()
        s1 = st.segmented_control("Choix 1", vids, key="s1")
        if st.button("Valider"):
            st.session_state["voted"] = True
            st.rerun()

# --- 6. MODE SOCIAL WALL (LIVE PAR DEFAUT) ---
else:
    # On force l'affichage plein écran
    st.markdown("<style>button {display:none;} [data-testid='stSidebar'] {display:none;}</style>", unsafe_allow_html=True)
    
    col_l, col_r = st.columns([1, 2])
    
    with col_l:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE)
        st.write("### 📲 Scannez pour voter")
        qr_url = "https://vote-voeux-2026-6rueeu6wcdbxa878nepqgf.streamlit.app/?mode=vote"
        qr_buf = BytesIO()
        qrcode.make(qr_url).save(qr_buf, format="PNG")
        st.image(qr_buf.getvalue(), use_container_width=True)
        
        nb_p, _ = get_stats()
        st.metric("Participants", nb_p)

    with col_r:
        st.title("✨ Bienvenue au Live !")
        if os.path.exists(PRESENCE_FILE):
            df_p = pd.read_csv(PRESENCE_FILE)
            noms = df_p['Pseudo'].unique().tolist()
            nuage = "  ".join([f"<span style='font-size:{random.randint(20,50)}px; color:red; margin:10px; font-weight:bold; display:inline-block;'>{n}</span>" for n in noms])
            st.markdown(f"<div style='text-align:center; padding:20px; border-radius:15px; background:rgba(255,255,255,0.1);'>{nuage}</div>", unsafe_allow_html=True)

    st.divider()
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    if imgs:
        cols = st.columns(5)
        for i, img in enumerate(imgs): cols[i%5].image(img, use_container_width=True)

    time.sleep(5)
    st.rerun()
