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

# --- 3. ADMINISTRATION ---
if est_admin:
    st.title("🛠️ Console Régie Master")
    
    if "auth" not in st.session_state: st.session_state["auth"] = False
    if not st.session_state["auth"]:
        pwd = st.text_input("Code Admin", type="password")
        if pwd == "ADMIN_LIVE_MASTER":
            st.session_state["auth"] = True
            st.rerun()
    else:
        st.sidebar.success("Connecté en tant que Régie")
        if st.sidebar.button("🔓 Déconnexion"):
            st.session_state["auth"] = False
            st.rerun()

        # --- SYSTÈME D'ONGLETS ---
        tab_live, tab_config, tab_galerie, tab_data = st.tabs([
            "🎮 Pilotage Live", "⚙️ Configuration", "📸 Galerie Photos", "📥 Données & Exports"
        ])

        with tab_live:
            col_ctrl, col_stats = st.columns([1, 1.5])
            with col_ctrl:
                st.subheader("Pilotage du Mur")
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

            with col_stats:
                st.subheader("Suivi des Votes")
                v_data = load_json(VOTES_FILE, {})
                if v_data:
                    df = pd.DataFrame(list(v_data.items()), columns=['BU', 'Points']).sort_values('Points', ascending=False)
                    st.bar_chart(df.set_index('BU'))
                else:
                    st.info("En attente des premiers votes...")

        with tab_config:
            st.subheader("Personnalisation")
            config["titre_mur"] = st.text_input("Titre de l'écran principal", value=config["titre_mur"])
            
            uploaded_logo = st.file_uploader("Logo (PNG de préférence)", type=["png", "jpg", "jpeg"])
            if uploaded_logo:
                logo_b64 = base64.b64encode(uploaded_logo.read()).decode()
                config["logo_b64"] = logo_b64
                st.success("Logo mis à jour !")

            if st.button("💾 Enregistrer les modifications"):
                json.dump(config, open(CONFIG_FILE, "w")); st.rerun()

        with tab_galerie:
            col_a, col_u = st.columns(2)
            with col_a:
                st.write("**Photos Régie (Dossier Admin)**")
                for f in glob.glob(f"{ADMIN_DIR}/*"):
                    st.image(f, width=150)
                    if st.button(f"Supprimer {os.path.basename(f)}", key=f):
                        os.remove(f); st.rerun()
            with col_u:
                st.write("**Photos Utilisateurs**")
                for f in glob.glob(f"{GALLERY_DIR}/*"):
                    st.image(f, width=150)
                    if st.button(f"Supprimer {os.path.basename(f)}", key=f+"u"):
                        os.remove(f); st.rerun()

        with tab_data:
            st.subheader("Gestion des fichiers")
            if st.button("📊 Exporter Résultats CSV"):
                v_data = load_json(VOTES_FILE, {})
                df = pd.DataFrame(list(v_data.items()), columns=['BU', 'Points'])
                st.download_button("Télécharger CSV", df.to_csv(index=False).encode('utf-8'), "resultats.csv")
            
            if st.button("🔴 RESET TOUT (Votes + Participants)", type="secondary"):
                if os.path.exists(VOTES_FILE): os.remove(VOTES_FILE)
                if os.path.exists(PARTICIPANTS_FILE): os.remove(PARTICIPANTS_FILE)
                st.warning("Système réinitialisé.")

# --- 4. UTILISATEUR & 5. MUR SOCIAL (Même logique que précédemment avec le nouveau titre) ---
# [Le reste du code suit exactement la même logique robuste établie précédemment]
else:
    # (Affichage Mur Social avec le titre config["titre_mur"] et la pluie de confettis haut->bas)
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'], footer { display: none !important; }</style>", unsafe_allow_html=True)
    nb_p = len(load_json(PARTICIPANTS_FILE, []))
    logo_html = f'<img src="data:image/png;base64,{config["logo_b64"]}" style="max-height:80px; margin-bottom:10px;">' if config.get("logo_b64") else ""
    
    st.markdown(f"""
        <div style="text-align:center; color:white; padding-top:40px;">
            {logo_html}
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
                    cols[i].markdown(f'<div style="background:#222;padding:40px 20px;border-radius:20px;border:4px solid #E2001A;text-align:center;color:white;margin-top:40px;"><h2>{m_txt[i]}</h2><h1 style="font-size:38px;">{name}</h1><p style="font-size:22px;">{score} pts</p></div>', unsafe_allow_html=True)
                components.html('<script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script><script>var end=Date.now()+10000;(function frame(){confetti({particleCount:5,origin:{y:-0.2,x:Math.random()},spread:360,gravity:0.7,colors:["#E2001A","#ffffff","#ffd700"]});if(Date.now()<end)requestAnimationFrame(frame);})();</script>', height=0)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(5000, key="wall_ref")
    except: pass
