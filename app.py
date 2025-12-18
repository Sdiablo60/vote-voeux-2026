import streamlit as st
import os
import glob
import base64
import qrcode
import json
import random
from io import BytesIO
import streamlit.components.v1 as components

# --- CONFIGURATION ---
st.set_page_config(page_title="Social Wall Pro", layout="wide")

GALLERY_DIR = "galerie_images"
ADMIN_DIR = "galerie_admin"
LOGO_FILE = "logo_entreprise.png"
VOTES_FILE = "votes.json"
PARTICIPANTS_FILE = "participants.json"
CONFIG_FILE = "config_mur.json"

for d in [GALLERY_DIR, ADMIN_DIR]:
    if not os.path.exists(d): os.makedirs(d)

# Chargement config
config = {"mode_affichage": "attente", "titre_mur": "CONCOURS VIDÉO 2026", "vote_version": 1, "session_ouverte": False}
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r") as f: config = json.load(f)
    except: pass

# --- LOGIQUE DE NAVIGATION ---
query_params = st.query_params
est_admin = query_params.get("admin") == "true"
est_utilisateur = query_params.get("mode") == "vote"

if est_admin:
    # --- CONSOLE ADMIN ---
    st.markdown("<style>div[data-testid='stSidebar'] button[kind='primary'] { background-color: #0000FF !important; color: white !important; }</style>", unsafe_allow_html=True)
    with st.sidebar:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE)
        if st.text_input("Code Admin", type="password") == "ADMIN_LIVE_MASTER":
            st.session_state["auth"] = True
        if st.session_state.get("auth"):
            st.subheader("🎮 Régie Mur")
            nouveau_titre = st.text_input("Sous-titre dynamique :", value=config.get("titre_mur"))
            session_active = st.checkbox("🔔 Afficher 'En attente des votes'", value=config.get("session_ouverte", False))
            new_mode = st.radio("Mode Affichage :", ["Attente (Admin)", "Live (Tout)", "Votes"], 
                                index=0 if config["mode_affichage"]=="attente" else (1 if config["mode_affichage"]=="live" else 2))
            
            if st.button("🔵 METTRE À JOUR LE MUR", type="primary", use_container_width=True):
                config["mode_affichage"] = "attente" if "Attente" in new_mode else ("live" if "Live" in new_mode else "votes")
                config["titre_mur"] = nouveau_titre
                config["session_ouverte"] = session_active
                with open(CONFIG_FILE, "w") as f: json.dump(config, f)
                st.rerun()

    if st.session_state.get("auth"):
        c1, c2 = st.columns([2, 1])
        c1.title("Console de Régie")
        if os.path.exists(LOGO_FILE): c2.image(LOGO_FILE, width=250)
        try: st.bar_chart(json.load(open(VOTES_FILE)))
        except: pass

elif not est_utilisateur:
    # --- MUR LIVE (AFFICHAGE CORRIGÉ) ---
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'], footer { display: none !important; }</style>", unsafe_allow_html=True)
    
    # 1. Préparation du bandeau d'attente
    attente_html = ""
    if config.get("session_ouverte", False):
        attente_html = """
        <div style="margin-top:20px;">
            <span style="background:#E2001A; color:white; padding:12px 35px; border-radius:12px; font-size:32px; font-weight:bold; border:3px solid white; animation: blinker 1.5s linear infinite; display: inline-block;">
                ⌛ En attente ouverture des votes...
            </span>
        </div>
        <style>@keyframes blinker { 50% { opacity: 0; } }</style>
        """

    # 2. Affichage des titres (Le bloc qui posait problème)
    st.markdown(f"""
        <div style="text-align:center; padding-top:20px; font-family:sans-serif;">
            <p style="color:#E2001A; font-size:30px; font-weight:bold; margin:0;">MUR PHOTO LIVE</p>
            <h1 style="color:white; font-size:55px; margin:0;">{config.get('titre_mur', 'CONCOURS VIDÉO 2026')}</h1>
            {attente_html}
        </div>
    """, unsafe_allow_html=True)

    # 3. Contenu (Photos ou Votes)
    if config["mode_affichage"] == "votes":
        try:
            v_data = json.load(open(VOTES_FILE))
            if v_data: st.bar_chart(v_data)
        except: pass
    else:
        img_list = glob.glob(os.path.join(ADMIN_DIR, "*"))
        if config["mode_affichage"] == "live":
            img_list += glob.glob(os.path.join(GALLERY_DIR, "*"))
        
        photos_html = ""
        for p in img_list[-12:]:
            try:
                with open(p, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                    photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:280px; top:{random.randint(35,65)}%; left:{random.randint(5,80)}%; animation-duration:{random.uniform(10,15)}s;">'
            except: pass
        
        components.html(f"""<style>.photo {{ position:absolute; border:5px solid white; border-radius:15px; animation:move alternate infinite ease-in-out; }} @keyframes move {{ from {{ transform:rotate(-3deg); }} to {{ transform:translate(40px,40px) rotate(3deg); }} }}</style><div style="width:100%; height:450px; position:relative;">{photos_html}</div>""", height=500)

    # 4. QR Code & Compteur
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
    try: nb_p = len(json.load(open(PARTICIPANTS_FILE)))
    except: nb_p = 0
    
    st.markdown(f"""<div style="position:fixed; bottom:30px; left:50%; transform:translateX(-50%); background:white; padding:10px; border-radius:15px; border:5px solid #E2001A; text-align:center;"><img src="data:image/png;base64,{qr_b64}" width="140"><p style="margin:5px 0 0 0; font-weight:bold; font-size:22px; color:black;">{nb_p} PARTICIPANTS</p></div>""", unsafe_allow_html=True)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=10000, key="refresh")
    except: pass

else:
    # --- INTERFACE VOTE ---
    st.title("🗳️ Vote Transdev")
    # (Logique de vote habituelle)
    pass
