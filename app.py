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

if not os.path.exists(GALLERY_DIR): os.makedirs(GALLERY_DIR)

# Chargement config
config = {"mode_affichage": "photos", "titre_mur": "CONCOURS VIDÉO 2026", "vote_version": 1}
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f: config = json.load(f)

VOTE_VERSION = config.get("vote_version", 1)

# Initialisation fichiers data
if not os.path.exists(VOTES_FILE):
    with open(VOTES_FILE, "w") as f: json.dump({}, f)
if not os.path.exists(PARTICIPANTS_FILE):
    with open(PARTICIPANTS_FILE, "w") as f: json.dump([], f)

# --- 2. FONCTIONS ---
def get_votes():
    with open(VOTES_FILE, "r") as f: return json.load(f)

def get_participants_count():
    try:
        with open(PARTICIPANTS_FILE, "r") as f: return len(json.load(f))
    except: return 0

# --- 3. NAVIGATION ---
query_params = st.query_params
est_admin = query_params.get("admin") == "true"
est_utilisateur = query_params.get("mode") == "vote"

# --- 4. ADMIN (Boutons Bleu/Rouge + Logo Droite) ---
if est_admin:
    st.markdown("""
        <style>
        div[data-testid="stSidebar"] button[kind="primary"] { background-color: #0000FF !important; color: white !important; border: 3px solid #0000FF !important; }
        div[data-testid="stSidebar"] button[kind="secondary"] { background-color: #FF0000 !important; color: white !important; border: 3px solid #FF0000 !important; }
        </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE)
        if st.text_input("Code Admin", type="password") == "ADMIN_LIVE_MASTER":
            st.session_state["auth"] = True
            
        if st.session_state.get("auth"):
            st.subheader("Paramètres")
            nouveau_titre = st.text_input("Sous-titre :", value=config.get("titre_mur"))
            new_mode = st.radio("Mode Mur :", ["Photos", "Votes"], index=0 if config["mode_affichage"]=="photos" else 1)
            
            if st.button("🔵 VALIDER : MISE À JOUR MUR", type="primary", use_container_width=True):
                with open(CONFIG_FILE, "w") as f: 
                    json.dump({"mode_affichage": new_mode.lower(), "titre_mur": nouveau_titre, "vote_version": VOTE_VERSION}, f)
                st.rerun()
            
            st.divider()
            if st.button("🔴 RESET : RÉINITIALISER TOUT", type="secondary", use_container_width=True):
                with open(CONFIG_FILE, "w") as f: 
                    json.dump({"mode_affichage": "photos", "titre_mur": nouveau_titre, "vote_version": VOTE_VERSION + 1}, f)
                with open(VOTES_FILE, "w") as f: json.dump({}, f)
                with open(PARTICIPANTS_FILE, "w") as f: json.dump([], f)
                st.rerun()

    if st.session_state.get("auth"):
        c1, c2 = st.columns([2, 1])
        c1.title("Console de Régie")
        if os.path.exists(LOGO_FILE): c2.image(LOGO_FILE, width=250)
        st.metric("Participants", get_participants_count())
        st.bar_chart(get_votes())

# --- 5. UTILISATEUR (Sécurité renforcée) ---
elif est_utilisateur:
    st.title("🗳️ Vote Transdev")
    vote_key = f"transdev_v{VOTE_VERSION}"
    
    components.html(f"""
        <script>
        if (localStorage.getItem("{vote_key}")) {{
            window.parent.postMessage({{type: 'streamlit:setComponentValue', value: true}}, '*');
        }}
        </script>
    """, height=0)

    if st.session_state.get("already_voted"):
        st.success("✅ Votre vote est déjà enregistré sur cet appareil.")
    else:
        pseudo = st.text_input("Votre Pseudo / Prénom :")
        options = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]
        choix = st.multiselect("Votre Top 3 :", options, max_selections=3)
        
        if st.button("Confirmer mon vote"):
            if pseudo and (0 < len(choix) <= 3):
                with open(PARTICIPANTS_FILE, "r") as f: participants = json.load(f)
                if pseudo not in participants:
                    participants.append(pseudo)
                    with open(PARTICIPANTS_FILE, "w") as f: json.dump(participants, f)
                votes = get_votes()
                for c in choix: votes[c] = votes.get(c, 0) + 1
                with open(VOTES_FILE, "w") as f: json.dump(votes, f)
                
                components.html(f"""<script>localStorage.setItem("{vote_key}", "true"); setTimeout(() => {{ window.parent.location.reload(); }}, 500);</script>""", height=0)
                st.session_state["already_voted"] = True
            else: st.error("Pseudo + 1 à 3 choix requis.")

# --- 6. MUR LIVE (Rétabli et complet) ---
else:
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'] { display: none; } footer {display:none;}</style>", unsafe_allow_html=True)
    nb = get_participants_count()
    
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    # TITRES
    st.markdown(f"""
        <div style='text-align:center; padding-top: 20px; font-family:sans-serif;'>
            <p style='color:#E2001A; font-size:30px; font-weight:bold; margin:0;'>MUR PHOTO LIVE</p>
            <h1 style='color:white; font-size:55px; margin-top:0;'>{config.get('titre_mur')}</h1>
        </div>
    """, unsafe_allow_html=True)

    if config["mode_affichage"] == "votes":
        v_data = get_votes()
        if any(v > 0 for v in v_data.values()):
            st.bar_chart(v_data)
            st.markdown(f"<div style='position:fixed; bottom:30px; right:30px; background:white; padding:15px; border-radius:15px; border:4px solid #E2001A; text-align:center;'><img src='data:image/png;base64,{qr_b64}' width='110'><p style='margin:10px 0 0 0; color:black; font-weight:bold; font-size:16px;'>{nb} PARTICIPANTS</p></div>", unsafe_allow_html=True)
        else:
            # QR CODE CENTRAL SI PAS DE VOTE
            st.markdown(f"<div style='text-align:center; margin-top:50px;'><div style='display:inline-block; background:white; padding:40px; border-radius:30px; border:8px solid #E2001A;'><img src='data:image/png;base64,{qr_b64}' width='320'><p style='margin-top:20px; font-weight:bold; font-size:30px; color:black;'>{nb} PARTICIPANTS</p><p style='color:#E2001A; font-weight:bold; font-size:20px;'>SCANNEZ POUR VOTER</p></div></div>", unsafe_allow_html=True)
    else:
        # Mode Photos animé
        img_list = [f for f in glob.glob(os.path.join(GALLERY_DIR, "*")) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        photos_html = ""
        for p in img_list[-12:]:
            with open(p, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
                photos_html += f'<img src="data:image/png;base64,{img_data}" class="photo" style="width:280px; top:{random.randint(20,65)}%; left:{random.randint(5,80)}%; animation-duration:{random.uniform(10,15)}s;">'
        
        html_content = f"""
        <style>.photo {{ position:absolute; border:6px solid white; border-radius:15px; animation:move alternate infinite ease-in-out; box-shadow: 10px 10px 20px rgba(0,0,0,0.5); }} @keyframes move {{ from {{ transform:rotate(-3deg); }} to {{ transform:translate(40px,40px) rotate(3deg); }} }}</style>
        <div style="width:100%; height:550px; position:relative;">{photos_html}</div>
        <div style="position:fixed; bottom:40px; left:50%; transform:translateX(-50%); background:white; padding:15px; border-radius:20px; border:5px solid #E2001A; text-align:center; z-index:1000;"><img src="data:image/png;base64,{qr_b64}" width="160"><p style="margin:5px 0 0 0; font-weight:bold; font-size:20px; color:black;">{nb} PARTICIPANTS</p></div>
        """
        components.html(html_content, height=800)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=15000, key="global_refresh")
    except: pass
