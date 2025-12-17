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

# --- 2. FONCTIONS DE GESTION (INCLUANT CELLE QUI MANQUAIT) ---
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

# CETTE FONCTION MANQUAIT SUREMENT :
def set_current_session(name):
    with open(SESSION_CONFIG, "w", encoding="utf-8") as f: f.write(name)

def load_videos():
    if os.path.exists(CONFIG_FILE): 
        return pd.read_csv(CONFIG_FILE)['Video'].tolist()
    return ["BU PAX", "BU FRET", "BU BTOB", "DPMI (ateliers)", "Service RH", "Service Finances", "Service AO", "Service QSSE", "Service IT", "Direction Pôle"]

def save_videos(liste):
    pd.DataFrame(liste, columns=['Video']).to_csv(CONFIG_FILE, index=False)

# --- 3. LOGIQUE INITIALISATION ---
admin_pass = get_admin_password()
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"
current_session = get_current_session()

if "auth_ok" not in st.session_state: st.session_state["auth_ok"] = False
if "voted" not in st.session_state: st.session_state["voted"] = False

# --- 4. INTERFACE ADMIN (RÉGIE) ---
if est_admin:
    st.title("🛠️ Console de Régie")
    
    with st.sidebar:
        st.header("🔑 Authentification")
        if not st.session_state["auth_ok"]:
            pwd_input = st.text_input("Saisir le code", type="password")
            if pwd_input == admin_pass:
                st.session_state["auth_ok"] = True
                st.rerun()
            elif pwd_input != "":
                st.error("Code incorrect")
        else:
            st.success("✅ Accès Autorisé")
            if st.button("Déconnexion"):
                st.session_state["auth_ok"] = False
                st.rerun()
            
            st.divider()
            with st.expander("**SECURITE**"):
                new_p = st.text_input("Nouveau code admin", type="password")
                if st.button("Mettre à jour le code"):
                    if len(new_p) > 2:
                        set_admin_password(new_p)
                        st.success("Code modifié !")
                    else: st.error("Trop court")
            
            with st.expander("**REINITIALISATION**"):
                st.warning("⚠️ Action critique")
                st.info("Indication mémoire : ADMIN_***_**26")
                check_confirm = st.checkbox("Confirmer la suppression totale")
                if st.button("RESET DU MOT DE PASSE D'USINE"):
                    if check_confirm:
                        if os.path.exists(PASS_FILE): os.remove(PASS_FILE)
                        if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
                        if os.path.exists(PRESENCE_FILE): os.remove(PRESENCE_FILE)
                        for f in glob.glob(os.path.join(VOTES_DIR, "*.csv")): os.remove(f)
                        st.session_state["auth_ok"] = False
                        st.rerun()

    if st.session_state["auth_ok"]:
        tab_res, tab_admin = st.tabs(["📊 Résultats", "⚙️ Configuration"])
        
        with tab_res:
            mode = st.radio("Affichage", ["Session en cours", "Cumul général"], horizontal=True)
            all_f = glob.glob(os.path.join(VOTES_DIR, "*.csv"))
            df_res = pd.concat([pd.read_csv(f) for f in all_f]) if mode == "Cumul général" and all_f else (pd.read_csv(os.path.join(VOTES_DIR, f"{current_session}.csv")) if os.path.exists(os.path.join(VOTES_DIR, f"{current_session}.csv")) else pd.DataFrame())
            
            if not df_res.empty:
                scores = {v: 0 for v in load_videos()}
                for _, r in df_res.iterrows():
                    for i, p in enumerate([5, 3, 1]):
                        if r[f'Top{i+1}'] in scores: scores[r[f'Top{i+1}']] += p
                df_p = pd.DataFrame(list(scores.items()), columns=['S', 'Pts']).sort_values('Pts', ascending=False)
                st.altair_chart(alt.Chart(df_p).mark_bar(color='#FF4B4B').encode(x='Pts', y=alt.Y('S', sort='-x')), use_container_width=True)
                st.download_button("📥 Export CSV", df_res.to_csv(index=False), "export.csv", "text/csv")

        with tab_admin:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📡 Sessions & Médias")
                ns = st.text_input("Nom de la nouvelle session")
                if st.button("Lancer la session"):
                    if ns: 
                        set_current_session(ns) # <--- La fonction est maintenant définie !
                        st.rerun()
                st.write(f"Session actuelle : **{current_session}**")
                st.divider()
                u_logo = st.file_uploader("Modifier le Logo", type=['png', 'jpg'])
                if u_logo: Image.open(u_logo).save(LOGO_FILE); st.rerun()
                u_gal = st.file_uploader("Ajouter photos galerie", type=['png', 'jpg'], accept_multiple_files=True)
                if u_gal:
                    for f in u_gal: Image.open(f).save(os.path.join(GALLERY_DIR, f.name)); st.rerun()
                if st.button("🗑️ Vider le Nuage de noms"):
                    if os.path.exists(PRESENCE_FILE): os.remove(PRESENCE_FILE); st.rerun()

            with c2:
                st.subheader("📝 Liste des Services")
                if "widget_ajout" not in st.session_state: st.session_state.widget_ajout = ""
                def add_cb():
                    v = st.session_state.widget_ajout
                    if v:
                        vids = load_videos(); vids.append(v); save_videos(vids)
                        st.session_state.widget_ajout = ""; st.toast("Ajouté !")

                st.text_input("Ajouter un service", key="widget_ajout", on_change=add_cb)
                st.button("➕ Ajouter", on_click=add_cb)
                st.divider()
                vids = load_videos()
                for i, v in enumerate(vids):
                    col_v, col_b = st.columns([0.7, 0.3])
                    col_v.write(f"• {v}")
                    if col_b.button("❌", key=f"del_{i}"):
                        vids.remove(v); save_videos(vids); st.rerun()
    else:
        st.warning("🔒 Authentifiez-vous dans la barre latérale.")

# --- 5. SOCIAL WALL / VOTE PARTICIPANTS ---
elif mode_vote:
    st.title("🗳️ Vote Vœux 2026")
    if st.session_state["voted"]:
        st.success("✅ Vote enregistré !")
    else:
        pseudo = st.text_input("Pseudo")
        vids = load_videos()
        s1 = st.segmented_control("Choix 1", vids, key="mv1")
        s2 = st.segmented_control("Choix 2", [v for v in vids if v != s1], key="mv2")
        s3 = st.segmented_control("Choix 3", [v for v in vids if v not in [s1, s2]], key="mv3")
        if st.button("Valider"):
            fn = os.path.join(VOTES_DIR, f"{current_session}.csv")
            df = pd.read_csv(fn) if os.path.exists(fn) else pd.DataFrame(columns=["Prenom", "Pseudo", "Top1", "Top2", "Top3"])
            pd.DataFrame([["", pseudo, s1, s2, s3]], columns=df.columns).to_csv(fn, mode='a', header=not os.path.exists(fn), index=False)
            st.session_state["voted"] = True; st.rerun()

else:
    # SOCIAL WALL
    st.title("✨ Social Wall")
    if os.path.exists(PRESENCE_FILE):
        noms = pd.read_csv(PRESENCE_FILE)['Pseudo'].unique().tolist()
        st.write(", ".join(noms))
    time.sleep(5); st.rerun()
