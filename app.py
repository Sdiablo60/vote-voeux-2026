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
LOGO_FILE = "logo_entreprise.png"
VOTES_FILE = "votes.json"
PARTICIPANTS_FILE = "participants.json"
CONFIG_FILE = "config_mur.json"

for d in [GALLERY_DIR]:
    if not os.path.exists(d): os.makedirs(d)

# Initialisation des fichiers
if not os.path.exists(VOTES_FILE):
    with open(VOTES_FILE, "w") as f: json.dump({}, f)
if not os.path.exists(PARTICIPANTS_FILE):
    with open(PARTICIPANTS_FILE, "w") as f: json.dump([], f)
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f: 
        json.dump({"mode_affichage": "photos", "titre_mur": "CONCOURS VIDÉO 2026"}, f)

# --- 2. FONCTIONS ---
def load_config():
    with open(CONFIG_FILE, "r") as f: return json.load(f)

def save_config(mode, titre):
    with open(CONFIG_FILE, "w") as f: 
        json.dump({"mode_affichage": mode, "titre_mur": titre}, f)

def get_votes():
    with open(VOTES_FILE, "r") as f: return json.load(f)

def get_participants_count():
    with open(PARTICIPANTS_FILE, "r") as f: return len(json.load(f))

def add_vote_session(pseudo, choix_list):
    # Ajouter le pseudo s'il est nouveau
    with open(PARTICIPANTS_FILE, "r") as f:
        participants = json.load(f)
    if pseudo not in participants:
        participants.append(pseudo)
        with open(PARTICIPANTS_FILE, "w") as f: json.dump(participants, f)
    
    # Ajouter les votes
    votes = get_votes()
    for c in choix_list:
        votes[c] = votes.get(c, 0) + 1
    with open(VOTES_FILE, "w") as f: json.dump(votes, f)

# --- 3. NAVIGATION ---
query_params = st.query_params
est_admin = query_params.get("admin") == "true"
est_utilisateur = query_params.get("mode") == "vote"

# --- 4. ADMIN ---
if est_admin:
    config = load_config()
    with st.sidebar:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, use_container_width=True)
        pwd = st.text_input("Code Admin", type="password")
        if pwd == "ADMIN_LIVE_MASTER": st.session_state["auth"] = True
        if st.session_state.get("auth"):
            nouveau_titre = st.text_input("Sous-titre :", value=config.get("titre_mur"))
            new_mode = st.radio("Mode Mur :", ["Photos", "Votes"], index=0 if config["mode_affichage"]=="photos" else 1)
            if st.button("Mettre à jour le Mur", type="primary", use_container_width=True):
                save_config(new_mode.lower(), nouveau_titre)
                st.rerun()
            if st.button("🧨 RESET DATA (Votes/Participants)"):
                with open(VOTES_FILE, "w") as f: json.dump({}, f)
                with open(PARTICIPANTS_FILE, "w") as f: json.dump([], f)
                st.rerun()

    if st.session_state.get("auth"):
        c1, c2 = st.columns([2, 1])
        c1.title("Console de Régie")
        if os.path.exists(LOGO_FILE): c2.image(LOGO_FILE, width=250)
        st.metric("Nombre de participants", get_participants_count())
        st.bar_chart(get_votes())

# --- 5. UTILISATEUR ---
elif est_utilisateur:
    st.title("🗳️ Vote Transdev")
    components.html("<script>if(localStorage.getItem('transdev_voted')){window.parent.postMessage({type:'voted'},'*');}</script>", height=0)

    if st.session_state.get("has_voted"):
        st.warning("✅ Merci ! Votre vote est déjà enregistré.")
    else:
        pseudo = st.text_input("Saisissez votre Pseudo :")
        options = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]
        choix = st.multiselect("Votre Top 3 :", options, max_selections=3)
        
        if st.button("Valider mon Vote"):
            if pseudo and (0 < len(choix) <= 3):
                add_vote_session(pseudo, choix)
                components.html("<script>localStorage.setItem('transdev_voted','true');window.parent.location.reload();</script>", height=0)
                st.session_state["has_voted"] = True
                st.success("Vote validé !")
            else: st.error("Pseudo et au moins 1 choix requis.")

# --- 6. MUR LIVE ---
else:
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'] { display: none; }</style>", unsafe_allow_html=True)
    config = load_config()
    nb_participants = get_participants_count()
    
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    # Affichage TITRES
    st.markdown(f"""
        <div style='text-align:center; padding-top: 20px;'>
            <p style='color:#E2001A; font-size:30px; font-weight:bold; margin:0; font-family:sans-serif;'>MUR PHOTO LIVE</p>
            <h1 style='color:white; font-size:55px; margin-top:0; font-family:sans-serif;'>{config.get('titre_mur')}</h1>
        </div>
    """, unsafe_allow_html=True)

    if config["mode_affichage"] == "votes":
        v_data = get_votes()
        if any(v > 0 for v in v_data.values()):
            st.bar_chart(v_data)
            # QR Code avec compteur
            st.markdown(f"""
                <div style='position:fixed; bottom:30px; right:30px; background:white; padding:15px; border-radius:15px; border:4px solid #E2001A; text-align:center;'>
                    <img src='data:image/png;base64,{qr_b64}' width='120'>
                    <p style='margin:10px 0 0 0; font-family:sans-serif; color:black; font-weight:bold; font-size:18px;'>{nb_participants} PARTICIPANTS</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            # QR CODE CENTRAL
            st.markdown(f"""
                <div style='text-align:center; margin-top:50px;'>
                    <div style='display:inline-block; background:white; padding:40px; border-radius:30px; border:8px solid #E2001A;'>
                        <img src='data:image/png;base64,{qr_b64}' width='320'>
                        <p style='margin-top:20px; font-family:sans-serif; font-weight:bold; font-size:30px; color:black;'>{nb_participants} PARTICIPANTS</p>
                        <p style='color:#E2001A; font-weight:bold; font-size:20px;'>SCANNEZ POUR VOTER</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        # Mode Photos animé
        img_list = [f for f in glob.glob(os.path.join(GALLERY_DIR, "*")) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        photos_html = ""
        for p in img_list[-12:]:
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:280px; top:{random.randint(20,65)}%; left:{random.randint(5,80)}%; animation-duration:{random.uniform(10,15)}s;">'
        
        html_content = f"""
        <style>.photo {{ position:absolute; border:6px solid white; border-radius:15px; animation:move alternate infinite ease-in-out; }} @keyframes move {{ from {{ transform:rotate(-3deg); }} to {{ transform:translate(40px,40px) rotate(3deg); }} }}</style>
        <div style="width:100%; height:550px; position:relative;">{photos_html}</div>
        <div style="position:fixed; bottom:40px; left:50%; transform:translateX(-50%); background:white; padding:15px; border-radius:20px; border:5px solid #E2001A; text-align:center; z-index:1000;">
            <img src="data:image/png;base64,{qr_b64}" width="160">
            <p style="margin:5px 0 0 0; font-family:sans-serif; font-weight:bold; font-size:20px; color:black;">{nb_participants} PARTICIPANTS</p>
        </div>
        """
        components.html(html_content, height=800)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=15000, key="global_refresh")
    except: pass
