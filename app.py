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
ADMIN_DIR = "galerie_admin"
LOGO_FILE = "logo_entreprise.png"
VOTES_FILE = "votes.json"
PARTICIPANTS_FILE = "participants.json"
CONFIG_FILE = "config_mur.json"

for d in [GALLERY_DIR, ADMIN_DIR]:
    if not os.path.exists(d): os.makedirs(d)

# Chargement robuste de la config
config = {"mode_affichage": "attente", "titre_mur": "CONCOURS VIDÉO 2026", "vote_version": 1, "session_ouverte": False}
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r") as f: config = json.load(f)
    except: pass

VOTE_VERSION = config.get("vote_version", 1)

# --- 2. ADMIN ---
query_params = st.query_params
est_admin = query_params.get("admin") == "true"
est_utilisateur = query_params.get("mode") == "vote"

if est_admin:
    st.markdown("""
        <style>
        div[data-testid="stSidebar"] button[kind="primary"] { background-color: #0000FF !important; color: white !important; }
        div[data-testid="stSidebar"] button[kind="secondary"] { background-color: #FF0000 !important; color: white !important; }
        </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE)
        if st.text_input("Code Admin", type="password") == "ADMIN_LIVE_MASTER":
            st.session_state["auth"] = True
            
        if st.session_state.get("auth"):
            st.subheader("🎮 Contrôle du Mur")
            nouveau_titre = st.text_input("Sous-titre :", value=config.get("titre_mur"))
            
            # État du bandeau d'attente
            session_active = st.toggle("📢 Afficher 'En attente des votes'", value=config.get("session_ouverte", False))
            
            new_mode = st.radio("Mode Mur :", ["Attente (Admin)", "Live (Tout)", "Votes"], 
                                index=0 if config["mode_affichage"]=="attente" else (1 if config["mode_affichage"]=="live" else 2))
            
            mode_key = "attente" if "Attente" in new_mode else ("live" if "Live" in new_mode else "votes")

            if st.button("🔵 VALIDER : MISE À JOUR MUR", type="primary", use_container_width=True):
                config["mode_affichage"] = mode_key
                config["titre_mur"] = nouveau_titre
                config["session_ouverte"] = session_active
                with open(CONFIG_FILE, "w") as f: json.dump(config, f)
                st.rerun()

# --- 3. MUR LIVE (LOGIQUE CORRIGÉE) ---
elif not est_utilisateur:
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'] { display: none; } footer {display:none;}</style>", unsafe_allow_html=True)
    
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    # 1. Double Titre fixe en haut
    st.markdown(f"""
        <div style='text-align:center; padding-top:20px; font-family:sans-serif;'>
            <p style='color:#E2001A; font-size:30px; font-weight:bold; margin:0;'>MUR PHOTO LIVE</p>
            <h1 style='color:white; font-size:55px; margin-top:0;'>{config.get('titre_mur')}</h1>
        </div>
    """, unsafe_allow_html=True)

    # 2. BANDEAU D'ATTENTE (S'affiche par-dessus tout si activé)
    if config.get("session_ouverte", False):
        st.markdown("""
            <div style='position: fixed; top: 180px; width: 100%; text-align: center; z-index: 2000;'>
                <div style='display: inline-block; background: #E2001A; color: white; padding: 15px 40px; 
                     border-radius: 50px; font-size: 32px; font-weight: bold; border: 4px solid white; 
                     box-shadow: 0 0 30px rgba(226,0,26,0.8); animation: flash 1.5s infinite;'>
                    ⌛ En attente ouverture des votes...
                </div>
            </div>
            <style>@keyframes flash { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }</style>
        """, unsafe_allow_html=True)

    # 3. Contenu (Votes ou Photos)
    if config["mode_affichage"] == "votes":
        try:
            v_data = json.load(open(VOTES_FILE))
            if any(v > 0 for v in v_data.values()): st.bar_chart(v_data)
        except: pass
    else:
        # Filtrage photos Admin vs Tout
        path = ADMIN_DIR if config["mode_affichage"] == "attente" else "*"
        img_list = glob.glob(os.path.join(ADMIN_DIR, "*"))
        if config["mode_affichage"] == "live":
            img_list += glob.glob(os.path.join(GALLERY_DIR, "*"))
        
        photos_html = ""
        for p in img_list[-12:]:
            try:
                with open(p, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                    photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:280px; top:{random.randint(25,65)}%; left:{random.randint(5,80)}%; animation-duration:{random.uniform(10,15)}s;">'
            except: pass
        
        html_content = f"""
        <style>.photo {{ position:absolute; border:6px solid white; border-radius:15px; animation:move alternate infinite ease-in-out; }} @keyframes move {{ from {{ transform:rotate(-3deg); }} to {{ transform:translate(40px,40px) rotate(3deg); }} }}</style>
        <div style="width:100%; height:500px; position:relative;">{photos_html}</div>
        """
        components.html(html_content, height=600)

    # 4. QR Code fixe en bas
    nb_p = 0
    try: nb_p = len(json.load(open(PARTICIPANTS_FILE)))
    except: pass
    
    st.markdown(f"""
        <div style='position:fixed; bottom:40px; left:50%; transform:translateX(-50%); background:white; padding:15px; border-radius:20px; border:5px solid #E2001A; text-align:center; z-index:1000;'>
            <img src="data:image/png;base64,{qr_b64}" width="150">
            <p style="margin:5px 0 0 0; font-weight:bold; font-size:22px; color:black; font-family:sans-serif;">{nb_p} PARTICIPANTS</p>
        </div>
    """, unsafe_allow_html=True)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=10000, key="wall_refresh")
    except: pass

# --- 4. UTILISATEUR (INCHANGÉ) ---
else:
    # (Le reste du code utilisateur pour le vote reste identique à la version précédente)
    pass
