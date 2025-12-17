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

# --- 4. INTERFACE ADMIN (RÉGIE) ---
if est_admin:
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
            st.metric("👥 Participants Live", nb_p)
            st.metric("📥 Votes Session", nb_v)
            
            st.divider()
            st.subheader("📡 Session Active")
            st.info(f"En cours : **{current_session}**")
            ns = st.text_input("Nom nouvelle session", key="side_ns")
            if st.button("🚀 Lancer la session", use_container_width=True):
                if ns:
                    set_current_session(ns)
                    fn = os.path.join(VOTES_DIR, f"{ns}.csv")
                    if not os.path.exists(fn):
                        pd.DataFrame(columns=["Prenom", "Pseudo", "Top1", "Top2", "Top3"]).to_csv(fn, index=False)
                    st.rerun()

            st.divider()
            with st.expander("**SECURITE**"):
                np = st.text_input("Nouveau code", type="password")
                if st.button("Changer code"):
                    if len(np) > 2:
                        set_admin_password(np); st.toast("Code modifié !"); st.rerun()
            
            with st.expander("**REINITIALISATION**"):
                st.warning("⚠️ Attention")
                st.info("Mémoire : ADMIN_***_**26")
                confirm_reset = st.checkbox("Confirmer le reset total")
                if st.button("RESET DU MOT DE PASSE D'USINE"):
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
            mode = st.radio("Périmètre", ["Session actuelle", "Cumul général"], horizontal=True)
            all_f = glob.glob(os.path.join(VOTES_DIR, "*.csv"))
            path_curr = os.path.join(VOTES_DIR, f"{current_session}.csv")
            df_res = pd.concat([pd.read_csv(f) for f in all_f]) if mode == "Cumul général" and all_f else (pd.read_csv(path_curr) if os.path.exists(path_curr) else pd.DataFrame())
            
            if not df_res.empty:
                vids_list = load_videos()
                scores = {v: 0 for v in vids_list}
                for _, r in df_res.iterrows():
                    for i, p in enumerate([5, 3, 1]):
                        choix = r.get(f'Top{i+1}')
                        if choix in scores: scores[choix] += p
                df_p = pd.DataFrame(list(scores.items()), columns=['S', 'Pts']).sort_values('Pts', ascending=False)
                st.altair_chart(alt.Chart(df_p).mark_bar(color='#FF4B4B').encode(x='Pts', y=alt.Y('S', sort='-x')), use_container_width=True)
                st.download_button("📥 Export CSV", df_res.to_csv(index=False), "export.csv", "text/csv")
            else: st.info("Aucun vote enregistré.")

        with t2:
            st.subheader("Gestion des Services")
            n_v = st.text_input("Ajouter un service", key="add_v")
            if st.button("➕ Ajouter"):
                if n_v: 
                    vids = load_videos(); vids.append(n_v); save_videos(vids); st.rerun()
            st.divider()
            vids = load_videos()
            for i, v in enumerate(vids):
                c_v, c_b = st.columns([0.7, 0.3])
                if st.session_state["editing_service"] == v:
                    nv = c_v.text_input("Edit", value=v, key=f"ed_{i}")
                    if c_b.button("💾", key=f"sv_{i}"):
                        vids[i] = nv; save_videos(vids); st.session_state["editing_service"] = None; st.rerun()
                else:
                    c_v.write(f"• {v}")
                    be, bd = c_b.columns(2)
                    if be.button("✏️", key=f"e_{i}"): st.session_state["editing_service"] = v; st.rerun()
                    if bd.button("❌", key=f"d_{i}"): vids.remove(v); save_videos(vids); st.rerun()

        with t3:
            st.subheader("🖼️ Galerie & Médias")
            u_logo = st.file_uploader("Modifier Logo Principal", type=['png', 'jpg'])
            if u_logo: Image.open(u_logo).save(LOGO_FILE); st.rerun()
            
            st.divider()
            st.write("### Ajouter des Photos")
            u_gal = st.file_uploader("Sélectionnez vos images", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key="gal_up")
            
            if u_gal:
                with st.spinner("Upload en cours..."):
                    for f in u_gal:
                        Image.open(f).save(os.path.join(GALLERY_DIR, f.name))
                st.success(f"✅ {len(u_gal)} photo(s) ajoutée(s) !")
                time.sleep(1.5)
                st.rerun()
            
            st.divider()
            col_t, col_r = st.columns([0.8, 0.2])
            col_t.write("### Photos en ligne")
            if col_r.button("🔄 Actualiser"): st.rerun()
            
            imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
            if imgs:
                cols = st.columns(4)
                for i, img_p in enumerate(imgs):
                    with cols[i%4]:
                        st.image(img_p, use_container_width=True)
                        if st.button("Supprimer", key=f"del_img_{i}", use_container_width=True):
                            os.remove(img_p); st.rerun()
            else: st.info("Galerie vide.")
    else:
        st.warning("🔒 Authentifiez-vous dans la barre latérale.")

# --- 5. MODE PARTICIPANT (VOTE MOBILE) ---
elif mode_vote:
    st.title("🗳️ Vote Vœux 2026")
    if st.session_state["voted"]:
        st.success("✅ Vote bien enregistré !")
    else:
        pseudo = st.text_input("Pseudo / Trigramme").strip()
        if pseudo and st.button("🚀 Apparaître sur l'écran"):
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
                df_v = pd.read_csv(fn) if os.path.exists(fn) else pd.DataFrame(columns=["Pseudo"])
                if pseudo.lower() in df_v['Pseudo'].str.lower().values:
                    st.error("Déjà voté pour cette session.")
                else:
                    new_v = pd.DataFrame([["", pseudo, s1, s2, s3]], columns=["Prenom", "Pseudo", "Top1", "Top2", "Top3"])
                    new_v.to_csv(fn, mode='a', header=not os.path.exists(fn), index=False)
                    st.session_state["voted"] = True; st.balloons(); time.sleep(1); st.rerun()

# --- 6. MODE SOCIAL WALL (LIVE PAR DÉFAUT) ---
else:
    st.markdown("<style>[data-testid='stSidebar'] {display:none;}</style>", unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 2.2])
    
    with col_l:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=200)
        st.write("### 📲 Scannez pour participer")
        qr_url = "https://vote-voeux-2026-6rueeu6wcdbxa878nepqgf.streamlit.app/?mode=vote"
        qr_buf = BytesIO()
        qrcode.make(qr_url).save(qr_buf, format="PNG")
        st.image(qr_buf.getvalue(), use_container_width=True)
        nb_p, _ = get_stats()
        st.metric("Participants", nb_p)

    with col_r:
        st.markdown("<h1 style='text-align:center; color:#FF4B4B;'>Bienvenue ! 👋</h1>", unsafe_allow_html=True)
        if os.path.exists(PRESENCE_FILE):
            noms = pd.read_csv(PRESENCE_FILE)['Pseudo'].unique().tolist()
            nuage = " ".join([f"<span style='font-size:{random.randint(22,58)}px; color:{random.choice(['#FF4B4B','#1f77b4','#2ca02c','#ff7f0e','#9467bd'])}; margin:15px; font-weight:bold; display:inline-block;'>{n}</span>" for n in noms])
            st.markdown(f"<div style='text-align:center; background:rgba(255,255,255,0.05); padding:30px; border-radius:20px; min-height:300px;'>{nuage}</div>", unsafe_allow_html=True)

    st.divider()
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    if imgs:
        cols = st.columns(6)
        for i, img_p in enumerate(imgs): cols[i%6].image(img_p, use_container_width=True)
    
    time.sleep(5)
    st.rerun()
