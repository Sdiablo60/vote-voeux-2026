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
    return ["BU PAX", "BU FRET", "BU BTOB", "DPMI (ateliers)", "Service RH", "Service Finances", "Service AO", "Service QSSE", "Service IT", "Direction Pôle"]

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
if "voted" not in st.session_state: st.session_state["voted"] = False
if "gal_key" not in st.session_state: st.session_state["gal_key"] = 0

# --- 4. INTERFACE ADMIN (RÉGIE) ---
if est_admin:
    st.markdown("""
        <style>
        [data-testid="stFileUploader"] {
            background-color: #1c1e26;
            border: 1px solid #3d444d;
            border-radius: 8px;
            padding: 10px;
        }
        [data-testid="stFileUploaderDropzone"] div div::before {
            content: "＋";
            font-size: 1.8rem;
            color: #58A6FF;
            display: block;
            margin-bottom: -5px;
        }
        [data-testid="stFileUploaderDropzone"] div div span { display: none; }
        [data-testid="stFileUploaderDropzone"]::after {
            content: "Importer une photo ou un logo";
            font-size: 0.85rem;
            color: #c9d1d9;
        }
        .stButton button { font-size: 0.7rem; padding: 2px 10px; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🛠️ Console de Régie")
    nb_p, nb_v = get_stats()
    
    with st.sidebar:
        st.header("🔑 Authentification")
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
            ns = st.text_input("Nom session", key="side_ns")
            if st.button("🚀 Lancer", use_container_width=True):
                if ns: set_current_session(ns); st.rerun()
            st.divider()
            if st.button("Déconnexion"): st.session_state["auth_ok"] = False; st.rerun()

    if st.session_state["auth_ok"]:
        t1, t2, t3 = st.tabs(["📊 Résultats", "📝 Services", "🖼️ Galerie"])
        
        with t1:
            all_f = glob.glob(os.path.join(VOTES_DIR, "*.csv"))
            path_curr = os.path.join(VOTES_DIR, f"{current_session}.csv")
            df_res = pd.read_csv(path_curr) if os.path.exists(path_curr) else pd.DataFrame()
            if not df_res.empty:
                vids_list = load_videos()
                scores = {v: 0 for v in vids_list}
                for _, r in df_res.iterrows():
                    for i, p in enumerate([5, 3, 1]):
                        c = r.get(f'Top{i+1}')
                        if c in scores: scores[c] += p
                df_p = pd.DataFrame(list(scores.items()), columns=['S', 'Pts']).sort_values('Pts', ascending=False)
                st.altair_chart(alt.Chart(df_p).mark_bar(color='#58A6FF').encode(x='Pts', y=alt.Y('S', sort='-x')), use_container_width=True)
            else: st.info("Aucun vote.")

        with t2:
            n_v = st.text_input("Nouveau service")
            if st.button("➕ Ajouter"):
                if n_v: vids = load_videos(); vids.append(n_v); save_videos(vids); st.rerun()
            vids = load_videos()
            for i, v in enumerate(vids):
                c1, c2 = st.columns([0.8, 0.2])
                c1.write(f"• {v}")
                if c2.button("🗑️", key=f"d_{i}"): vids.remove(v); save_videos(vids); st.rerun()

        with t3:
            # UN SEUL UPLOADER
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
                        # Options pour chaque image
                        if st.button("Définir Logo", key=f"logo_{i}"):
                            Image.open(img_p).save(LOGO_FILE); st.toast("Logo modifié !")
                        if st.button("Retirer", key=f"del_{i}"):
                            os.remove(img_p); st.rerun()

# --- 5. MOBILE & SOCIAL WALL ---
elif mode_vote:
    st.title("🗳️ Vote 2026")
    if st.session_state["voted"]: st.success("✅ Voté !")
    else:
        pseudo = st.text_input("Pseudo")
        if pseudo and st.button("🚀 Apparaître"):
            df_p = pd.read_csv(PRESENCE_FILE) if os.path.exists(PRESENCE_FILE) else pd.DataFrame(columns=["Pseudo"])
            if pseudo not in df_p['Pseudo'].values:
                pd.DataFrame([[pseudo]], columns=["Pseudo"]).to_csv(PRESENCE_FILE, mode='a', header=not os.path.exists(PRESENCE_FILE), index=False)
        vids = load_videos()
        s1 = st.segmented_control("Top 1", vids)
        if st.button("Valider"):
            fn = os.path.join(VOTES_DIR, f"{current_session}.csv")
            pd.DataFrame([["", pseudo, s1, "", ""]], columns=["Prenom","Pseudo","Top1","Top2","Top3"]).to_csv(fn, mode='a', header=not os.path.exists(fn), index=False)
            st.session_state["voted"] = True; st.rerun()
else:
    st.markdown("<style>[data-testid='stSidebar'] {display:none;}</style>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2.5])
    with c1:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=150)
        qr_url = "https://vote-voeux-2026-6rueeu6wcdbxa878nepqgf.streamlit.app/?mode=vote"
        qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
        st.image(qr_buf.getvalue(), use_container_width=True)
    with c2:
        if os.path.exists(PRESENCE_FILE):
            noms = pd.read_csv(PRESENCE_FILE)['Pseudo'].unique().tolist()
            nuage = " ".join([f"<span style='font-size:{random.randint(20,50)}px; color:{random.choice(['#58A6FF','#FF4B4B'])}; font-weight:bold;'>{n}</span>" for n in noms])
            st.markdown(f"<div style='text-align:center;'>{nuage}</div>", unsafe_allow_html=True)
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    if imgs:
        cols = st.columns(6)
        for i, img_p in enumerate(imgs): cols[i%6].image(img_p, use_container_width=True)
    time.sleep(5); st.rerun()
