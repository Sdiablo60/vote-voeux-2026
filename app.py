import streamlit as st
import os
import glob
import base64
import qrcode
import json
import random
from io import BytesIO
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Social Wall Pro", layout="wide")

GALLERY_DIR = "galerie_images"
ADMIN_DIR = "galerie_admin" # Nouveau dossier pour vos photos officielles
LOGO_FILE = "logo_entreprise.png"
VOTES_FILE = "votes.json"
PARTICIPANTS_FILE = "participants.json"
CONFIG_FILE = "config_mur.json"

for d in [GALLERY_DIR, ADMIN_DIR]:
    if not os.path.exists(d): os.makedirs(d)

config = {"mode_affichage": "attente", "titre_mur": "CONCOURS VIDÉO 2026", "vote_version": 1}
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f: config = json.load(f)

VOTE_VERSION = config.get("vote_version", 1)

# --- 2. ADMIN (CONSOLE AVEC DOUBLE GALERIE) ---
query_params = st.query_params
est_admin = query_params.get("admin") == "true"
est_utilisateur = query_params.get("mode") == "vote"

if est_admin:
    st.markdown("<style>div[data-testid='stSidebar'] button[kind='primary'] { background-color: #0000FF !important; color: white !important; } div[data-testid='stSidebar'] button[kind='secondary'] { background-color: #FF0000 !important; color: white !important; }</style>", unsafe_allow_html=True)
    
    with st.sidebar:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE)
        if st.text_input("Code Admin", type="password") == "ADMIN_LIVE_MASTER":
            st.session_state["auth"] = True
            
        if st.session_state.get("auth"):
            st.subheader("🎮 Contrôle du Mur")
            nouveau_titre = st.text_input("Sous-titre :", value=config.get("titre_mur"))
            # Ajout du mode "Attente"
            new_mode = st.radio("Mode Mur :", ["Attente (Photos Admin uniquement)", "Live (Tout afficher)", "Votes"], 
                                index=0 if config["mode_affichage"]=="attente" else (1 if config["mode_affichage"]=="live" else 2))
            
            mode_key = "attente" if "Attente" in new_mode else ("live" if "Live" in new_mode else "votes")

            if st.button("🔵 VALIDER : MISE À JOUR MUR", type="primary", use_container_width=True):
                with open(CONFIG_FILE, "w") as f: 
                    json.dump({"mode_affichage": mode_key, "titre_mur": nouveau_titre, "vote_version": VOTE_VERSION}, f)
                st.rerun()

    if st.session_state.get("auth"):
        t1, t2 = st.tabs(["📸 Galerie Équipes (Admin)", "📱 Photos Utilisateurs"])
        
        with t1:
            st.subheader("Photos Officielles (Visibles en mode Attente)")
            up_admin = st.file_uploader("Ajouter des photos d'équipes", accept_multiple_files=True, key="up_admin")
            if up_admin:
                for f in up_admin:
                    with open(os.path.join(ADMIN_DIR, f.name), "wb") as out: out.write(f.getbuffer())
                st.rerun()
            
            imgs_admin = glob.glob(os.path.join(ADMIN_DIR, "*"))
            for i in range(0, len(imgs_admin), 8):
                cols = st.columns(8)
                for j in range(8):
                    if i+j < len(imgs_admin):
                        img = imgs_admin[i+j]
                        cols[j].image(img, use_container_width=True)
                        if cols[j].button("🗑️", key=f"del_adm_{i+j}"): os.remove(img); st.rerun()

        with t2:
            st.subheader("Photos reçues par les téléphones")
            # (Même logique de grille 8 colonnes pour les photos utilisateurs)
            imgs_user = glob.glob(os.path.join(GALLERY_DIR, "*"))
            if st.button("🧨 VIDER LES PHOTOS UTILISATEURS", type="secondary"):
                for f in imgs_user: os.remove(f)
                st.rerun()

# --- 3. MUR LIVE (LOGIQUE DE FILTRE) ---
elif not est_utilisateur:
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'] { display: none; }</style>", unsafe_allow_html=True)
    
    # Sélection des images selon le mode
    if config["mode_affichage"] == "attente":
        # UNIQUEMENT les photos du dossier ADMIN
        img_list = [f for f in glob.glob(os.path.join(ADMIN_DIR, "*")) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    else:
        # TOUTES les photos (Admin + Utilisateurs)
        img_list = [f for f in glob.glob(os.path.join(ADMIN_DIR, "*"))] + [f for f in glob.glob(os.path.join(GALLERY_DIR, "*"))]
        img_list = [f for f in img_list if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    # Génération du Mur (QR Code + Titres + Photos filtrées)
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    st.markdown(f"<div style='text-align:center; padding-top:20px;'><p style='color:#E2001A; font-size:30px; font-weight:bold; margin:0;'>MUR PHOTO LIVE</p><h1 style='color:white; font-size:55px; margin-top:0;'>{config.get('titre_mur')}</h1></div>", unsafe_allow_html=True)

    if config["mode_affichage"] == "votes":
        # (Affichage du graphique de vote comme précédemment)
        st.bar_chart(json.load(open(VOTES_FILE)))
    else:
        photos_html = ""
        for p in img_list[-15:]:
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:280px; top:{random.randint(20,65)}%; left:{random.randint(5,80)}%; animation-duration:{random.uniform(10,15)}s;">'
        
        html_content = f"""
        <style>.photo {{ position:absolute; border:6px solid white; border-radius:15px; animation:move alternate infinite ease-in-out; }} @keyframes move {{ from {{ transform:rotate(-3deg); }} to {{ transform:translate(40px,40px) rotate(3deg); }} }}</style>
        <div style="width:100%; height:550px; position:relative;">{photos_html}</div>
        <div style="position:fixed; bottom:40px; left:50%; transform:translateX(-50%); background:white; padding:15px; border-radius:20px; border:5px solid #E2001A; text-align:center;"><img src="data:image/png;base64,{qr_b64}" width="160"><p style="margin:5px 0 0 0; font-weight:bold; font-size:18px; color:black;">{len(json.load(open(PARTICIPANTS_FILE)))} PARTICIPANTS</p></div>
        """
        components.html(html_content, height=800)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=15000, key="global_refresh")
    except: pass

# --- 4. UTILISATEUR (INCHANGÉ) ---
else:
    # (Code utilisateur avec pseudo et vote Top 3...)
