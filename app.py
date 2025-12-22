import streamlit as st
import os, glob, base64, qrcode, json, random, pandas as pd
from io import BytesIO
import streamlit.components.v1 as components

# --- 1. CONFIGURATION & FICHIERS ---
st.set_page_config(page_title="Social Wall Master - Transdev", layout="wide")

GALLERY_DIR, ADMIN_DIR = "galerie_images", "galerie_admin"
VOTES_FILE, PARTICIPANTS_FILE, CONFIG_FILE = "votes.json", "participants.json", "config_mur.json"

for d in [GALLERY_DIR, ADMIN_DIR]:
    if not os.path.exists(d): os.makedirs(d)

default_config = {
    "mode_affichage": "attente", 
    "titre_mur": "CONCOURS VIDÉO 2026", 
    "vote_version": 1, 
    "session_ouverte": False, 
    "reveal_resultats": False
}

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r") as f: return json.load(f)
        except: return default
    return default

config = load_json(CONFIG_FILE, default_config)
VOTE_VERSION = config.get("vote_version", 1)

# --- 2. NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"

# --- 3. ADMINISTRATION ---
if est_admin:
    st.sidebar.title("🎮 Régie Master")
    
    if "auth" not in st.session_state:
        st.session_state["auth"] = False

    if not st.session_state["auth"]:
        pwd = st.sidebar.text_input("Code Admin", type="password")
        if pwd == "ADMIN_LIVE_MASTER":
            st.session_state["auth"] = True
            st.rerun()
    else:
        # --- SESSION ---
        if st.sidebar.button("🔓 Déconnexion", use_container_width=True):
            st.session_state["auth"] = False
            st.rerun()
        
        # --- STATS ---
        nb_p = len(load_json(PARTICIPANTS_FILE, []))
        st.sidebar.info(f"👥 {nb_p} Participants connectés")
        
        # --- APERÇU DU MUR (NOUVEAU) ---
        st.sidebar.markdown("---")
        st.sidebar.caption("📺 Aperçu du Mur Social :")
        current_state_desc = "⏸️ ATTENTE"
        if config["mode_affichage"] == "live": current_state_desc = "📸 LIVE PHOTOS"
        if config["mode_affichage"] == "votes":
            current_state_desc = "🗳️ VOTE OUVERT" if config["session_ouverte"] else "🏁 FIN DU VOTE"
            if config["reveal_resultats"]: current_state_desc = "🏆 PODIUM"
        
        st.sidebar.markdown(f"""
            <div style="background:#333; padding:10px; border-radius:5px; border:1px solid #E2001A; text-align:center;">
                <span style="color:white; font-size:12px;">Mode Actif :</span><br>
                <strong style="color:#E2001A; font-size:14px;">{current_state_desc}</strong>
            </div>
            """, unsafe_allow_html=True)

        st.sidebar.markdown("---")

        # --- WORKFLOW ÉVÉNEMENT (BOUTONS) ---
        st.sidebar.subheader("🕹️ Pilotage direct")

        m = config["mode_affichage"]
        vo = config["session_ouverte"]
        re = config["reveal_resultats"]

        if st.sidebar.button("1️⃣ Début : Mode Attente", type="primary" if m == "attente" else "secondary", use_container_width=True):
            config.update({"mode_affichage": "attente", "session_ouverte": False, "reveal_resultats": False})
            with open(CONFIG_FILE, "w") as f: json.dump(config, f); st.rerun()

        if st.sidebar.button("2️⃣ Lancer les Votes", type="primary" if (m == "votes" and vo) else "secondary", use_container_width=True):
            config.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False})
            with open(CONFIG_FILE, "w") as f: json.dump(config, f); st.rerun()

        if st.sidebar.button("3️⃣ Clôturer les Votes", type="primary" if (not vo and m == "votes" and not re) else "secondary", use_container_width=True):
            config.update({"session_ouverte": False})
            with open(CONFIG_FILE, "w") as f: json.dump(config, f); st.rerun()

        if st.sidebar.button("4️⃣ Afficher le Podium 🏆", type="primary" if re else "secondary", use_container_width=True):
            config.update({"mode_affichage": "votes", "reveal_resultats": True, "session_ouverte": False})
            with open(CONFIG_FILE, "w") as f: json.dump(config, f); st.rerun()

        if st.sidebar.button("5️⃣ Mode Live (Photos)", type="primary" if m == "live" else "secondary", use_container_width=True):
            config.update({"mode_affichage": "live", "session_ouverte": False, "reveal_resultats": False})
            with open(CONFIG_FILE, "w") as f: json.dump(config, f); st.rerun()

        st.sidebar.markdown("---")
        config["titre_mur"] = st.sidebar.text_input("Titre du Mur", value=config["titre_mur"])
        if st.sidebar.button("💾 Sauver Titre", use_container_width=True):
            with open(CONFIG_FILE, "w") as f: json.dump(config, f); st.rerun()

        if st.sidebar.button("🔴 RESET COMPLET", type="secondary", use_container_width=True):
            config.update({"vote_version": VOTE_VERSION+1, "session_ouverte": False, "reveal_resultats": False, "mode_affichage": "attente"})
            with open(CONFIG_FILE, "w") as f: json.dump(config, f)
            with open(VOTES_FILE, "w") as f: json.dump({}, f)
            with open(PARTICIPANTS_FILE, "w") as f: json.dump([], f)
            st.rerun()

    if st.session_state.get("auth"):
        st.title("📊 Résultats & Export")
        v_data = load_json(VOTES_FILE, {})
        if v_data:
            sorted_v = dict(sorted(v_data.items(), key=lambda x: x[1], reverse=True))
            st.bar_chart(sorted_v)
            df = pd.DataFrame(list(sorted_v.items()), columns=['Service/BU', 'Points'])
            st.download_button("📥 Télécharger CSV", df.to_csv(index=False).encode('utf-8'), f'resultats_v{VOTE_VERSION}.csv', 'text/csv')
        else:
            st.info("Aucun vote pour le moment.")

# --- 4. UTILISATEUR & 5. MUR SOCIAL (Codes identiques aux étapes précédentes) ---
# ... (Gardez le reste du code tel quel)
