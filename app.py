import streamlit as st
import pandas as pd
import os
import base64
from PIL import Image
import altair as alt
from io import BytesIO

# --- CONFIGURATION ET CHEMINS ---
ADMIN_PASSWORD = "ADMIN_VOEUX_2026"  # Modifiez ce mot de passe si besoin
VOTES_DIR = "sessions_votes"
GALLERY_DIR = "galerie_images"
SOUNDS_DIR = "sons_admin"
CONFIG_FILE = "config_videos.csv"
SETTINGS_FILE = "settings.csv"
LOCK_FILE = "vote_lock.txt"
LOGO_FILE = "logo_entreprise.png"

# Création automatique des dossiers
for d in [VOTES_DIR, GALLERY_DIR, SOUNDS_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

st.set_page_config(page_title="Régie Vote Vœux 2026", layout="wide", page_icon="🎬")

# --- FONCTIONS TECHNIQUES ---

def jouer_son(nom_fichier):
    """Déclenche la lecture d'un fichier MP3 via HTML/JS"""
    path = os.path.join(SOUNDS_DIR, nom_fichier)
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            audio_html = f"""
                <audio autoplay="true">
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
            """
            st.components.v1.html(audio_html, height=0)

def load_settings():
    """Charge les paramètres de l'application (nb de choix, effets)"""
    if os.path.exists(SETTINGS_FILE):
        return pd.read_csv(SETTINGS_FILE).iloc[0].to_dict()
    return {"nb_choix": 3, "effet": "Ballons", "son": "Aucun"}

def save_settings(nb, effet, son):
    """Sauvegarde les paramètres"""
    pd.DataFrame([{"nb_choix": nb, "effet": effet, "son": son}]).to_csv(SETTINGS_FILE, index=False)

def load_videos():
    """Charge la liste des services configurés"""
    if os.path.exists(CONFIG_FILE):
        return pd.read_csv(CONFIG_FILE)['Video'].tolist()
    return ["BU PAX", "BU FRET", "BU BTOB", "DPMI (ateliers)", "Service RH", 
            "Service Finances", "Service AO", "Service QSSE", "Service IT", "Direction Pôle"]

def save_videos(video_list):
    pd.DataFrame(video_list, columns=['Video']).to_csv(CONFIG_FILE, index=False)

def get_session_file():
    session = st.session_state.get('session_name', 'Principale')
    return os.path.join(VOTES_DIR, f"votes_{session}.csv")

# --- CHARGEMENT DES PARAMÈTRES ---
settings = load_settings()
nb_requis = int(settings["nb_choix"])
effet_final = settings["effet"]
son_final = settings["son"]

# --- AFFICHAGE LOGO ET TITRE ---
if os.path.exists(LOGO_FILE):
    st.image(Image.open(LOGO_FILE), width=150)

st.title("🎬 Élection Vidéo Vœux 2026")

tab1, tab2, tab3 = st.tabs(["🗳️ Espace Vote", "📊 Résultats & Podium", "🛠️ Console Admin"])

# --- ONGLET 1 : ESPACE VOTE ---
with tab1:
    # Affichage de la galerie d'images si elle existe
    imgs = [f for f in os.listdir(GALLERY_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if imgs:
        cols = st.columns(len(imgs))
        for i, img_path in enumerate(imgs):
            cols[i].image(os.path.join(GALLERY_DIR, img_path), use_container_width=True)

    if os.path.exists(LOCK_FILE):
        st.warning("🔒 Les votes sont désormais clos. Merci pour votre participation !")
    elif st.session_state.get("voted", False):
        st.success("✅ Votre vote a bien été enregistré. Merci !")
    else:
        st.info(f"Consigne : Choisissez obligatoirement vos **{nb_requis}** vidéos préférées.")
        with st.form("form_vote"):
            c1, c2 = st.columns(2)
            prenom = c1.text_input("Votre Prénom")
            pseudo = c2.text_input("Votre Pseudo")
            st.divider()
            
            vids_list = load_videos()
            choix_utilisateurs = []
            for i in range(nb_requis):
                options = [v for v in vids_list if v not in choix_utilisateurs]
                sel = st.selectbox(f"Votre choix n°{i+1}", options, index=None, key=f"sel_{i}")
                if sel:
                    choix_utilisateurs.append(sel)
            
            if st.form_submit_button("Valider mon vote 🚀"):
                if not (prenom and pseudo) or len(choix_utilisateurs) < nb_requis:
                    st.error(f"⚠️ Veuillez remplir tous les champs et faire vos {nb_requis} choix.")
                else:
                    fname = get_session_file()
                    df_v = pd.read_csv(fname) if os.path.exists(fname) else pd.DataFrame(columns=["Prenom", "Pseudo"] + [f"Top{j+1}" for j in range(nb_requis)])
                    if pseudo.lower() in df_v['Pseudo'].str.lower().values:
                        st.error("❌ Ce pseudo a déjà voté.")
                    else:
                        new_row = pd.DataFrame([[prenom, pseudo] + choix_utilisateurs], columns=df_v.columns)
                        new_row.to_csv(fname, mode='a', header=not os.path.exists(fname), index=False)
                        st.session_state["voted"] = True
                        st.balloons()
                        st.rerun()

# --- ONGLET 2 : RÉSULTATS ---
with tab2:
    if st.text_input("Mot de passe Résultats", type="password", key="p_res") == ADMIN_PASSWORD:
        fname = get_session_file()
        if os.path.exists(fname):
            df_res = pd.read_csv(fname)
            # Calcul des scores (5pts, 3pts, 1pt...)
            scores = {v: 0 for v in load_videos()}
            poids = [5, 3, 1, 1, 1, 1]
            for _, r in df_res.iterrows():
                for j in range(nb_requis):
                    col = f"Top{j+1}"
                    if col in r and r[col] in scores:
                        scores[r[col]] += poids[j] if j < len(poids) else 1
            
            final_df = pd.DataFrame(list(scores.items()), columns=['Service', 'Points']).sort_values('Points', ascending=False)
            
            st.subheader(f"📊 Participation : {len(df_res)} votants")
            chart = alt.Chart(final_df).mark_bar(color='#FF4B4B').encode(
                x='Points', y=alt.Y('Service', sort='-x'), tooltip=['Service', 'Points']
            ).properties(height=400)
            st.altair_chart(chart, use_container_width=True)

            st.divider()
            if st.button("📣 PROCLAMER LE VAINQUEUR ET LANCER L'EFFET"):
                if son_final != "Aucun": jouer_son(son_final)
                if effet_final == "Ballons": st.balloons()
                elif effet_final == "Pluie d'étoiles": st.snow()
                elif effet_final == "Confettis": st.toast("FÉLICITATIONS !"); st.balloons()
        else:
            st.info("Aucun vote enregistré pour le moment.")

# --- ONGLET 3 : CONSOLE ADMIN ---
with tab3:
    if st.text_input("Accès Super Admin", type="password", key="p_adm") == ADMIN_PASSWORD:
        col_m, col_c = st.columns(2)
        
        with col_m:
            st.subheader("🖼️ Médias et Exports")
            up_logo = st.file_uploader("Logo Entreprise (PNG/JPG)", type=['png', 'jpg'])
            if up_logo: Image.open(up_logo).save(LOGO_FILE); st.rerun()
            
            up_gal = st.file_uploader("Images Galerie", type=['png', 'jpg'], accept_multiple_files=True)
            if up_gal:
                for f in up_gal: Image.open(f).save(os.path.join(GALLERY_DIR, f.name))
                st.rerun()
            
            up_mp3 = st.file_uploader("Ajouter Son (MP3)", type=['mp3'])
            if up_mp3:
                with open(os.path.join(SOUNDS_DIR, up_mp3.name), "wb") as f: f.write(up_mp3.getbuffer())
                st.success("Son ajouté !"); st.rerun()

            st.divider()
            # Export Excel
            fname = get_session_file()
            if os.path.exists(fname):
                output = BytesIO()
                pd.read_csv(fname).to_excel(output, index=False, engine='openpyxl')
                st.download_button("📥 Télécharger les votes (Excel)", data=output.getvalue(), file_name="resultats_2026.xlsx")

        with col_c:
            st.subheader("⚙️ Paramètres & Tests")
            n_nb = st.number_input("Choix obligatoires", 1, 5, nb_requis)
            n_eff = st.selectbox("Effet Visuel", ["Ballons", "Pluie d'étoiles", "Confettis"], index=0)
            sons_dispo = ["Aucun"] + os.listdir(SOUNDS_DIR)
            n_son = st.selectbox("Son de victoire", sons_list if 'sons_list' in locals() else sons_dispo)
            
            if st.button("💾 Sauvegarder la Config"):
                save_settings(n_nb, n_eff, n_son); st.rerun()
            
            if st.button("▶️ TESTER L'ANIMATION"):
                if n_son != "Aucun": jouer_son(n_son)
                if n_eff == "Ballons": st.balloons()
                elif n_eff == "Pluie d'étoiles": st.snow()
                elif n_eff == "Confettis": st.balloons()

            st.divider()
            if st.button("🔒 Clôturer" if not os.path.exists(LOCK_FILE) else "🔓 Rouvrir"):
                if os.path.exists(LOCK_FILE): os.remove(LOCK_FILE)
                else: 
                    with open(LOCK_FILE, "w") as f: f.write("LOCKED")
                st.rerun()