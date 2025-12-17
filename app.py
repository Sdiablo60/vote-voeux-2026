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

# --- 2. FONCTIONS ---
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
    """Récupère le nombre de participants et de votes"""
    nb_participants = 0
    if os.path.exists(PRESENCE_FILE):
        nb_participants = len(pd.read_csv(PRESENCE_FILE)['Pseudo'].unique())
    
    current_session = get_current_session()
    path_curr = os.path.join(VOTES_DIR, f"{current_session}.csv")
    nb_votes = 0
    if os.path.exists(path_curr):
        nb_votes = len(pd.read_csv(path_curr))
        
    return nb_participants, nb_votes

# --- 3. LOGIQUE INITIALISATION ---
admin_pass = get_admin_password()
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"
current_session = get_current_session()

if "auth_ok" not in st.session_state: st.session_state["auth_ok"] = False
if "editing_service" not in st.session_state: st.session_state["editing_service"] = None

# --- 4. INTERFACE ADMIN (RÉGIE) ---
if est_admin:
    st.title("🛠️ Console de Régie")
    
    nb_p, nb_v = get_stats() # Calcul des stats en temps réel
    
    with st.sidebar:
        st.header("🔑 Authentification")
        if not st.session_state["auth_ok"]:
            pwd_input = st.text_input("Saisir le code", type="password")
            if pwd_input == admin_pass:
                st.session_state["auth_ok"] = True
                st.rerun()
        else:
            st.success("✅ Accès Autorisé")
            
            # --- COMPTEUR LIVE DANS LA SIDEBAR ---
            st.divider()
            st.metric(label="👥 Participants Actifs", value=nb_p)
            st.metric(label="📥 Votes (Session)", value=nb_v)
            
            # --- SECTION 📡 SESSION LIVE ---
            st.divider()
            st.subheader("📡 Session Live")
            st.info(f"En cours : **{current_session}**")
            ns = st.text_input("Nouveau nom", key="side_ns")
            if st.button("🚀 Lancer", use_container_width=True):
                if ns:
                    set_current_session(ns)
                    fn = os.path.join(VOTES_DIR, f"{ns}.csv")
                    if not os.path.exists(fn):
                        pd.DataFrame(columns=["Prenom", "Pseudo", "Top1", "Top2", "Top3"]).to_csv(fn, index=False)
                    st.rerun()

            # --- SECTION 📁 MÉDIAS ---
            st.divider()
            st.subheader("📁 Médias")
            u_logo = st.file_uploader("Logo", type=['png', 'jpg'], key="side_logo")
            if u_logo: Image.open(u_logo).save(LOGO_FILE); st.rerun()
            
            if st.button("🗑️ Reset Nuage de noms", use_container_width=True):
                if os.path.exists(PRESENCE_FILE): os.remove(PRESENCE_FILE); st.rerun()

            # --- SECTION 🔒 SECURITE & RESET ---
            st.divider()
            with st.expander("**SECURITE**"):
                new_p = st.text_input("Nouveau code", type="password")
                if st.button("Enregistrer"):
                    set_admin_password(new_p); st.toast("Modifié !"); st.rerun()
            
            with st.expander("**REINITIALISATION**"):
                st.info("Mémoire : ADMIN_***_**26")
                confirm = st.checkbox("Confirmer Reset")
                if st.button("RESET USINE"):
                    if confirm:
                        for f in [PASS_FILE, CONFIG_FILE, PRESENCE_FILE]:
                            if os.path.exists(f): os.remove(f)
                        for f in glob.glob(os.path.join(VOTES_DIR, "*.csv")): os.remove(f)
                        st.session_state["auth_ok"] = False; st.rerun()

            st.divider()
            if st.button("Déconnexion"):
                st.session_state["auth_ok"] = False; st.rerun()

    # --- CONTENU CENTRAL (Si authentifié) ---
    if st.session_state["auth_ok"]:
        tab_res, tab_vids, tab_gal = st.tabs(["📊 Résultats", "📝 Liste des Services", "🖼️ Galerie"])
        
        with tab_res:
            col_s1, col_s2 = st.columns(2)
            col_s1.metric("Participants total", nb_p)
            col_s2.metric("Votes enregistrés", nb_v)
            
            mode = st.radio("Périmètre", ["Session actuelle", "Total général"], horizontal=True)
            all_f = glob.glob(os.path.join(VOTES_DIR, "*.csv"))
            path_curr = os.path.join(VOTES_DIR, f"{current_session}.csv")
            df_res = pd.concat([pd.read_csv(f) for f in all_f]) if mode == "Total général" and all_f else (pd.read_csv(path_curr) if os.path.exists(path_curr) else pd.DataFrame())
            
            if not df_res.empty:
                scores = {v: 0 for v in load_videos()}
                for _, r in df_res.iterrows():
                    for i, p in enumerate([5, 3, 1]):
                        if r[f'Top{i+1}'] in scores: scores[r[f'Top{i+1}']] += p
                df_p = pd.DataFrame(list(scores.items()), columns=['S', 'Pts']).sort_values('Pts', ascending=False)
                st.altair_chart(alt.Chart(df_p).mark_bar(color='#FF4B4B').encode(x='Pts', y=alt.Y('S', sort='-x')), use_container_width=True)
            else: st.info("En attente des premiers votes...")

        with tab_vids:
            # (Gestion des services identique à la version précédente)
            st.subheader("Services / Vidéos")
            n_vid = st.text_input("Nom du service")
            if st.button("Ajouter"):
                vids = load_videos(); vids.append(n_vid); save_videos(vids); st.rerun()
            st.divider()
            vids = load_videos()
            for i, v in enumerate(vids):
                c_v, c_b = st.columns([0.8, 0.2])
                c_v.write(f"• {v}")
                if c_b.button("❌", key=f"d_{i}"): vids.remove(v); save_videos(vids); st.rerun()

        with tab_gal:
            # (Galerie identique)
            u_gal = st.file_uploader("Images", type=['png', 'jpg'], accept_multiple_files=True)
            if u_gal:
                for f in u_gal: Image.open(f).save(os.path.join(GALLERY_DIR, f.name))
                st.rerun()
            if st.button("🗑️ Vider Galerie"):
                for f in os.listdir(GALLERY_DIR): os.remove(os.path.join(GALLERY_DIR, f))
                st.rerun()
    else:
        st.warning("🔒 Authentifiez-vous dans la barre latérale.")

# --- 5. SOCIAL WALL / VOTE (Participant) ---
# ... [Le reste du code reste identique]
