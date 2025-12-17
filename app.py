import streamlit as st
import pandas as pd
import os
import base64
from PIL import Image
import altair as alt
from io import BytesIO
import qrcode

# --- 1. CONFIGURATION ---
ADMIN_PASSWORD = "ADMIN_VOEUX_2026"
VOTES_DIR = "sessions_votes"
GALLERY_DIR = "galerie_images"
SOUNDS_DIR = "sons_admin"
CONFIG_FILE = "config_videos.csv"
TITRE_FILE = "titre_config.txt"
LOCK_FILE = "vote_lock.txt"
LOGO_FILE = "logo_entreprise.png"

for d in [VOTES_DIR, GALLERY_DIR, SOUNDS_DIR]:
    if not os.path.exists(d): os.makedirs(d)

st.set_page_config(page_title="Régie Vote 2026", layout="wide")

# --- 2. FONCTIONS ---
if "voted" not in st.session_state: st.session_state["voted"] = False
if "edit_mode_title" not in st.session_state: st.session_state["edit_mode_title"] = False
if "editing_service" not in st.session_state: st.session_state["editing_service"] = None

def load_videos():
    if os.path.exists(CONFIG_FILE): 
        return pd.read_csv(CONFIG_FILE)['Video'].tolist()
    return ["BU PAX", "BU FRET", "BU BTOB", "DPMI", "RH", "Finances", "AO", "QSSE", "IT", "Direction"]

def save_videos(liste):
    pd.DataFrame(liste, columns=['Video']).to_csv(CONFIG_FILE, index=False)

def get_admin_title():
    if os.path.exists(TITRE_FILE):
        with open(TITRE_FILE, "r", encoding="utf-8") as f: return f.read()
    return "Gestion des Services"

def save_admin_title(nouveau_titre):
    with open(TITRE_FILE, "w", encoding="utf-8") as f: f.write(nouveau_titre)

def generer_qr(url):
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

# --- 3. LOGIQUE AFFICHAGE ---
est_admin = st.query_params.get("admin") == "true"
if os.path.exists(LOGO_FILE):
    st.image(Image.open(LOGO_FILE), width=150)

st.title("🎬 Élection Vidéo Vœux 2026")

if est_admin:
    tab_vote, tab_res, tab_admin = st.tabs(["🗳️ Espace Vote", "📊 Résultats", "🛠️ Console Admin"])
else:
    tab_vote = st.container()

# --- 4. ONGLET VOTE ---
with tab_vote:
    if est_admin:
        c1, c2 = st.columns([2, 1])
        with c2:
            st.write("📲 **Scannez pour voter**")
            st.image(generer_qr("https://vote-voeux-2026-6rueeu6wcdbxa878nepqgf.streamlit.app/"), width=180)
    
    imgs = [f for f in os.listdir(GALLERY_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if imgs:
        cols_gal = st.columns(min(len(imgs), 5))
        for i, img_name in enumerate(imgs):
            cols_gal[i % 5].image(os.path.join(GALLERY_DIR, img_name), use_container_width=True)

    st.divider()
    if os.path.exists(LOCK_FILE):
        st.warning("🔒 Les votes sont clos.")
    elif st.session_state["voted"]:
        st.success("✅ Votre vote a bien été enregistré !")
    else:
        st.write("### 📝 Votre profil")
        p1 = st.text_input("Votre Prénom")
        p2 = st.text_input("Votre Pseudo (ex: trigramme)")
        
        st.divider()
        st.write("### 🏆 Vos choix (cliquez sur les boutons)")
        
        vids = load_videos()
        
        # --- NOUVELLE MÉTHODE : BOUTONS SEGMENTÉS (PILLS) ---
        st.write("**1er choix (5 points) :**")
        s1 = st.segmented_control("choix1", vids, label_visibility="collapsed", key="s1")
        
        st.write("**2ème choix (3 points) :**")
        vids2 = [v for v in vids if v != s1]
        s2 = st.segmented_control("choix2", vids2, label_visibility="collapsed", key="s2")
        
        st.write("**3ème choix (1 point) :**")
        vids3 = [v for v in vids if v not in [s1, s2]]
        s3 = st.segmented_control("choix3", vids3, label_visibility="collapsed", key="s3")
        
        st.write("")
        if st.button("Valider mon vote 🚀", use_container_width=True):
            if not p1 or not p2 or s1 is None or s2 is None or s3 is None:
                st.error("⚠️ Veuillez remplir votre profil et cliquer sur 3 boutons.")
            else:
                fn = os.path.join(VOTES_DIR, "votes_principale.csv")
                df = pd.read_csv(fn) if os.path.exists(fn) else pd.DataFrame(columns=["Prenom", "Pseudo", "Top1", "Top2", "Top3"])
                if p2.lower() in df['Pseudo'].str.lower().values:
                    st.warning("❌ Pseudo déjà utilisé.")
                else:
                    new_v = pd.DataFrame([[p1, p2, s1, s2, s3]], columns=df.columns)
                    new_v.to_csv(fn, mode='a', header=not os.path.exists(fn), index=False)
                    st.session_state["voted"] = True
                    st.balloons(); st.rerun()

# --- 5 & 6 : RÉSULTATS ET ADMIN (Inchangés pour la gestion) ---
if est_admin:
    with tab_res:
        if st.text_input("Code Résultats", type="password", key="res_pwd") == ADMIN_PASSWORD:
            fn = os.path.join(VOTES_DIR, "votes_principale.csv")
            if os.path.exists(fn):
                df_r = pd.read_csv(fn)
                scores = {v: 0 for v in load_videos()}
                for _, r in df_r.iterrows():
                    for i, p in enumerate([5, 3, 1]):
                        if r[f'Top{i+1}'] in scores: scores[r[f'Top{i+1}']] += p
                df_p = pd.DataFrame(list(scores.items()), columns=['Service', 'Points']).sort_values('Points', ascending=False)
                st.altair_chart(alt.Chart(df_p).mark_bar(color='#FF4B4B').encode(x='Points', y=alt.Y('Service', sort='-x')), use_container_width=True)
    
    with tab_admin:
        if st.text_input("Code Admin", type="password", key="adm_pwd") == ADMIN_PASSWORD:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📁 Médias")
                u_logo = st.file_uploader("Logo", type=['png', 'jpg'])
                if u_logo: Image.open(u_logo).save(LOGO_FILE); st.rerun()
                u_gal = st.file_uploader("Photos", type=['png', 'jpg'], accept_multiple_files=True)
                if u_gal:
                    for f in u_gal: Image.open(f).save(os.path.join(GALLERY_DIR, f.name)); st.rerun()
                if st.button("🗑️ Vider la Galerie"):
                    for f in os.listdir(GALLERY_DIR): os.unlink(os.path.join(GALLERY_DIR, f))
                    st.rerun()
            with c2:
                # GESTION DES SERVICES
                current_title = get_admin_title()
                h1, h2 = st.columns([0.8, 0.2])
                h1.subheader(f"📝 {current_title}")
                if h2.button("✏️", key="et"): st.session_state["edit_mode_title"] = not st.session_state["edit_mode_title"]; st.rerun()
                if st.session_state["edit_mode_title"]:
                    nt = st.text_input("Nom:", value=current_title)
                    if st.button("OK"): save_admin_title(nt); st.session_state["edit_mode_title"]=False; st.rerun()
                st.write("---")
                vids = load_videos()
                for i, v in enumerate(vids):
                    col_v, col_btn = st.columns([0.7, 0.3])
                    col_v.write(f"• {v}")
                    if col_btn.button("❌", key=f"d_{i}"): vids.remove(v); save_videos(vids); st.rerun()
                new_s = st.text_input("Ajouter élément")
                if st.button("➕"):
                    if new_s: vids.append(new_s); save_videos(vids); st.rerun()
