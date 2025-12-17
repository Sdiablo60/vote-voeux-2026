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
ADMIN_PASSWORD = "ADMIN_VOEUX_2026"
VOTES_DIR = "sessions_votes"
GALLERY_DIR = "galerie_images"
CONFIG_FILE = "config_videos.csv"
LOGO_FILE = "logo_entreprise.png"
SESSION_CONFIG = "current_session.txt"
PRESENCE_FILE = "presence_live.csv"
TITRE_FILE = "titre_config.txt"

for d in [VOTES_DIR, GALLERY_DIR]:
    if not os.path.exists(d): os.makedirs(d)

st.set_page_config(page_title="Régie Master 2026", layout="wide")

# --- 2. FONCTIONS ---
def get_current_session():
    if os.path.exists(SESSION_CONFIG):
        with open(SESSION_CONFIG, "r") as f: return f.read().strip()
    return "session_1"

def set_current_session(name):
    with open(SESSION_CONFIG, "w") as f: f.write(name)

def load_videos():
    if os.path.exists(CONFIG_FILE): 
        return pd.read_csv(CONFIG_FILE)['Video'].tolist()
    return ["BU PAX", "BU FRET", "BU BTOB", "DPMI (ateliers)", "Service RH", "Service Finances", "Service AO", "Service QSSE", "Service IT", "Direction Pôle"]

def save_videos(liste):
    pd.DataFrame(liste, columns=['Video']).to_csv(CONFIG_FILE, index=False)

def ajouter_service_callback():
    nouveau = st.session_state["widget_ajout"].strip()
    if nouveau:
        vids = load_videos()
        if nouveau not in vids:
            vids.append(nouveau); save_videos(vids)
            st.toast(f"✅ {nouveau} ajouté !")
        st.session_state["widget_ajout"] = ""

def get_admin_title():
    if os.path.exists(TITRE_FILE):
        with open(TITRE_FILE, "r", encoding="utf-8") as f: return f.read()
    return "Gestion des Services"

# --- 3. LOGIQUE INITIALISATION ---
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
    if st.session_state["voted"]:
        st.success("✅ Vote enregistré !")
        if st.button("Voter à nouveau"): st.session_state["voted"] = False; st.rerun()
    else:
        pseudo = st.text_input("Votre Pseudo / Trigramme")
        if pseudo and st.button("🚀 Apparaître sur l'écran"):
            df_p = pd.read_csv(PRESENCE_FILE) if os.path.exists(PRESENCE_FILE) else pd.DataFrame(columns=["Pseudo"])
            if pseudo not in df_p['Pseudo'].values:
                pd.DataFrame([[pseudo]], columns=["Pseudo"]).to_csv(PRESENCE_FILE, mode='a', header=not os.path.exists(PRESENCE_FILE), index=False)
            st.toast("Regardez le grand écran !")
        st.write("---")
        vids = load_videos()
        s1 = st.segmented_control("Top 1 (5 pts)", vids, key="mv1")
        s2 = st.segmented_control("Top 2 (3 pts)", [v for v in vids if v != s1], key="mv2")
        s3 = st.segmented_control("Top 3 (1 pt)", [v for v in vids if v not in [s1, s2]], key="mv3")
        if st.button("Valider mon vote 🗳️", use_container_width=True):
            if pseudo and s1 and s2 and s3:
                fn = os.path.join(VOTES_DIR, f"{current_session}.csv")
                df = pd.read_csv(fn) if os.path.exists(fn) else pd.DataFrame(columns=["Prenom", "Pseudo", "Top1", "Top2", "Top3"])
                pd.DataFrame([["", pseudo, s1, s2, s3]], columns=df.columns).to_csv(fn, mode='a', header=not os.path.exists(fn), index=False)
                st.session_state["voted"] = True; st.balloons(); st.rerun()

# --- 6. INTERFACE ADMIN : CONSOLE COMPLÈTE ---
elif est_admin:
    tab_res, tab_admin = st.tabs(["📊 Résultats & Exports", "🛠️ Configuration Régie"])
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
            st.download_button("📥 Télécharger CSV", df_res.to_csv(index=False), "export.csv", "text/csv", use_container_width=True)
    with tab_admin:
        if st.text_input("Code Admin", type="password") == ADMIN_PASSWORD:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("⚙️ Maintenance Live")
                if st.button("🗑️ Vider le Nuage de noms"):
                    if os.path.exists(PRESENCE_FILE): os.remove(PRESENCE_FILE); st.rerun()
                if st.button("🗑️ Reset Session Active"):
                    fn = os.path.join(VOTES_DIR, f"{current_session}.csv"); 
                    if os.path.exists(fn): os.remove(fn); st.rerun()
                st.divider()
                st.subheader("📁 Médias")
                u_logo = st.file_uploader("Logo", type=['png', 'jpg'])
                if u_logo: Image.open(u_logo).save(LOGO_FILE); st.rerun()
                u_gal = st.file_uploader("Photos Galerie", type=['png', 'jpg'], accept_multiple_files=True)
                if u_gal:
                    for f in u_gal: Image.open(f).save(os.path.join(GALLERY_DIR, f.name)); st.rerun()
                if st.button("🗑️ Vider Galerie"):
                    for f in os.listdir(GALLERY_DIR): os.remove(os.path.join(GALLERY_DIR, f)); st.rerun()
            with c2:
                st.subheader(f"📝 {get_admin_title()}")
                st.text_input("Ajouter un service", key="widget_ajout", on_change=ajouter_service_callback)
                st.button("➕ Ajouter", on_click=ajouter_service_callback)
                st.divider()
                vids = load_videos()
                for i, v in enumerate(vids):
                    col_v, col_btn = st.columns([0.7, 0.3])
                    if st.session_state["editing_service"] == v:
                        nv = col_v.text_input("Modif", value=v, key=f"inp_{i}")
                        if col_btn.button("💾", key=f"s_{i}"):
                            vids[i] = nv; save_videos(vids); st.session_state["editing_service"] = None; st.rerun()
                    else:
                        col_v.write(f"• {v}")
                        b_e, b_d = col_btn.columns(2)
                        if b_e.button("✏️", key=f"e_{i}"): st.session_state["editing_service"] = v; st.rerun()
                        if b_d.button("❌", key=f"d_{i}"): vids.remove(v); save_videos(vids); st.rerun()
