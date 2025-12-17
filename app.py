import streamlit as st
import pandas as pd
import os
import base64
from PIL import Image
import altair as alt
from io import BytesIO
import qrcode
import glob

# --- 1. CONFIGURATION DES RÉPERTOIRES ---
ADMIN_PASSWORD = "ADMIN_VOEUX_2026"
VOTES_DIR = "sessions_votes"
GALLERY_DIR = "galerie_images"
CONFIG_FILE = "config_videos.csv"
TITRE_FILE = "titre_config.txt"
LOCK_FILE = "vote_lock.txt"
LOGO_FILE = "logo_entreprise.png"
SESSION_CONFIG = "current_session.txt"

for d in [VOTES_DIR, GALLERY_DIR]:
    if not os.path.exists(d): os.makedirs(d)

st.set_page_config(page_title="Régie Master 2026", layout="wide")

# --- 2. FONCTIONS DE GESTION ---
def get_current_session():
    if os.path.exists(SESSION_CONFIG):
        with open(SESSION_CONFIG, "r") as f: return f.read().strip()
    return "session_initiale"

def set_current_session(name):
    with open(SESSION_CONFIG, "w") as f: f.write(name)

def load_videos():
    if os.path.exists(CONFIG_FILE): 
        return pd.read_csv(CONFIG_FILE)['Video'].tolist()
    return ["BU PAX", "BU FRET", "BU BTOB", "DPMI", "RH", "Finances", "IT", "Direction"]

def save_videos(liste):
    pd.DataFrame(liste, columns=['Video']).to_csv(CONFIG_FILE, index=False)

def get_admin_title():
    if os.path.exists(TITRE_FILE):
        with open(TITRE_FILE, "r", encoding="utf-8") as f: return f.read()
    return "Gestion des Services"

# --- 3. LOGIQUE INITIALISATION ---
current_session = get_current_session()
all_files = glob.glob(os.path.join(VOTES_DIR, "*.csv"))
nb_sessions = len(all_files)

if "voted" not in st.session_state: st.session_state["voted"] = False
if "editing_service" not in st.session_state: st.session_state["editing_service"] = None

est_admin = st.query_params.get("admin") == "true"
if os.path.exists(LOGO_FILE):
    st.image(Image.open(LOGO_FILE), width=150)

st.title("🎬 Élection Vidéo Vœux 2026")

if est_admin:
    tab_vote, tab_res, tab_admin = st.tabs(["🗳️ Espace Vote", "📊 Résultats", "🛠️ Console Admin"])
else:
    tab_vote = st.container()

# --- 4. ONGLET VOTE ---
with tab_vote:
    if est_admin:
        s_col1, s_col2, s_col3 = st.columns([1.5, 1, 1])
        s_col1.info(f"📍 Session active : **{current_session.upper()}**")
        s_col2.metric("Sessions totales", nb_sessions)
        with s_col3.popover("➕ Nouvelle Session"):
            ns = st.text_input("Nom de la session")
            if st.button("Démarrer"):
                if ns: set_current_session(ns); st.rerun()

        v_col1, v_col2 = st.columns([2, 1])
        with v_col2:
            st.write("📲 **QR Code**")
            qr_buf = BytesIO()
            qrcode.make("https://vote-voeux-2026-6rueeu6wcdbxa878nepqgf.streamlit.app/").save(qr_buf, format="PNG")
            st.image(qr_buf.getvalue(), width=150)
    
    # Galerie
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    if imgs:
        cols = st.columns(5)
        for i, img in enumerate(imgs): cols[i%5].image(img, use_container_width=True)

    st.divider()
    if os.path.exists(LOCK_FILE):
        st.warning("🔒 Les votes sont clos.")
    elif st.session_state["voted"]:
        st.success(f"✅ Vote enregistré pour {current_session} !")
        if st.button("Nouveau vote"): st.session_state["voted"] = False; st.rerun()
    else:
        p1 = st.text_input("Prénom")
        p2 = st.text_input("Pseudo / Trigramme")
        vids = load_videos()
        
        s1 = st.segmented_control("1er choix (5 pts)", vids, key="v1")
        s2 = st.segmented_control("2ème choix (3 pts)", [v for v in vids if v != s1], key="v2")
        s3 = st.segmented_control("3ème choix (1 pt)", [v for v in vids if v not in [s1, s2]], key="v3")
        
        if st.button("Valider 🚀", use_container_width=True):
            if p1 and p2 and s1 and s2 and s3:
                fn = os.path.join(VOTES_DIR, f"{current_session}.csv")
                df = pd.read_csv(fn) if os.path.exists(fn) else pd.DataFrame(columns=["Prenom", "Pseudo", "Top1", "Top2", "Top3"])
                if p2.lower() in df['Pseudo'].str.lower().values:
                    st.error("❌ Déjà voté")
                else:
                    pd.DataFrame([[p1, p2, s1, s2, s3]], columns=df.columns).to_csv(fn, mode='a', header=not os.path.exists(fn), index=False)
                    st.session_state["voted"] = True; st.balloons(); st.rerun()
            else: st.error("⚠️ Incomplet")

# --- 5. ONGLET RÉSULTATS ---
if est_admin:
    with tab_res:
        mode = st.radio("Affichage", ["Session en cours", "Cumul général"], horizontal=True)
        df_res = pd.DataFrame()
        if mode == "Session en cours":
            fn = os.path.join(VOTES_DIR, f"{current_session}.csv")
            if os.path.exists(fn): df_res = pd.read_csv(fn)
        else:
            if all_files: df_res = pd.concat([pd.read_csv(f) for f in all_files])

        if not df_res.empty:
            scores = {v: 0 for v in load_videos()}
            for _, r in df_res.iterrows():
                for i, p in enumerate([5, 3, 1]):
                    if r[f'Top{i+1}'] in scores: scores[r[f'Top{i+1}']] += p
            df_p = pd.DataFrame(list(scores.items()), columns=['S', 'Pts']).sort_values('Pts', ascending=False)
            st.altair_chart(alt.Chart(df_p).mark_bar(color='#FF4B4B').encode(x='Pts', y=alt.Y('S', sort='-x')), use_container_width=True)
        else: st.info("Aucun vote.")

# --- 6. ONGLET ADMIN ---
    with tab_admin:
        if st.text_input("Code Admin", type="password") == ADMIN_PASSWORD:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("⚙️ Contrôle")
                u_logo = st.file_uploader("Logo", type=['png', 'jpg'])
                if u_logo: Image.open(u_logo).save(LOGO_FILE); st.rerun()
                if st.button("🔒 Clôturer / Ouvrir"):
                    if os.path.exists(LOCK_FILE): os.remove(LOCK_FILE)
                    else: open(LOCK_FILE, "w").write("L")
                    st.rerun()
                if st.button("🗑️ Reset Session Active"):
                    fn = os.path.join(VOTES_DIR, f"{current_session}.csv")
                    if os.path.exists(fn): os.remove(fn)
                    st.rerun()
            with c2:
                st.subheader("📝 Services")
                ns = st.text_input("Ajouter service")
                if st.button("➕"):
                    vids = load_videos(); vids.append(ns); save_videos(vids); st.rerun()
                vids = load_videos()
                for i, v in enumerate(vids):
                    col_v, col_d = st.columns([0.8, 0.2])
                    col_v.write(f"• {v}")
                    if col_d.button("❌", key=f"d_{i}"): vids.remove(v); save_videos(vids); st.rerun()
