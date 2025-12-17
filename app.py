import streamlit as st
import pandas as pd
import os
import base64
from PIL import Image
import altair as alt
from io import BytesIO
import qrcode

# --- CONFIGURATION ---
ADMIN_PASSWORD = "ADMIN_VOEUX_2026"
VOTES_DIR = "sessions_votes"
GALLERY_DIR = "galerie_images"
SOUNDS_DIR = "sons_admin"
CONFIG_FILE = "config_videos.csv"
LOCK_FILE = "vote_lock.txt"
LOGO_FILE = "logo_entreprise.png"

for d in [VOTES_DIR, GALLERY_DIR, SOUNDS_DIR]:
    if not os.path.exists(d): os.makedirs(d)

st.set_page_config(page_title="Régie Vote 2026", layout="wide")

# --- INITIALISATION DE L'ÉTAT (POUR ÉVITER LE BUG MOBILE) ---
if "voted" not in st.session_state: st.session_state["voted"] = False
if "choix_1" not in st.session_state: st.session_state["choix_1"] = None
if "choix_2" not in st.session_state: st.session_state["choix_2"] = None
if "choix_3" not in st.session_state: st.session_state["choix_3"] = None

# --- FONCTIONS ---
def generer_qr(url):
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

def load_videos():
    if os.path.exists(CONFIG_FILE): return pd.read_csv(CONFIG_FILE)['Video'].tolist()
    return ["BU PAX", "BU FRET", "BU BTOB", "DPMI (ateliers)", "Service RH", "Service Finances", "Service AO", "Service QSSE", "Service IT", "Direction Pôle"]

# --- LOGIQUE AFFICHAGE ---
est_admin = st.query_params.get("admin") == "true"
if os.path.exists(LOGO_FILE):
    st.image(Image.open(LOGO_FILE), width=150)

st.title("🎬 Élection Vidéo Vœux 2026")

if est_admin:
    tab_vote, tab_res, tab_admin = st.tabs(["🗳️ Espace Vote", "📊 Résultats", "🛠️ Console Admin"])
else:
    tab_vote = st.container()

with tab_vote:
    if est_admin:
        c1, c2 = st.columns([2, 1])
        with c2:
            st.write("📲 **Scannez pour voter**")
            st.image(generer_qr("https://vote-voeux-2026-6rueeu6wcdbxa878nepqgf.streamlit.app/"), width=180)
    
    if os.path.exists(LOCK_FILE):
        st.warning("🔒 Les votes sont clos.")
    elif st.session_state["voted"]:
        st.success("✅ Votre vote a bien été enregistré !")
    else:
        # FORMULAIRE SANS "WITH ST.FORM" (plus stable sur mobile pour les Selectbox)
        st.subheader("Exprimez vos choix")
        p1 = st.text_input("Votre Prénom")
        p2 = st.text_input("Votre Pseudo (ex: trigramme)")
        
        vids = load_videos()
        
        s1 = st.selectbox("Choix n°1 (5 pts)", [None] + vids, key="choix_1")
        s2 = st.selectbox("Choix n°2 (3 pts)", [None] + [v for v in vids if v != s1], key="choix_2")
        s3 = st.selectbox("Choix n°3 (1 pt)", [None] + [v for v in vids if v not in [s1, s2]], key="choix_3")
        
        if st.button("Valider mon vote 🚀"):
            if not p1 or not p2 or not s1 or not s2 or not s3:
                st.error("⚠️ Veuillez remplir votre profil et faire vos 3 choix.")
            else:
                fn = os.path.join(VOTES_DIR, "votes_principale.csv")
                df = pd.read_csv(fn) if os.path.exists(fn) else pd.DataFrame(columns=["Prenom", "Pseudo", "Top1", "Top2", "Top3"])
                
                if p2.lower() in df['Pseudo'].str.lower().values:
                    st.warning("❌ Vous avez déjà voté avec ce pseudo.")
                    st.session_state["voted"] = True
                else:
                    new_vote = pd.DataFrame([[p1, p2, s1, s2, s3]], columns=df.columns)
                    new_vote.to_csv(fn, mode='a', header=not os.path.exists(fn), index=False)
                    st.session_state["voted"] = True
                    st.balloons()
                    st.rerun()

if est_admin:
    with tab_res:
        if st.text_input("Code Résultats", type="password", key="res_pwd") == ADMIN_PASSWORD:
            fn = os.path.join(VOTES_DIR, "votes_principale.csv")
            if os.path.exists(fn):
                df_r = pd.read_csv(fn)
                st.write(f"**Votants : {len(df_r)}**")
                
                # Calcul des points
                scores = {v: 0 for v in load_videos()}
                for _, r in df_r.iterrows():
                    if r['Top1'] in scores: scores[r['Top1']] += 5
                    if r['Top2'] in scores: scores[r['Top2']] += 3
                    if r['Top3'] in scores: scores[r['Top3']] += 1
                
                df_plot = pd.DataFrame(list(scores.items()), columns=['Service', 'Points']).sort_values('Points', ascending=False)
                chart = alt.Chart(df_plot).mark_bar(color='#FF4B4B').encode(x='Points:Q', y=alt.Y('Service:N', sort='-x'))
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("Aucun vote enregistré.")

    with tab_admin:
        if st.text_input("Code Admin", type="password", key="adm_pwd") == ADMIN_PASSWORD:
            u_logo = st.file_uploader("Modifier le Logo", type=['png', 'jpg'])
            if u_logo: 
                Image.open(u_logo).save(LOGO_FILE)
                st.rerun()
            if st.button("🗑️ Vider les votes"):
                fn = os.path.join(VOTES_DIR, "votes_principale.csv")
                if os.path.exists(fn): os.remove(fn)
                st.session_state["voted"] = False
                st.rerun()
