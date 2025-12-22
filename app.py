import streamlit as st
import os, glob, base64, qrcode, json, random, pandas as pd
from io import BytesIO
import streamlit.components.v1 as components
import time

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
    "reveal_resultats": False,
    "timestamp_podium": 0
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

BADGE_CSS = "margin-top:20px; background:#E2001A; display:inline-block; padding:10px 30px; border-radius:10px; font-size:22px; font-weight:bold; border:2px solid white; color:white;"

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
        # États actuels pour la coloration des boutons
        m, vo, re = config["mode_affichage"], config["session_ouverte"], config["reveal_resultats"]
        
        st.sidebar.subheader("🕹️ Pilotage")
        
        # Bouton 1 : Attente
        type_1 = "primary" if m == "attente" else "secondary"
        if st.sidebar.button("1️⃣ Mode Attente", use_container_width=True, type=type_1):
            config.update({"mode_affichage": "attente", "session_ouverte": False, "reveal_resultats": False})
            json.dump(config, open(CONFIG_FILE, "w")); st.rerun()

        # Bouton 2 : Lancer les Votes
        type_2 = "primary" if (m == "votes" and vo) else "secondary"
        if st.sidebar.button("2️⃣ Lancer les Votes", use_container_width=True, type=type_2):
            config.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False})
            json.dump(config, open(CONFIG_FILE, "w")); st.rerun()

        # Bouton 3 : Clôturer les Votes
        type_3 = "primary" if (m == "votes" and not vo and not re) else "secondary"
        if st.sidebar.button("3️⃣ Clôturer les Votes", use_container_width=True, type=type_3):
            config.update({"session_ouverte": False})
            json.dump(config, open(CONFIG_FILE, "w")); st.rerun()

        # Bouton 4 : Podium
        type_4 = "primary" if re else "secondary"
        if st.sidebar.button("4️⃣ Afficher Podium 🏆", use_container_width=True, type=type_4):
            config.update({"mode_affichage": "votes", "reveal_resultats": True, "session_ouverte": False, "timestamp_podium": time.time()})
            json.dump(config, open(CONFIG_FILE, "w")); st.rerun()

        st.sidebar.markdown("---")
        config["titre_mur"] = st.sidebar.text_input("Titre du Mur", value=config["titre_mur"])
        if st.sidebar.button("💾 Sauver Titre", use_container_width=True):
            json.dump(config, open(CONFIG_FILE, "w")); st.rerun()

        # PAGE CENTRALE ADMIN : STATISTIQUES
        st.title("📊 Tableau de Bord")
        nb_p = len(load_json(PARTICIPANTS_FILE, []))
        st.metric("Participants Connectés", nb_p)
        
        v_data = load_json(VOTES_FILE, {})
        if v_data:
            st.subheader("Classement en Temps Réel")
            df = pd.DataFrame(list(v_data.items()), columns=['Unité (BU)', 'Points']).sort_values('Points', ascending=False)
            st.bar_chart(df.set_index('Unité (BU)'))
            st.table(df)

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
    st.markdown(f'<div style="text-align:center; color:white; padding-top:40px;"><h1 style="font-size:55px; font-weight:bold; text-transform:uppercase; margin:0;">{config["titre_mur"]}</h1><div style="background:white; display:inline-block; padding:3px 15px; border-radius:20px; color:black; font-weight:bold; margin-top:10px;">👥 {nb_p} CONNECTÉS</div></div>', unsafe_allow_html=True)

    if config["mode_affichage"] == "attente":
        st.markdown(f'<div style="text-align:center; color:white;"><div style="{BADGE_CSS}">⌛ En attente de l\'ouverture des Votes</div><h2 style="font-size:55px; margin-top:60px;">Bienvenue ! 👋</h2></div>', unsafe_allow_html=True)

    elif config["mode_affichage"] == "votes" and not config["reveal_resultats"]:
        if config["session_ouverte"]:
            host = st.context.headers.get('host', 'localhost')
            qr_url = f"https://{host}/?mode=vote"
            qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            st.markdown(f'<div style="text-align:center;"><div style="{BADGE_CSS} animation:blink 1.5s infinite;">🚀 LES VOTES SONT OUVERTS</div></div>', unsafe_allow_html=True)
            st.markdown("<div style='margin-top:40px;'>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 0.8, 1])
            with c1:
                for opt in OPTS_BU[:5]: st.markdown(f'<div style="background:#222; color:white; padding:12px; margin-bottom:12px; border-left:5px solid #E2001A; font-weight:bold; font-size:18px;">🎥 {opt}</div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div style="background:white; padding:10px; border-radius:15px; text-align:center;"><img src="data:image/png;base64,{qr_b64}" width="180"><p style="color:black; font-weight:bold; margin-top:10px; font-size:14px;">SCANNEZ POUR VOTER</p></div>', unsafe_allow_html=True)
            with c3:
                for opt in OPTS_BU[5:]: st.markdown(f'<div style="background:#222; color:white; padding:12px; margin-bottom:12px; border-left:5px solid #E2001A; font-weight:bold; font-size:18px;">🎥 {opt}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            components.html(f"""
                <div style="text-align:center; font-family: sans-serif; color:white; background:black;">
                    <div style="{BADGE_CSS} background:#333;">🏁 LES VOTES SONT CLOS</div>
                    <div style="font-size:100px; animation: clap 0.5s infinite alternate; margin-top:30px;">👏</div>
                    <h1 style="color:#E2001A; font-size:45px;">MERCI À TOUS !</h1>
                </div>
                <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
                <script>
                    var end = Date.now() + (7 * 1000);
                    (function frame() {{
                        confetti({{ particleCount: 3, origin: {{ y: -0.2, x: Math.random() }}, spread: 360, gravity: 0.8, colors: ['#E2001A', '#ffffff'] }});
                        if (Date.now() < end) requestAnimationFrame(frame);
                    }}());
                </script>
                <style> @keyframes clap {{ from {{ transform: scale(1); }} to {{ transform: scale(1.2); }} }} </style>
            """, height=600)

    elif config["reveal_resultats"]:
        temps_ecoule = time.time() - config.get("timestamp_podium", 0)
        compte_a_rebours = 10 - int(temps_ecoule)
        if compte_a_rebours > 0:
            st.markdown(f'<div style="text-align:center; margin-top:100px;"><h2 style="color:white; font-size:40px;">Révélation du Podium dans...</h2><div style="font-size:200px; color:#E2001A; font-weight:bold; animation: pulse 1s infinite;">{compte_a_rebours}</div></div>', unsafe_allow_html=True)
            time.sleep(0.5); st.rerun()
        else:
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)[:3]
                st.markdown(f'<div style="text-align:center;"><div style="{BADGE_CSS}">🏆 LE PODIUM 2026</div><h2 style="color:white; font-style:italic; margin-top:20px;">✨ Félicitations aux grands gagnants ! ✨</h2></div>', unsafe_allow_html=True)
                cols = st.columns(3)
                m_txt = ["🥇 1er", "🥈 2ème", "🥉 3ème"]
                for i, (name, score) in enumerate(sorted_v):
                    cols[i].markdown(f'<div style="background:#222;padding:40px 20px;border-radius:20px;border:4px solid #E2001A;text-align:center;color:white;margin-top:40px;"><h2>{m_txt[i]}</h2><h1 style="font-size:38px;">{name}</h1><p style="font-size:22px;">{score} pts</p></div>', unsafe_allow_html=True)
                components.html("""
                    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
                    <script>
                        var end = Date.now() + 10000;
                        (function frame() {
                            confetti({ particleCount: 5, origin: { y: -0.2, x: Math.random() }, spread: 360, gravity: 0.7, colors: ['#E2001A', '#ffffff', '#ffd700'] });
                            if (Date.now() < end) requestAnimationFrame(frame);
                        }());
                    </script>
                """, height=0)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(5000, key="wall_ref")
    except: pass
