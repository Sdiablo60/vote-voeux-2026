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
OPTS_BU = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]

# --- 2. NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"

# --- 3. ADMINISTRATION ---
if est_admin:
    st.sidebar.title("🎮 Régie Master")
    if "auth" not in st.session_state: st.session_state["auth"] = False

    if not st.session_state["auth"]:
        pwd = st.sidebar.text_input("Code Admin", type="password")
        if pwd == "ADMIN_LIVE_MASTER":
            st.session_state["auth"] = True
            st.rerun()
    else:
        nb_p = len(load_json(PARTICIPANTS_FILE, []))
        st.sidebar.info(f"👥 {nb_p} Participants")
        
        m, vo, re = config["mode_affichage"], config["session_ouverte"], config["reveal_resultats"]
        
        if st.sidebar.button("1️⃣ Mode Attente", use_container_width=True):
            config.update({"mode_affichage": "attente", "session_ouverte": False, "reveal_resultats": False})
            json.dump(config, open(CONFIG_FILE, "w")); st.rerun()

        if st.sidebar.button("2️⃣ Lancer les Votes", use_container_width=True):
            config.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False})
            json.dump(config, open(CONFIG_FILE, "w")); st.rerun()

        if st.sidebar.button("3️⃣ Clôturer les Votes", use_container_width=True):
            config.update({"session_ouverte": False})
            json.dump(config, open(CONFIG_FILE, "w")); st.rerun()

        if st.sidebar.button("4️⃣ Afficher Podium 🏆", use_container_width=True):
            config.update({"mode_affichage": "votes", "reveal_resultats": True, "session_ouverte": False})
            json.dump(config, open(CONFIG_FILE, "w")); st.rerun()

        if st.sidebar.button("5️⃣ Mode Live Photos", use_container_width=True):
            config.update({"mode_affichage": "live", "session_ouverte": False, "reveal_resultats": False})
            json.dump(config, open(CONFIG_FILE, "w")); st.rerun()

# --- 4. UTILISATEUR (VOTE) ---
elif est_utilisateur:
    st.title("🗳️ Vote Transdev")
    if not config["session_ouverte"]:
        st.warning("⌛ Les votes sont clos ou pas encore ouverts.")
    else:
        choix = st.multiselect("Votre Top 3 :", OPTS_BU)
        if len(choix) == 3 and st.button("🚀 VALIDER"):
            vts = load_json(VOTES_FILE, {})
            for v, pts in zip(choix, [5, 3, 1]): vts[v] = vts.get(v, 0) + pts
            json.dump(vts, open(VOTES_FILE, "w"))
            st.success("✅ Voté !")

# --- 5. MUR SOCIAL ---
else:
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'], footer { display: none !important; }</style>", unsafe_allow_html=True)
    nb_p = len(load_json(PARTICIPANTS_FILE, []))
    st.markdown(f'<div style="text-align:center; color:white; padding-top:40px;"><h1 style="font-size:50px; font-weight:bold;">{config["titre_mur"]}</h1><div style="background:white; display:inline-block; padding:3px 15px; border-radius:20px; color:black; font-weight:bold;">👥 {nb_p} CONNECTÉS</div></div>', unsafe_allow_html=True)

    # MODE ATTENTE
    if config["mode_affichage"] == "attente":
        st.markdown('<div style="text-align:center; margin-top:100px; color:white;"><h2>⌛ En attente des votes...</h2><h1 style="font-size:60px;">Bienvenue ! 👋</h1></div>', unsafe_allow_html=True)

    # MODE VOTES
    elif config["mode_affichage"] == "votes" and not config["reveal_resultats"]:
        if config["session_ouverte"]:
            host = st.context.headers.get('host', 'localhost')
            qr_url = f"https://{host}/?mode=vote"
            qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            st.markdown(f'<div style="text-align:center; margin-top:50px;"><div style="background:white; display:inline-block; padding:15px; border-radius:15px;"><img src="data:image/png;base64,{qr_b64}" width="200"></div><h2 style="color:white; margin-top:20px;">🚀 VOTES OUVERTS</h2></div>', unsafe_allow_html=True)
        else:
            # --- ICI L'EFFET FEU D'ARTIFICE (CONFÉTTIS) ---
            components.html("""
                <div style="text-align:center; font-family: sans-serif; color:white;">
                    <style>
                        .clap-emoji { font-size: 120px; display: inline-block; animation: clap-move 0.5s infinite alternate; }
                        @keyframes clap-move { from { transform: scale(1) rotate(-10deg); } to { transform: scale(1.3) rotate(10deg); } }
                    </style>
                    <div class="clap-emoji">👏</div>
                    <h1 style="font-size:50px; color:#E2001A;">🏁 VOTES CLOS !</h1>
                    <h2 style="font-size:35px;">MERCI À TOUS !</h2>
                    <p style="font-size:20px; color:#ccc;">Préparez-vous pour les résultats...</p>
                </div>
                <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
                <script>
                    function fireworks() {
                        var end = Date.now() + (5 * 1000);
                        (function frame() {
                            confetti({ particleCount: 5, angle: 60, spread: 55, origin: { x: 0 }, colors: ['#E2001A', '#ffffff', '#ff0000'] });
                            confetti({ particleCount: 5, angle: 120, spread: 55, origin: { x: 1 }, colors: ['#E2001A', '#ffffff', '#ff0000'] });
                            if (Date.now() < end) { requestAnimationFrame(frame); }
                        }());
                    }
                    fireworks();
                </script>
            """, height=500)

    # MODE PODIUM
    elif config["reveal_resultats"]:
        v_data = load_json(VOTES_FILE, {})
        if v_data:
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)[:3]
            cols = st.columns(3)
            for i, (name, score) in enumerate(sorted_v):
                cols[i].markdown(f'<div style="background:#222;padding:30px;border-radius:20px;border:4px solid #E2001A;text-align:center;color:white;"><h1>{name}</h1><p>{score} pts</p></div>', unsafe_allow_html=True)

    # Rafraîchissement
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(5000, key="wall_ref")
    except: pass
