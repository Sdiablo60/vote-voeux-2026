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
LOGO_FILE = "logo_entreprise.png"
SESSION_CONFIG = "current_session.txt"

for d in [VOTES_DIR, GALLERY_DIR]:
    if not os.path.exists(d): os.makedirs(d)

st.set_page_config(page_title="Régie Master 2026", layout="wide")

# --- 2. FONCTIONS ---
def get_current_session():
    if os.path.exists(SESSION_CONFIG):
        with open(SESSION_CONFIG, "r") as f: return f.read().strip()
    return "session_1"

def set_current_session(name):
    with open(SESSION_CONFIG, "w") as f: f.write(name)

def load_videos():
    if os.path.exists(CONFIG_FILE): 
        return pd.read_csv(CONFIG_FILE)['Video'].tolist()
    return ["BU PAX", "BU FRET", "BU BTOB", "DPMI (ateliers)", "Service RH", "Service Finances", "Service AO", "Service QSSE", "Service IT", "Direction Pôle"]

def save_videos(liste):
    pd.DataFrame(liste, columns=['Video']).to_csv(CONFIG_FILE, index=False)

def ajouter_service_callback():
    nouveau = st.session_state["widget_ajout"].strip()
    if nouveau:
        vids = load_videos()
        if nouveau not in vids:
            vids.append(nouveau)
            save_videos(vids)
            st.toast(f"✅ {nouveau} ajouté !")
        st.session_state["widget_ajout"] = ""

# --- 3. INITIALISATION ---
current_session = get_current_session()
all_files = glob.glob(os.path.join(VOTES_DIR, "*.csv"))
if "voted" not in st.session_state: st.session_state["voted"] = False
if "editing_service" not in st.session_state: st.session_state["editing_service"] = None

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
        c1, c2, c3 = st.columns([1.5, 1, 1])
        c1.info(f"📍 Session active : **{current_session.upper()}**")
        c2.metric("Total Sessions", len(all_files))
        with c3.popover("➕ Nouvelle Session"):
            ns = st.text_input("Nom de la session")
            if st.button("Démarrer"):
                if ns: set_current_session(ns); st.rerun()
    
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    if imgs:
        cols = st.columns(5)
        for i, img in enumerate(imgs): cols[i%5].image(img, use_container_width=True)

    st.divider()
    if st.session_state["voted"]:
        st.success("✅ Vote bien pris en compte !")
        if st.button("Voter à nouveau"): st.session_state["voted"] = False; st.rerun()
    else:
        p1 = st.text_input("Votre Prénom")
        p2 = st.text_input("Votre Pseudo / Trigramme")
        vids = load_videos()
        s1 = st.segmented_control("Choix 1 (5 pts)", vids, key="v1")
        s2 = st.segmented_control("Choix 2 (3 pts)", [v for v in vids if v != s1], key="v2")
        s3 = st.segmented_control("Choix 3 (1 pt)", [v for v in vids if v not in [s1, s2]], key="v3")
        
        if st.button("Valider 🚀", use_container_width=True):
            if p1 and p2 and s1 and s2 and s3:
                fn = os.path.join(VOTES_DIR, f"{current_session}.csv")
                df = pd.read_csv(fn) if os.path.exists(fn) else pd.DataFrame(columns=["Prenom", "Pseudo", "Top1", "Top2", "Top3"])
                pd.DataFrame([[p1, p2, s1, s2, s3]], columns=df.columns).to_csv(fn, mode='a', header=not os.path.exists(fn), index=False)
                st.session_state["voted"] = True; st.balloons(); st.rerun()

# --- 5. ONGLET RÉSULTATS (Avec Export Excel/CSV) ---
if est_admin:
    with tab_res:
        mode = st.radio("Affichage", ["Session en cours", "Cumul général"], horizontal=True)
        df_res = pd.DataFrame()
        if mode == "Session en cours":
            fn = os.path.join(VOTES_DIR, f"{current_session}.csv")
            if os.path.exists(fn): df_res = pd.read_csv(fn)
            file_label = f"votes_{current_session}.csv"
        else:
            if all_files: df_res = pd.concat([pd.read_csv(f) for f in all_files])
            file_label = "cumul_global_votes.csv"

        if not df_res.empty:
            # Graphique
            scores = {v: 0 for v in load_videos()}
            for _, r in df_res.iterrows():
                for i, p in enumerate([5, 3, 1]):
                    if r[f'Top{i+1}'] in scores: scores[r[f'Top{i+1}']] += p
            df_p = pd.DataFrame(list(scores.items()), columns=['S', 'Pts']).sort_values('Pts', ascending=False)
            st.altair_chart(alt.Chart(df_p).mark_bar(color='#FF4B4B').encode(x='Pts', y=alt.Y('S', sort='-x')), use_container_width=True)
            
            # --- SECTION EXPORT ---
            st.divider()
            st.write(f"📥 **Exporter les données ({mode})**")
            csv_data = df_res.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"Télécharger {file_label}",
                data=csv_data,
                file_name=file_label,
                mime='text/csv',
                use_container_width=True
            )
        else: st.info("Aucun vote à afficher.")

# --- 6. ONGLET ADMIN ---
    with tab_admin:
        if st.text_input("Code Admin", type="password") == ADMIN_PASSWORD:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("⚙️ Contrôle")
                u_logo = st.file_uploader("Logo", type=['png', 'jpg'])
                if u_logo: Image.open(u_logo).save(LOGO_FILE); st.rerun()
                if st.button("🗑️ Reset Session Active"):
                    fn = os.path.join(VOTES_DIR, f"{current_session}.csv")
                    if os.path.exists(fn): os.remove(fn); st.rerun()
            with c2:
                st.subheader("📝 Gestion Services")
                st.text_input("Ajouter un service", key="widget_ajout", on_change=ajouter_service_callback)
                st.button("➕ Ajouter", on_click=ajouter_service_callback)
                st.divider()
                vids = load_videos()
                for i, v in enumerate(vids):
                    col_v, col_btn = st.columns([0.7, 0.3])
                    if st.session_state["editing_service"] == v:
                        new_val = col_v.text_input(f"Modif", value=v, key=f"inp_{i}")
                        if col_btn.button("💾", key=f"save_{i}"):
                            vids[i] = new_val; save_videos(vids)
                            st.session_state["editing_service"] = None; st.rerun()
                    else:
                        col_v.write(f"• {v}")
                        b_e, b_d = col_btn.columns(2)
                        if b_e.button("✏️", key=f"e_{i}"): st.session_state["editing_service"] = v; st.rerun()
                        if b_d.button("❌", key=f"d_{i}"): vids.remove(v); save_videos(vids); st.rerun()
