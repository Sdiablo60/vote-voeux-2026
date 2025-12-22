import streamlit as st
import os, glob, base64, qrcode, json, random, pandas as pd
from io import BytesIO
import streamlit.components.v1 as components
import time

# --- 1. CONFIGURATION & FICHIERS ---
st.set_page_config(page_title="Régie Master - Transdev", layout="wide")

GALLERY_DIR, ADMIN_DIR = "galerie_images", "galerie_admin"
VOTES_FILE, PARTICIPANTS_FILE, CONFIG_FILE = "votes.json", "participants.json", "config_mur.json"

for d in [GALLERY_DIR, ADMIN_DIR]:
    if not os.path.exists(d): os.makedirs(d)

default_config = {
    "mode_affichage": "attente", 
    "titre_mur": "CONCOURS VIDÉO 2026", 
    "vote_version": 1, 
    "session_ouverte": False, 
    "reveal_resultats": False,
    "timestamp_podium": 0,
    "logo_b64": None
}

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r") as f: return json.load(f)
        except: return default
    return default

config = load_json(CONFIG_FILE, default_config)
OPTS_BU = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]
BADGE_CSS = "margin-top:20px; background:#E2001A; display:inline-block; padding:10px 30px; border-radius:10px; font-size:22px; font-weight:bold; border:2px solid white; color:white;"

# --- 2. NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"

# --- 3. ADMINISTRATION ---
if est_admin:
    st.title("🛠️ Console d'Administration")
    
    if "auth" not in st.session_state: st.session_state["auth"] = False
    if not st.session_state["auth"]:
        pwd = st.text_input("Code Admin", type="password")
        if pwd == "ADMIN_LIVE_MASTER":
            st.session_state["auth"] = True
            st.rerun()
    else:
        # CRÉATION DES ONGLETS
        tab_live, tab_params, tab_photos, tab_exports = st.tabs([
            "🎮 Pilotage Live", "⚙️ Paramétrage", "📸 Gestion Photos", "📥 Exports & Données"
        ])

        # --- ONGLET 1 : PILOTAGE LIVE ---
        with tab_live:
            col_btn, col_view = st.columns([1, 2])
            with col_btn:
                st.subheader("Contrôle du Mur")
                m, vo, re = config["mode_affichage"], config["session_ouverte"], config["reveal_resultats"]
                
                if st.button("1️⃣ Mode Attente", use_container_width=True, type="primary" if m=="attente" else "secondary"):
                    config.update({"mode_affichage": "attente", "session_ouverte": False, "reveal_resultats": False})
                    json.dump(config, open(CONFIG_FILE, "w")); st.rerun()

                if st.button("2️⃣ Lancer les Votes", use_container_width=True, type="primary" if (m=="votes" and vo) else "secondary"):
                    config.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False})
                    json.dump(config, open(CONFIG_FILE, "w")); st.rerun()

                if st.button("3️⃣ Clôturer les Votes", use_container_width=True, type="primary" if (m=="votes" and not vo and not re) else "secondary"):
                    config.update({"session_ouverte": False})
                    json.dump(config, open(CONFIG_FILE, "w")); st.rerun()

                if st.button("4️⃣ Afficher Podium 🏆", use_container_width=True, type="primary" if re else "secondary"):
                    config.update({"mode_affichage": "votes", "reveal_resultats": True, "session_ouverte": False, "timestamp_podium": time.time()})
                    json.dump(config, open(CONFIG_FILE, "w")); st.rerun()
            
            with col_view:
                st.subheader("Aperçu des Scores")
                v_data = load_json(VOTES_FILE, {})
                if v_data:
                    df = pd.DataFrame(list(v_data.items()), columns=['BU', 'Points']).sort_values('Points', ascending=False)
                    st.bar_chart(df.set_index('BU'))
                else:
                    st.info("Aucun vote pour le moment.")

        # --- ONGLET 2 : PARAMÉTRAGE ---
        with tab_params:
            st.subheader("Identité Visuelle")
            config["titre_mur"] = st.text_input("Titre de l'événement", value=config["titre_mur"])
            
            uploaded_logo = st.file_uploader("Télécharger le Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])
            if uploaded_logo:
                logo_b64 = base64.b64encode(uploaded_logo.read()).decode()
                config["logo_b64"] = logo_b64
                st.success("Logo chargé !")

            if st.button("💾 Enregistrer les paramètres"):
                json.dump(config, open(CONFIG_FILE, "w"))
                st.rerun()

        # --- ONGLET 3 : GESTION PHOTOS ---
        with tab_photos:
            sub1, sub2 = st.tabs(["🖼️ Photos Admin (Diffusées)", "📱 Photos Utilisateurs"])
            with sub1:
                st.write("Photos présentes dans le dossier Admin :")
                files_admin = glob.glob(f"{ADMIN_DIR}/*")
                for f in files_admin:
                    col_img, col_del = st.columns([3, 1])
                    col_img.image(f, width=150)
                    if col_del.button("Supprimer", key=f):
                        os.remove(f); st.rerun()
            with sub2:
                st.write("Photos envoyées par les participants :")
                files_user = glob.glob(f"{GALLERY_DIR}/*")
                if not files_user: st.info("Aucune photo reçue.")
                for f in files_user:
                    col_img, col_del = st.columns([3, 1])
                    col_img.image(f, width=150)
                    if col_del.button("Supprimer", key=f+"u"):
                        os.remove(f); st.rerun()

        # --- ONGLET 4 : EXPORTS ---
        with tab_exports:
            st.subheader("Téléchargement des données")
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                df_export = pd.DataFrame(list(v_data.items()), columns=['BU', 'Points'])
                csv = df_export.to_csv(index=False).encode('utf-8')
                st.download_button("📊 Exporter les Votes (CSV)", csv, "resultats_votes.csv", "text/csv")
            
            if st.button("🗑️ Réinitialiser tous les Votes", type="secondary"):
                if os.path.exists(VOTES_FILE): os.remove(VOTES_FILE)
                st.warning("Données de votes supprimées.")

# --- 4. UTILISATEUR (VOTE) ---
elif est_utilisateur:
    st.markdown("<style>.stApp { background-color: black !important; color: white !important; }</style>", unsafe_allow_html=True)
    st.title("🗳️ Vote Transdev")
    if not config["session_ouverte"]:
        st.warning("⌛ Les votes sont clos ou en attente.")
    else:
        choix = st.multiselect("Top 3 Vidéos :", OPTS_BU)
        if len(choix) == 3 and st.button("🚀 VALIDER"):
            vts = load_json(VOTES_FILE, {})
            for v, pts in zip(choix, [5, 3, 1]): vts[v] = vts.get(v, 0) + pts
            json.dump(vts, open(VOTES_FILE, "w"))
            st.success("✅ Vote enregistré !")

# --- 5. MUR SOCIAL ---
else:
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'], footer { display: none !important; }</style>", unsafe_allow_html=True)
    nb_p = len(load_json(PARTICIPANTS_FILE, []))
    
    # Affichage du logo si présent
    logo_html = f'<img src="data:image/png;base64,{config["logo_b64"]}" width="150">' if config.get("logo_b64") else ""
    
    st.markdown(f"""
        <div style="text-align:center; color:white; padding-top:20px;">
            {logo_html}
            <h1 style="font-size:55px; font-weight:bold; text-transform:uppercase; margin-top:10px;">{config["titre_mur"]}</h1>
            <div style="background:white; display:inline-block; padding:3px 15px; border-radius:20px; color:black; font-weight:bold;">👥 {nb_p} CONNECTÉS</div>
        </div>
    """, unsafe_allow_html=True)

    # Logique d'affichage (Attente / Votes / Podium) identique aux versions précédentes...
    # [Le reste du code pour le Mur Social reste le même que précédemment]
    if config["mode_affichage"] == "attente":
        st.markdown(f'<div style="text-align:center; color:white;"><div style="{BADGE_CSS}">⌛ En attente des Votes</div><h2 style="font-size:55px; margin-top:60px;">Bienvenue ! 👋</h2></div>', unsafe_allow_html=True)
    elif config["mode_affichage"] == "votes" and not config["reveal_resultats"]:
        # (Logique QR Code et listes BU)
        host = st.context.headers.get('host', 'localhost')
        qr_url = f"https://{host}/?mode=vote"
        qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        
        st.markdown(f'<div style="text-align:center;"><div style="{BADGE_CSS}">🚀 VOTES OUVERTS</div></div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 0.8, 1])
        with col1:
            for opt in OPTS_BU[:5]: st.markdown(f'<div style="background:#222; color:white; padding:12px; margin-bottom:12px; border-left:5px solid #E2001A; font-weight:bold;">🎥 {opt}</div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div style="background:white; padding:10px; border-radius:15px; text-align:center;"><img src="data:image/png;base64,{qr_b64}" width="180"></div>', unsafe_allow_html=True)
        with col3:
            for opt in OPTS_BU[5:]: st.markdown(f'<div style="background:#222; color:white; padding:12px; margin-bottom:12px; border-left:5px solid #E2001A; font-weight:bold;">🎥 {opt}</div>', unsafe_allow_html=True)

    elif config["reveal_resultats"]:
        # (Logique Compte à rebours + Podium)
        temps_ecoule = time.time() - config.get("timestamp_podium", 0)
        compte = 10 - int(temps_ecoule)
        if compte > 0:
            st.markdown(f'<div style="text-align:center; margin-top:80px;"><div style="font-size:250px; color:#E2001A; font-weight:bold;">{compte}</div></div>', unsafe_allow_html=True)
            time.sleep(0.5); st.rerun()
        else:
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)[:3]
                st.markdown(f'<div style="text-align:center;"><div style="{BADGE_CSS}">🏆 LE PODIUM</div></div>', unsafe_allow_html=True)
                cols = st.columns(3)
                for i, (name, score) in enumerate(sorted_v):
                    cols[i].markdown(f'<div style="background:#222;padding:30px;border-radius:20px;border:3px solid #E2001A;text-align:center;color:white;margin-top:20px;"><h2>{name}</h2><h1>{score} pts</h1></div>', unsafe_allow_html=True)
                components.html('<script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script><script>confetti({particleCount:150, spread:70, origin:{y:0.6}, colors:["#E2001A","#ffffff"]});</script>')

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(5000, key="wall_ref")
    except: pass
