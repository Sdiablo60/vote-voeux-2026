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

# --- 1. CONFIGURATION ---
DEFAULT_PASSWORD = "ADMIN_VOEUX_2026"
PASS_FILE = "pass_config.txt"
VOTES_DIR = "sessions_votes"
GALLERY_DIR = "galerie_images"
CONFIG_FILE = "config_videos.csv"
LOGO_FILE = "logo_entreprise.png"
SESSION_CONFIG = "current_session.txt"
PRESENCE_FILE = "presence_live.csv"

for d in [VOTES_DIR, GALLERY_DIR]:
    if not os.path.exists(d): os.makedirs(d)

st.set_page_config(page_title="Régie Master 2026", layout="wide")

# --- 2. FONCTIONS DE GESTION ---
def get_admin_password():
    if os.path.exists(PASS_FILE):
        with open(PASS_FILE, "r", encoding="utf-8") as f: return f.read().strip()
    return DEFAULT_PASSWORD

def set_current_session(name):
    with open(SESSION_CONFIG, "w", encoding="utf-8") as f: f.write(name)

def get_current_session():
    if os.path.exists(SESSION_CONFIG):
        with open(SESSION_CONFIG, "r", encoding="utf-8") as f: return f.read().strip()
    return "session_1"

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

# --- 3. INITIALISATION ---
admin_pass = get_admin_password()
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"
current_session = get_current_session()

if "auth_ok" not in st.session_state: st.session_state["auth_ok"] = False
if "gal_key" not in st.session_state: st.session_state["gal_key"] = 0

# --- 4. INTERFACE ADMIN ---
if est_admin:
    # CSS Custom pour les uploaders
    st.markdown("""
        <style>
        /* Style général Uploader */
        [data-testid="stFileUploader"] { background-color: #1c1e26; border: 1px solid #3d444d; border-radius: 8px; }
        [data-testid="stFileUploaderDropzone"] div div span { display: none; }
        
        /* Spécifique LOGO (Sidebar) */
        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]::after {
            content: "Ajouter un Logo";
            font-size: 0.85rem;
            color: #c9d1d9;
        }
        
        /* Spécifique GALERIE (Main) */
        .main [data-testid="stFileUploaderDropzone"]::after {
            content: "Importer des photos";
            font-size: 0.85rem;
            color: #c9d1d9;
        }
        
        [data-testid="stFileUploaderDropzone"] div div::before { content: "＋"; font-size: 1.5rem; color: #58A6FF; display: block; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🛠️ Console de Régie")
    nb_p, nb_v = get_stats()
    
    with st.sidebar:
        # LOGO TOUT EN HAUT
        st.subheader("🖼️ Logo")
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, use_container_width=True)
            if st.button("🗑️ Supprimer", key="del_logo"):
                os.remove(LOGO_FILE)
                st.rerun()
        
        u_logo = st.file_uploader("", type=['png', 'jpg', 'jpeg'], key="sidebar_logo")
        if u_logo:
            Image.open(u_logo).save(LOGO_FILE)
            st.rerun()
        
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
            if st.button("Enregistrer session"):
                set_current_session(ns); st.rerun()
            if st.button("Déconnexion"): st.session_state["auth_ok"] = False; st.rerun()

    if st.session_state["auth_ok"]:
        t1, t2, t3 = st.tabs(["📊 Résultats", "📝 Services", "🖼️ Galerie Photos"])
        
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
                st.altair_chart(alt.Chart(df_p).mark_bar(color='#58A6FF').encode(x='Pts', y=alt.Y('S', sort='-x')), use_container_width=True)
            else: st.info("Aucun vote enregistré.")

        with t2:
            n_v = st.text_input("Ajouter un service")
            if st.button("➕ Valider"):
                if n_v: 
                    v = load_videos(); v.append(n_v); save_videos(v); st.rerun()
            st.divider()
            vids = load_videos()
            for i, v in enumerate(vids):
                c1, c2 = st.columns([0.8, 0.2])
                c1.write(f"• {v}")
                if c2.button("🗑️", key=f"ds_{i}"):
                    vids.remove(v); save_videos(vids); st.rerun()

        with t3:
            st.write("### 📸 Gestion de la Galerie")
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
                        if st.button("Supprimer", key=f"del_{i}", use_container_width=True):
                            os.remove(img_p); st.rerun()

# --- 5. MOBILE & LIVE ---
elif mode_vote:
    st.title("🗳️ Vote 2026")
    pseudo = st.text_input("Pseudo")
    vids = load_videos()
    s1 = st.segmented_control("Choix", vids)
    if st.button("Voter"):
        if pseudo and s1:
            fn = os.path.join(VOTES_DIR, f"{current_session}.csv")
            pd.DataFrame([[pseudo, s1]], columns=["Pseudo","Top1"]).to_csv(fn, mode='a', header=not os.path.exists(fn), index=False)
            st.success("Vote envoyé !")
else:
    st.markdown("<style>[data-testid='stSidebar'] {display:none;}</style>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2.5])
    with c1:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=180)
        qr_url = f"https://{st.context.headers.get('Host', '')}/?mode=vote"
        qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
        st.image(qr_buf.getvalue(), use_container_width=True)
    with c2:
        st.header("Social Wall")
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    if imgs:
        cols = st.columns(6)
        for i, img_p in enumerate(imgs): cols[i%6].image(img_p, use_container_width=True)
    time.sleep(5); st.rerun()
