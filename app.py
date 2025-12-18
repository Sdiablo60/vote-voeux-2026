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

config = {"mode_affichage": "attente", "titre_mur": "CONCOURS VIDÉO 2026", "vote_version": 1, "session_ouverte": False}
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r") as f: config = json.load(f)
    except: pass

VOTE_VERSION = config.get("vote_version", 1)

# Initialisation fichiers
if not os.path.exists(VOTES_FILE): json.dump({}, open(VOTES_FILE, "w"))
if not os.path.exists(PARTICIPANTS_FILE): json.dump([], open(PARTICIPANTS_FILE, "w"))

# --- 2. NAVIGATION ---
query_params = st.query_params
est_admin = query_params.get("admin") == "true"
est_utilisateur = query_params.get("mode") == "vote"

# --- 3. ADMINISTRATION ---
if est_admin:
    st.markdown("<style>div[data-testid='stSidebar'] button[kind='primary'] { background-color: #0000FF !important; color: white !important; }</style>", unsafe_allow_html=True)
    with st.sidebar:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE)
        if st.text_input("Code Admin", type="password") == "ADMIN_LIVE_MASTER":
            st.session_state["auth"] = True
        if st.session_state.get("auth"):
            st.subheader("🎮 Régie Mur")
            nouveau_titre = st.text_input("Sous-titre dynamique :", value=config.get("titre_mur"))
            session_active = st.checkbox("📢 Ouvrir la session de vote", value=config.get("session_ouverte", False))
            new_mode = st.radio("Mode Mur :", ["Attente (Admin)", "Live (Tout)", "Votes"], 
                                index=0 if config["mode_affichage"]=="attente" else (1 if config["mode_affichage"]=="live" else 2))
            
            if st.button("🔵 METTRE À JOUR LE MUR", type="primary", use_container_width=True):
                config["mode_affichage"] = "attente" if "Attente" in new_mode else ("live" if "Live" in new_mode else "votes")
                config["titre_mur"] = nouveau_titre
                config["session_ouverte"] = session_active
                with open(CONFIG_FILE, "w") as f: json.dump(config, f)
                st.rerun()
            
            st.divider()
            if st.button("🔴 RESET COMPLET", type="secondary", use_container_width=True):
                config["vote_version"] += 1
                config["session_ouverte"] = False
                with open(CONFIG_FILE, "w") as f: json.dump(config, f)
                json.dump({}, open(VOTES_FILE, "w"))
                json.dump([], open(PARTICIPANTS_FILE, "w"))
                st.rerun()

    if st.session_state.get("auth"):
        st.title("Console de Régie")
        st.metric("Nombre de participants connectés", len(json.load(open(PARTICIPANTS_FILE))))
        st.bar_chart(json.load(open(VOTES_FILE)))

# --- 4. INTERFACE UTILISATEUR (TÉLÉPHONE) ---
elif est_utilisateur:
    st.markdown("<style>.stApp { background-color: white !important; }</style>", unsafe_allow_html=True)
    st.title("🗳️ Vote Transdev")
    vote_key = f"transdev_v{VOTE_VERSION}"
    components.html(f'<script>if(localStorage.getItem("{vote_key}")){{window.parent.postMessage({{type:"voted"}},"*");}}</script>', height=0)

    if st.session_state.get("voted"):
        st.success("✅ Vote enregistré. Merci !")
    else:
        if "user_pseudo" not in st.session_state:
            with st.form("pseudo_form"):
                p = st.text_input("Entrez votre Prénom / Pseudo :")
                if st.form_submit_button("VALIDER"):
                    if p:
                        st.session_state["user_pseudo"] = p
                        parts = json.load(open(PARTICIPANTS_FILE))
                        if p not in parts:
                            parts.append(p)
                            json.dump(parts, open(PARTICIPANTS_FILE, "w"))
                        st.rerun()
                    else: st.error("Pseudo requis.")
        else:
            if not config.get("session_ouverte", False):
                st.markdown(f"<div style='text-align:center; padding:40px; border:2px dashed #E2001A; border-radius:15px; margin-top:20px;'><h2 style='color:#E2001A;'>⌛ En attente ouverture des votes...</h2><p>Bienvenue {st.session_state['user_pseudo']}. Le formulaire apparaîtra bientôt.</p></div>", unsafe_allow_html=True)
                if st.button("Actualiser"): st.rerun()
            else:
                with st.form("vote_real"):
                    options = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]
                    choix = st.multiselect("Votre Top 3 :", options, max_selections=3)
                    if st.form_submit_button("CONFIRMER MON VOTE"):
                        if choix:
                            vts = json.load(open(VOTES_FILE))
                            for c in choix: vts[c] = vts.get(c, 0) + 1
                            json.dump(vts, open(VOTES_FILE, "w"))
                            components.html(f'<script>localStorage.setItem("{vote_key}", "true"); window.parent.location.reload();</script>', height=0)
                            st.session_state["voted"] = True
                            st.rerun()
                        else: st.error("Choisissez au moins 1 option.")

# --- 5. MUR SOCIAL ---
else:
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'], footer { display: none !important; }</style>", unsafe_allow_html=True)
    
    # Génération du QR Code
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    # BANDEAU DOUBLE QR CODE (Attente)
    attente_html = ""
    if not config.get("session_ouverte", False):
        attente_html = f"""
        <div style="display: flex; align-items: center; justify-content: center; gap: 40px; margin-top: 25px;">
            <div style="background: white; padding: 10px; border-radius: 10px; border: 3px solid #E2001A;">
                <img src="data:image/png;base64,{qr_b64}" width="100">
            </div>
            <div style="background:#E2001A; color:white; padding:15px 40px; border-radius:12px; font-size:35px; font-weight:bold; border:3px solid white; animation: blinker 1.5s linear infinite;">
                ⌛ En attente ouverture des votes...
            </div>
            <div style="background: white; padding: 10px; border-radius: 10px; border: 3px solid #E2001A;">
                <img src="data:image/png;base64,{qr_b64}" width="100">
            </div>
        </div>
        <style>@keyframes blinker {{ 50% {{ opacity: 0; }} }}</style>
        """

    st.markdown(f"""
        <div style="text-align:center; padding-top:20px; font-family:sans-serif;">
            <p style="color:#E2001A; font-size:30px; font-weight:bold; margin:0;">MUR PHOTO LIVE</p>
            <h1 style="color:white; font-size:55px; margin:0;">{config.get('titre_mur')}</h1>
            {attente_html}
        </div>
    """, unsafe_allow_html=True)

    # Photos ou Votes
    if config["mode_affichage"] == "votes":
        st.bar_chart(json.load(open(VOTES_FILE)))
    else:
        img_list = glob.glob(os.path.join(ADMIN_DIR, "*"))
        if config["mode_affichage"] == "live": img_list += glob.glob(os.path.join(GALLERY_DIR, "*"))
        
        photos_html = "".join([f'<img src="data:image/png;base64,{base64.b64encode(open(p,"rb").read()).decode()}" class="photo" style="width:280px; top:{random.randint(35,65)}%; left:{random.randint(5,80)}%; animation-duration:{random.uniform(10,15)}s;">' for p in img_list[-12:]])
        components.html(f"""<style>.photo {{ position:absolute; border:5px solid white; border-radius:15px; animation:move alternate infinite ease-in-out; }} @keyframes move {{ from {{ transform:rotate(-3deg); }} to {{ transform:translate(40px,40px) rotate(3deg); }} }}</style><div style="width:100%; height:450px; position:relative;">{photos_html}</div>""", height=500)

    # Bas de page avec Compteur
    nb_p = len(json.load(open(PARTICIPANTS_FILE)))
    st.markdown(f"""
        <div style="position:fixed; bottom:30px; left:50%; transform:translateX(-50%); background:white; padding:10px 30px; border-radius:15px; border:5px solid #E2001A; text-align:center; z-index:1000;">
            <p style="margin:0; font-weight:bold; font-size:24px; color:black; font-family:sans-serif;">{nb_p} PARTICIPANTS CONNECTÉS</p>
        </div>
    """, unsafe_allow_html=True)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=5000, key="wall_refresh")
    except: pass
