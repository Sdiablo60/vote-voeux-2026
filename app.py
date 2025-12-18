import streamlit as st
import os
import glob
import base64
import qrcode
import json
import random
from io import BytesIO
import streamlit.components.v1 as components

# --- 1. CONFIGURATION INITIALE ---
st.set_page_config(page_title="Social Wall Pro", layout="wide")

GALLERY_DIR = "galerie_images"
ADMIN_DIR = "galerie_admin"
LOGO_FILE = "logo_entreprise.png"
VOTES_FILE = "votes.json"
PARTICIPANTS_FILE = "participants.json"
CONFIG_FILE = "config_mur.json"

for d in [GALLERY_DIR, ADMIN_DIR]:
    if not os.path.exists(d): os.makedirs(d)

# Chargement de la configuration
config = {"mode_affichage": "attente", "titre_mur": "CONCOURS VIDÉO 2026", "vote_version": 1, "session_ouverte": False}
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r") as f: config = json.load(f)
    except: pass

VOTE_VERSION = config.get("vote_version", 1)

# Initialisation des fichiers de données si inexistants
if not os.path.exists(VOTES_FILE): json.dump({}, open(VOTES_FILE, "w"))
if not os.path.exists(PARTICIPANTS_FILE): json.dump([], open(PARTICIPANTS_FILE, "w"))

# --- 2. NAVIGATION ---
query_params = st.query_params
est_admin = query_params.get("admin") == "true"
est_utilisateur = query_params.get("mode") == "vote"

# --- 3. MODE ADMINISTRATION ---
if est_admin:
    st.markdown("""<style>
        div[data-testid='stSidebar'] button[kind='primary'] { background-color: #0000FF !important; color: white !important; }
        div[data-testid='stSidebar'] button[kind='secondary'] { background-color: #FF0000 !important; color: white !important; }
    </style>""", unsafe_allow_html=True)
    
    with st.sidebar:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE)
        pwd = st.text_input("Code Admin", type="password")
        if pwd == "ADMIN_LIVE_MASTER":
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
                # On incrémente la version pour bloquer les anciens votes et vider les fichiers
                config["vote_version"] = VOTE_VERSION + 1
                config["session_ouverte"] = False
                config["mode_affichage"] = "attente"
                with open(CONFIG_FILE, "w") as f: json.dump(config, f)
                with open(VOTES_FILE, "w") as f: json.dump({}, f)
                with open(PARTICIPANTS_FILE, "w") as f: json.dump([], f)
                st.rerun()

    if st.session_state.get("auth"):
        st.title("Console de Régie")
        st.metric("Participants connectés", len(json.load(open(PARTICIPANTS_FILE))))
        st.bar_chart(json.load(open(VOTES_FILE)))

# --- 4. MODE UTILISATEUR (TÉLÉPHONE) ---
elif est_utilisateur:
    st.markdown("<style>.stApp { background-color: black !important; color: white !important; }</style>", unsafe_allow_html=True)
    st.title("🗳️ Vote Transdev")
    vote_key = f"transdev_v{VOTE_VERSION}"
    
    # Sécurité LocalStorage
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
                            parts.append(p); json.dump(parts, open(PARTICIPANTS_FILE, "w"))
                        st.rerun()
                    else: st.error("Pseudo requis.")
        else:
            if not config.get("session_ouverte", False):
                # Auto-refresh pour détecter l'ouverture des votes sans cliquer
                try:
                    from streamlit_autorefresh import st_autorefresh
                    st_autorefresh(interval=5000, key="mobile_check")
                except: pass

                st.markdown(f"""
                    <div style='text-align:center; padding:40px; border:2px dashed #E2001A; border-radius:15px; margin-top:20px;'>
                        <h2 style='color:#E2001A;'>⌛ En attente ouverture des votes...</h2>
                        <p style='color:white;'>Bienvenue {st.session_state['user_pseudo']}.<br>Le formulaire apparaîtra automatiquement.</p>
                    </div>
                """, unsafe_allow_html=True)
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

# --- 5. MODE MUR LIVE (SOCIAL) ---
else:
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'], footer { display: none !important; }</style>", unsafe_allow_html=True)
    
    # Données & QR
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
    
    try:
        with open(PARTICIPANTS_FILE, "r") as f: nb_p = len(json.load(f))
        with open(VOTES_FILE, "r") as f: v_data = json.load(f)
    except: nb_p = 0; v_data = {}

    # Bandeau d'attente Double QR
    attente_html = ""
    if not config.get("session_ouverte", False):
        attente_html = f"""
        <div style="display: flex; align-items: center; justify-content: center; gap: 40px; margin-top: 25px;">
            <div style="background: white; padding: 8px; border-radius: 10px; border: 3px solid #E2001A;"><img src="data:image/png;base64,{qr_b64}" width="110"></div>
            <div style="background:#E2001A; color:white; padding:15px 40px; border-radius:12px; font-size:32px; font-weight:bold; border:3px solid white; animation: blinker 1.5s linear infinite;">⌛ En attente ouverture des votes...</div>
            <div style="background: white; padding: 8px; border-radius: 10px; border: 3px solid #E2001A;"><img src="data:image/png;base64,{qr_b64}" width="110"></div>
        </div>
        """

    # Bloc Header : Titre + Compteur Participants
    st.markdown(f"""
        <style>@keyframes blinker {{ 50% {{ opacity: 0; }} }}</style>
        <div style="text-align:center; padding-top:20px; font-family:sans-serif;">
            <p style="color:#E2001A; font-size:30px; font-weight:bold; margin:0;">MUR PHOTO LIVE</p>
            <div style="background: white; display: inline-block; padding: 8px 30px; border-radius: 25px; margin: 15px 0; border: 3px solid #E2001A;">
                <p style="color: black; font-size: 26px; font-weight: bold; margin: 0;">{nb_p} PARTICIPANTS CONNECTÉS</p>
            </div>
            <h1 style="color:white; font-size:58px; margin:5px 0;">{config.get('titre_mur')}</h1>
            {attente_html}
        </div>
    """, unsafe_allow_html=True)

    # Affichage dynamique (Graphique ou Photos)
    # Correction : On n'affiche le graphique que si le mode est "votes" ET qu'il y a des données
    if config["mode_affichage"] == "votes" and any(v > 0 for v in v_data.values()):
        st.bar_chart(v_data)
    else:
        # Galerie photos
        img_list = glob.glob(os.path.join(ADMIN_DIR, "*"))
        if config["mode_affichage"] == "live":
            img_list += glob.glob(os.path.join(GALLERY_DIR, "*"))
        
        if img_list:
            photos_html = "".join([f'<img src="data:image/png;base64,{base64.b64encode(open(p,"rb").read()).decode()}" class="photo" style="width:280px; top:{random.randint(45,75)}%; left:{random.randint(5,85)}%; animation-duration:{random.uniform(10,15)}s;">' for p in img_list[-12:]])
            components.html(f"""<style>.photo {{ position:absolute; border:5px solid white; border-radius:15px; animation:move alternate infinite ease-in-out; box-shadow: 5px 5px 15px rgba(0,0,0,0.5); }} @keyframes move {{ from {{ transform:rotate(-3deg); }} to {{ transform:translate(40px,40px) rotate(3deg); }} }}</style><div style="width:100%; height:400px; position:relative;">{photos_html}</div>""", height=450)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=5000, key="wall_refresh")
    except: pass
