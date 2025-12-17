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
    return ["BU PAX", "BU FRET", "BU BTOB", "DPMI", "RH", "Finances", "AO", "QSSE", "IT", "Direction"]

def save_videos(liste):
    pd.DataFrame(liste, columns=['Video']).to_csv(CONFIG_FILE, index=False)

# --- 3. GESTION DES MODES (Query Params) ---
# ?admin=true -> Console Régie
# ?mode=vote -> Interface Mobile Participants
# (rien)     -> Social Wall (Grand Écran)
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"
current_session = get_current_session()

# --- 4. INTERFACE PUBLIC : SOCIAL WALL (MODE PAR DÉFAUT) ---
if not est_admin and not mode_vote:
    # Auto-refresh toutes les 5 secondes pour le nuage de noms
    if "refresh" not in st.session_state: st.session_state.refresh = 0
    st.empty() # Placeholder pour forcer le rafraîchissement
    
    col_l, col_r = st.columns([1, 2])
    
    with col_l:
        if os.path.exists(LOGO_FILE): st.image(Image.open(LOGO_FILE), width=200)
        st.write("## 📲 Scannez pour participer")
        # URL vers le mode vote (à adapter selon votre URL finale)
        qr_url = "https://vote-voeux-2026-6rueeu6wcdbxa878nepqgf.streamlit.app/?mode=vote"
        qr_buf = BytesIO()
        qrcode.make(qr_url).save(qr_buf, format="PNG")
        st.image(qr_buf.getvalue(), use_container_width=True)
        st.markdown("<h2 style='text-align:center;'>Votez pour votre vidéo préférée !</h2>", unsafe_allow_html=True)

    with col_r:
        st.markdown("<h1 style='text-align:center; color:#FF4B4B;'>Bienvenue ! 👋</h1>", unsafe_allow_html=True)
        st.write("### 👥 Qui est avec nous ?")
        
        if os.path.exists(PRESENCE_FILE):
            df_p = pd.read_csv(PRESENCE_FILE)
            noms = df_p['Pseudo'].unique().tolist()
            nuage_html = ""
            couleurs = ["#FF4B4B", "#1f77b4", "#2ca02c", "#ff7f0e", "#9467bd", "#e377c2", "#17becf"]
            for nom in noms:
                taille = random.randint(20, 50)
                c = random.choice(couleurs)
                nuage_html += f'<span style="font-size:{taille}px; color:{c}; margin:15px; font-weight:bold; display:inline-block; animation: fadeIn 2s;">{nom}</span>'
            
            st.markdown(f"""
                <div style="background:rgba(255,255,255,0.05); padding:40px; border-radius:30px; text-align:center; min-height:400px; border: 2px solid #333;">
                    {nuage_html}
                </div>
                <style> @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }} </style>
            """, unsafe_allow_html=True)
        else:
            st.info("Scannez le QR Code pour rejoindre l'écran !")

    st.divider()
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    if imgs:
        cols = st.columns(min(len(imgs), 6))
        for i, img in enumerate(imgs): cols[i % 6].image(img, use_container_width=True)

    # Commande de rafraîchissement
    time.sleep(5)
    st.rerun()

# --- 5. INTERFACE MOBILE : MODE VOTE ---
elif mode_vote:
    st.title("🗳️ Vote Vœux 2026")
    if "voted" not in st.session_state: st.session_state["voted"] = False
    
    if st.session_state["voted"]:
        st.success("✅ Merci ! Votre vote est enregistré.")
    else:
        pseudo = st.text_input("Votre Pseudo / Trigramme", placeholder="Ex: JDO")
        
        if pseudo and st.button("🚀 Apparaître sur l'écran", use_container_width=True):
            df_p = pd.read_csv(PRESENCE_FILE) if os.path.exists(PRESENCE_FILE) else pd.DataFrame(columns=["Pseudo"])
            if pseudo not in df_p['Pseudo'].values:
                pd.DataFrame([[pseudo]], columns=["Pseudo"]).to_csv(PRESENCE_FILE, mode='a', header=not os.path.exists(PRESENCE_FILE), index=False)
            st.toast("Regardez le grand écran ! ✨")

        st.write("---")
        vids = load_videos()
        s1 = st.segmented_control("Top 1 (5 pts)", vids, key="mv1")
        s2 = st.segmented_control("Top 2 (3 pts)", [v for v in vids if v != s1], key="mv2")
        s3 = st.segmented_control("Top 3 (1 pt)", [v for v in vids if v not in [s1, s2]], key="mv3")
        
        if st.button("Valider mon vote 🗳️", use_container_width=True):
            if pseudo and s1 and s2 and s3:
                fn = os.path.join(VOTES_DIR, f"{current_session}.csv")
                df = pd.read_csv(fn) if os.path.exists(fn) else pd.DataFrame(columns=["Prenom", "Pseudo", "Top1", "Top2", "Top3"])
                pd.DataFrame([["", pseudo, s1, s2, s3]], columns=df.columns).to_csv(fn, mode='a', header=not os.path.exists(fn), index=False)
                st.session_state["voted"] = True
                st.balloons(); time.sleep(2); st.rerun()
            else:
                st.error("⚠️ Pseudo + 3 choix requis")

# --- 6. INTERFACE ADMIN : CONSOLE RÉGIE ---
elif est_admin:
    tab_res, tab_admin = st.tabs(["📊 Résultats", "🛠️ Console Admin"])
    
    with tab_res:
        mode = st.radio("Mode :", ["Session en cours", "Cumul"], horizontal=True)
        # (Code graphique Altair et Export CSV identique aux versions précédentes)
        st.write("Graphiques et Exports ici...")
        
    with tab_admin:
        if st.text_input("Code Admin", type="password") == ADMIN_PASSWORD:
            st.subheader("🧹 Maintenance Live")
            if st.button("🗑️ Vider le Nuage de noms"):
                if os.path.exists(PRESENCE_FILE): os.remove(PRESENCE_FILE)
                st.rerun()
            st.divider()
            # (Gestion des services, suppression, ajout, etc.)
            st.write("Gestion des services...")
