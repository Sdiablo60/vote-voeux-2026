import streamlit as st
import os, glob, base64, qrcode, json, random
from io import BytesIO
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Social Wall Master", layout="wide")

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

if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r") as f: 
            config = json.load(f)
            for key, value in default_config.items():
                if key not in config: config[key] = value
    except: config = default_config
else:
    config = default_config

VOTE_VERSION = config.get("vote_version", 1)

# --- 2. NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"

# --- 3. ADMINISTRATION ---
if est_admin:
    st.sidebar.title("🎮 Régie Master")
    if st.sidebar.text_input("Code Admin", type="password") == "ADMIN_LIVE_MASTER":
        st.session_state["auth"] = True
        if st.session_state.get("auth"):
            config["titre_mur"] = st.sidebar.text_input("Titre", value=config["titre_mur"])
            config["session_ouverte"] = st.sidebar.checkbox("📢 Ouvrir les votes", value=config["session_ouverte"])
            config["reveal_resultats"] = st.sidebar.checkbox("🏆 RÉVÉLER LE PODIUM FINAL", value=config["reveal_resultats"])
            modes = ["Attente (Admin)", "Live (Tout)", "Votes (Écran de vote)"]
            sel_mode = st.sidebar.radio("Mode Mur :", modes, index=0 if config["mode_affichage"]=="attente" else (1 if config["mode_affichage"]=="live" else 2))
            config["mode_affichage"] = "attente" if "Attente" in sel_mode else ("live" if "Live" in sel_mode else "votes")
            if st.sidebar.button("🔵 METTRE À JOUR LE MUR", type="primary"):
                with open(CONFIG_FILE, "w") as f: json.dump(config, f); st.rerun()
            if st.sidebar.button("🔴 RESET COMPLET", type="secondary"):
                config.update({"vote_version": VOTE_VERSION+1, "session_ouverte": False, "reveal_resultats": False, "mode_affichage": "attente"})
                with open(CONFIG_FILE, "w") as f: json.dump(config, f)
                with open(VOTES_FILE, "w") as f: json.dump({}, f)
                with open(PARTICIPANTS_FILE, "w") as f: json.dump([], f); st.rerun()
    st.title("📊 Console")
    try:
        v_data = json.load(open(VOTES_FILE))
        st.bar_chart(v_data)
    except: pass

# --- 4. UTILISATEUR (ZÉRO ANGLAIS) ---
elif est_utilisateur:
    st.markdown("<style>.stApp { background-color: black !important; color: white !important; } .stMultiSelect span { color: white !important; }</style>", unsafe_allow_html=True)
    st.title("🗳️ Vote Transdev")
    vote_key = f"transdev_v{VOTE_VERSION}"
    
    components.html(f'<script>if(localStorage.getItem("{vote_key}")){{ window.parent.postMessage({{type: "streamlit:setComponentValue", value: true, key: "voted_check"}}, "*"); }}</script>', height=0)

    if st.session_state.get("voted_final") or st.session_state.get("voted_check"):
        st.balloons(); st.success("✅ Votre Top 3 a été enregistré !")
    else:
        if "user_pseudo" not in st.session_state:
            with st.form("pseudo"):
                p = st.text_input("Votre Prénom / Pseudo :")
                if st.form_submit_button("REJOINDRE"):
                    if p:
                        st.session_state["user_pseudo"] = p
                        parts = json.load(open(PARTICIPANTS_FILE))
                        if p not in parts: parts.append(p); json.dump(parts, open(PARTICIPANTS_FILE, "w"))
                        st.rerun()
        else:
            if not config["session_ouverte"]:
                st.warning("⌛ En attente ouverture des votes...")
                try: from streamlit_autorefresh import st_autorefresh; st_autorefresh(interval=5000, key="m_ref")
                except: pass
            else:
                st.write(f"Bonjour **{st.session_state['user_pseudo']}**")
                options = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]
                
                # Pas de max_selections ici pour éviter le message en anglais
                choix = st.multiselect("Sélectionnez vos 3 vidéos préférées (l'ordre compte) :", options)
                
                if len(choix) > 0:
                    st.markdown("---")
                    labels = ["🥇 **+5 points**", "🥈 **+3 points**", "🥉 **+1 point**"]
                    for i in range(min(len(choix), 3)):
                        st.write(f"{labels[i]} pour : **{choix[i]}**")
                    
                    if len(choix) > 3:
                        st.error(f"⚠️ Trop de choix ! Veuillez en retirer {len(choix)-3}.")
                    st.markdown("---")

                if len(choix) == 3:
                    if st.button("🚀 VALIDER MON VOTE", use_container_width=True, type="primary"):
                        vts = json.load(open(VOTES_FILE))
                        for v, pts in zip(choix[:3], [5, 3, 1]): vts[v] = vts.get(v, 0) + pts
                        with open(VOTES_FILE, "w") as f: json.dump(vts, f)
                        components.html(f'<script>localStorage.setItem("{vote_key}", "true"); setTimeout(() => {{ window.parent.location.reload(); }}, 300);</script>', height=0)
                        st.session_state["voted_final"] = True; st.rerun()
                elif len(choix) > 0 and len(choix) < 3:
                    st.info(f"Encore {3-len(choix)} choix à faire...")

# --- 5. MUR SOCIAL ---
else:
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'], footer { display: none !important; }</style>", unsafe_allow_html=True)
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
    try:
        nb_p = len(json.load(open(PARTICIPANTS_FILE))); v_data = json.load(open(VOTES_FILE))
    except: nb_p = 0; v_data = {}

    st.markdown(f"""<div style="text-align:center;color:white;font-family:sans-serif;padding-top:20px;">
        <p style="color:#E2001A;font-size:30px;font-weight:bold;margin:0;">MUR PHOTO LIVE</p>
        <div style="background:white;display:inline-block;padding:8px 30px;border-radius:25px;margin:15px 0;border:3px solid #E2001A;"><p style="color:black;font-size:26px;font-weight:bold;margin:0;">{nb_p} PARTICIPANTS CONNECTÉS</p></div>
        <h1 style="font-size:58px;margin:0;">{config['titre_mur']}</h1></div>""", unsafe_allow_html=True)

    if not config["session_ouverte"]:
        st.markdown(f"""<div style="display:flex;align-items:center;justify-content:center;gap:30px;margin-top:20px;">
            <div style="background:white;padding:8px;border-radius:10px;"><img src="data:image/png;base64,{qr_b64}" width="110"></div>
            <div style="background:#E2001A;color:white;padding:15px 40px;border-radius:12px;font-size:32px;font-weight:bold;border:3px solid white;animation:blink 1.5s infinite;">⌛ En attente ouverture des votes...</div>
            <div style="background:white;padding:8px;border-radius:10px;"><img src="data:image/png;base64,{qr_b64}" width="110"></div>
        </div><style>@keyframes blink {{ 50% {{ opacity: 0; }} }}</style>""", unsafe_allow_html=True)

    if config["mode_affichage"] == "votes" and config["session_ouverte"]:
        if config["reveal_resultats"] and v_data:
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)[:3]
            cols = st.columns(3)
            medailles = ["🥇 1er", "🥈 2ème", "🥉 3ème"]
            for i, (name, score) in enumerate(sorted_v):
                cols[i].markdown(f"""<div style="background:#222;padding:30px;border-radius:20px;border:4px solid #E2001A;text-align:center;">
                    <h2 style="color:#E2001A;">{medailles[i]}</h2><h1 style="color:white;font-size:40px;">{name}</h1><p style="font-size:25px;color:white;">{score} pts</p></div>""", unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align:center;margin-top:50px;color:white;'><h2>LES VOTES SONT OUVERTS !</h2></div>", unsafe_allow_html=True)
    else:
        img_list = glob.glob(os.path.join(ADMIN_DIR, "*")) + (glob.glob(os.path.join(GALLERY_DIR, "*")) if config["mode_affichage"]=="live" else [])
        if img_list:
            photos_html = "".join([f'<img src="data:image/png;base64,{base64.b64encode(open(p,"rb").read()).decode()}" class="photo" style="width:280px;top:{random.randint(45,75)}%;left:{random.randint(5,85)}%;animation-duration:{random.uniform(10,15)}s;">' for p in img_list[-12:]])
            components.html(f"""<style>.photo {{ position:absolute; border:5px solid white; border-radius:15px; animation:move alternate infinite ease-in-out; box-shadow: 5px 5px 15px rgba(0,0,0,0.5); }} @keyframes move {{ from {{ transform:rotate(-3deg); }} to {{ transform:translate(35px,35px) rotate(3deg); }} }}</style><div style="width:100%; height:450px; position:relative;">{photos_html}</div>""", height=500)

    try: from streamlit_autorefresh import st_autorefresh; st_autorefresh(interval=5000, key="w_ref")
    except: pass
