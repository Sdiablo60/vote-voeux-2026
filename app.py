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

# Chargement de la config avec sécurité
config = {"mode_affichage": "attente", "titre_mur": "CONCOURS VIDÉO 2026", "vote_version": 1, "session_ouverte": False}
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r") as f: config = json.load(f)
    except: pass

VOTE_VERSION = config.get("vote_version", 1)

# --- 2. NAVIGATION ---
query_params = st.query_params
est_admin = query_params.get("admin") == "true"
est_utilisateur = query_params.get("mode") == "vote"

# --- 3. ADMIN (CONSOLE) ---
if est_admin:
    st.markdown("""<style>div[data-testid='stSidebar'] button[kind='primary'] { background-color: #0000FF !important; color: white !important; }</style>""", unsafe_allow_html=True)
    with st.sidebar:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE)
        if st.text_input("Code Admin", type="password") == "ADMIN_LIVE_MASTER":
            st.session_state["auth"] = True
            
        if st.session_state.get("auth"):
            st.subheader("🎮 Régie Mur")
            nouveau_titre = st.text_input("Sous-titre dynamique :", value=config.get("titre_mur"))
            
            # État du message d'attente
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
        st.metric("Participants", len(json.load(open(PARTICIPANTS_FILE))))
        st.bar_chart(json.load(open(VOTES_FILE)))

# --- 4. MUR LIVE (AFFICHAGE CORRIGÉ) ---
elif not est_utilisateur:
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'] { display: none; } footer {display:none;}</style>", unsafe_allow_html=True)
    
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    # BLOC TITRE AVEC MESSAGE D'ATTENTE CONDITIONNEL
    attente_html = ""
    if config.get("session_ouverte", False):
        attente_html = f"""
            <div style='margin-top:20px;'>
                <span style='background:#E2001A; color:white; padding:12px 35px; border-radius:12px; font-size:32px; font-weight:bold; border:3px solid white; animation: blinker 1.5s linear infinite; display: inline-block;'>
                    ⌛ En attente ouverture des votes...
                </span>
            </div>
            <style>@keyframes blinker {{ 50% {{ opacity: 0; }} }}</style>
        """

    st.markdown(f"""
        <div style='text-align:center; padding-top:20px; font-family:sans-serif;'>
            <p style='color:#E2001A; font-size:30px; font-weight:bold; margin:0;'>MUR PHOTO LIVE</p>
            <h1 style='color:white; font-size:55px; margin:0;'>{config.get('titre_mur')}</h1>
            {attente_html}
        </div>
    """, unsafe_allow_html=True)

    if config["mode_affichage"] == "votes":
        v_data = json.load(open(VOTES_FILE))
        if any(v > 0 for v in v_data.values()): st.bar_chart(v_data)
    else:
        # Affichage des photos
        img_list = glob.glob(os.path.join(ADMIN_DIR, "*"))
        if config["mode_affichage"] == "live":
            img_list += glob.glob(os.path.join(GALLERY_DIR, "*"))
        
        photos_html = ""
        for p in img_list[-12:]:
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:280px; top:{random.randint(35,65)}%; left:{random.randint(5,80)}%; animation-duration:{random.uniform(10,15)}s;">'
        
        html_content = f"""<style>.photo {{ position:absolute; border:5px solid white; border-radius:15px; animation:move alternate infinite ease-in-out; }} @keyframes move {{ from {{ transform:rotate(-3deg); }} to {{ transform:translate(40px,40px) rotate(3deg); }} }}</style><div style="width:100%; height:450px; position:relative;">{photos_html}</div>"""
        components.html(html_content, height=500)

    # BAS DE PAGE : QR CODE ET COMPTEUR
    nb_p = len(json.load(open(PARTICIPANTS_FILE)))
    st.markdown(f"""
        <div style='position:fixed; bottom:30px; left:50%; transform:translateX(-50%); background:white; padding:10px; border-radius:15px; border:5px solid #E2001A; text-align:center;'>
            <img src="data:image/png;base64,{qr_b64}" width="140">
            <p style="margin:5px 0 0 0; font-weight:bold; font-size:22px; color:black; font-family:sans-serif;">{nb_p} PARTICIPANTS</p>
        </div>
    """, unsafe_allow_html=True)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=10000, key="wall_refresh")
    except: pass

# --- 5. UTILISATEUR (VOTE UNIQUE) ---
elif est_utilisateur:
    st.title("🗳️ Vote Transdev")
    vote_key = f"transdev_v{VOTE_VERSION}"
    components.html(f"<script>if(localStorage.getItem('{vote_key}')){{window.parent.postMessage({{type:'voted'}},'*');}}</script>", height=0)
    
    if st.session_state.get("voted"):
        st.success("✅ Vote déjà enregistré sur cet appareil.")
    else:
        pseudo = st.text_input("Pseudo / Prénom :")
        options = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]
        choix = st.multiselect("Votre Top 3 :", options, max_selections=3)
        if st.button("Confirmer le vote"):
            if pseudo and (0 < len(choix) <= 3):
                with open(PARTICIPANTS_FILE, "r") as f: parts = json.load(f)
                if pseudo not in parts: parts.append(pseudo); json.dump(parts, open(PARTICIPANTS_FILE, "w"))
                vts = json.load(open(VOTES_FILE))
                for c in choix: vts[c] = vts.get(c, 0) + 1
                with open(VOTES_FILE, "w") as f: json.dump(vts, f)
                components.html(f"""<script>localStorage.setItem('{vote_key}', 'true'); setTimeout(()=>{{window.parent.location.reload();}},500);</script>""", height=0)
                st.session_state["voted"] = True
            else: st.error("Pseudo + 1 à 3 choix requis.")
