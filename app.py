import streamlit as st
import os, glob, base64, qrcode, json, random
from io import BytesIO
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Social Wall Pro", layout="wide")

GALLERY_DIR, ADMIN_DIR = "galerie_images", "galerie_admin"
VOTES_FILE, PARTICIPANTS_FILE, CONFIG_FILE = "votes.json", "participants.json", "config_mur.json"
LOGO_FILE = "logo_entreprise.png"

for d in [GALLERY_DIR, ADMIN_DIR]:
    if not os.path.exists(d): os.makedirs(d)

config = {"mode_affichage": "attente", "titre_mur": "CONCOURS VIDÉO 2026", "vote_version": 1, "session_ouverte": False, "reveal_resultats": False}
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r") as f: config = json.load(f)
    except: pass

VOTE_VERSION = config.get("vote_version", 1)
if not os.path.exists(VOTES_FILE): json.dump({}, open(VOTES_FILE, "w"))
if not os.path.exists(PARTICIPANTS_FILE): json.dump([], open(PARTICIPANTS_FILE, "w"))

# --- 2. NAVIGATION ---
query_params = st.query_params
est_admin = query_params.get("admin") == "true"
est_utilisateur = query_params.get("mode") == "vote"

# --- 3. ADMINISTRATION ---
if est_admin:
    st.sidebar.title("🎮 Régie Master")
    if st.sidebar.text_input("Code Admin", type="password") == "ADMIN_LIVE_MASTER":
        st.session_state["auth"] = True
        if st.session_state.get("auth"):
            config["titre_mur"] = st.sidebar.text_input("Titre", value=config["titre_mur"])
            config["session_ouverte"] = st.sidebar.checkbox("📢 Ouvrir les votes", value=config["session_ouverte"])
            config["reveal_resultats"] = st.sidebar.checkbox("🏆 RÉVÉLER LE PODIUM (TOP 3)", value=config["reveal_resultats"])
            
            modes = ["Attente (Admin)", "Live (Tout)", "Votes (Noms seuls)"]
            sel_mode = st.sidebar.radio("Mode Mur :", modes, index=0 if config["mode_affichage"]=="attente" else (1 if config["mode_affichage"]=="live" else 2))
            config["mode_affichage"] = "attente" if "Attente" in sel_mode else ("live" if "Live" in sel_mode else "votes")

            if st.sidebar.button("🔵 METTRE À JOUR LE MUR", type="primary", use_container_width=True):
                with open(CONFIG_FILE, "w") as f: json.dump(config, f)
                st.rerun()
            
            if st.sidebar.button("🔴 RESET COMPLET", type="secondary", use_container_width=True):
                config.update({"vote_version": VOTE_VERSION+1, "session_ouverte": False, "reveal_resultats": False, "mode_affichage": "attente"})
                with open(CONFIG_FILE, "w") as f: json.dump(config, f)
                json.dump({}, open(VOTES_FILE, "w")); json.dump([], open(PARTICIPANTS_FILE, "w"))
                st.rerun()
    
    st.title("Console de Suivi")
    col1, col2 = st.columns(2)
    col1.metric("Participants", len(json.load(open(PARTICIPANTS_FILE))))
    st.write("Scores actuels (Points pondérés) :", json.load(open(VOTES_FILE)))

# --- 4. UTILISATEUR (VOTE PONDÉRÉ) ---
elif est_utilisateur:
    st.markdown("<style>.stApp { background-color: black !important; color: white !important; }</style>", unsafe_allow_html=True)
    st.title("🗳️ Vote Transdev")
    vote_key = f"transdev_v{VOTE_VERSION}"
    components.html(f'<script>if(localStorage.getItem("{vote_key}")){{window.parent.postMessage({{type:"voted"}},"*");}}</script>', height=0)

    if st.session_state.get("voted"):
        st.success("✅ Vote enregistré. Merci !")
    else:
        if "user_pseudo" not in st.session_state:
            with st.form("pseudo_form"):
                p = st.text_input("Votre Pseudo / Prénom :")
                if st.form_submit_button("VALIDER"):
                    if p:
                        st.session_state["user_pseudo"] = p
                        parts = json.load(open(PARTICIPANTS_FILE))
                        if p not in parts: parts.append(p); json.dump(parts, open(PARTICIPANTS_FILE, "w"))
                        st.rerun()
        else:
            if not config["session_ouverte"]:
                st.warning("⌛ En attente ouverture des votes...")
                try:
                    from streamlit_autorefresh import st_autorefresh
                    st_autorefresh(interval=5000, key="mobile_refresh")
                except: pass
            else:
                st.write(f"Classez vos 3 vidéos préférées, {st.session_state['user_pseudo']} :")
                options = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]
                with st.form("vote_pondere"):
                    v1 = st.selectbox("Choix 1 (5 pts) :", [""] + options)
                    v2 = st.selectbox("Choix 2 (3 pts) :", [""] + [o for o in options if o != v1])
                    v3 = st.selectbox("Choix 3 (1 pt) :", [""] + [o for o in options if o not in [v1, v2]])
                    if st.form_submit_button("VALIDER MON TOP 3"):
                        if v1 and v2 and v3:
                            vts = json.load(open(VOTES_FILE))
                            for v, pts in zip([v1, v2, v3], [5, 3, 1]):
                                vts[v] = vts.get(v, 0) + pts
                            json.dump(vts, open(VOTES_FILE, "w"))
                            components.html(f'<script>localStorage.setItem("{vote_key}", "true"); window.parent.location.reload();</script>', height=0)
                            st.session_state["voted"] = True
                            st.rerun()
                        else: st.error("Sélectionnez 3 vidéos différentes.")

# --- 5. MUR SOCIAL (REVEAL & PONDÉRATION) ---
else:
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'], footer { display: none !important; }</style>", unsafe_allow_html=True)
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
    nb_p = len(json.load(open(PARTICIPANTS_FILE)))
    v_data = json.load(open(VOTES_FILE))

    # HEADER
    attente_html = f"""<div style="display:flex;align-items:center;justify-content:center;gap:30px;margin-top:20px;">
        <div style="background:white;padding:8px;border-radius:10px;"><img src="data:image/png;base64,{qr_b64}" width="100"></div>
        <div style="background:#E2001A;color:white;padding:15px 30px;border-radius:12px;font-size:30px;font-weight:bold;border:3px solid white;animation:blink 1.5s infinite;">⌛ En attente ouverture des votes...</div>
        <div style="background:white;padding:8px;border-radius:10px;"><img src="data:image/png;base64,{qr_b64}" width="100"></div>
    </div><style>@keyframes blink {{ 50% {{ opacity: 0; }} }}</style>""" if not config["session_ouverte"] else ""

    st.markdown(f"""<div style="text-align:center;color:white;font-family:sans-serif;padding-top:20px;">
        <p style="color:#E2001A;font-size:30px;font-weight:bold;margin:0;">MUR PHOTO LIVE</p>
        <div style="background:white;display:inline-block;padding:5px 20px;border-radius:20px;margin:10px 0;"><p style="color:black;font-size:22px;font-weight:bold;margin:0;">{nb_p} PARTICIPANTS CONNECTÉS</p></div>
        <h1 style="font-size:55px;margin:0;">{config['titre_mur']}</h1>{attente_html}</div>""", unsafe_allow_html=True)

    # CONTENU DYNAMIQUE
    if config["mode_affichage"] == "votes":
        if config["reveal_resultats"]:
            # TRI ET RÉVÉLATION DU TOP 3
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)[:3]
            st.markdown("<div style='text-align:center;margin-top:40px;'>", unsafe_allow_html=True)
            cols = st.columns(3)
            medailles = ["🥇 1er", "🥈 2ème", "🥉 3ème"]
            for i, (name, score) in enumerate(sorted_v):
                cols[i].markdown(f"""<div style="background:#222;padding:30px;border-radius:20px;border:4px solid #E2001A;text-align:center;">
                    <h2 style="color:#E2001A;">{medailles[i]}</h2><h1 style="color:white;font-size:40px;">{name}</h1><p style="font-size:25px;color:white;">{score} points</p></div>""", unsafe_allow_html=True)
        else:
            # MODE VOTE EN COURS : NOMS SEULS
            st.markdown("<div style='text-align:center;margin-top:50px;color:white;'><h2>LES VOTES SONT OUVERTS !</h2><p>Le podium sera révélé bientôt...</p></div>", unsafe_allow_html=True)
            st.write(", ".join(v_data.keys()) if v_data else "En attente des premiers votes...")
    else:
        # PHOTOS
        img_list = glob.glob(os.path.join(ADMIN_DIR, "*")) + (glob.glob(os.path.join(GALLERY_DIR, "*")) if config["mode_affichage"]=="live" else [])
        photos_html = "".join([f'<img src="data:image/png;base64,{base64.b64encode(open(p,"rb").read()).decode()}" class="photo" style="width:260px;top:{random.randint(40,75)}%;left:{random.randint(5,85)}%;animation-duration:{random.uniform(10,15)}s;">' for p in img_list[-12:]])
        components.html(f"""<style>.photo {{ position:absolute; border:5px solid white; border-radius:15px; animation:move alternate infinite ease-in-out; }} @keyframes move {{ from {{ transform:rotate(-3deg); }} to {{ transform:translate(30px,30px) rotate(3deg); }} }}</style><div style="width:100%; height:450px; position:relative;">{photos_html}</div>""", height=500)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=5000, key="wall_refresh")
    except: pass
