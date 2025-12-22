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
        # --- SESSION & STATS ---
        if st.sidebar.button("🔓 Déconnexion", use_container_width=True):
            st.session_state["auth"] = False
            st.rerun()
        
        nb_p = len(load_json(PARTICIPANTS_FILE, []))
        st.sidebar.info(f"👥 {nb_p} Participants connectés")
        
        # --- APERÇU DU STATUT ---
        st.sidebar.markdown("---")
        st.sidebar.caption("📺 État actuel du Mur :")
        desc = "⏸️ ATTENTE"
        if config["mode_affichage"] == "live": desc = "📸 LIVE PHOTOS"
        if config["mode_affichage"] == "votes":
            desc = "🗳️ VOTE OUVERT" if config["session_ouverte"] else "🏁 FIN DU VOTE"
            if config["reveal_resultats"]: desc = "🏆 PODIUM"
        
        st.sidebar.markdown(f'<div style="background:#333;padding:10px;border-radius:5px;border:1px solid #E2001A;text-align:center;color:white;">{desc}</div>', unsafe_allow_html=True)
        st.sidebar.markdown("---")

        # --- WORKFLOW ÉVÉNEMENT ---
        st.sidebar.subheader("🕹️ Pilotage direct")
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

        st.sidebar.markdown("---")
        config["titre_mur"] = st.sidebar.text_input("Titre du Mur", value=config["titre_mur"])
        if st.sidebar.button("💾 Sauver Titre", use_container_width=True):
            with open(CONFIG_FILE, "w") as f: json.dump(config, f); st.rerun()

        if st.sidebar.button("🔴 RESET COMPLET", type="secondary", use_container_width=True):
            config.update({"vote_version": VOTE_VERSION+1, "session_ouverte": False, "reveal_resultats": False, "mode_affichage": "attente"})
            for f_path, content in [(CONFIG_FILE, config), (VOTES_FILE, {}), (PARTICIPANTS_FILE, [])]:
                with open(f_path, "w") as f: json.dump(content, f)
            st.rerun()

    if st.session_state.get("auth"):
        st.title("📊 Résultats & Export")
        v_data = load_json(VOTES_FILE, {})
        if v_data:
            sorted_v = dict(sorted(v_data.items(), key=lambda x: x[1], reverse=True))
            st.bar_chart(sorted_v)
            df = pd.DataFrame(list(sorted_v.items()), columns=['BU', 'Points'])
            st.download_button("📥 Télécharger CSV", df.to_csv(index=False).encode('utf-8'), f'resultats_v{VOTE_VERSION}.csv', 'text/csv')
        else:
            st.info("Aucun vote pour le moment.")

# --- 4. UTILISATEUR (VOTE) ---
elif est_utilisateur:
    st.markdown("<style>.stApp { background-color: black !important; color: white !important; }</style>", unsafe_allow_html=True)
    st.title("🗳️ Vote Transdev")
    v_key = f"v_{VOTE_VERSION}"
    components.html(f'<script>if(localStorage.getItem("{v_key}")){{ window.parent.postMessage({{type: "streamlit:setComponentValue", value: true, key: "voted"}}, "*"); }}</script>', height=0)

    if st.session_state.get("voted") or st.session_state.get("voted_final"):
        st.balloons(); st.success("✅ Vote enregistré !")
    else:
        if "pseudo" not in st.session_state:
            with st.form("p"):
                name = st.text_input("Prénom / Pseudo :")
                if st.form_submit_button("REJOINDRE"):
                    if name:
                        st.session_state["pseudo"] = name
                        ps = load_json(PARTICIPANTS_FILE, [])
                        if name not in ps: ps.append(name); json.dump(ps, open(PARTICIPANTS_FILE, "w"))
                        st.rerun()
        elif not config["session_ouverte"]:
            st.warning("⌛ En attente de l'ouverture des votes...")
            try: from streamlit_autorefresh import st_autorefresh; st_autorefresh(5000, key="u_ref")
            except: pass
        else:
            opts = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]
            choix = st.multiselect("Top 3 (l'ordre compte) :", opts)
            if len(choix) == 3 and st.button("🚀 VALIDER", use_container_width=True, type="primary"):
                vts = load_json(VOTES_FILE, {})
                for v, pts in zip(choix, [5, 3, 1]): vts[v] = vts.get(v, 0) + pts
                with open(VOTES_FILE, "w") as f: json.dump(vts, f)
                components.html(f'<script>localStorage.setItem("{v_key}", "true"); setTimeout(()=>{{window.parent.location.reload();}}, 300);</script>', height=0)
                st.session_state["voted_final"] = True; st.rerun()

# --- 5. MUR SOCIAL ---
else:
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'], footer { display: none !important; }</style>", unsafe_allow_html=True)
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
    
    nb_p = len(load_json(PARTICIPANTS_FILE, []))
    v_data = load_json(VOTES_FILE, {})

    st.markdown(f'<div style="text-align:center;color:white;"><p style="color:#E2001A;font-size:30px;font-weight:bold;margin:0;">MUR LIVE TRANSDEV</p><div style="background:white;display:inline-block;padding:5px 25px;border-radius:20px;margin:10px 0;color:black;font-weight:bold;">{nb_p} CONNECTÉS</div><h1 style="font-size:50px;margin:0;">{config["titre_mur"]}</h1></div>', unsafe_allow_html=True)

    if config["mode_affichage"] == "attente":
        st.markdown(f'<div style="text-align:center;margin-top:50px;"><img src="data:image/png;base64,{qr_b64}" width="250" style="border:10px solid white;border-radius:15px;"><h2 style="color:white;margin-top:20px;">Scannez pour voter !</h2></div>', unsafe_allow_html=True)
    
    elif config["mode_affichage"] == "votes":
        if config["reveal_resultats"] and v_data:
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)[:3]
            cols = st.columns(3)
            m_txt = ["🥇 1er", "🥈 2ème", "🥉 3ème"]
            for i, (name, score) in enumerate(sorted_v):
                cols[i].markdown(f'<div style="background:#222;padding:20px;border-radius:20px;border:3px solid #E2001A;text-align:center;color:white;"><h2>{m_txt[i]}</h2><h1 style="font-size:35px;">{name}</h1><p>{score} pts</p></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="display:flex;justify-content:center;align-items:center;gap:30px;margin-top:50px;"><img src="data:image/png;base64,{qr_b64}" width="150" style="border:5px solid white;"><div style="background:#E2001A;color:white;padding:20px 40px;border-radius:15px;font-size:40px;font-weight:bold;border:3px solid white;animation:blink 1.5s infinite;">🗳️ À VOS VOTES !</div><img src="data:image/png;base64,{qr_b64}" width="150" style="border:5px solid white;"></div><style>@keyframes blink{{50%{{opacity:0.3;}}}}</style>', unsafe_allow_html=True)
    
    elif config["mode_affichage"] == "live":
        img_list = glob.glob(os.path.join(ADMIN_DIR, "*")) + glob.glob(os.path.join(GALLERY_DIR, "*"))
        if img_list:
            photos_html = "".join([f'<img src="data:image/png;base64,{base64.b64encode(open(p,"rb").read()).decode()}" style="position:absolute;width:250px;border:5px solid white;border-radius:10px;top:{random.randint(10,50)}%;left:{random.randint(5,75)}%;transform:rotate({random.randint(-10,10)}deg);box-shadow:5px 5px 15px rgba(0,0,0,0.5);">' for p in img_list[-12:]])
            components.html(f'<div style="position:relative;width:100%;height:500px;overflow:hidden;">{photos_html}</div>', height=550)
        else:
            st.markdown(f'<div style="text-align:center;margin-top:50px;"><img src="data:image/png;base64,{qr_b64}" width="200" style="border:5px solid white;border-radius:15px;"><h3 style="color:gray;margin-top:20px;">En attente des photos...</h3></div>', unsafe_allow_html=True)

    try: from streamlit_autorefresh import st_autorefresh; st_autorefresh(5000, key="wall_ref")
    except: pass
