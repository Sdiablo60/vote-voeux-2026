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

# --- 4. ADMIN (STRUCTURE MASTER FIGÉE) ---
if est_admin:
    config = load_config()
    st.markdown("""<style>.main-header { position: sticky; top: 0; background: white; z-index: 1000; border-bottom: 3px solid #E2001A; padding: 10px; }</style>""", unsafe_allow_html=True)
    
    with st.sidebar:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, use_container_width=True)
        pwd = st.text_input("Code Admin", type="password")
        if pwd == "ADMIN_LIVE_MASTER": st.session_state["auth"] = True
            
        if st.session_state.get("auth"):
            st.subheader("Paramètres")
            nouveau_titre = st.text_input("Sous-titre :", value=config.get("titre_mur"))
            new_mode = st.radio("Mode Mur :", ["Photos", "Votes"], index=0 if config["mode_affichage"]=="photos" else 1)
            if st.button("Mettre à jour le Mur", type="primary", use_container_width=True):
                save_config(new_mode.lower(), nouveau_titre)
                st.rerun()

    if st.session_state.get("auth"):
        c_title, c_logo = st.columns([2, 1])
        c_title.title("Console de Régie")
        if os.path.exists(LOGO_FILE): c_logo.image(LOGO_FILE, width=250)
        st.subheader("Résultats des votes")
        st.bar_chart(get_votes())

# --- 5. UTILISATEUR (AVEC SÉCURITÉ ANTI-DOUBLE VOTE) ---
elif est_utilisateur:
    st.title("🗳️ Vote Transdev")
    
    # Injection JavaScript pour vérifier le LocalStorage
    components.html("""
        <script>
        const hasVoted = localStorage.getItem('transdev_voted_2026');
        if (hasVoted) {
            window.parent.postMessage({type: 'voted', value: true}, '*');
        }
        </script>
    """, height=0)

    # État du vote stocké dans la session Streamlit via le message JS
    if "user_already_voted" not in st.session_state:
        st.session_state["user_already_voted"] = False

    if st.session_state["user_already_voted"]:
        st.warning("📢 Vous avez déjà enregistré votre vote pour ce concours. Merci !")
    else:
        options = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]
        choix = st.multiselect("Choisissez vos 3 vidéos préférées :", options, max_selections=3)
        
        if st.button("Valider mon Top 3"):
            if 0 < len(choix) <= 3:
                add_votes_multiple(choix)
                # Marquer comme voté dans le navigateur via JS
                components.html(f"""
                    <script>
                    localStorage.setItem('transdev_voted_2026', 'true');
                    window.parent.location.reload();
                    </script>
                """, height=0)
                st.session_state["user_already_voted"] = True
                st.success("Merci pour votre vote !")
                st.balloons()
            else:
                st.error("Sélectionnez au moins 1 vidéo.")

# --- 6. MUR LIVE (RESTE INCHANGÉ) ---
else:
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'] { display: none; }</style>", unsafe_allow_html=True)
    config = load_config()
    sous_titre = config.get("titre_mur", "")
    
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    st.markdown(f"""
        <div style='text-align:center; padding-top: 20px; font-family:sans-serif;'>
            <p style='color:#E2001A; font-size:30px; font-weight:bold; margin:0;'>MUR PHOTO LIVE</p>
            <h1 style='color:white; font-size:55px; margin-top:0;'>{sous_titre}</h1>
        </div>
    """, unsafe_allow_html=True)

    if config["mode_affichage"] == "votes":
        v_data = get_votes()
        has_votes = any(v > 0 for v in v_data.values()) if v_data else False
        if has_votes:
            st.bar_chart(v_data)
            st.markdown(f"<div style='position:fixed; bottom:30px; right:30px; background:white; padding:10px; border-radius:15px; border:4px solid #E2001A; text-align:center;'><p style='margin:0; font-size:14px; font-weight:bold;'>VOTEZ ICI</p><img src='data:image/png;base64,{qr_b64}' width='110'></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align:center; margin-top:50px;'><p style='color:#aaaaaa; font-size:24px; margin-bottom:30px;'>En attente des premiers votes...</p><div style='display:inline-block; background:white; padding:30px; border-radius:30px; border:8px solid #E2001A;'><img src='data:image/png;base64,{qr_b64}' width='300'><p style='margin-top:20px; font-weight:bold; font-size:25px; color:black;'>SCANNEZ POUR VOTER</p></div></div>", unsafe_allow_html=True)
    else:
        img_list = [f for f in glob.glob(os.path.join(GALLERY_DIR, "*")) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        photos_html = ""
        for p in img_list[-12:]:
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:280px; top:{random.randint(20,65)}%; left:{random.randint(5,80)}%; animation-duration:{random.uniform(10,15)}s;">'
        
        html_content = f"""
        <style>.photo {{ position:absolute; border:6px solid white; border-radius:15px; animation:move alternate infinite ease-in-out; box-shadow: 10px 10px 20px rgba(0,0,0,0.5); }} @keyframes move {{ from {{ transform:rotate(-3deg); }} to {{ transform:translate(40px,40px) rotate(3deg); }} }}</style>
        <div style="width:100%; height:550px; position:relative;">{photos_html}</div>
        <div style="position:fixed; bottom:40px; left:50%; transform:translateX(-50%); background:white; padding:15px; border-radius:20px; border:5px solid #E2001A; text-align:center; z-index:1000;"><img src="data:image/png;base64,{qr_b64}" width="160"><p style="margin:5px 0 0 0; font-weight:bold; font-size:14px;">PARTICIPEZ ICI</p></div>
        """
        components.html(html_content, height=800)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=15000, key="global_refresh")
    except: pass
