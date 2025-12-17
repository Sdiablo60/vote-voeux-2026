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
if "editing_service" not in st.session_state: st.session_state["editing_service"] = None
if "gal_key" not in st.session_state: st.session_state["gal_key"] = 0

# --- 4. INTERFACE ADMIN (RÉGIE) ---
if est_admin:
    st.markdown("""
        <style>
        /* Design du bouton d'importation épuré */
        [data-testid="stFileUploader"] {
            background-color: #1c1e26;
            border: 1px solid #3d444d;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
        }
        
        /* Personnalisation du texte et du + */
        [data-testid="stFileUploaderDropzone"] div div::before {
            content: "＋";
            font-size: 1.8rem;
            color: #58A6FF;
            font-weight: 200;
            display: block;
            margin-bottom: -5px;
        }
        
        /* Remplacement du texte Browse files */
        [data-testid="stFileUploaderDropzone"] div div span {
            display: none;
        }
        [data-testid="stFileUploaderDropzone"]::after {
            content: "Importer une nouvelle photo";
            font-size: 0.85rem;
            color: #c9d1d9;
            letter-spacing: 0.5px;
        }
        
        /* Suppression des encadrements grossiers */
        .stTabs [data-baseweb="tab-list"] { gap: 20px; }
        .stTabs [data-baseweb="tab"] { border: none !important; font-weight: 600; }
        
        /* Cartes d'images élégantes */
        [data-testid="stImage"] {
            border: 1px solid #30363d;
            border-radius: 6px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        
        /* Boutons Retirer minimalistes */
        .stButton button {
            border: 1px solid #444;
            background-color: transparent;
            color: #8b949e;
            font-size: 0.75rem;
            text-transform: uppercase;
        }
        .stButton button:hover {
            border-color: #f85149;
            color: #f85149;
            background-color: rgba(248, 81, 73, 0.05);
        }
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
            st.success("✅ Accès Autorisé")
            st.metric("👥 Participants", nb_p)
            st.metric("📥 Votes", nb_v)
            
            st.divider()
            st.subheader("📡 Session Active")
            st.info(f"**{current_session}**")
            ns = st.text_input("Nom nouvelle session", key="side_ns")
            if st.button("🚀 Lancer", use_container_width=True):
                if ns:
                    set_current_session(ns)
                    fn = os.path.join(VOTES_DIR, f"{ns}.csv")
                    if not os.path.exists(fn):
                        pd.DataFrame(columns=["Prenom", "Pseudo", "Top1", "Top2", "Top3"]).to_csv(fn, index=False)
                    st.rerun()

            st.divider()
            with st.expander("**SECURITE**"):
                np = st.text_input("Nouveau code", type="password")
                if st.button("Modifier"):
                    if len(np) > 2:
                        set_admin_password(np); st.toast("Code modifié !"); st.rerun()
            
            with st.expander("**REINITIALISATION**"):
                confirm_reset = st.checkbox("Confirmer le reset total")
                if st.button("RESET USINE"):
                    if confirm_reset:
                        for f in [PASS_FILE, CONFIG_FILE, PRESENCE_FILE, SESSION_CONFIG]:
                            if os.path.exists(f): os.remove(f)
                        for f in glob.glob(os.path.join(VOTES_DIR, "*.csv")): os.remove(f)
                        st.session_state["auth_ok"] = False
                        st.rerun()
            
            st.divider()
            if st.button("Déconnexion"):
                st.session_state["auth_ok"] = False
                st.rerun()

    if st.session_state["auth_ok"]:
        t1, t2, t3 = st.tabs(["📊 Résultats", "📝 Services", "🖼️ Galerie"])
        
        with t1:
            mode = st.radio("Périmètre", ["Session actuelle", "Total général"], horizontal=True)
            all_f = glob.glob(os.path.join(VOTES_DIR, "*.csv"))
            path_curr = os.path.join(VOTES_DIR, f"{current_session}.csv")
            df_res = pd.concat([pd.read_csv(f) for f in all_f]) if mode == "Total général" and all_f else (pd.read_csv(path_curr) if os.path.exists(path_curr) else pd.DataFrame())
            
            if not df_res.empty:
                vids_list = load_videos()
                scores = {v: 0 for v in vids_list}
                for _, r in df_res.iterrows():
                    for i, p in enumerate([5, 3, 1]):
                        choix = r.get(f'Top{i+1}')
                        if choix in scores: scores[choix] += p
                df_p = pd.DataFrame(list(scores.items()), columns=['S', 'Pts']).sort_values('Pts', ascending=False)
                st.altair_chart(alt.Chart(df_p).mark_bar(color='#58A6FF', cornerRadiusEnd=4).encode(x='Pts', y=alt.Y('S', sort='-x')), use_container_width=True)
            else: st.info("En attente des premiers votes...")

        with t2:
            st.subheader("Services")
            n_v = st.text_input("Nouveau nom", placeholder="Ex: Service RH")
            if st.button("➕ Ajouter service"):
                if n_v: 
                    vids = load_videos(); vids.append(n_v); save_videos(vids); st.rerun()
            st.divider()
            vids = load_videos()
            for i, v in enumerate(vids):
                c_v, c_b = st.columns([0.85, 0.15])
                c_v.write(f"• {v}")
                if c_b.button("🗑️", key=f"d_{i}"): vids.remove(v); save_videos(vids); st.rerun()

        with t3:
            st.subheader("Galerie")
            u_logo = st.file_uploader("Modifier le logo", type=['png', 'jpg'], key="logo_up")
            if u_logo: 
                Image.open(u_logo).save(LOGO_FILE)
                st.rerun()
            
            st.divider()
            
            # Zone d'importation ultra-sleek
            u_gal = st.file_uploader("", 
                                    type=['png', 'jpg', 'jpeg'], 
                                    accept_multiple_files=True, 
                                    key=f"gal_up_{st.session_state['gal_key']}")
            
            if u_gal:
                with st.spinner("Synchronisation..."):
                    for f in u_gal:
                        Image.open(f).save(os.path.join(GALLERY_DIR, f.name))
                st.session_state["gal_key"] += 1
                time.sleep(0.5)
                st.rerun()
            
            st.divider()
            imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
            if imgs:
                imgs.sort(key=os.path.getmtime, reverse=True)
                cols = st.columns(5)
                for i, img_p in enumerate(imgs):
                    with cols[i%5]:
                        st.image(img_p, use_container_width=True)
                        if st.button("Retirer", key=f"del_img_{i}", use_container_width=True):
                            os.remove(img_p)
                            st.rerun()
            else: st.info("Bibliothèque vide.")

# --- 5. MODE PARTICIPANT (VOTE) ---
elif mode_vote:
    st.title("🗳️ Vote Vœux 2026")
    if st.session_state["voted"]:
        st.success("✅ Vote enregistré !")
    else:
        pseudo = st.text_input("Pseudo / Trigramme").strip()
        if pseudo and st.button("🚀 Rejoindre l'écran"):
            df_p = pd.read_csv(PRESENCE_FILE) if os.path.exists(PRESENCE_FILE) else pd.DataFrame(columns=["Pseudo"])
            if pseudo not in df_p['Pseudo'].values:
                pd.DataFrame([[pseudo]], columns=["Pseudo"]).to_csv(PRESENCE_FILE, mode='a', header=not os.path.exists(PRESENCE_FILE), index=False)
            st.toast("Regardez le grand écran !")
        
        st.divider()
        vids = load_videos()
        s1 = st.segmented_control("Choix 1 (5 pts)", vids, key="s1")
        s2 = st.segmented_control("Choix 2 (3 pts)", [v for v in vids if v != s1], key="s2")
        s3 = st.segmented_control("Choix 3 (1 pt)", [v for v in vids if v not in [s1, s2]], key="s3")
        
        if st.button("Valider mon vote", use_container_width=True):
            if pseudo and s1 and s2 and s3:
                fn = os.path.join(VOTES_DIR, f"{current_session}.csv")
                pd.DataFrame([["", pseudo, s1, s2, s3]], columns=["Prenom","Pseudo","Top1","Top2","Top3"]).to_csv(fn, mode='a', header=not os.path.exists(fn), index=False)
                st.session_state["voted"] = True; st.balloons(); time.sleep(1); st.rerun()

# --- 6. MODE SOCIAL WALL (LIVE) ---
else:
    st.markdown("<style>[data-testid='stSidebar'] {display:none;}</style>", unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 2.5])
    with col_l:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=180)
        qr_url = "https://vote-voeux-2026-6rueeu6wcdbxa878nepqgf.streamlit.app/?mode=vote"
        qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
        st.image(qr_buf.getvalue(), use_container_width=True)
        nb_p, _ = get_stats()
        st.metric("Participants", nb_p)
    with col_r:
        if os.path.exists(PRESENCE_FILE):
            noms = pd.read_csv(PRESENCE_FILE)['Pseudo'].unique().tolist()
            nuage = " ".join([f"<span style='font-size:{random.randint(22,55)}px; color:{random.choice(['#58A6FF','#FF4B4B','#2ca02c','#ff7f0e'])}; margin:15px; font-weight:bold; display:inline-block;'>{n}</span>" for n in noms])
            st.markdown(f"<div style='text-align:center;'>{nuage}</div>", unsafe_allow_html=True)
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    if imgs:
        cols = st.columns(6)
        for i, img_p in enumerate(imgs): cols[i%6].image(img_p, use_container_width=True)
    time.sleep(5); st.rerun()
