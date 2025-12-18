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
    with open(CONFIG_FILE, "w") as f: 
        json.dump({"mode_affichage": "photos", "titre_mur": "SOIRÉE DE GALA 2026"}, f)

# --- 2. GESTION DE LA SESSION ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "admin_password" not in st.session_state:
    st.session_state["admin_password"] = "ADMIN_LIVE_MASTER"

# --- 3. FONCTIONS ---
def load_config():
    with open(CONFIG_FILE, "r") as f: return json.load(f)

def save_config(mode, titre):
    with open(CONFIG_FILE, "w") as f: 
        json.dump({"mode_affichage": mode, "titre_mur": titre}, f)

def get_votes():
    with open(VOTES_FILE, "r") as f: return json.load(f)

def add_vote(candidat):
    votes = get_votes()
    votes[candidat] = votes.get(candidat, 0) + 1
    with open(VOTES_FILE, "w") as f: json.dump(votes, f)

# --- 4. NAVIGATION ---
query_params = st.query_params
est_admin = query_params.get("admin") == "true"
est_utilisateur = query_params.get("mode") == "vote"

# --- 5. INTERFACE ADMINISTRATION (MASTER) ---
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

    config = load_config()

    with st.sidebar:
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, use_container_width=True)
        st.markdown("<h3 style='text-align: center;'>Régie Social Wall</h3>", unsafe_allow_html=True)
        pwd_input = st.text_input("Code Accès", type="password")
        if pwd_input == st.session_state["admin_password"]: st.session_state["authenticated"] = True
        
        st.divider()
        if st.session_state["authenticated"]:
            st.subheader("🎮 Configuration Live")
            nouveau_titre = st.text_input("Sous-titre (modifiable) :", value=config.get("titre_mur", "ÉVÉNEMENT 2026"))
            new_mode = st.radio("Affichage Mur :", ["Photos", "Votes"], index=0 if config["mode_affichage"] == "photos" else 1)
            
            if st.button("Mettre à jour le Mur", use_container_width=True, type="primary"):
                save_config(new_mode.lower(), nouveau_titre)
                st.rerun()
            
            st.divider()
            if st.button("🧨 RESET TOTAL", use_container_width=True):
                for f in glob.glob(os.path.join(GALLERY_DIR, "*")): os.remove(f)
                with open(VOTES_FILE, "w") as f: json.dump({}, f)
                st.rerun()

    if st.session_state["authenticated"]:
        st.markdown('<div class="main-header-sticky">', unsafe_allow_html=True)
        c_title_main, c_logo_main = st.columns([2, 1])
        with c_title_main:
            st.markdown("<h1 style='margin-bottom:0;'>Console de Modération</h1>", unsafe_allow_html=True)
            st.caption(f"Sous-titre actuel : {config.get('titre_mur')}")
        if os.path.exists(LOGO_FILE):
            c_logo_main.image(LOGO_FILE, width=280) 
        st.link_button("🖥️ OUVRIR LE MUR LIVE", f"https://{st.context.headers.get('host', 'localhost')}/", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Galerie Master (8 colonnes vignettes / 4 colonnes liste)
        all_imgs = [f for f in glob.glob(os.path.join(GALLERY_DIR, "*")) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        sorted_imgs = sorted(all_imgs, key=os.path.getmtime, reverse=True)
        mode_vue = st.radio("Vue", ["Vignettes", "Liste"], horizontal=True, label_visibility="collapsed")
        
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
                                if st.button("Supprimer", key=f"bl_{idx}", use_container_width=True): os.remove(img_p); st.rerun()

# --- 6. INTERFACE UTILISATEUR (QR CODE) ---
elif est_utilisateur:
    st.title("📲 Participation")
    t1, t2 = st.tabs(["📸 Photo", "🗳️ Vote Vidéo"])
    with t1:
        f = st.file_uploader("Envoyer une photo", type=['jpg', 'png'])
        if f:
            with open(os.path.join(GALLERY_DIR, f"u_{random.randint(100,999)}.jpg"), "wb") as out: out.write(f.getbuffer())
            st.success("Photo envoyée !")
    with t2:
        st.subheader("Votez pour le projet gagnant :")
        video_choice = st.radio("Sélectionnez :", ["Projet 1 : Innovation", "Projet 2 : Équipe", "Projet 3 : Durabilité", "Projet 4 : Clients"])
        if st.button("Valider mon vote"):
            add_vote(video_choice); st.success("Vote pris en compte !")

# --- 7. MODE LIVE (MUR NOIR) ---
else:
    st.markdown("<style>:root { background-color: black; } [data-testid='stAppViewContainer'], .stApp { background-color: black !important; } [data-testid='stHeader'], footer { display: none !important; } </style>", unsafe_allow_html=True)
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=20000, key="refresh")
    except: pass
    
    config = load_config()
    sous_titre = config.get("titre_mur", "")
    
    if config["mode_affichage"] == "votes":
        st.markdown(f"""
            <div style='text-align:center; padding-top:40px; font-family:sans-serif;'>
                <h2 style='color:#E2001A; font-size:30px; margin-bottom:0;'>MUR PHOTO LIVE</h2>
                <h1 style='color:white; font-size:50px; margin-top:0;'>{sous_titre}</h1>
            </div>
        """, unsafe_allow_html=True)
        st.bar_chart(get_votes())
    else:
        img_list = [f for f in glob.glob(os.path.join(GALLERY_DIR, "*")) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
        qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        logo_b64 = ""
        if os.path.exists(LOGO_FILE):
            with open(LOGO_FILE, "rb") as f: logo_b64 = base64.b64encode(f.read()).decode()
        
        photos_html = "".join([f'<img src="data:image/png;base64,{base64.b64encode(open(p,"rb").read()).decode()}" class="photo" style="width:{random.randint(220,320)}px; top:{random.randint(10,70)}%; left:{random.randint(5,85)}%; animation
