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

# --- 2. FONCTIONS DE CHARGEMENT ---
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
    
    imgs = [f for f in os.listdir(GALLERY_DIR) if f.lower().endswith(('.png', '.jpg'))]
    if imgs:
        cols_gal = st.columns(len(imgs))
        for i, img in enumerate(imgs): cols_gal[i].image(os.path.join(GALLERY_DIR, img), use_container_width=True)

    st.divider()
    if os.path.exists(LOCK_FILE):
        st.warning("🔒 Les votes sont clos.")
    elif st.session_state["voted"]:
        st.success("✅ Votre vote a bien été enregistré !")
    else:
        p1 = st.text_input("Votre Prénom")
        p2 = st.text_input("Votre Pseudo (ex: trigramme)")
        vids = load_videos()
        s1 = st.selectbox("Choix n°1 (5 pts)", [None] + vids, key="s1")
        s2 = st.selectbox("Choix n°2 (3 pts)", [None] + [v for v in vids if v != s1], key="s2")
        s3 = st.selectbox("Choix n°3 (1 pt)", [None] + [v for v in vids if v not in [s1, s2]], key="s3")
        
        if st.button("Valider mon vote 🚀"):
            if not p1 or not p2 or not s1 or not s2 or not s3:
                st.error("⚠️ Veuillez remplir votre profil et faire vos 3 choix.")
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

# --- 5. ONGLET RÉSULTATS ---
if est_admin:
    with tab_res:
        if st.text_input("Code Résultats", type="password", key="res_pwd") == ADMIN_PASSWORD:
            fn = os.path.join(VOTES_DIR, "votes_principale.csv")
            if os.path.exists(fn):
                df_r = pd.read_csv(fn)
                st.write(f"**Votants : {len(df_r)}**")
                scores = {v: 0 for v in load_videos()}
                for _, r in df_r.iterrows():
                    for i, p in enumerate([5, 3, 1]):
                        if r[f'Top{i+1}'] in scores: scores[r[f'Top{i+1}']] += p
                df_p = pd.DataFrame(list(scores.items()), columns=['Service', 'Points']).sort_values('Points', ascending=False)
                st.altair_chart(alt.Chart(df_p).mark_bar(color='#FF4B4B').encode(x='Points', y=alt.Y('Service', sort='-x')), use_container_width=True)
            else: st.info("Aucun vote.")

# --- 6. ONGLET ADMIN ---
    with tab_admin:
        if st.text_input("Code Admin", type="password", key="adm_pwd") == ADMIN_PASSWORD:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📁 Médias & Galerie")
                u_logo = st.file_uploader("Logo", type=['png', 'jpg'])
                if u_logo: Image.open(u_logo).save(LOGO_FILE); st.rerun()
                u_gal = st.file_uploader("Photos", type=['png', 'jpg'], accept_multiple_files=True)
                if u_gal:
                    for f in u_gal: Image.open(f).save(os.path.join(GALLERY_DIR, f.name))
                    st.rerun()
                if st.button("🗑️ Vider la Galerie"):
                    for f in os.listdir(GALLERY_DIR): os.remove(os.path.join(GALLERY_DIR, f))
                    st.rerun()
                st.divider()
                st.subheader("⚙️ Contrôle")
                if st.button("🔒 Verrouiller/Déverrouiller"):
                    if os.path.exists(LOCK_FILE): os.remove(LOCK_FILE)
                    else: open(LOCK_FILE, "w").write("L")
                    st.rerun()
                if st.button("🗑️ Reset Votes"):
                    fn = os.path.join(VOTES_DIR, "votes_principale.csv")
                    if os.path.exists(fn): os.remove(fn)
                    st.session_state["voted"] = False; st.rerun()

            with c2:
                # TITRE SECTION
                current_title = get_admin_title()
                h_c1, h_c2 = st.columns([0.8, 0.2])
                h_c1.subheader(f"📝 {current_title}")
                if h_c2.button("✏️", key="edit_title"):
                    st.session_state["edit_mode_title"] = not st.session_state["edit_mode_title"]
                    st.rerun()
                
                if st.session_state["edit_mode_title"]:
                    nt = st.text_input("Nouveau nom section :", value=current_title)
                    if st.button("OK"): save_admin_title(nt); st.session_state["edit_mode_title"]=False; st.rerun()
                
                st.divider()

                # --- NOUVEAUTÉ : AJOUT EN HAUT ---
                new_s = st.text_input("Ajouter un nouvel élément (ex: Service RH)")
                if st.button("➕ Ajouter à la liste"):
                    if new_s:
                        vids = load_videos()
                        vids.append(new_s)
                        save_videos(vids)
                        st.rerun()
                
                st.write("---")
                
                # LISTE DES SERVICES EXISTANTS
                vids = load_videos()
                for i, v in enumerate(vids):
                    col_v, col_btn = st.columns([0.7, 0.3])
                    
                    if st.session_state["editing_service"] == v:
                        new_val = col_v.text_input(f"Modifier", value=v, key=f"inp_{i}")
                        if col_btn.button("💾", key=f"save_{i}"):
                            vids[i] = new_val
                            save_videos(vids)
                            st.session_state["editing_service"] = None
                            st.rerun()
                    else:
                        col_v.write(f"• {v}")
                        b_edit, b_del = col_btn.columns(2)
                        if b_edit.button("✏️", key=f"edit_s_{i}"):
                            st.session_state["editing_service"] = v
                            st.rerun()
                        if b_del.button("❌", key=f"del_s_{i}"):
                            vids.remove(v); save_videos(vids); st.rerun()
