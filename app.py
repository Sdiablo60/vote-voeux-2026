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
    if not os.path.exists(d): 
        os.makedirs(d)

st.set_page_config(page_title="Régie Master 2026", layout="wide")

# --- 2. TOUTES LES FONCTIONS DE GESTION ---
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

def add_service_callback():
    nouveau = st.session_state.get("widget_ajout", "").strip()
    if nouveau:
        vids = load_videos()
        if nouveau not in vids:
            vids.append(nouveau)
            save_videos(vids)
            st.toast(f"✅ {nouveau} ajouté !")
        st.session_state["widget_ajout"] = ""

# --- 3. LOGIQUE INITIALISATION ---
admin_pass = get_admin_password()
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"
current_session = get_current_session()

if "auth_ok" not in st.session_state: st.session_state["auth_ok"] = False
if "voted" not in st.session_state: st.session_state["voted"] = False
if "editing_service" not in st.session_state: st.session_state["editing_service"] = None

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
                if st.button("Enregistrer"):
                    if len(new_p) > 2:
                        set_admin_password(new_p)
                        st.success("Code modifié !")
                    else: st.error("Trop court")
            
            with st.expander("**REINITIALISATION**"):
                st.warning("⚠️ Action critique")
                st.info("Mémoire : ADMIN_***_**26")
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
            path_curr = os.path.join(VOTES_DIR, f"{current_session}.csv")
            df_res = pd.concat([pd.read_csv(f) for f in all_f]) if mode == "Cumul général" and all_f else (pd.read_csv(path_curr) if os.path.exists(path_curr) else pd.DataFrame())
            
            if not df_res.empty:
                scores = {v: 0 for v in load_videos()}
                for _, r in df_res.iterrows():
                    for i, p in enumerate([5, 3, 1]):
                        if r[f'Top{i+1}'] in scores: scores[r[f'Top{i+1}']] += p
                df_p = pd.DataFrame(list(scores.items()), columns=['S', 'Pts']).sort_values('Pts', ascending=False)
                st.altair_chart(alt.Chart(df_p).mark_bar(color='#FF4B4B').encode(x='Pts', y=alt.Y('S', sort='-x')), use_container_width=True)
                st.download_button("📥 Export CSV", df_res.to_csv(index=False), "export.csv", "text/csv")
            else: st.info("Aucun vote enregistré.")

        with tab_admin:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📡 Sessions & Médias")
                st.success(f"Session actuelle : **{current_session}**")
                ns = st.text_input("Nom de la nouvelle session", key="input_new_session")
                if st.button("🚀 Lancer la session"):
                    if ns:
                        set_current_session(ns)
                        fn = os.path.join(VOTES_DIR, f"{ns}.csv")
                        if not os.path.exists(fn):
                            pd.DataFrame(columns=["Prenom", "Pseudo", "Top1", "Top2", "Top3"]).to_csv(fn, index=False)
                        st.rerun()
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
                st.text_input("Ajouter un service", key="widget_ajout", on_change=add_service_callback)
                st.button("➕ Ajouter", on_click=add_service_callback)
                st.divider()
                vids = load_videos()
                for i, v in enumerate(vids):
                    col_v, col_b = st.columns([0.7, 0.3])
                    if st.session_state["editing_service"] == v:
                        nv = col_v.text_input("Editer", value=v, key=f"edit_{i}")
                        if col_b.button("💾", key=f"s_{i}"):
                            vids[i] = nv; save_videos(vids); st.session_state["editing_service"] = None; st.rerun()
                    else:
                        col_v.write(f"• {v}")
                        be, bd = col_b.columns(2)
                        if be.button("✏️", key=f"e_{i}"): st.session_state["editing_service"] = v; st.rerun()
                        if bd.button("❌", key=f"d_{i}"): vids.remove(v); save_videos(vids); st.rerun()
    else:
        st.warning("🔒 Authentifiez-vous dans la barre latérale.")

# --- 5. INTERFACE MOBILE (MODE VOTE) ---
elif mode_vote:
    st.title("🗳️ Vote Vœux 2026")
    if st.session_state["voted"]:
        st.success("✅ Vote enregistré !")
    else:
        pseudo = st.text_input("Pseudo / Trigramme")
        if pseudo and st.button("🚀 Apparaître sur l'écran"):
            df_p = pd.read_csv(PRESENCE_FILE) if os.path.exists(PRESENCE_FILE) else pd.DataFrame(columns=["Pseudo"])
            if pseudo not in df_p['Pseudo'].values:
                pd.DataFrame([[pseudo]], columns=["Pseudo"]).to_csv(PRESENCE_FILE, mode='a', header=not os.path.exists(PRESENCE_FILE), index=False)
            st.toast("Regardez le grand écran !")
        st.divider()
        vids = load_videos()
        s1 = st.segmented_control("Choix 1 (5pts)", vids, key="v1")
        s2 = st.segmented_control("Choix 2 (3pts)", [v for v in vids if v != s1], key="v2")
        s3 = st.segmented_control("Choix 3 (1pt)", [v for v in vids if v not in [s1, s2]], key="v3")
        if st.button("Valider le vote", use_container_width=True):
            if pseudo and s1 and s2 and s3:
                fn = os.path.join(VOTES_DIR, f"{current_session}.csv")
                df = pd.read_csv(fn) if os.path.exists(fn) else pd.DataFrame(columns=["Prenom", "Pseudo", "Top1", "Top2", "Top3"])
                pd.DataFrame([["", pseudo, s1, s2, s3]], columns=df.columns).to_csv(fn, mode='a', header=not os.path.exists(fn), index=False)
                st.session_state["voted"] = True; st.balloons(); time.sleep(1); st.rerun()

# --- 6. INTERFACE PUBLIC (SOCIAL WALL) ---
else:
    col_l, col_r = st.columns([1, 2])
    with col_l:
        if os.path.exists(LOGO_FILE): st.image(Image.open(LOGO_FILE), width=200)
        st.write("## 📲 Scannez pour participer")
        qr_url = "https://vote-voeux-2026-6rueeu6wcdbxa878nepqgf.streamlit.app/?mode=vote"
        qr_buf = BytesIO()
        qrcode.make(qr_url).save(qr_buf, format="PNG")
        st.image(qr_buf.getvalue(), use_container_width=True)
    with col_r:
        st.markdown("<h1 style='text-align:center; color:#FF4B4B;'>Bienvenue ! 👋</h1>", unsafe_allow_html=True)
        if os.path.exists(PRESENCE_FILE):
            noms = pd.read_csv(PRESENCE_FILE)['Pseudo'].unique().tolist()
            nuage = "".join([f'<span style="font-size:{random.randint(20,50)}px; color:{random.choice(["#FF4B4B","#1f77b4","#2ca02c","#ff7f0e"])}; margin:15px; font-weight:bold; display:inline-block;">{n}</span>' for n in noms])
            st.markdown(f'<div style="background:rgba(255,255,255,0.05); padding:40px; border-radius:30px; text-align:center; min-height:400px;">{nuage}</div>', unsafe_allow_html=True)
    st.divider()
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    if imgs:
        cols = st.columns(6)
        for i, img in enumerate(imgs): cols[i%6].image(img, use_container_width=True)
    time.sleep(5); st.rerun()
