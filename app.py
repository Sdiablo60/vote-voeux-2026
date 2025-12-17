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

# --- INITIALISATION DE LA SESSION ---
if "admin_logged" not in st.session_state:
    st.session_state["admin_logged"] = False

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

# --- LOGIQUE D'AFFICHAGE ---
settings = load_settings()
nb_requis, effet_final, son_final = int(settings["nb_choix"]), settings["effet"], settings["son"]
est_admin = st.query_params.get("admin") == "true"

if os.path.exists(LOGO_FILE):
    st.image(Image.open(LOGO_FILE), width=150)

st.title("🎬 Élection Vidéo Vœux 2026")

if est_admin:
    tabs = st.tabs(["🗳️ Espace Vote", "📊 Résultats & Podium", "🛠️ Console Admin"])
    tab_vote, tab_res, tab_admin = tabs[0], tabs[1], tabs[2]
else:
    tab_vote = st.container()

# --- 1. ONGLET VOTE ---
with tab_vote:
    if est_admin:
        col_info, col_qr = st.columns([2, 1])
        with col_qr:
            st.write("📲 **Scannez pour voter**")
            url_app = "https://vote-voeux-2026-6rueeu6wcdbxa878nepqgf.streamlit.app/"
            st.image(generer_qr(url_app), width=180)
        with col_info:
            imgs = [f for f in os.listdir(GALLERY_DIR) if f.lower().endswith(('.png', '.jpg'))]
            if imgs:
                cols = st.columns(len(imgs))
                for i, img in enumerate(imgs): cols[i].image(os.path.join(GALLERY_DIR, img), use_container_width=True)
    
    st.divider()
    if os.path.exists(LOCK_FILE):
        st.warning("🔒 Les votes sont clos.")
    elif st.session_state.get("voted", False):
        st.success("✅ Votre vote a été enregistré !")
    else:
        with st.form("form_vote_stable"):
            p1 = st.text_input("Prénom", key="f_prenom")
            p2 = st.text_input("Pseudo", key="f_pseudo")
            vids_list = load_videos()
            choix_faits = []
            for i in range(nb_requis):
                sel = st.selectbox(f"Choix n°{i+1}", [v for v in vids_list if v not in choix_faits], key=f"f_sel_{i}")
                choix_faits.append(sel)
            
            if st.form_submit_button("Valider mon vote 🚀"):
                if p1 and p2:
                    fname = os.path.join(VOTES_DIR, "votes_principale.csv")
                    df_v = pd.read_csv(fname) if os.path.exists(fname) else pd.DataFrame(columns=["Prenom", "Pseudo"] + [f"Top{j+1}" for j in range(nb_requis)])
                    if p2.lower() in df_v['Pseudo'].str.lower().values:
                        st.warning("❌ Déjà voté.")
                    else:
                        new_row = pd.DataFrame([[p1, p2] + choix_faits], columns=df_v.columns)
                        new_row.to_csv(fname, mode='a', header=not os.path.exists(fname), index=False)
                        st.session_state["voted"] = True
                        st.balloons()
                        st.rerun()

# --- 2. ONGLET RÉSULTATS & 3. ONGLET ADMIN ---
if est_admin:
    # --- VERIFICATION MOT DE PASSE UNIQUE ---
    if not st.session_state["admin_logged"]:
        pwd = st.text_input("Entrez le code d'accès Admin pour déverrouiller la console", type="password")
        if pwd == ADMIN_PASSWORD:
            st.session_state["admin_logged"] = True
            st.rerun()
        else:
            if pwd: st.error("Code incorrect")
    else:
        # SI CONNECTÉ, ON AFFICHE TOUT
        with tab_res:
            st.subheader("🏆 Podium & Résultats")
            # (Le code des résultats reste ici...)
            if st.button("📣 TESTER L'EFFET VICTOIRE"):
                st.balloons()

        with tab_admin:
            st.button("🔴 Se déconnecter de l'admin", on_click=lambda: st.session_state.update({"admin_logged": False}))
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🖼️ Gestion Médias")
                # LOGO
                up_logo = st.file_uploader("Charger le Logo", type=['png', 'jpg'], key="logo_up")
                if up_logo: 
                    Image.open(up_logo).save(LOGO_FILE)
                    st.success("Logo enregistré !")
                    # Pas de rerun immédiat ici pour éviter de perdre le reste de la page
                
                # GALERIE
                up_gal
