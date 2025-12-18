import streamlit as st
import pandas as pd
import os
from PIL import Image
import altair as alt
from io import BytesIO
import qrcode
import glob
import random
import time
import base64

# --- 1. CONFIGURATION & RÉPERTOIRES ---
DEFAULT_PASSWORD = "ADMIN_VOEUX_2026"
PASS_FILE = "pass_config.txt"
VOTES_DIR = "sessions_votes"
GALLERY_DIR = "galerie_images"
CONFIG_FILE = "config_videos.csv"
LOGO_FILE = "logo_entreprise.png"
SESSION_CONFIG = "current_session.txt"
PRESENCE_FILE = "presence_live.csv"
MSG_FILE = "live_message.csv"

# Création des dossiers
for d in [VOTES_DIR, GALLERY_DIR]:
    if not os.path.exists(d): os.makedirs(d)

st.set_page_config(page_title="Régie Master 2026", layout="wide")

# --- 2. FONCTIONS DE GESTION ---
def get_admin_password():
    if os.path.exists(PASS_FILE):
        with open(PASS_FILE, "r", encoding="utf-8") as f: return f.read().strip()
    return DEFAULT_PASSWORD

def get_msg():
    if os.path.exists(MSG_FILE): 
        return pd.read_csv(MSG_FILE).iloc[0].to_dict()
    return {"texte": "Bienvenue à la soirée des Vœux 2026 !", "couleur": "#FF4B4B", "taille": 50, "font": "sans-serif"}

def save_msg(t, c, s, f):
    pd.DataFrame([{"texte": t, "couleur": c, "taille": s, "font": f}]).to_csv(MSG_FILE, index=False)

def get_stats():
    nb_p = 0
    if os.path.exists(PRESENCE_FILE):
        try: nb_p = len(pd.read_csv(PRESENCE_FILE)['Pseudo'].unique())
        except: nb_p = 0
    return nb_p

def img_to_base64(img_path):
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# --- 3. INITIALISATION ---
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"
current_session = (open(SESSION_CONFIG).read().strip() if os.path.exists(SESSION_CONFIG) else "session_1")

if "auth_ok" not in st.session_state: st.session_state["auth_ok"] = False
if "gal_key" not in st.session_state: st.session_state["gal_key"] = 0

# --- 4. INTERFACE ADMIN (RÉGIE) ---
if est_admin:
    st.title("🛠️ Console Régie Master")
    
    with st.sidebar:
        st.header("🔐 Connexion")
        pwd_input = st.text_input("Code Admin", type="password")
        if pwd_input == get_admin_password():
            st.session_state["auth_ok"] = True
            st.success("Accès autorisé")
        
        if st.session_state["auth_ok"]:
            st.divider()
            if os.path.exists(LOGO_FILE):
                st.image(LOGO_FILE, use_container_width=True)
                if st.button("Supprimer Logo", use_container_width=True):
                    os.remove(LOGO_FILE); st.rerun()
            else:
                u_logo = st.file_uploader("Ajouter Logo", type=['png','jpg'], label_visibility="collapsed")
                if u_logo: Image.open(u_logo).save(LOGO_FILE); st.rerun()

    if st.session_state["auth_ok"]:
        t1, t2, t3 = st.tabs(["✨ Message Live", "🖼️ Galerie Social Wall", "📊 Stats & Sessions"])
        
        with t1:
            st.subheader("Configuration du message d'accueil")
            curr_m = get_msg()
            new_t = st.text_area("Texte du message", curr_m["texte"])
            c1, c2, c3 = st.columns(3)
            new_c = c1.color_picker("Couleur", curr_m["couleur"])
            new_s = c2.slider("Taille (px)", 20, 120, int(curr_m["taille"]))
            new_f = c3.selectbox("Police", ["sans-serif", "serif", "monospace", "cursive"], index=0)
            
            if st.button("Mettre à jour le Social Wall", use_container_width=True):
                save_msg(new_t, new_c, new_s, new_f)
                st.toast("Message mis à jour !")

        with t2:
            st.subheader("Gestion des photos")
            u_files = st.file_uploader("Importer des photos", type=['png','jpg','jpeg'], accept_multiple_files=True, key=f"up_{st.session_state['gal_key']}")
            if u_files:
                for f in u_files: Image.open(f).save(os.path.join(GALLERY_DIR, f.name))
                st.session_state["gal_key"] += 1; st.rerun()
            
            st.divider()
            imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
            cols = st.columns(5)
            for i, img_p in enumerate(imgs):
                with cols[i%5]:
                    st.image(img_p, use_container_width=True)
                    if st.button("Supprimer", key=f"del_{i}"):
                        os.remove(img_p); st.rerun()

        with t3:
            st.metric("Participants en direct", get_stats())
            if st.button("Réinitialiser la liste de présence"):
                if os.path.exists(PRESENCE_FILE): os.remove(PRESENCE_FILE); st.rerun()

# --- 5. MODE LIVE (SOCIAL WALL) ---
elif not mode_vote:
    # CSS POUR L'EFFET BULLES ET ANIMATIONS
    st.markdown(f"""
        <style>
        [data-testid="stSidebar"] {{display: none;}}
        .main {{background-color: #0e1117; color: white;}}
        
        .bubble {{
            border-radius: 50%;
            border: 4px solid white;
            object-fit: cover;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            animation: float 6s ease-in-out infinite;
            transition: all 0.5s ease;
        }}
        
        @keyframes float {{
            0% {{ transform: translateY(0px) rotate(0deg); }}
            50% {{ transform: translateY(-20px) rotate(5deg); }}
            100% {{ transform: translateY(0px) rotate(0deg); }}
        }}
        
        .container {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            align-items: center;
            gap: 30px;
            padding: 40px;
        }}
        </style>
    """, unsafe_allow_html=True)

    # Logo et Message d'accueil
    msg = get_msg()
    col_l, col_m = st.columns([1, 4])
    with col_l:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=150)
    with col_m:
        st.markdown(f"<h1 style='text-align:left; color:{msg['couleur']}; font-size:{msg['taille']}px; font-family:{msg['font']};'>{msg['texte']}</h1>", unsafe_allow_html=True)

    # Zone centrale : Nuage de noms
    if os.path.exists(PRESENCE_FILE):
        noms = pd.read_csv(PRESENCE_FILE)['Pseudo'].unique().tolist()
        random.shuffle(noms)
        nuage = " ".join([f"<span style='font-size:{random.randint(20,50)}px; opacity:0.7; margin:15px; display:inline-block;'>{n}</span>" for n in noms[:30]])
        st.markdown(f"<div style='text-align:center; padding:20px; border-top:1px solid #333;'>{nuage}</div>", unsafe_allow_html=True)

    # Galerie Fun : Les photos en bulles
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    if imgs:
        st.markdown("<div class='container'>", unsafe_allow_html=True)
        # Affichage des 15 dernières photos
        for i, path in enumerate(imgs[-15:]):
            b64 = img_to_base64(path)
            size = random.randint(150, 250)
            delay = random.uniform(0, 5)
            st.markdown(f"""
                <img src="data:image/png;base64,{b64}" class="bubble" 
                style="width:{size}px; height:{size}px; animation-delay:{delay}s;">
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # QR Code flottant en bas
    qr_url = f"https://{st.context.headers.get('Host', '')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    st.markdown("<div style='position:fixed; bottom:20px; right:20px; text-align:center; background:white; padding:10px; border-radius:10px;'>", unsafe_allow_html=True)
    st.image(qr_buf.getvalue(), width=120)
    st.markdown("<p style='color:black; margin:0; font-weight:bold; font-size:12px;'>Scannez pour voter</p></div>", unsafe_allow_html=True)

    time.sleep(10); st.rerun()

# --- 6. MODE VOTE (MOBILE) ---
else:
    st.title("🗳️ Vote & Présence")
    pseudo = st.text_input("Entrez votre Trigramme / Pseudo").strip()
    if pseudo and st.button("🚀 Valider ma présence"):
        df = pd.read_csv(PRESENCE_FILE) if os.path.exists(PRESENCE_FILE) else pd.DataFrame(columns=["Pseudo"])
        if pseudo not in df['Pseudo'].values:
            pd.DataFrame([[pseudo]], columns=["Pseudo"]).to_csv(PRESENCE_FILE, mode='a', header=not os.path.exists(PRESENCE_FILE), index=False)
        st.success("Vous êtes sur le mur !")
        st.balloons()
