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
        if st.sidebar.button("🔓 Déconnexion", use_container_width=True):
            st.session_state["auth"] = False
            st.rerun()
        
        nb_p = len(load_json(PARTICIPANTS_FILE, []))
        st.sidebar.info(f"👥 {nb_p} Participants connectés")
        
        st.sidebar.markdown("---")
        m, vo, re = config["mode_affichage"], config["session_ouverte"], config["reveal_resultats"]

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

# --- 4. UTILISATEUR (VOTE) ---
elif est_utilisateur:
    st.markdown("<style>.stApp { background-color: black !important; color: white !important; }</style>", unsafe_allow_html=True)
    st.title("🗳️ Vote Transdev")
    v_key = f"v_{VOTE_VERSION}"
    if not config["session_ouverte"]:
        st.warning("⌛ Les votes sont clos ou pas encore ouverts.")
    else:
        choix = st.multiselect("Top 3 :", OPTS_BU)
        if len(choix) == 3 and st.button("🚀 VALIDER", use_container_width=True, type="primary"):
            vts = load_json(VOTES_FILE, {})
            for v, pts in zip(choix, [5, 3, 1]): vts[v] = vts.get(v, 0) + pts
            with open(VOTES_FILE, "w") as f: json.dump(vts, f)
            st.success("✅ Vote enregistré !")

# --- 5. MUR SOCIAL ---
else:
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'], footer { display: none !important; }</style>", unsafe_allow_html=True)
    
    # Titre et Participants
    nb_p = len(load_json(PARTICIPANTS_FILE, []))
    st.markdown(f'<div style="text-align:center; color:white; padding-top:40px;"><h1 style="font-size:50px; margin:0; text-transform:uppercase; font-weight:bold;">{config["titre_mur"]}</h1><div style="margin-top:10px; background:white; display:inline-block; padding:3px 15px; border-radius:20px; color:black; font-weight:bold; font-size:16px;">👥 {nb_p} CONNECTÉS</div></div>', unsafe_allow_html=True)

    # Logique d'affichage
    if config["mode_affichage"] == "attente":
        st.markdown('<div style="text-align:center; margin-top:50px; color:white;"><h2>⌛ En attente de l\'ouverture des Votes</h2><h1 style="font-size:60px; margin-top:40px;">Bienvenue ! 👋</h1></div>', unsafe_allow_html=True)

    elif config["mode_affichage"] == "votes" and not config["reveal_resultats"]:
        if config["session_ouverte"]:
            # Mode VOTE OUVERT : Affichage QR Code + Liste
            host = st.context.headers.get('host', 'localhost')
            qr_url = f"https://{host}/?mode=vote"
            qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            
            st.markdown('<div style="text-align:center; margin-top:20px;"><div style="background:#E2001A; color:white; padding:10px 30px; border-radius:10px; font-size:24px; font-weight:bold; border:2px solid white;">🚀 VOTES OUVERTS</div></div>', unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 0.8, 1])
            with col1:
                for opt in OPTS_BU[:5]: st.markdown(f'<div style="background:#222; color:white; padding:10px; margin-bottom:10px; border-left:5px solid #E2001A;">🎥 {opt}</div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div style="background:white; padding:10px; border-radius:15px; text-align:center;"><img src="data:image/png;base64,{qr_b64}" width="180"></div>', unsafe_allow_html=True)
            with col3:
                for opt in OPTS_BU[5:]: st.markdown(f'<div style="background:#222; color:white; padding:10px; margin-bottom:10px; border-left:5px solid #E2001A;">🎥 {opt}</div>', unsafe_allow_html=True)
        else:
            # Mode VOTE CLOS : FEUX D'ARTIFICE ET CLAPS
            components.html("""
                <canvas id="fireworks" style="position:fixed; top:0; left:0; width:100vw; height:100vh; pointer-events:none; z-index:999;"></canvas>
                <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
                <script>
                    var count = 200;
                    var defaults = { origin: { y: 0.7 } };
                    function fire(particleRatio, opts) {
                        confetti(Object.assign({}, defaults, opts, { particleCount: Math.floor(count * particleRatio) }));
                    }
                    fire(0.25, { spread: 26, startVelocity: 55 });
                    fire(0.2, { spread: 60 });
                    fire(0.35, { spread: 100, decay: 0.91, scalar: 0.8 });
                    fire(0.1, { spread: 120, startVelocity: 25, decay: 0.92, scalar: 1.2 });
                    fire(0.1, { spread: 120, startVelocity: 45 });
                </script>
            """, height=0)
            
            st.markdown("""
                <div style="text-align:center; margin-top:40px;">
                    <div style="background:#333; color:white; padding:10px 30px; border-radius:10px; font-size:24px; font-weight:bold; border:2px solid white; display:inline-block;">🏁 VOTES CLOS</div>
                    <div style="margin-top:50px; color:white;">
                        <div class="clap-emoji">👏</div>
                        <h1 style="font-size:50px; color:#E2001A;">MERCI À TOUS !</h1>
                        <h3>Préparation des résultats...</h3>
                    </div>
                </div>
                <style>
                    .clap-emoji { font-size: 100px; animation: clap 0.6s infinite alternate; }
                    @keyframes clap { from { transform: scale(1) rotate(-10deg); } to { transform: scale(1.3) rotate(10deg); } }
                </style>
            """, unsafe_allow_html=True)

    elif config["reveal_resultats"]:
        v_data = load_json(VOTES_FILE, {})
        if v_data:
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)[:3]
            cols = st.columns(3)
            m_txt = ["🥇 1er", "🥈 2ème", "🥉 3ème"]
            for i, (name, score) in enumerate(sorted_v):
                cols[i].markdown(f'<div style="background:#222;padding:30px;border-radius:20px;border:4px solid #E2001A;text-align:center;color:white;"><h2>{m_txt[i]}</h2><h1>{name}</h1><p>{score} pts</p></div>', unsafe_allow_html=True)

    # Rafraîchissement automatique
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(5000, key="wall_ref")
    except: pass
