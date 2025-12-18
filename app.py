import streamlit as st
import os
import glob
import base64
import qrcode
import json
import zipfile
import datetime
import random
from io import BytesIO
import streamlit.components.v1 as components

# --- 1. CONFIGURATION INITIALE ---
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
        json.dump({"mode_affichage": "photos", "titre_mur": "SOIRÉE DE GALA 2026"}, f)

# --- 2. GESTION DE LA SESSION ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "admin_password" not in st.session_state:
    st.session_state["admin_password"] = "ADMIN_LIVE_MASTER"

# --- 3. FONCTIONS ---
def load_config():
    with open(CONFIG_FILE, "r") as f: return json.load(f)

def save_config(mode, titre):
    with open(CONFIG_FILE, "w") as f: 
        json.dump({"mode_affichage": mode, "titre_mur": titre}, f)

def get_votes():
    with open(VOTES_FILE, "r") as f: return json.load(f)

def add_vote(candidat):
    votes = get_votes()
    votes[candidat] = votes.get(candidat, 0) + 1
    with open(VOTES_FILE, "w") as f: json.dump(votes, f)

# --- 4. NAVIGATION ---
query_params = st.query_params
est_admin = query_params.get("admin") == "true"
est_utilisateur = query_params.get("mode") == "vote"

# --- 5. INTERFACE ADMINISTRATION (MASTER) ---
if est_admin:
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
        html, body, [data-testid="stAppViewContainer"] { font-family: 'Roboto', sans-serif; }
        .main-header-sticky {
            position: sticky; top: 0px; background-color: white; z-index: 1000;
            padding: 20px 0; border-bottom: 3px solid #E2001A;
        }
        </style>
    """, unsafe_allow_html=True)

    config = load_config()

    with st.sidebar:
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, use_container_width=True)
        st.markdown("<h3 style='text-align: center;'>Régie Social Wall</h3>", unsafe_allow_html=True)
        pwd_input = st.text_input("Code Accès", type="password")
        if pwd_input == st.session_state["admin_password"]: st.session_state["authenticated"] = True
        
        st.divider()
        if st.session_state["authenticated"]:
            st.subheader("🎮 Configuration Live")
            nouveau_titre = st.text_input("Sous-titre (modifiable) :", value=config.get("titre_mur", "ÉVÉNEMENT 2026"))
            new_mode = st.radio("Affichage Mur :", ["Photos", "Votes"], index=0 if config["mode_affichage"] == "photos" else 1)
            
            if st.button("Mettre à jour le Mur", use_container_width=True, type="primary"):
                save_config(new_mode.lower(), nouveau_titre)
                st.rerun()
            
            st.divider()
            if st.button("🧨 RESET TOTAL", use_container_width=True):
                for f in glob.glob(os.path.join(GALLERY_DIR, "*")): 
                    try: os.remove(f)
                    except: pass
                with open(VOTES_FILE, "w") as f: json.dump({}, f)
                st.rerun()

    if st.session_state["authenticated"]:
        st.markdown('<div class="main-header-sticky">', unsafe_allow_html=True)
        c_title_main, c_logo_main = st.columns([2, 1])
        with c_title_main:
            st.markdown("<h1 style='margin-bottom:0;'>Console de Modération</h1>", unsafe_allow_html=True)
            st.caption(f"Sous-titre actuel : {config.get('titre_mur')}")
        if os.path.exists(LOGO_FILE):
            c_logo_main.image(LOGO_FILE, width=280) 
        st.link_button("🖥️ OUVRIR LE MUR LIVE", f"https://{st.context.headers.get('host', 'localhost')}/", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        all_imgs = [f for f in glob.glob(os.path.join(GALLERY_DIR, "*")) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        sorted_imgs = sorted(all_imgs, key=os.path.getmtime, reverse=True)
        mode_vue = st.radio("Vue", ["Vignettes", "Liste"], horizontal=True, label_visibility="collapsed")
        
        if mode_vue == "Vignettes":
            for i in range(0, len(sorted_imgs), 8):
                cols = st.columns(8)
                for j in range(8):
                    idx = i + j
                    if idx < len(sorted_imgs):
                        img_p = sorted_imgs[idx]
                        with cols[j]:
                            st.image(img_p, use_container_width=True)
                            if st.button("🗑️", key=f"d_{idx}"): 
                                try: os.remove(img_p)
                                except: pass
                                st.rerun()
        else:
            for i in range(0, len(sorted_imgs), 4):
                cols = st.columns(4)
                for j in range(4):
                    idx = i + j
                    if idx < len(sorted_imgs):
                        img_p = sorted_imgs[idx]
                        with cols[j]:
                            with st.container(border=True):
                                st.image(img_p, use_container_width=True)
                                if st.button("Supprimer", key=f"bl_{idx}", use_container_width=True): 
                                    try: os.remove(img_p)
                                    except: pass
                                    st.rerun()
    else:
        st.info("🔒 Accès restreint. Utilisez la barre latérale.")

# --- 6. INTERFACE UTILISATEUR (QR CODE) ---
elif est_utilisateur:
    st.title("📲 Participation")
    t1, t2 = st.tabs(["📸 Photo", "🗳️ Vote Vidéo"])
    with t1:
        f = st.file_uploader("Envoyer une photo", type=['jpg', 'png'])
        if f:
            with open(os.path.join(GALLERY_DIR, f"u_{random.randint(100,999)}.jpg"), "wb") as out: out.write(f.getbuffer())
            st.success("Photo envoyée !")
    with t2:
        st.subheader("Votez pour le projet gagnant :")
        video_choice = st.radio("Sélectionnez :", ["Projet 1 : Innovation", "Projet 2 : Équipe", "Projet 3 : Durabilité", "Projet 4 : Clients"])
        if st.button("Valider mon vote"):
            add_vote(video_choice); st.success("Vote pris en compte !")

# --- 7. MODE LIVE (MUR NOIR) ---
else:
    st.markdown("<style>:root { background-color: black; } [data-testid='stAppViewContainer'], .stApp { background-color: black !important; } [data-testid='stHeader'], footer { display: none !important; } </style>", unsafe_allow_html=True)
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=20000, key="refresh")
    except: pass
    
    config = load_config()
    sous_titre = config.get("titre_mur", "")
    
    if config["mode_affichage"] == "votes":
        st.markdown(f"""
            <div style='text-align:center; padding-top:40px; font-family:sans-serif;'>
                <p style='color:#E2001A; font-size:35px; font-weight:bold; margin:0;'>MUR PHOTO LIVE</p>
                <h1 style='color:white; font-size:55px; margin-top:0;'>{sous_titre}</h1>
            </div>
        """, unsafe_allow_html=True)
        st.bar_chart(get_votes())
    else:
        img_list = [f for f in glob.glob(os.path.join(GALLERY_DIR, "*")) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
        qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        logo_b64 = ""
        if os.path.exists(LOGO_FILE):
            with open(LOGO_FILE, "rb") as f: logo_b64 = base64.b64encode(f.read()).decode()
        
        # Correction de la ligne photos_html (SyntaxError)
        photos_html = ""
        for p in img_list[-15:]:
            with open(p, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
                w = random.randint(220,320)
                t = random.randint(10,70)
                l = random.randint(5,85)
                dur = random.uniform(9,15)
                photos_html += f'<img src="data:image/png;base64,{img_data}" class="photo" style="width:{w}px; top:{t}%; left:{l}%; animation-duration:{dur}s;">'
        
        html_code = f"""
        <html><body style="margin:0; background:black; overflow:hidden; width:100vw; height:100vh;">
        <style>
            .header-box {{ position:absolute; top:30px; width:100%; text-align:center; z-index:1001; font-family:'Roboto', sans-serif; }}
            .title-fixed {{ color:#E2001A; font-size:35px; font-weight:bold; margin:0; text-shadow: 0 0 10px rgba(226,0,26,0.3); }}
            .title-dynamic {{ color:white; font-size:55px; font-weight:bold; margin:0; text-shadow: 0 0 20px rgba(255,255,255,0.5); }}
            .center-stack {{ position:absolute; top:58%; left:50%; transform:translate(-50%, -50%); z-index:1000; display:flex; flex-direction:column; align-items:center; gap:25px; }}
            .logo {{ max-width:380px; filter:drop-shadow(0 0 20px white); }}
            .qr-box {{ background:white; padding:15px; border-radius:15px; border: 5px solid #E2001A; }}
            .photo {{ position:absolute; border:6px solid white; border-radius:15px; animation:move alternate infinite ease-in-out; opacity:0.95; box-shadow: 15px 15px 35px rgba(0,0,0,0.6); }}
            @keyframes move {{ from {{ transform:translate(0,0) rotate(-3deg); }} to {{ transform:translate(60px, 60px) rotate(4deg); }} }}
        </style>
        <div class="header-box">
            <p class="title-fixed">MUR PHOTO LIVE</p>
            <h1 class="title-dynamic">{sous_titre}</h1>
        </div>
        <div class="center-stack">
            {f'<img src="data:image/png;base64,{logo_b64}" class="logo">' if logo_b64 else ''}
            <div class="qr-box"><img src="data:image/png;base64,{qr_b64}" width="170"></div>
        </div>
        {photos_html}
        </body></html>
        """
        components.html(html_code, height=1000)
