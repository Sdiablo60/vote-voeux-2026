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

# --- PARAMÈTRES ET MODE ---
settings = load_settings()
nb_requis, effet_final, son_final = int(settings["nb_choix"]), settings["effet"], settings["son"]
est_admin = st.query_params.get("admin") == "true"

# --- LOGO ---
if os.path.exists(LOGO_FILE):
    st.image(Image.open(LOGO_FILE), width=150)

st.title("🎬 Élection Vidéo Vœux 2026")

# --- STRUCTURE DES ONGLETS ---
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
    else:
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
        with st.form("form_vote_stable", clear_on_submit=False):
            p1 = st.text_input("Prénom", key="f_prenom")
            p2 = st.text_input("Pseudo", key="f_pseudo")
            vids_list = load_videos()
            choix_faits = []
            for i in range(nb_requis):
                options = [v for v in vids_list if v not in choix_faits]
                sel = st.selectbox(f"Choix n°{i+1}", options, key=f"f_sel_{i}")
                choix_faits.append(sel)
            
            if st.form_submit_button("Valider mon vote 🚀"):
                if not p1 or not p2:
                    st.error("Prénom et Pseudo obligatoires.")
                else:
                    fname = get_session_file()
                    df_v = pd.read_csv(fname) if os.path.exists(fname) else pd.DataFrame(columns=["Prenom", "Pseudo"] + [f"Top{j+1}" for j in range(nb_requis)])
                    if p2.lower() in df_v['Pseudo'].str.lower().values:
                        st.warning("❌ Ce pseudo a déjà voté.")
                    else:
                        new_row = pd.DataFrame([[p1, p2] + choix_faits], columns=df_v.columns)
                        new_row.to_csv(fname, mode='a', header=not os.path.exists(fname), index=False)
                        st.session_state["voted"] = True
                        st.balloons()
                        st.rerun()

# --- 2. ONGLET RÉSULTATS (ADMIN SEULEMENT) ---
if est_admin:
    with tab_res:
        if st.text_input("Code Résultats", type="password", key="p_res") == ADMIN_PASSWORD:
            fname = get_session_file()
            if os.path.exists(fname):
                df_res = pd.read_csv(fname)
                st.subheader(f"📊 Participation : {len(df_res)} votants")
                scores = {v: 0 for v in load_videos()}
                for _, r in df_res.iterrows():
                    for j in range(nb_requis):
                        if r[f"Top{j+1}"] in scores: scores[r[f"Top{j+1}"]] += [5,3,1,1,1][j]
                
                final_df = pd.DataFrame(list(scores.items()), columns=['Service', 'Points']).sort_values('Points', ascending=False)
                st.altair_chart(alt.Chart(final_df).mark_bar(color='#FF4B4B').encode(x='Points', y=alt.Y('Service', sort='-x')), use_container_width=True)
                
                if st.button("📣 PROCLAMER LE VAINQUEUR"):
                    if son_final != "Aucun": jouer_son(son_final)
                    if effet_final == "Ballons": st.balloons()
                    elif effet_final == "Pluie d'étoiles": st.snow()
                    else: st.balloons()
            else: st.info("Aucun vote.")

# --- 3. ONGLET ADMIN (TOUTE LA CONFIGURATION) ---
    with tab_admin:
        if st.text_input("Code Super Admin", type="password", key="p_adm") == ADMIN_PASSWORD:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🖼️ Médias")
                up_logo = st.file_uploader("Logo", type=['png', 'jpg'])
                if up_logo: Image.open(up_logo).save(LOGO_FILE); st.rerun()
                
                up_gal = st.file_uploader("Galerie Photos", type=['png', 'jpg'], accept_multiple_files=True)
                if up_gal:
                    for f in up_gal: Image.open(f).save(os.path.join(GALLERY_DIR, f.name))
                    st.rerun()
                
                up_mp3 = st.file_uploader("Sons MP3", type=['mp3'])
                if up_mp3:
                    with open(os.path.join(SOUNDS_DIR, up_mp3.name), "wb") as f: f.write(up_mp3.getbuffer())
                    st.success("Son ajouté !")
                
                if st.button("🗑️ Vider la Galerie"):
                    for f in os.listdir(GALLERY_DIR): os.remove(os.path.join(GALLERY_DIR, f))
                    st.rerun()

            with col2:
                st.subheader("⚙️ Paramètres")
                n_nb = st.number_input("Nb choix requis", 1, 5, nb_requis)
                n_eff = st.selectbox("Effet", ["Ballons", "Pluie d'étoiles"], index=0)
                sons_list = ["Aucun"] + os.listdir(SOUNDS_DIR)
                n_son = st.selectbox("Son victoire", sons_list, index=0)
                if st.button("💾 Sauvegarder"): save_settings(n_nb, n_eff, n_son); st.rerun()
                
                st.divider()
                st.subheader("📝 Services")
                new_v = st.text_input("Nom du service")
                if st.button("Ajouter Service"):
                    l = load_videos(); l.append(new_v); save_videos(l); st.rerun()
                
                st.divider()
                if st.button("🔒 Clôturer" if not os.path.exists(LOCK_FILE) else "🔓 Rouvrir"):
                    if os.path.exists(LOCK_FILE): os.remove(LOCK_FILE)
                    else: open(LOCK_FILE, "w").write("L")
                    st.rerun()

                if os.path.exists(get_session_file()):
                    out = BytesIO()
                    pd.read_csv(get_session_file()).to_excel(out, index=False, engine='openpyxl')
                    st.download_button("📥 Excel", out.getvalue(), "resultats.xlsx")
