import streamlit as st
import os
import glob
import base64
import qrcode
import json
import zipfile
import datetime
import random
from io import BytesIO
import streamlit.components.v1 as components

# --- 1. CONFIGURATION INITIALE ---
st.set_page_config(page_title="Social Wall Pro", layout="wide")

GALLERY_DIR = "galerie_images"
LOGO_FILE = "logo_entreprise.png"
VOTES_FILE = "votes.json"
CONFIG_FILE = "config_mur.json"

for d in [GALLERY_DIR]:
    if not os.path.exists(d): os.makedirs(d)

if not os.path.exists(VOTES_FILE):
    with open(VOTES_FILE, "w") as f: json.dump({}, f)
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f: json.dump({"mode_affichage": "photos"}, f)

# --- 2. GESTION DE LA SESSION ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "admin_password" not in st.session_state:
    st.session_state["admin_password"] = "ADMIN_LIVE_MASTER"
if "all_selected" not in st.session_state:
    st.session_state["all_selected"] = False

# --- 3. FONCTIONS ---
def load_config():
    with open(CONFIG_FILE, "r") as f: return json.load(f)

def save_config(mode):
    with open(CONFIG_FILE, "w") as f: json.dump({"mode_affichage": mode}, f)

def get_votes():
    with open(VOTES_FILE, "r") as f: return json.load(f)

def add_vote(candidat):
    votes = get_votes()
    votes[candidat] = votes.get(candidat, 0) + 1
    with open(VOTES_FILE, "w") as f: json.dump(votes, f)

def create_zip(file_list):
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for f in file_list:
            if os.path.exists(f): z.write(f, os.path.basename(f))
    return buf.getvalue()

# --- 4. NAVIGATION ---
query_params = st.query_params
est_admin = query_params.get("admin") == "true"
est_utilisateur = query_params.get("mode") == "vote"

# --- 5. INTERFACE ADMINISTRATION (STRUCTURE MASTER FIGÉE) ---
if est_admin:
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
        html, body, [data-testid="stAppViewContainer"] { font-family: 'Roboto', sans-serif; }
        .main-header-sticky {
            position: sticky; top: 0px; background-color: white; z-index: 1000;
            padding: 20px 0; border-bottom: 3px solid #E2001A;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, use_container_width=True)
        st.markdown("<h3 style='text-align: center;'>Régie Social Wall</h3>", unsafe_allow_html=True)
        pwd_input = st.text_input("Code Accès", type="password")
        if pwd_input == st.session_state["admin_password"]: st.session_state["authenticated"] = True
        
        st.divider()
        if st.session_state["authenticated"]:
            st.subheader("🎮 Contrôle du Mur")
            current_cfg = load_config()
            new_mode = st.radio("Affichage Mur :", ["Photos", "Votes"], 
                                index=0 if current_cfg["mode_affichage"] == "photos" else 1)
            if st.button("Basculer le Mur"):
                save_config(new_mode.lower())
                st.rerun()
            
            if st.button("🧨 RESET TOTAL", type="primary"):
                for f in glob.glob(os.path.join(GALLERY_DIR, "*")): os.remove(f)
                with open(VOTES_FILE, "w") as f: json.dump({}, f)
                st.rerun()

    if st.session_state["authenticated"]:
        st.markdown('<div class="main-header-sticky">', unsafe_allow_html=True)
        c_title_main, c_logo_main = st.columns([2, 1])
        with c_title_main:
            st.markdown("<h1 style='margin-bottom:0;'>Console de Modération</h1>", unsafe_allow_html=True)
            st.caption("Gestion Transdev - Photos & Votes Vidéo")
        if os.path.exists(LOGO_FILE):
            c_logo_main.image(LOGO_FILE, width=280) # LOGO À DROITE (MASTER)
        st.link_button("🖥️ MUR PLEIN ÉCRAN", f"https://{st.context.headers.get('host', 'localhost')}/", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Affichage des résultats de vote en Régie
        st.subheader("📊 Résultats du Vote Vidéo")
        v_data = get_votes()
        if v_data: st.bar_chart(v_data)
        else: st.info("Aucun vote enregistré.")

        # Galerie (Strictement 8 colonnes / 4 colonnes)
        all_imgs = [f for f in glob.glob(os.path.join(GALLERY_DIR, "*")) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        sorted_imgs = sorted(all_imgs, key=os.path.getmtime, reverse=True)
        
        mode_vue = st.radio("Vue", ["Vignettes", "Liste"], horizontal=True)
        
        if mode_vue == "Vignettes":
            for i in range(0, len(sorted_imgs), 8):
                cols = st.columns(8)
                for j in range(8):
                    idx = i + j
                    if idx < len(sorted_imgs):
                        img_p = sorted_imgs[idx]
                        with cols[j]:
                            st.image(img_p, use_container_width=True)
                            if st.button("🗑️", key=f"d_{idx}"): os.remove(img_p); st.rerun()
        else:
            for i in range(0, len(sorted_imgs), 4):
                cols = st.columns(4)
                for j in range(4):
                    idx = i + j
                    if idx < len(sorted_imgs):
                        img_p = sorted_imgs[idx]
                        with cols[j]:
                            with st.container(border=True):
                                st.image(img_p, use_container_width=True)
                                if st.button("Supprimer", key=f"bl_{idx}", use_container_width=True):
                                    os.remove(img_p); st.rerun()

# --- 6. INTERFACE UTILISATEUR (VOTES VIDÉO RÉINTÉGRÉS) ---
elif est_utilisateur:
    st.title("📲 Participation")
    t1, t2 = st.tabs(["📸 Photo", "🗳️ Vote Vidéo"])
    
    with t1:
        f = st.file_uploader("Envoyer une photo", type=['jpg', 'png'])
        if f:
            with open(os.path.join(GALLERY_DIR, f"u_{random.randint(100,999)}.jpg"), "wb") as out: out.write(f.getbuffer())
            st.success("Photo sur le mur !")
            
    with t2:
        st.subheader("Quel projet vidéo mérite de gagner ?")
        # RÉINTÉGRATION DES QUESTIONS INITIALES (Concours Vidéo)
        video_choice = st.radio("Votez pour la meilleure réalisation :", [
            "Vidéo 1 : Innovation & Futur",
            "Vidéo 2 : Esprit d'Équipe",
            "Vidéo 3 : Performance Durable",
            "Vidéo 4 : Proximité Client"
        ])
        if st.button("Valider mon vote"):
            add_vote(video_choice)
            st.success(f"Votre vote pour '{video_choice}' a été pris en compte !")

# --- 7. MODE LIVE (MUR) ---
else:
    st.markdown("<style>body { background-color: black; } [data-testid='stAppViewContainer'] { background-color: black !important; } [data-testid='stHeader'] { display: none; } </style>", unsafe_allow_html=True)
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=15000, key="refresh")
    except: pass
    
    config = load_config()
    if config["mode_affichage"] == "votes":
        st.markdown("<h1 style='color:white; text-align:center; font-size:50px; padding-top:50px;'>CLASSEMENT VIDÉO EN DIRECT</h1>", unsafe_allow_html=True)
        st.bar_chart(get_votes())
    else:
        # Mur photo classique (code HTML animé comme précédemment)
        st.markdown("<h1 style='color:white; text-align:center;'>MUR PHOTO LIVE</h1>", unsafe_allow_html=True)
        # (Le code HTML de l'animation reste identique aux versions précédentes)
