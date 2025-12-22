import streamlit as st
import os, glob, base64, qrcode, json, random, pandas as pd
from io import BytesIO
import streamlit.components.v1 as components
import time

# --- 1. CONFIGURATION & FICHIERS ---
st.set_page_config(page_title="Régie Master - Pôle Aéroportuaire", layout="wide")

GALLERY_DIR, ADMIN_DIR = "galerie_images", "galerie_admin"
VOTES_FILE, PARTICIPANTS_FILE, CONFIG_FILE = "votes.json", "participants.json", "config_mur.json"

for d in [GALLERY_DIR, ADMIN_DIR]:
    if not os.path.exists(d): os.makedirs(d)

default_config = {
    "mode_affichage": "attente", 
    "titre_mur": "CONCOURS VIDÉO PÔLE AEROPORTUAIRE", 
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

# --- 3. ADMINISTRATION (Menus en Sidebar) ---
if est_admin:
    if "auth" not in st.session_state: st.session_state["auth"] = False
    
    if not st.session_state["auth"]:
        st.title("🔐 Accès Régie")
        pwd = st.text_input("Code Admin", type="password")
        if pwd == "ADMIN_LIVE_MASTER":
            st.session_state["auth"] = True
            st.rerun()
    else:
        # NAVIGATION DANS LA BARRE LATÉRALE
        with st.sidebar:
            st.title("🎮 RÉGIE")
            onglet = st.radio("Navigation", ["🕹️ Pilotage Live", "⚙️ Paramétrage", "📸 Gestion Photos", "📥 Exports & Data"])
            st.markdown("---")
            if st.button("🔓 Déconnexion", use_container_width=True):
                st.session_state["auth"] = False
                st.rerun()

        # ZONE CENTRALE ADMIN
        if onglet == "🕹️ Pilotage Live":
            st.header("🕹️ Pilotage du Mur Social")
            col_ctrl, col_stats = st.columns([1, 1.5])
            
            with col_ctrl:
                m, vo, re = config["mode_affichage"], config["session_ouverte"], config["reveal_resultats"]
                st.subheader("Actions")
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

            with col_stats:
                st.subheader("Scores en direct")
                v_data = load_json(VOTES_FILE, {})
                nb_p = len(load_json(PARTICIPANTS_FILE, []))
                st.metric("Participants connectés", nb_p)
                if v_data:
                    df = pd.DataFrame(list(v_data.items()), columns=['BU', 'Points']).sort_values('Points', ascending=False)
                    st.bar_chart(df.set_index('BU'))
                else: st.info("Aucun vote pour le moment.")

        elif onglet == "⚙️ Paramétrage":
            st.header("⚙️ Configuration")
            config["titre_mur"] = st.text_input("Titre du Mur", value=config["titre_mur"])
            uploaded_logo = st.file_uploader("Télécharger le Logo", type=["png", "jpg"])
            if uploaded_logo:
                config["logo_b64"] = base64.b64encode(uploaded_logo.read()).decode()
                st.success("Logo chargé !")
            if st.button("💾 Enregistrer les réglages"):
                json.dump(config, open(CONFIG_FILE, "w")); st.rerun()

        elif onglet == "📸 Gestion Photos":
            st.header("📸 Galerie")
            col_adm, col_usr = st.columns(2)
            with col_adm:
                st.subheader("Photos Admin")
                for f in glob.glob(f"{ADMIN_DIR}/*"):
                    st.image(f, width=150)
                    if st.button("Supprimer", key=f): os.remove(f); st.rerun()
            with col_usr:
                st.subheader("Photos Utilisateurs")
                for f in glob.glob(f"{GALLERY_DIR}/*"):
                    st.image(f, width=150)
                    if st.button("Supprimer", key=f+"u"): os.remove(f); st.rerun()

        elif onglet == "📥 Exports & Data":
            st.header("📥 Exports")
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                df = pd.DataFrame(list(v_data.items()), columns=['BU', 'Points'])
                st.download_button("📥 Télécharger CSV", df.to_csv(index=False).encode('utf-8'), "resultats_votes.csv")
            if st.button("🔴 RESET COMPLET", type="secondary"):
                for f in [VOTES_FILE, PARTICIPANTS_FILE]:
                    if os.path.exists(f): os.remove(f)
                st.warning("Système réinitialisé.")

# --- 4. UTILISATEUR ---
elif est_utilisateur:
    st.markdown("<style>.stApp { background-color: black !important; color: white !important; }</style>", unsafe_allow_html=True)
    st.title("🗳️ Vote Transdev")
    if not config["session_ouverte"]:
        st.warning("⌛ Les votes sont clos ou pas encore ouverts.")
    else:
        choix = st.multiselect("Sélectionnez vos 3 favoris :", OPTS_BU)
        if len(choix) == 3 and st.button("🚀 VALIDER MON VOTE", use_container_width=True, type="primary"):
            vts = load_json(VOTES_FILE, {})
            for v, pts in zip(choix, [5, 3, 1]): vts[v] = vts.get(v, 0) + pts
            json.dump(vts, open(VOTES_FILE, "w"))
            st.success("✅ Vote enregistré !")

# --- 5. MUR SOCIAL (CORRECTION AFFICHAGE) ---
else:
    # Suppression de tout le contenu par défaut et mise en noir
    st.markdown("""
        <style>
            body, .stApp { background-color: black !important; }
            [data-testid='stHeader'], footer { display: none !important; }
        </style>
    """, unsafe_allow_html=True)
    
    nb_p = len(load_json(PARTICIPANTS_FILE, []))
    logo_img = f'<img src="data:image/png;base64,{config["logo_b64"]}" style="max-height:80px; margin-bottom:10px;">' if config.get("logo_b64") else ""
    
    # EN-TÊTE MUR SOCIAL
    st.markdown(f"""
        <div style="text-align:center; color:white; padding-top:40px;">
            {logo_img}
            <h1 style="font-size:50px; font-weight:bold; text-transform:uppercase; margin:0;">{config["titre_mur"]}</h1>
            <div style="background:white; display:inline-block; padding:3px 15px; border-radius:20px; color:black; font-weight:bold; margin-top:10px;">
                👥 {nb_p} CONNECTÉS
            </div>
        </div>
    """, unsafe_allow_html=True)

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
            # MODE CLOS : PLUIE DE CONFETTIS
            components.html(f"""
                <div style="text-align:center; font-family:sans-serif; color:white; background:black; height:100%;">
                    <div style="{BADGE_CSS} background:#333;">🏁 LES VOTES SONT CLOS</div>
                    <div style="font-size:100px; animation: clap 0.5s infinite alternate; margin-top:30px;">👏</div>
                    <h1 style="color:#E2001A; font-size:45px;">MERCI À TOUS !</h1>
                </div>
                <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
                <script>
                    var end = Date.now() + 7000;
                    (function frame() {{
                        confetti({{ particleCount: 3, origin: {{ y: -0.2, x: Math.random() }}, spread: 360, gravity: 0.8, colors: ['#E2001A', '#ffffff'] }});
                        if (Date.now() < end) requestAnimationFrame(frame);
                    }}());
                </script>
                <style> @keyframes clap {{ from {{ transform: scale(1); }} to {{ transform: scale(1.2); }} }} </style>
            """, height=600)

    elif config["reveal_resultats"]:
        temps_ecoule = time.time() - config.get("timestamp_podium", 0)
        compte = 10 - int(temps_ecoule)
        if compte > 0:
            st.markdown(f'<div style="text-align:center; margin-top:100px;"><div style="font-size:200px; color:#E2001A; font-weight:bold; animation: pulse 1s infinite;">{compte}</div></div>', unsafe_allow_html=True)
            time.sleep(0.5); st.rerun()
        else:
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)[:3]
                st.markdown(f'<div style="text-align:center;"><div style="{BADGE_CSS}">🏆 LE PODIUM 2026</div><h2 style="color:white; font-style:italic; margin-top:20px;">✨ Félicitations aux grands gagnants ! ✨</h2></div>', unsafe_allow_html=True)
                cols = st.columns(3)
                m_txt = ["🥇 1er", "🥈 2ème", "🥉 3ème"]
                for i, (name, score) in enumerate(sorted_v):
                    cols[i].markdown(f'<div style="background:#222;padding:40px 20px;border-radius:20px;border:4px solid #E2001A;text-align:center;color:white;margin-top:40px;"><h2>{m_txt[i]}</h2><h1>{name}</h1><p>{score} pts</p></div>', unsafe_allow_html=True)
                components.html('<script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script><script>var end=Date.now()+10000;(function frame(){confetti({particleCount:5,origin:{y:-0.2,x:Math.random()},spread:360,gravity:0.7,colors:["#E2001A","#ffffff","#ffd700"]});if(Date.now()<end)requestAnimationFrame(frame);})();</script>', height=0)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(5000, key="wall_ref")
    except: pass
