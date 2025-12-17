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

# --- 3. LOGIQUE INITIALISATION ---
admin_pass = get_admin_password()
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"
current_session = get_current_session()

if "voted" not in st.session_state: st.session_state["voted"] = False
if "editing_service" not in st.session_state: st.session_state["editing_service"] = None

# --- 4. INTERFACE PUBLIC : SOCIAL WALL ---
if not est_admin and not mode_vote:
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

# --- 5. INTERFACE MOBILE : MODE VOTE ---
elif mode_vote:
    st.title("🗳️ Vote Vœux 2026")
    fn_check = os.path.join(VOTES_DIR, f"{current_session}.csv")
    if st.session_state["voted"]:
        st.success("✅ Vote enregistré !")
    else:
        pseudo = st.text_input("Votre Pseudo / Trigramme").strip()
        if pseudo and st.button("🚀 Apparaître sur l'écran"):
            df_p = pd.read_csv(PRESENCE_FILE) if os.path.exists(PRESENCE_FILE) else pd.DataFrame(columns=["Pseudo"])
            if pseudo not in df_p['Pseudo'].values:
                pd.DataFrame([[pseudo]], columns=["Pseudo"]).to_csv(PRESENCE_FILE, mode='a', header=not os.path.exists(PRESENCE_FILE), index=False)
            st.toast("Regardez le grand écran !")
        st.write("---")
        vids = load_videos()
        s1 = st.segmented_control("Choix 1", vids, key="mv1")
        s2 = st.segmented_control("Choix 2", [v for v in vids if v != s1], key="mv2")
        s3 = st.segmented_control("Choix 3", [v for v in vids if v not in [s1, s2]], key="mv3")
        if st.button("Valider mon vote 🗳️", use_container_width=True):
            if pseudo and s1 and s2 and s3:
                df_v = pd.read_csv(fn_check) if os.path.exists(fn_check) else pd.DataFrame(columns=["Pseudo"])
                if pseudo.lower() in df_v['Pseudo'].str.lower().values:
                    st.error("❌ Déjà voté.")
                else:
                    new_v = pd.DataFrame([["", pseudo, s1, s2, s3]], columns=["Prenom", "Pseudo", "Top1", "Top2", "Top3"])
                    new_v.to_csv(fn_check, mode='a', header=not os.path.exists(fn_check), index=False)
                    st.session_state["voted"] = True; st.balloons(); time.sleep(1); st.rerun()

# --- 6. INTERFACE ADMIN : CONSOLE ---
elif est_admin:
    st.title("🛠️ Console de Régie")
    with st.sidebar:
        st.header("🔑 Authentification")
        pwd_input = st.text_input("Mot de passe Admin", type="password")
    
    if pwd_input == admin_pass:
        tab_res, tab_admin = st.tabs(["📊 Résultats", "⚙️ Configuration & Sécurité"])
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
                ns = st.text_input("Nom session")
                if st.button("Lancer"): set_current_session(ns); st.rerun()
                st.divider()
                u_logo = st.file_uploader("Logo", type=['png', 'jpg'])
                if u_logo: Image.open(u_logo).save(LOGO_FILE); st.rerun()
                u_gal = st.file_uploader("Galerie", type=['png', 'jpg'], accept_multiple_files=True)
                if u_gal:
                    for f in u_gal: Image.open(f).save(os.path.join(GALLERY_DIR, f.name)); st.rerun()
            with c2:
                st.subheader("📝 Services")
                st.text_input("Ajouter", key="widget_ajout", on_change=lambda: None) # Callback simplifié
                if st.button("➕ Ajouter"):
                    v = st.session_state.widget_ajout
                    if v: vids = load_videos(); vids.append(v); save_videos(vids); st.rerun()
                st.divider()
                vids = load_videos()
                for i, v in enumerate(vids):
                    cv, cb = st.columns([0.7, 0.3])
                    cv.write(f"• {v}")
                    if cb.button("❌", key=f"del_{i}"): vids.remove(v); save_videos(vids); st.rerun()
            
            st.divider()
            st.subheader("🔒 Sécurité & Reset")
            new_p = st.text_input("Nouveau mot de passe", type="password")
            if st.button("Modifier le mot de passe"):
                set_admin_password(new_p); st.success("Modifié !"); st.rerun()
            
            if st.button("🚨 RÉINITIALISATION D'USINE (Tout vider)", type="secondary"):
                if os.path.exists(PASS_FILE): os.remove(PASS_FILE)
                if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
                if os.path.exists(PRESENCE_FILE): os.remove(PRESENCE_FILE)
                for f in glob.glob(os.path.join(VOTES_DIR, "*.csv")): os.remove(f)
                st.warning("Système réinitialisé. Rechargez la page."); time.sleep(2); st.rerun()
    else:
        st.warning("🔒 Saisissez le mot de passe dans la barre latérale.")
