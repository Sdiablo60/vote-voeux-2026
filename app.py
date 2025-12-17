import streamlit as st
import pandas as pd
import os
import base64
from PIL import Image
import altair as alt
from io import BytesIO
import qrcode

# --- CONFIGURATION DES RÉPERTOIRES ---
ADMIN_PASSWORD = "ADMIN_VOEUX_2026"
VOTES_DIR = "sessions_votes"
GALLERY_DIR = "galerie_images"
SOUNDS_DIR = "sons_admin"
CONFIG_FILE = "config_videos.csv"
LOCK_FILE = "vote_lock.txt"
LOGO_FILE = "logo_entreprise.png"

# Création des dossiers si nécessaires
for d in [VOTES_DIR, GALLERY_DIR, SOUNDS_DIR]:
    if not os.path.exists(d): 
        os.makedirs(d)

st.set_page_config(page_title="Régie Vote 2026", layout="wide")

# --- FONCTIONS TECHNIQUES ---
def generer_qr(url):
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

def load_videos():
    if os.path.exists(CONFIG_FILE): 
        return pd.read_csv(CONFIG_FILE)['Video'].tolist()
    return ["BU PAX", "BU FRET", "BU BTOB", "DPMI (ateliers)", "Service RH", "Service Finances", "Service AO", "Service QSSE", "Service IT", "Direction Pôle"]

# --- LOGIQUE D'AFFICHAGE ---
est_admin = st.query_params.get("admin") == "true"

if os.path.exists(LOGO_FILE):
    st.image(Image.open(LOGO_FILE), width=150)

st.title("🎬 Élection Vidéo Vœux 2026")

# --- STRUCTURE DES ONGLETS ---
if est_admin:
    tab_vote, tab_res, tab_admin = st.tabs(["🗳️ Espace Vote", "📊 Résultats", "🛠️ Console Admin"])
else:
    tab_vote = st.container()

# --- 1. ONGLET VOTE ---
with tab_vote:
    if est_admin:
        col_txt, col_qr = st.columns([2, 1])
        with col_qr:
            st.write("📲 **Scannez pour voter**")
            url_fixe = "https://vote-voeux-2026-6rueeu6wcdbxa878nepqgf.streamlit.app/"
            st.image(generer_qr(url_fixe), width=180)
    
    if os.path.exists(LOCK_FILE):
        st.warning("🔒 Les votes sont clos. Merci de votre participation !")
    elif st.session_state.get("voted", False):
        st.success("✅ Votre vote a bien été enregistré sur cet appareil.")
    else:
        with st.form("vote_form_final"):
            p1 = st.text_input("Prénom", key="input_prenom")
            p2 = st.text_input("Pseudo", key="input_pseudo")
            vids_list = load_videos()
            choix_utilisateurs = []
            
            # Formulaire de sélection
            for i in range(3):
                sel = st.selectbox(
                    f"Choix n°{i+1}", 
                    [v for v in vids_list if v not in choix_utilisateurs], 
                    index=None, 
                    placeholder="Sélectionnez un service...", 
                    key=f"select_v_{i}"
                )
                if sel:
                    choix_utilisateurs.append(sel)
            
            if st.form_submit_button("Valider mon vote 🚀"):
                if p1 and p2 and len(choix_utilisateurs) == 3:
                    fn = os.path.join(VOTES_DIR, "votes_principale.csv")
                    # Vérification/Création du fichier de votes
                    if os.path.exists(fn):
                        df_v = pd.read_csv(fn)
                    else:
                        df_v = pd.DataFrame(columns=["Prenom", "Pseudo", "Top1", "Top2", "Top3"])
                    
                    if p2.lower() in df_v['Pseudo'].str.lower().values:
                        st.warning("❌ Ce pseudo a déjà été utilisé pour voter.")
                    else:
                        new_row = pd.DataFrame([[p1, p2] + choix_utilisateurs], columns=df_v.columns)
                        new_row.to_csv(fn, mode='a', header=not os.path.exists(fn), index=False)
                        st.session_state["voted"] = True
                        st.balloons()
                        st.rerun()
                else:
                    st.error("⚠️ Veuillez remplir votre profil et sélectionner 3 services différents.")

# --- 2. ONGLET RÉSULTATS (ADMIN SEULEMENT) ---
if est_admin:
    with tab_res:
        pwd_res = st.text_input("Mot de passe Résultats", type="password", key="pwd_res_field")
        if pwd_res == ADMIN_PASSWORD:
            st.subheader("📊 Classement en temps réel")
            fn = os.path.join(VOTES_DIR, "votes_principale.csv")
            if os.path.exists(fn):
                df_res = pd.read_csv(fn)
                st.write(f"**Total des votants : {len(df_res)}**")
                
                # Calcul des points (5, 3, 1)
                services = load_videos()
                scores = {s: 0 for s in services}
                for _, row in df_res.iterrows():
                    if row['Top1'] in scores: scores[row['Top1']] += 5
                    if row['Top2'] in scores: scores[row['Top2']] += 3
                    if row['Top3'] in scores: scores[row['Top3']] += 1
                
                # Affichage du graphique
                df_plot = pd.DataFrame(list(scores.items()), columns=['Service', 'Points']).sort_values('Points', ascending=False)
                chart = alt.Chart(df_plot).mark_bar(color='#FF4B4B').encode(
                    x='Points:Q',
                    y=alt.Y('Service:N', sort='-x')
                )
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("Aucun vote n'a encore été enregistré.")

# --- 3. ONGLET ADMIN (ADMIN SEULEMENT) ---
    with tab_admin:
        pwd_admin = st.text_input("Mot de passe Console Admin", type="password", key="pwd_admin_field")
        if pwd_admin == ADMIN_PASSWORD:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📁 Médias")
                u_logo = st.file_uploader("Modifier le Logo", type=['png', 'jpg'], key="u_logo_btn")
                if u_logo: 
                    Image.open(u_logo).save(LOGO_FILE)
                    st.success("Logo mis à jour !")
                    st.rerun()
            
            with col2:
                st.subheader("⚙️ Configuration")
                if st.button("🗑️ Réinitialiser tous les votes"):
                    fn = os.path.join(VOTES_DIR, "votes_principale.csv")
                    if os.path.exists(fn): 
                        os.remove(fn)
                    st.success("La base de données des votes a été vidée.")
                    st.rerun()
                
                if st.button("🔒 Clôturer / 🔓 Ouvrir les votes"):
                    if os.path.exists(LOCK_FILE):
                        os.remove(LOCK_FILE)
                    else:
                        with open(LOCK_FILE, "w") as f:
                            f.write("LOCKED")
                    st.rerun()
