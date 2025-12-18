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

# Valeurs par défaut avec état de session
config = {"mode_affichage": "attente", "titre_mur": "CONCOURS VIDÉO 2026", "vote_version": 1, "session_ouverte": False}
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f: config = json.load(f)

VOTE_VERSION = config.get("vote_version", 1)

if not os.path.exists(VOTES_FILE):
    with open(VOTES_FILE, "w") as f: json.dump({}, f)
if not os.path.exists(PARTICIPANTS_FILE):
    with open(PARTICIPANTS_FILE, "w") as f: json.dump([], f)

# --- 2. NAVIGATION ---
query_params = st.query_params
est_admin = query_params.get("admin") == "true"
est_utilisateur = query_params.get("mode") == "vote"

# --- 3. ADMIN ---
if est_admin:
    st.markdown("""
        <style>
        div[data-testid="stSidebar"] button[kind="primary"] { background-color: #0000FF !important; color: white !important; }
        div[data-testid="stSidebar"] button[kind="secondary"] { background-color: #FF0000 !important; color: white !important; }
        .stButton>button[key="start_btn"] { background-color: #28a745 !important; color: white !important; font-weight: bold !important; border: 2px solid #1e7e34 !important; }
        </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE)
        if st.text_input("Code Admin", type="password") == "ADMIN_LIVE_MASTER":
            st.session_state["auth"] = True
            
        if st.session_state.get("auth"):
            st.subheader("🎮 Contrôle du Mur")
            nouveau_titre = st.text_input("Sous-titre :", value=config.get("titre_mur"))
            new_mode = st.radio("Mode Mur :", ["Attente (Photos Admin)", "Live (Tout afficher)", "Votes"], 
                                index=0 if config["mode_affichage"]=="attente" else (1 if config["mode_affichage"]=="live" else 2))
            
            mode_key = "attente" if "Attente" in new_mode else ("live" if "Live" in new_mode else "votes")

            # BOUTON VERT : DÉMARRER LA SESSION (Affiche le texte d'attente sur le mur)
            if not config.get("session_ouverte", False):
                if st.button("🚀 LANCER L'ANNONCE DES VOTES", key="start_btn", use_container_width=True):
                    config["session_ouverte"] = True
                    with open(CONFIG_FILE, "w") as f: json.dump(config, f)
                    st.rerun()
            else:
                if st.button("⏹️ ARRÊTER L'ANNONCE", use_container_width=True):
                    config["session_ouverte"] = False
                    with open(CONFIG_FILE, "w") as f: json.dump(config, f)
                    st.rerun()

            if st.button("🔵 VALIDER : MISE À JOUR MUR", type="primary", use_container_width=True):
                config["mode_affichage"] = mode_key
                config["titre_mur"] = nouveau_titre
                with open(CONFIG_FILE, "w") as f: json.dump(config, f)
                st.rerun()
            
            st.divider()
            if st.button("🔴 RESET : RÉINITIALISER LES VOTES", type="secondary", use_container_width=True):
                new_config = {"mode_affichage": "attente", "titre_mur": nouveau_titre, "vote_version": VOTE_VERSION + 1, "session_ouverte": False}
                with open(CONFIG_FILE, "w") as f: json.dump(new_config, f)
                with open(VOTES_FILE, "w") as f: json.dump({}, f)
                with open(PARTICIPANTS_FILE, "w") as f: json.dump([], f)
                st.rerun()

    if st.session_state.get("auth"):
        c1, c2 = st.columns([2, 1])
        c1.title("Console de Régie")
        if os.path.exists(LOGO_FILE): c2.image(LOGO_FILE, width=250)
        st.metric("Participants", len(json.load(open(PARTICIPANTS_FILE))))
        st.bar_chart(json.load(open(VOTES_FILE)))

# --- 4. UTILISATEUR (VOTE) ---
elif est_utilisateur:
    st.title("🗳️ Vote Transdev")
    vote_key = f"transdev_v{VOTE_VERSION}"
    components.html(f"<script>if(localStorage.getItem('{vote_key}')){{window.parent.postMessage({{type:'voted'}},'*');}}</script>", height=0)
    
    if st.session_state.get("voted"):
        st.success("✅ Vote déjà enregistré.")
    else:
        pseudo = st.text_input("Pseudo / Prénom :")
        options = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]
        choix = st.multiselect("Votre Top 3 :", options, max_selections=3)
        if st.button("Confirmer le vote"):
            if pseudo and (0 < len(choix) <= 3):
                vts = json.load(open(VOTES_FILE))
                for c in choix: vts[c] = vts.get(c, 0) + 1
                with open(VOTES_FILE, "w") as f: json.dump(vts, f)
                with open(PARTICIPANTS_FILE, "r") as f: parts = json.load(f)
                if pseudo not in parts: parts.append(pseudo); json.dump(parts, open(PARTICIPANTS_FILE, "w"))
                components.html(f"<script>localStorage.setItem('{vote_key}', 'true'); setTimeout(()=>{{window.parent.location.reload();}},500);</script>", height=0)
                st.session_state["voted"] = True
            else: st.error("Champs requis.")

# --- 5. MUR LIVE ---
else:
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'] { display: none; } footer {display:none;}</style>", unsafe_allow_html=True)
    
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    # TITRES
    st.markdown(f"<div style='text-align:center; padding-top:20px;'><p style='color:#E2001A; font-size:30px; font-weight:bold; margin:0;'>MUR PHOTO LIVE</p><h1 style='color:white; font-size:55px; margin-top:0;'>{config.get('titre_mur')}</h1></div>", unsafe_allow_html=True)

    # TEXTE D'ATTENTE (Si activé par l'admin)
    if config.get("session_ouverte", False) and config["mode_affichage"] != "votes":
        st.markdown("""
            <div style='text-align:center; margin: 20px 0;'>
                <div style='display:inline-block; background:rgba(226, 0, 26, 0.8); color:white; padding:15px 40px; border-radius:50px; font-size:28px; font-weight:bold; border: 2px solid white; animation: pulse 2s infinite;'>
                    ⌛ En attente ouverture des votes...
                </div>
            </div>
            <style>@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }</style>
        """, unsafe_allow_html=True)

    if config["mode_affichage"] == "votes":
        st.bar_chart(json.load(open(VOTES_FILE)))
    else:
        # Photos (Admin en mode attente, Tout en mode live)
        if config["mode_affichage"] == "attente":
            img_list = glob.glob(os.path.join(ADMIN_DIR, "*"))
        else:
            img_list = glob.glob(os.path.join(ADMIN_DIR, "*")) + glob.glob(os.path.join(GALLERY_DIR, "*"))
        
        photos_html = ""
        for p in img_list[-12:]:
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:280px; top:{random.randint(25,65)}%; left:{random.randint(5,80)}%; animation-duration:{random.uniform(10,15)}s;">'
        
        html_content = f"""<style>.photo {{ position:absolute; border:6px solid white; border-radius:15px; animation:move alternate infinite ease-in-out; }} @keyframes move {{ from {{ transform:rotate(-3deg); }} to {{ transform:translate(40px,40px) rotate(3deg); }} }}</style><div style="width:100%; height:500px; position:relative;">{photos_html}</div><div style="position:fixed; bottom:40px; left:50%; transform:translateX(-50%); background:white; padding:15px; border-radius:20px; border:5px solid #E2001A; text-align:center; z-index:1000;"><img src="data:image/png;base64,{qr_b64}" width="160"><p style="margin:5px 0 0 0; font-weight:bold; font-size:20px; color:black;">{len(json.load(open(PARTICIPANTS_FILE)))} PARTICIPANTS</p></div>"""
        components.html(html_content, height=750)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=10000, key="global_refresh")
    except: pass
