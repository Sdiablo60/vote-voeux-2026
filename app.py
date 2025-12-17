import streamlit as st
import pandas as pd
import os
from PIL import Image
import altair as alt
from io import BytesIO
import qrcode
import glob

# --- 1. CONFIGURATION ---
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

st.set_page_config(page_title="Régie Vote 2026", layout="wide")

# --- 2. FONCTIONS DE GESTION ---
def get_current_session():
    if os.path.exists(SESSION_CONFIG):
        with open(SESSION_CONFIG, "r") as f: return f.read().strip()
    return "session_1"

def set_current_session(name):
    with open(SESSION_CONFIG, "w") as f: f.write(name)

def load_videos():
    if os.path.exists(CONFIG_FILE): 
        return pd.read_csv(CONFIG_FILE)['Video'].tolist()
    return ["Service A", "Service B", "Service C"]

def save_videos(liste):
    pd.DataFrame(liste, columns=['Video']).to_csv(CONFIG_FILE, index=False)

def get_admin_title():
    if os.path.exists(TITRE_FILE):
        with open(TITRE_FILE, "r", encoding="utf-8") as f: return f.read()
    return "Gestion des Services"

# --- 3. LOGIQUE INITIALISATION ---
current_session = get_current_session()
if "voted" not in st.session_state: st.session_state["voted"] = False
if "edit_mode_title" not in st.session_state: st.session_state["edit_mode_title"] = False

est_admin = st.query_params.get("admin") == "true"
if os.path.exists(LOGO_FILE):
    st.image(Image.open(LOGO_FILE), width=150)

st.title("🎬 Élection Vidéo Vœux 2026")

if est_admin:
    tab_vote, tab_res, tab_admin = st.tabs(["🗳️ Espace Vote", "📊 Résultats", "🛠️ Console Admin"])
else:
    tab_vote = st.container()

# --- 4. ONGLET VOTE (Version Mobile OK) ---
with tab_vote:
    if est_admin:
        c1, c2 = st.columns([2, 1])
        with c2:
            st.write(f"📍 Session active : **{current_session}**")
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
        st.success("✅ Vote enregistré !")
    else:
        p1 = st.text_input("Prénom")
        p2 = st.text_input("Pseudo / Trigramme")
        vids = load_videos()
        
        st.write("**1er choix (5 pts) :**")
        s1 = st.segmented_control("c1", vids, label_visibility="collapsed", key="s1")
        st.write("**2ème choix (3 pts) :**")
        s2 = st.segmented_control("c2", [v for v in vids if v != s1], label_visibility="collapsed", key="s2")
        st.write("**3ème choix (1 pt) :**")
        s3 = st.segmented_control("c3", [v for v in vids if v not in [s1, s2]], label_visibility="collapsed", key="s3")
        
        if st.button("Valider mon vote 🚀", use_container_width=True):
            if not p1 or not p2 or not s1 or not s2 or not s3:
                st.error("⚠️ Formulaire incomplet")
            else:
                fn = os.path.join(VOTES_DIR, f"{current_session}.csv")
                df = pd.read_csv(fn) if os.path.exists(fn) else pd.DataFrame(columns=["Prenom", "Pseudo", "Top1", "Top2", "Top3"])
                if p2.lower() in df['Pseudo'].str.lower().values:
                    st.warning("❌ Déjà voté")
                else:
                    new_v = pd.DataFrame([[p1, p2, s1, s2, s3]], columns=df.columns)
                    new_v.to_csv(fn, mode='a', header=not os.path.exists(fn), index=False)
                    st.session_state["voted"] = True
                    st.balloons(); st.rerun()

# --- 5. ONGLET RÉSULTATS (Avec option Cumul) ---
if est_admin:
    with tab_res:
        mode_res = st.radio("Affichage :", ["Session en cours", "Cumul de toutes les sessions"], horizontal=True)
        all_files = glob.glob(os.path.join(VOTES_DIR, "*.csv"))
        
        df_final = pd.DataFrame()
        if mode_res == "Session en cours":
            fn = os.path.join(VOTES_DIR, f"{current_session}.csv")
            if os.path.exists(fn): df_final = pd.read_csv(fn)
        else:
            if all_files: df_final = pd.concat([pd.read_csv(f) for f in all_files])

        if not df_final.empty:
            st.write(f"📈 Total votants : **{len(df_final)}**")
            scores = {v: 0 for v in load_videos()}
            for _, r in df_final.iterrows():
                for i, p in enumerate([5, 3, 1]):
                    if r[f'Top{i+1}'] in scores: scores[r[f'Top{i+1}']] += p
            df_plot = pd.DataFrame(list(scores.items()), columns=['Service', 'Pts']).sort_values('Pts', ascending=False)
            st.altair_chart(alt.Chart(df_plot).mark_bar(color='#FF4B4B').encode(x='Pts', y=alt.Y('Service', sort='-x')), use_container_width=True)
        else: st.info("Aucune donnée.")

# --- 6. ONGLET ADMIN (Sessions + Reset + Services) ---
    with tab_admin:
        if st.text_input("Code Admin", type="password") == ADMIN_PASSWORD:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📡 Gestion des Sessions")
                new_sess = st.text_input("Créer une nouvelle session :")
                if st.button("🚀 Créer et Basculer"):
                    set_current_session(new_sess); st.rerun()
                
                sessions_dispos = [os.path.basename(f).replace(".csv", "") for f in all_files]
                sess_select = st.selectbox("Basculer sur une session existante :", list(set(sessions_dispos + [current_session])))
                if st.button("🔄 Basculer"):
                    set_current_session(sess_select); st.rerun()

                st.divider()
                st.subheader("⚠️ Danger Zone")
                if st.button("🗑️ Réinitialiser la session actuelle"):
                    fn = os.path.join(VOTES_DIR, f"{current_session}.csv")
                    if os.path.exists(fn): os.remove(fn)
                    st.session_state["voted"] = False; st.rerun()
                
                if st.button("🔒 Clôturer / Ouvrir"):
                    if os.path.exists(LOCK_FILE): os.remove(LOCK_FILE)
                    else: open(LOCK_FILE, "w").write("L")
                    st.rerun()

            with c2:
                # GESTION SERVICES (Identique)
                current_title = get_admin_title()
                st.subheader(f"📝 {current_title}")
                new_s = st.text_input("Ajouter service")
                if st.button("➕"):
                    vids = load_videos(); vids.append(new_s); save_videos(vids); st.rerun()
                st.write("---")
                vids = load_videos()
                for i, v in enumerate(vids):
                    col_v, col_btn = st.columns([0.8, 0.2])
                    col_v.write(f"• {v}")
                    if col_btn.button("❌", key=f"d_{i}"): vids.remove(v); save_videos(vids); st.rerun()
