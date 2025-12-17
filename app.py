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

st.set_page_config(page_title="Régie Vote 2026", layout="wide", page_icon="🎬")

# --- FONCTION AUDIO & QR ---
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

# --- GESTION PARAMÈTRES ---
def load_settings():
    if os.path.exists(SETTINGS_FILE): return pd.read_csv(SETTINGS_FILE).iloc[0].to_dict()
    return {"nb_choix": 3, "effet": "Ballons", "son": "Aucun"}

def save_settings(nb, effet, son):
    pd.DataFrame([{"nb_choix": nb, "effet": effet, "son": son}]).to_csv(SETTINGS_FILE, index=False)

# --- INTERFACE ---
settings = load_settings()
nb_requis, effet_final, son_final = int(settings["nb_choix"]), settings["effet"], settings["son"]

if os.path.exists(LOGO_FILE): st.image(Image.open(LOGO_FILE), width=150)
st.title("🎬 Élection Vidéo Vœux 2026")

tab1, tab2, tab3 = st.tabs(["🗳️ Espace Vote", "📊 Résultats & Podium", "🛠️ Console Admin"])

# --- ONGLET 1 : ESPACE VOTE (Avec QR Code) ---
with tab1:
    col_info, col_qr = st.columns([2, 1])
    
    with col_info:
        imgs = [f for f in os.listdir(GALLERY_DIR) if f.lower().endswith(('.png', '.jpg'))]
        if imgs:
            cols_img = st.columns(len(imgs))
            for i, img in enumerate(imgs): cols_img[i].image(os.path.join(GALLERY_DIR, img), use_container_width=True)
    
    with col_qr:
        # Détection automatique de l'URL de l'app ou saisie manuelle en Admin
        st.write("📲 **Scannez pour voter**")
        # On essaie de récupérer l'URL actuelle, sinon on met un texte par défaut
        try:
            current_url = https://vote-voeux-2026-6rueeu6wcdbxa878nepqgf.streamlit.app/
            st.image(generer_qr(current_url), width=200)
        except:
            st.write("Configurez l'URL dans l'onglet Admin")

    st.divider()
    if os.path.exists(LOCK_FILE): st.warning("🔒 Les votes sont clos.")
    elif st.session_state.get("voted", False): st.success("✅ Vote enregistré !")
    else:
        with st.form("vote"):
            p1 = st.text_input("Prénom"); p2 = st.text_input("Pseudo")
            vids = ["Vidéo 1", "Vidéo 2", "Vidéo 3"] # À lier à load_videos()
            if st.form_submit_button("Voter"): st.session_state["voted"] = True; st.rerun()

# --- ONGLET 2 : RÉSULTATS ---
with tab2:
    if st.text_input("Accès Podium", type="password", key="p_pod") == ADMIN_PASSWORD:
        st.subheader("🏆 Podium")
        if st.button("📣 LANCER LE FINAL"):
            if son_final != "Aucun": jouer_son(son_final)
            if effet_final == "Ballons": st.balloons()
            elif effet_final == "Pluie d'étoiles": st.snow()
            elif effet_final == "Confettis": st.balloons()

# --- ONGLET 3 : CONSOLE ADMIN ---
with tab3:
    if st.text_input("Accès Admin", type="password", key="p_adm") == ADMIN_PASSWORD:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🖼️ Médias & Export")
            up_logo = st.file_uploader("Logo", type=['png', 'jpg'])
            if up_logo: Image.open(up_logo).save(LOGO_FILE); st.rerun()
            
            up_mp3 = st.file_uploader("Sons (MP3)", type=['mp3'])
            if up_mp3: 
                with open(os.path.join(SOUNDS_DIR, up_mp3.name), "wb") as f: f.write(up_mp3.getbuffer())
                st.success("Son ajouté !")
            
            if st.button("📥 Exporter Excel"):
                st.write("Génération du fichier...")

        with col2:
            st.subheader("⚙️ Config & Animations")
            n_nb = st.number_input("Nombre de choix", 1, 5, nb_requis)
            n_eff = st.selectbox("Effet", ["Ballons", "Pluie d'étoiles", "Confettis"], index=0)
            sons_list = ["Aucun"] + os.listdir(SOUNDS_DIR)
            n_son = st.selectbox("Son", sons_list, index=0)
            
            if st.button("💾 Sauvegarder"): save_settings(n_nb, n_eff, n_son); st.rerun()
            
            st.divider()
            if st.button("▶️ TESTER L'ANIMATION"):
                if n_son != "Aucun": jouer_son(n_son)
                if n_eff == "Ballons": st.balloons()
                elif n_eff == "Pluie d'étoiles": st.snow()
                elif n_eff == "Confettis": st.balloons()

