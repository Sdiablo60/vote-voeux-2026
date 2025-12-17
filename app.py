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

# --- 1. CONFIGURATION & RÉPERTOIRES ---
DEFAULT_PASSWORD = "ADMIN_VOEUX_2026"
PASS_FILE = "pass_config.txt"
VOTES_DIR = "sessions_votes"
GALLERY_DIR = "galerie_images"
CONFIG_FILE = "config_videos.csv"
LOGO_FILE = "logo_entreprise.png"
SESSION_CONFIG = "current_session.txt"
PRESENCE_FILE = "presence_live.csv"

# Création des dossiers si inexistants
for d in [VOTES_DIR, GALLERY_DIR]:
    if not os.path.exists(d): os.makedirs(d)

st.set_page_config(page_title="Régie Master 2026", layout="wide")

# --- 2. FONCTIONS DE GESTION ---
def get_admin_password():
    if os.path.exists(PASS_FILE):
        with open(PASS_FILE, "r", encoding="utf-8") as f: return f.read().strip()
    return DEFAULT_PASSWORD

def set_admin_password(new_pass):
    with open(PASS_FILE, "w", encoding="utf-8") as f: f.write(new_pass)

def get_current_session():
    if os.path.exists(SESSION_CONFIG):
        with open(SESSION_CONFIG, "r", encoding="utf-8") as f: return f.read().strip()
    return "session_1"

def set_current_session(name):
    with open(SESSION_CONFIG, "w", encoding="utf-8") as f: f.write(name)

def load_videos():
    if os.path.exists(CONFIG_FILE): 
        return pd.read_csv(CONFIG_FILE)['Video'].tolist()
    return ["BU PAX", "BU FRET", "BU BTOB", "DPMI", "RH", "Finances", "AO", "QSSE", "IT", "Direction"]

def save_videos(liste):
    pd.DataFrame(liste, columns=['Video']).to_csv(CONFIG_FILE, index=False)

def get_stats():
    nb_p = 0
    if os.path.exists(PRESENCE_FILE):
        try: nb_p = len(pd.read_csv(PRESENCE_FILE)['Pseudo'].unique())
        except: nb_p = 0
    curr = get_current_session()
    path_v = os.path.join(VOTES_DIR, f"{curr}.csv")
    nb_v = len(pd.read_csv(path_v)) if os.path.exists(path_v) else 0
    return nb_p, nb_v

# --- 3. INITIALISATION DES VARIABLES ---
admin_pass = get_admin_password()
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"
current_session = get_current_session()

if "auth_ok" not in st.session_state: st.session_state["auth_ok"] = False
if "voted" not in st.session_state: st.session_state["voted"] = False
if "gal_key" not in st.session_state: st.session_state["gal_key"] = 0

# --- 4. INTERFACE ADMIN (RÉGIE) ---
if est_admin:
    # CSS AVANCÉ POUR BOUTONS ET GALERIE
    st.markdown("""
        <style>
        /* Sidebar : Transformer l'uploader de logo en bouton pur */
        [data-testid="stSidebar"] [data-testid="stFileUploader"] > section {
            padding: 0 !important;
            border: none !important;
            background-color: transparent !important;
        }
        [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {
            border: 1px solid rgba(250, 250, 250, 0.2) !important;
            background-color: transparent !important;
            border-radius: 4px !important;
            height: 38px !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            cursor: pointer;
        }
        [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] > div {
            display: none !important; /* Cache Browse Files, icônes, etc. */
        }
        [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"]::after {
            content: "Ajouter un Logo";
            font-size: 0.875rem;
            color: white;
        }
        [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"]:hover {
            border-color: #FF4B4B !important;
            background-color: rgba(255, 75, 75, 0.05) !important;
        }

        /* Main Galerie : Design épuré */
        .main [data-testid="stFileUploader"] {
            background-color: #1c1e26;
            border: 1px solid #3d444d;
            border-radius: 8px;
        }
        .main [data-testid="stFileUploaderDropzone"] div div::before {
            content: "＋"; font-size: 1.8rem; color: #58A6FF; display: block; margin-bottom: -5px;
        }
        .main [data-testid="stFileUploaderDropzone"] div div span { display: none; }
        .main [data-testid="stFileUploaderDropzone"]::after {
            content: "Importer des photos pour le Live"; font-size: 0.85rem; color: #c9d1d9;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🛠️ Console de Régie")
    nb_p, nb_v = get_stats()
    
    with st.sidebar:
        st.subheader("🖼️ Logo")
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, use_container_width=True)
            if st.button("Supprimer le Logo", key="del_logo", use_container_width=True):
                os.remove(LOGO_FILE)
                st.rerun()
        else:
            u_logo = st.file_uploader("", type=['png', 'jpg', 'jpeg'], key="sidebar_logo")
            if u_logo:
                Image.open(u_logo).save(LOGO_FILE); st.rerun()
        
        st.divider()
        st.header("🔑 Accès")
        if not st.session_state["auth_ok"]:
            pwd_input = st.text_input("Code Admin", type="password")
            if pwd_input == admin_pass:
                st.session_state["auth_ok"] = True
                st.rerun()
        else:
            st.success("✅ Connecté")
            st.metric("👥 Participants", nb_p)
            st.metric("📥 Votes", nb_v)
            st.divider()
            ns = st.text_input("Session active", value=current_session)
            if st.button("Enregistrer session", use_container_width=True):
                set_current_session(ns); st.rerun()
            if st.button("Déconnexion", use_container_width=True): 
                st.session_state["auth_ok"] = False; st.rerun()

    if st.session_state["auth_ok"]:
        t1, t2, t3 = st.tabs(["📊 Résultats", "📝 Services", "🖼️ Galerie"])
        
        with t1:
            path_curr = os.path.join(VOTES_DIR, f"{current_session}.csv")
            df_res = pd.read_csv(path_curr) if os.path.exists(path_curr) else pd.DataFrame()
            if not df_res.empty:
                vids = load_videos()
                scores = {v: 0 for v in vids}
                for _, r in df_res.iterrows():
                    for i, p in enumerate([5, 3, 1]):
                        c = r.get(f'Top{i+1}')
                        if c in scores: scores[c] += p
                df_p = pd.DataFrame(list(scores.items()), columns=['S', 'Pts']).sort_values('Pts', ascending=False)
                st.altair_chart(alt.Chart(df_p).mark_bar(color='#58A6FF', cornerRadiusEnd=4).encode(x='Pts', y=alt.Y('S', sort='-x')), use_container_width=True)
            else: st.info("Aucun vote enregistré pour le moment.")

        with t2:
            st.subheader("Gestion des Services")
            n_v = st.text_input("Ajouter un service")
            if st.button("➕ Valider"):
                if n_v: v = load_videos(); v.append(n_v); save_videos(v); st.rerun()
            st.divider()
            vids = load_videos()
            for i, v in enumerate(vids):
                c1, c2 = st.columns([0.85, 0.15])
                c1.write(f"• {v}")
                if c2.button("🗑️", key=f"ds_{i}"): vids.remove(v); save_videos(vids); st.rerun()

        with t3:
            st.subheader("Bibliothèque Photos")
            u_file = st.file_uploader("", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key=f"gal_up_{st.session_state['gal_key']}")
            if u_file:
                for f in u_file: Image.open(f).save(os.path.join(GALLERY_DIR, f.name))
                st.session_state["gal_key"] += 1
                st.rerun()
            st.divider()
            imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
            if imgs:
                imgs.sort(key=os.path.getmtime, reverse=True)
                cols = st.columns(5)
                for i, img_p in enumerate(imgs):
                    with cols[i%5]:
                        st.image(img_p, use_container_width=True)
                        if st.button("Retirer", key=f"del_{i}", use_container_width=True):
                            os.remove(img_p); st.rerun()

# --- 5. MODE PARTICIPANT (VOTE MOBILE) ---
elif mode_vote:
    st.title("🗳️ Vote Vœux 2026")
    if st.session_state["voted"]: st.success("✅ Votre vote a été enregistré !")
    else:
        pseudo = st.text_input("Votre Pseudo / Trigramme").strip()
        if pseudo and st.button("🚀 Apparaître sur le Live"):
            df_p = pd.read_csv(PRESENCE_FILE) if os.path.exists(PRESENCE_FILE) else pd.DataFrame(columns=["Pseudo"])
            if pseudo not in df_p['Pseudo'].values:
                pd.DataFrame([[pseudo]], columns=["Pseudo"]).to_csv(PRESENCE_FILE, mode='a', header=not os.path.exists(PRESENCE_FILE), index=False)
            st.toast("Regardez le grand écran !")
        st.divider()
        vids = load_videos()
        s1 = st.segmented_control("Quel est votre service préféré ? (5 pts)", vids, key="s1")
        if st.button("Valider mon vote", use_container_width=True):
            if pseudo and s1:
                fn = os.path.join(VOTES_DIR, f"{current_session}.csv")
                pd.DataFrame([[pseudo, s1]], columns=["Pseudo","Top1"]).to_csv(fn, mode='a', header=not os.path.exists(fn), index=False)
                st.session_state["voted"] = True; st.balloons(); time.sleep(1); st.rerun()

# --- 6. MODE LIVE (SOCIAL WALL PAR DÉFAUT) ---
else:
    st.markdown("<style>[data-testid='stSidebar'] {display:none;}</style>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2.5])
    with c1:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=180)
        qr_url = f"https://{st.context.headers.get('Host', '')}/?mode=vote"
        qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
        st.image(qr_buf.getvalue(), use_container_width=True)
        nb_p, _ = get_stats(); st.metric("Participants", nb_p)
    with c2:
        if os.path.exists(PRESENCE_FILE):
            noms = pd.read_csv(PRESENCE_FILE)['Pseudo'].unique().tolist()
            nuage = " ".join([f"<span style='font-size:{random.randint(22,55)}px; color:{random.choice(['#58A6FF','#FF4B4B','#2ca02c','#ff7f0e'])}; margin:15px; font-weight:bold; display:inline-block;'>{n}</span>" for n in noms])
            st.markdown(f"<div style='text-align:center;'>{nuage}</div>", unsafe_allow_html=True)
    st.divider()
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    if imgs:
        cols = st.columns(6)
        for i, img_p in enumerate(imgs): cols[i%6].image(img_p, use_container_width=True)
    time.sleep(5); st.rerun()
