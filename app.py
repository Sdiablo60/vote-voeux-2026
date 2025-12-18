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
CONFIG_FILE = "config_mur.json"

for d in [GALLERY_DIR]:
    if not os.path.exists(d): os.makedirs(d)

if not os.path.exists(VOTES_FILE):
    with open(VOTES_FILE, "w") as f: json.dump({}, f)
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

def add_votes_multiple(choix_list):
    votes = get_votes()
    for c in choix_list:
        votes[c] = votes.get(c, 0) + 1
    with open(VOTES_FILE, "w") as f: json.dump(votes, f)

# --- 3. NAVIGATION ---
query_params = st.query_params
est_admin = query_params.get("admin") == "true"
est_utilisateur = query_params.get("mode") == "vote"

# --- 4. ADMIN (MASTER) ---
if est_admin:
    config = load_config()
    st.markdown("""<style>.main-header { position: sticky; top: 0; background: white; z-index: 1000; border-bottom: 3px solid #E2001A; padding: 10px; }</style>""", unsafe_allow_html=True)
    
    with st.sidebar:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE)
        pwd = st.text_input("Code Admin", type="password")
        if pwd == "ADMIN_LIVE_MASTER":
            st.session_state["auth"] = True
            
        if st.session_state.get("auth"):
            st.subheader("Paramètres")
            nouveau_titre = st.text_input("Sous-titre :", value=config.get("titre_mur"))
            new_mode = st.radio("Mode Mur :", ["Photos", "Votes"], index=0 if config["mode_affichage"]=="photos" else 1)
            if st.button("Mise à jour du Mur", type="primary", use_container_width=True):
                save_config(new_mode.lower(), nouveau_titre)
                st.rerun()

    if st.session_state.get("auth"):
        cols = st.columns([2, 1])
        cols[0].title("Console de Régie")
        if os.path.exists(LOGO_FILE): cols[1].image(LOGO_FILE, width=250)
        
        st.subheader("Résultats actuels")
        st.bar_chart(get_votes())

# --- 5. UTILISATEUR (VOTE TOP 3) ---
elif est_utilisateur:
    st.title("🗳️ Vote Transdev")
    options = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]
    choix = st.multiselect("Choisissez vos 3 vidéos préférées :", options, max_selections=3)
    if st.button("Valider mon Top 3"):
        if 0 < len(choix) <= 3:
            add_votes_multiple(choix)
            st.success("Merci pour votre vote !")
            st.balloons()
        else: st.error("Sélectionnez au moins 1 vidéo.")

# --- 6. MUR LIVE (SOCIAL) ---
else:
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'] { display: none; }</style>", unsafe_allow_html=True)
    config = load_config()
    sous_titre = config.get("titre_mur", "")
    
    # Génération QR Code
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_img = qrcode.make(qr_url)
    buf = BytesIO(); qr_img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    # Affichage des TITRES (Communs aux deux modes)
    st.markdown(f"""
        <div style='text-align:center; padding: 20px;'>
            <p style='color:#E2001A; font-size:30px; font-weight:bold; margin:0;'>MUR PHOTO LIVE</p>
            <h1 style='color:white; font-size:50px; margin:0;'>{sous_titre}</h1>
        </div>
    """, unsafe_allow_html=True)

    if config["mode_affichage"] == "votes":
        v_data = get_votes()
        if v_data:
            st.bar_chart(v_data)
        else:
            st.markdown("<p style='color:gray; text-align:center;'>En attente des premiers votes...</p>", unsafe_allow_html=True)
        
        # QR Code flottant en bas pour le mode vote
        st.markdown(f"""
            <div style='position:fixed; bottom:30px; right:30px; background:white; padding:10px; border-radius:10px; border:3px solid #E2001A; z-index:2000;'>
                <p style='margin:0; font-size:12px; font-weight:bold; text-align:center;'>VOTEZ ICI</p>
                <img src="data:image/png;base64,{qr_b64}" width="120">
            </div>
        """, unsafe_allow_html=True)
    else:
        # Mode Photos (Animation classique)
        img_list = [f for f in glob.glob(os.path.join(GALLERY_DIR, "*")) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        photos_html = ""
        for p in img_list[-12:]:
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:280px; top:{random.randint(20,60)}%; left:{random.randint(10,80)}%; animation-duration:{random.uniform(10,15)}s;">'
        
        html_content = f"""
        <style>
            .photo {{ position:absolute; border:5px solid white; border-radius:10px; animation:move alternate infinite ease-in-out; }}
            @keyframes move {{ from {{ transform:rotate(-2deg); }} to {{ transform:translate(30px,30px) rotate(2deg); }} }}
        </style>
        <div style="width:100%; height:600px; position:relative;">{photos_html}</div>
        <div style="position:fixed; bottom:50%; left:50%; transform:translate(-50%, -50%); text-align:center;">
            <div style="background:white; padding:20px; border-radius:20px; border:5px solid #E2001A;">
                <img src="data:image/png;base64,{qr_b64}" width="180">
            </div>
        </div>
        """
        components.html(html_content, height=800)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=15000, key="wall")
    except: pass
