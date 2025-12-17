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
SETTINGS_FILE = "settings.csv"
LOCK_FILE = "vote_lock.txt"
LOGO_FILE = "logo_entreprise.png"

for d in [VOTES_DIR, GALLERY_DIR, SOUNDS_DIR]:
    if not os.path.exists(d): os.makedirs(d)

st.set_page_config(page_title="Vote Vœux 2026", layout="wide", page_icon="🎬")

# --- FONCTIONS TECHNIQUES ---
def jouer_son(nom_fichier):
    path = os.path.join(SOUNDS_DIR, nom_fichier)
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            audio_html = f"""<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>"""
            st.components.v1.html(audio_html, height=0)

def generer_qr(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def load_settings():
    if os.path.exists(SETTINGS_FILE): return pd.read_csv(SETTINGS_FILE).iloc[0].to_dict()
    return {"nb_choix": 3, "effet": "Ballons", "son": "Aucun"}

def save_settings(nb, effet, son):
    pd.DataFrame([{"nb_choix": nb, "effet": effet, "son": son}]).to_csv(SETTINGS_FILE, index=False)

def load_videos():
    if os.path.exists(CONFIG_FILE): return pd.read_csv(CONFIG_FILE)['Video'].tolist()
    return ["BU PAX", "BU FRET", "BU BTOB", "DPMI (ateliers)", "Service RH", "Service Finances", "Service AO", "Service QSSE", "Service IT", "Direction Pôle"]

def save_videos(video_list):
    pd.DataFrame(video_list, columns=['Video']).to_csv(CONFIG_FILE, index=False)

def get_session_file():
    return os.path.join(VOTES_DIR, "votes_principale.csv")

# --- CHARGEMENT PARAMÈTRES ---
settings = load_settings()
nb_requis, effet_final, son_final = int(settings["nb_choix"]), settings["effet"], settings["son"]

# --- DÉTECTION DU MODE (ADMIN OU PUBLIC) ---
# Si l'URL contient ?admin=true, on est en mode régie
est_admin = st.query_params.get("admin") == "true"

# --- AFFICHAGE LOGO ---
if os.path.exists(LOGO_FILE):
    st.image(Image.open(LOGO_FILE), width=150)

st.title("🎬 Élection Vidéo Vœux 2026")

# --- GESTION DES ONGLETS ---
if est_admin:
    tabs = st.tabs(["🗳️ Espace Vote", "📊 Résultats & Podium", "🛠️ Console Admin"])
    tab_vote, tab_res, tab_admin = tabs[0], tabs[1], tabs[2]
else:
    # Mode Public : Pas d'onglets, on affiche directement le vote
    tab_vote = st.container()

# --- CONTENU : ESPACE VOTE (Version Ultra-Stable) ---
with tab_vote:
    if est_admin:
        col_info, col_qr = st.columns([2, 1])
        with col_qr:
            st.write("📲 **Scannez pour voter**")
            url_app = "https://vote-voeux-2026-6rueeu6wcdbxa878nepqgf.streamlit.app/"
            st.image(generer_qr(url_app), width=200)
        with col_info:
            imgs = [f for f in os.listdir(GALLERY_DIR) if f.lower().endswith(('.png', '.jpg'))]
            if imgs:
                cols_img = st.columns(len(imgs))
                for i, img in enumerate(imgs): 
                    cols_img[i].image(os.path.join(GALLERY_DIR, img), use_container_width=True)
    else:
        imgs = [f for f in os.listdir(GALLERY_DIR) if f.lower().endswith(('.png', '.jpg'))]
        if imgs:
            cols_img = st.columns(len(imgs))
            for i, img in enumerate(imgs): 
                cols_img[i].image(os.path.join(GALLERY_DIR, img), use_container_width=True)

    st.divider()
    
    if os.path.exists(LOCK_FILE):
        st.warning("🔒 Les votes sont clos. Merci !")
    elif st.session_state.get("voted", False):
        st.success("✅ Votre vote a été enregistré !")
    else:
        # Création du formulaire avec une clé unique pour éviter les bugs
        with st.form("formulaire_vote_final", clear_on_submit=False):
            p1 = st.text_input("Votre Prénom", key="prenom_input")
            p2 = st.text_input("Votre Pseudo", key="pseudo_input")
            st.divider()
            
            vids_list = load_videos()
            choix_utilisateurs = []
            
            # Affichage des menus déroulants
            for i in range(nb_requis):
                # On filtre les vidéos pour ne pas proposer deux fois la même
                options_dispo = [v for v in vids_list if v not in choix_utilisateurs]
                label = f"Votre choix n°{i+1}"
                
                # IMPORTANT : On ne définit pas de "index=None" ici pour forcer la stabilité
                sel = st.selectbox(label, options_dispo, key=f"select_video_{i}")
                choix_utilisateurs.append(sel)
            
            submit = st.form_submit_button("Valider mon vote 🚀")
            
            if submit:
                # Vérification stricte
                if not p1 or not p2:
                    st.error("⚠️ Veuillez renseigner votre prénom et votre pseudo.")
                elif len(set(choix_utilisateurs)) < nb_requis:
                    st.error(f"⚠️ Veuillez faire {nb_requis} choix différents.")
                else:
                    fname = get_session_file()
                    # Vérification si fichier existe
                    df_v = pd.read_csv(fname) if os.path.exists(fname) else pd.DataFrame(columns=["Prenom", "Pseudo"] + [f"Top{j+1}" for j in range(nb_requis)])
                    
                    # Vérification doublon pseudo
                    if p2.lower() in df_v['Pseudo'].str.lower().values:
                        st.warning("❌ Ce pseudo a déjà été utilisé pour voter.")
                    else:
                        # Enregistrement
                        new_data = [p1, p2] + choix_utilisateurs
                        new_row = pd.DataFrame([new_data], columns=df_v.columns)
                        new_row.to_csv(fname, mode='a', header=not os.path.exists(fname), index=False)
                        
                        st.session_state["voted"] = True
                        st.balloons()
                        st.rerun()

# --- CONTENU : RÉSULTATS (UNIQUEMENT SI ADMIN) ---
if est_admin:
    with tab_res:
        if st.text_input("Mot de passe Résultats", type="password", key="p_res") == ADMIN_PASSWORD:
            fname = get_session_file()
            if os.path.exists(fname):
                df_res = pd.read_csv(fname)
                st.subheader(f"📊 Participation : {len(df_res)} votants")
                scores = {v: 0 for v in load_videos()}
                poids = [5, 3, 1, 1, 1]
                for _, row in df_res.iterrows():
                    for j in range(nb_requis):
                        c = f"Top{j+1}"
                        if c in row and row[c] in scores: scores[row[c]] += poids[j]
                
                final_df = pd.DataFrame(list(scores.items()), columns=['Service', 'Points']).sort_values('Points', ascending=False)
                chart = alt.Chart(final_df).mark_bar(color='#FF4B4B').encode(x='Points', y=alt.Y('Service', sort='-x'))
                st.altair_chart(chart, use_container_width=True)

                if st.button("📣 PROCLAMER LE VAINQUEUR"):
                    if son_final != "Aucun": jouer_son(son_final)
                    if effet_final == "Ballons": st.balloons()
                    elif effet_final == "Pluie d'étoiles": st.snow()
                    elif effet_final == "Confettis": st.balloons(); st.toast("BRAVO !")
            else:
                st.info("En attente des premiers votes...")

# --- CONTENU : CONSOLE ADMIN (UNIQUEMENT SI ADMIN) ---
    with tab_admin:
        if st.text_input("Accès Super Admin", type="password", key="p_adm") == ADMIN_PASSWORD:
            col_m, col_c = st.columns(2)
            with col_m:
                st.subheader("🖼️ Médias")



