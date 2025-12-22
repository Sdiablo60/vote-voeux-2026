import streamlit as st
import os, glob, base64, qrcode, json, random, pandas as pd
from io import BytesIO
import streamlit.components.v1 as components
import time
from PIL import Image
from datetime import datetime

# --- 1. CONFIGURATION & FICHIERS ---
st.set_page_config(page_title="Régie Master - Pôle Aéroportuaire", layout="wide")

# DOSSIERS
GALLERY_DIR = "galerie_images"       # Images importées par les participants (ancien code, gardé par sécu)
ADMIN_DIR = "galerie_admin"          # Images système (Logos, etc)
LIVE_DIR = "galerie_live_users"      # NOUVEAU : Photos prises en direct

# FICHIERS DE DONNÉES
VOTES_FILE = "votes.json"
PARTICIPANTS_FILE = "participants.json"
CONFIG_FILE = "config_mur.json"
VOTERS_FILE = "voters.json"

# Création des dossiers manquants
for d in [GALLERY_DIR, ADMIN_DIR, LIVE_DIR]:
    if not os.path.exists(d): os.makedirs(d)

DEFAULT_CANDIDATS = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]

default_config = {
    "mode_affichage": "attente", 
    "titre_mur": "CONCOURS VIDÉO PÔLE AEROPORTUAIRE", 
    "session_ouverte": False, 
    "reveal_resultats": False,
    "timestamp_podium": 0,
    "logo_b64": None,
    "candidats": DEFAULT_CANDIDATS,
    "candidats_images": {}, 
    "points_ponderation": [5, 3, 1]
}

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r") as f: return json.load(f)
        except: return default
    return default

# --- GESTION ÉTAT SESSION ---
if "config" not in st.session_state:
    st.session_state.config = load_json(CONFIG_FILE, default_config)

# Sécurités structure
if "candidats" not in st.session_state.config: st.session_state.config["candidats"] = DEFAULT_CANDIDATS
if "candidats_images" not in st.session_state.config: st.session_state.config["candidats_images"] = {}
if "points_ponderation" not in st.session_state.config: st.session_state.config["points_ponderation"] = [5, 3, 1]

BADGE_CSS = "margin-top:20px; background:#E2001A; display:inline-block; padding:10px 30px; border-radius:10px; font-size:22px; font-weight:bold; border:2px solid white; color:white;"

# --- FONCTIONS CRITIQUES ---

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(st.session_state.config, f)

def process_image_upload(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        if img.mode != "RGBA": img = img.convert("RGBA")
        img.thumbnail((300, 300))
        buffered = BytesIO()
        img.save(buffered, format="PNG") 
        return base64.b64encode(buffered.getvalue()).decode()
    except: return None

def save_live_photo(uploaded_file):
    """Sauvegarde une photo prise en direct"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"live_{timestamp}_{random.randint(100,999)}.jpg"
        filepath = os.path.join(LIVE_DIR, filename)
        
        img = Image.open(uploaded_file)
        # Orientation fix pour mobile souvent nécessaire, ici on fait simple : convert RGB et save
        img = img.convert("RGB")
        # Compression pour fluidité mur
        img.thumbnail((500, 500)) 
        img.save(filepath, "JPEG", quality=80)
        return True
    except Exception as e:
        print(e)
        return False

# --- 2. NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"

# --- 3. ADMINISTRATION ---
if est_admin:
    if "auth" not in st.session_state: st.session_state["auth"] = False
    
    if not st.session_state["auth"]:
        st.markdown("<br><br><h1 style='text-align:center;'>🔐 ACCÈS RÉGIE</h1>", unsafe_allow_html=True)
        col_c, col_p, col_d = st.columns([1,2,1])
        with col_p:
            pwd = st.text_input("Mot de passe", type="password")
            if pwd == "ADMIN_LIVE_MASTER":
                st.session_state["auth"] = True
                st.rerun()
    else:
        with st.sidebar:
            st.title("🎛️ RÉGIE MASTER")
            st.markdown("---")
            menu = st.radio("Navigation :", ["🔴 PILOTAGE LIVE", "⚙️ Paramétrage", "📸 Médiathèque", "📊 Data & Exports"], label_visibility="collapsed")
            st.markdown("---")
            if st.button("🔓 Déconnexion", use_container_width=True):
                st.session_state["auth"] = False
                st.rerun()

        # --- CONTENU ---
        if menu == "🔴 PILOTAGE LIVE":
            st.title("🔴 COCKPIT LIVE")
            
            # --- SÉQUENCEUR ---
            st.subheader("1️⃣ Séquenceur")
            
            # Ligne 1 : Les modes classiques
            c1, c2, c3, c4 = st.columns(4)
            cfg = st.session_state.config
            m, vo, re = cfg["mode_affichage"], cfg["session_ouverte"], cfg["reveal_resultats"]

            if c1.button("1. ACCUEIL", use_container_width=True, type="primary" if m=="attente" else "secondary"):
                cfg.update({"mode_affichage": "attente", "session_ouverte": False, "reveal_resultats": False}); save_config(); st.rerun()
            if c2.button("2. VOTES ON", use_container_width=True, type="primary" if (m=="votes" and vo) else "secondary"):
                cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False}); save_config(); st.rerun()
            if c3.button("3. VOTES OFF", use_container_width=True, type="primary" if (m=="votes" and not vo and not re) else "secondary"):
                cfg.update({"session_ouverte": False}); save_config(); st.rerun()
            if c4.button("4. PODIUM", use_container_width=True, type="primary" if re else "secondary"):
                cfg.update({"mode_affichage": "votes", "reveal_resultats": True, "session_ouverte": False, "timestamp_podium": time.time()}); save_config(); st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            
            # Ligne 2 : LE NOUVEAU MODE PHOTO
            c_live, c_vide = st.columns([1, 3])
            with c_live:
                if st.button("5. 📸 MUR PHOTOS LIVE", use_container_width=True, type="primary" if m=="photos_live" else "secondary"):
                    cfg.update({"mode_affichage": "photos_live", "session_ouverte": False, "reveal_resultats": False})
                    save_config()
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("🗑️ OPTIONS DE RÉINITIALISATION (Zone de danger)"):
                col_rst, col_info = st.columns([1, 2])
                with col_rst:
                    if st.button("♻️ VIDER LES VOTES", use_container_width=True, help="Remet tout à 0 (Scores, Participants, Votants)"):
                        for f in [VOTES_FILE, PARTICIPANTS_FILE, VOTERS_FILE]:
                            if os.path.exists(f): os.remove(f)
                        st.toast("✅ Session entièrement réinitialisée !")
                        time.sleep(1); st.rerun()
                    
                    if st.button("🗑️ VIDER PHOTOS LIVE", use_container_width=True):
                        files = glob.glob(f"{LIVE_DIR}/*")
                        for f in files: os.remove(f)
                        st.toast("✅ Galerie Live vidée !")
                        time.sleep(1); st.rerun()

                with col_info:
                    st.info("Efface les scores, compteurs ou les photos prises en direct.")

            st.markdown("---")
            st.subheader("2️⃣ Monitoring")
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                valid = {k:v for k,v in v_data.items() if k in cfg["candidats"]}
                if valid:
                    import altair as alt
                    df = pd.DataFrame(list(valid.items()), columns=['Candidat', 'Points'])
                    df = df.sort_values('Points', ascending=False).reset_index(drop=True)
                    df['Rang'] = df.index + 1
                    
                    def get_color(rank):
                        if rank == 1: return '#FFD700'
                        if rank == 2: return '#C0C0C0'
                        if rank == 3: return '#CD7F32'
                        return '#E2001A'
                    
                    df['Color'] = df['Rang'].apply(get_color)

                    base = alt.Chart(df).encode(
                        x=alt.X('Points', axis=None),
                        y=alt.Y('Candidat', sort='-x', axis=alt.Axis(labelFontSize=14, title=None))
                    )
                    bars = base.mark_bar().encode(color=alt.Color('Color', scale=None))
                    text = base.mark_text(align='left', baseline='middle', dx=3).encode(text='Points')
                    st.altair_chart((bars + text).properties(height=500).configure_view(strokeWidth=0), use_container_width=True)
                else: st.info("Aucun vote actif.")
            else: st.info("En attente de votes...")

        elif menu == "⚙️ Paramétrage":
            st.title("⚙️ Paramétrage")
            t1, t2 = st.tabs(["Identité", "Gestion Questions"])
            
            with t1:
                new_t = st.text_input("Titre", value=st.session_state.config["titre_mur"])
                if st.button("Sauver Titre"):
                    st.session_state.config["titre_mur"] = new_t; save_config(); st.success("Enregistré !")
                
                up_l = st.file_uploader("Logo", type=["png", "jpg"])
                if up_l:
                    b64 = process_image_upload(up_l)
                    if b64:
                        st.session_state.config["logo_b64"] = b64; save_config(); st.success("Logo chargé !"); st.rerun()
                
                if st.session_state.config.get("logo_b64"):
                    st.markdown(f'<img src="data:image/png;base64,{st.session_state.config["logo_b64"]}" width="150" style="background:gray; padding:10px;">', unsafe_allow_html=True)

            with t2:
                st.subheader("📋 Liste des Questions")
                df_cands = pd.DataFrame(st.session_state.config["candidats"], columns=["Nom du Candidat"])
                edited_df = st.data_editor(df_cands, num_rows="dynamic", use_container_width=True)

                if st.button("💾 ENREGISTRER LISTE", type="primary"):
                    new_list = [x for x in edited_df["Nom du Candidat"].astype(str).tolist() if x.strip() != ""]
                    st.session_state.config["candidats"] = new_list
                    save_config(); st.success("Mise à jour !"); time.sleep(1); st.rerun()

                st.markdown("---")
                st.subheader("🖼️ Photos Questions")
                if st.session_state.config["candidats"]:
                    sel = st.selectbox("Candidat :", st.session_state.config["candidats"])
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        if sel in st.session_state.config["candidats_images"]:
                            st.image(BytesIO(base64.b64decode(st.session_state.config["candidats_images"][sel])), width=100)
                            if st.button("Supprimer"):
                                del st.session_state.config["candidats_images"][sel]; save_config(); st.rerun()
                        else: st.info("Aucune image")
                    with c2:
                        up = st.file_uploader(f"Image pour {sel}", type=["png", "jpg"])
                        if up:
                            b64 = process_image_upload(up)
                            if b64:
                                st.session_state.config["candidats_images"][sel] = b64; save_config(); st.rerun()

        elif menu == "📸 Médiathèque":
            st.title("📸 Médiathèque")
            # AJOUT DU TAB POUR LES PHOTOS LIVE
            t_adm, t_live, t_old = st.tabs(["📂 Admin (Logos)", "🔴 Photos Live Users", "📂 Uploads Vrac"])
            
            with t_adm:
                up_sys = st.file_uploader("Ajout Admin", type=['png', 'jpg'], key="up_sys")
                if up_sys:
                    with open(os.path.join(ADMIN_DIR, up_sys.name), "wb") as f: f.write(up_sys.getbuffer())
                    st.rerun()
                files = glob.glob(f"{ADMIN_DIR}/*")
                if files:
                    cols = st.columns(5)
                    for i, f in enumerate(files):
                        with cols[i%5]:
                            st.image(f, use_container_width=True)
                            if st.button("🗑️", key=f"da_{i}"): os.remove(f); st.rerun()
            
            with t_live:
                st.info("Photos prises par les utilisateurs en mode 'Mur Photos Live'.")
                files = glob.glob(f"{LIVE_DIR}/*")
                # Tri par date décroissante (plus récent en premier)
                files.sort(key=os.path.getmtime, reverse=True)
                
                if files:
                    cols = st.columns(5)
                    for i, f in enumerate(files):
                        with cols[i%5]:
                            st.image(f, use_container_width=True)
                            if st.button("🗑️", key=f"dl_{i}"): os.remove(f); st.rerun()
                else: st.write("Aucune photo live pour le moment.")

            with t_old:
                files = glob.glob(f"{GALLERY_DIR}/*")
                if files:
                    cols = st.columns(5)
                    for i, f in enumerate(files):
                        with cols[i%5]:
                            st.image(f, use_container_width=True)
                            if st.button("🗑️", key=f"do_{i}"): os.remove(f); st.rerun()

        elif menu == "📊 Data & Exports":
            if st.button("RESET TOUT"):
                 for f in [VOTES_FILE, PARTICIPANTS_FILE, VOTERS_FILE]:
                     if os.path.exists(f): os.remove(f)
                 files = glob.glob(f"{LIVE_DIR}/*")
                 for f in files: os.remove(f)
                 st.success("Reset complet !"); st.rerun()

# --- 4. UTILISATEUR (MOBILE) ---
elif est_utilisateur:
    st.markdown("<style>.stApp { background-color: black !important; color: white !important; }</style>", unsafe_allow_html=True)
    cfg = load_json(CONFIG_FILE, default_config)
    
    # Logo
    if cfg.get("logo_b64"):
        st.markdown(f"""<div style="text-align:center; margin-bottom:20px; background:transparent;"><img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:80px; width:auto; background:transparent;"></div>""", unsafe_allow_html=True)
    
    # Enregistrement présence
    if "participant_recorded" not in st.session_state:
        parts = load_json(PARTICIPANTS_FILE, [])
        parts.append(time.time())
        with open(PARTICIPANTS_FILE, "w") as f: json.dump(parts, f)
        st.session_state["participant_recorded"] = True

    # --- MODE PHOTOS LIVE ---
    if cfg["mode_affichage"] == "photos_live":
        st.title("📸 Mode Photo")
        st.info("Prenez une photo, elle apparaîtra sur l'écran géant !")
        
        # Widget Caméra
        photo = st.camera_input("Prendre une photo")
        
        if photo:
            if save_live_photo(photo):
                st.balloons()
                st.success("Envoyé sur le mur ! 🚀")
                time.sleep(2)
                # On ne rerun pas forcément pour laisser l'utilisateur en reprendre une autre
            else:
                st.error("Erreur lors de l'envoi.")

    # --- MODE VOTE ---
    else:
        st.title("🗳️ Vote Transdev")
        
        if "user_id" not in st.session_state: st.session_state.user_id = None

        if not st.session_state.user_id:
            nom = st.text_input("Votre Nom / Matricule :")
            if st.button("Commencer"):
                if len(nom) > 2:
                    clean_id = nom.strip().lower()
                    voters = load_json(VOTERS_FILE, [])
                    if clean_id in voters: st.error("Déjà voté.")
                    else: st.session_state.user_id = clean_id; st.rerun()
                else: st.warning("Nom invalide.")
        else:
            if st.session_state.get("a_vote", False):
                st.balloons()
                st.markdown("""<div style="text-align:center; padding-top:50px;"><div style="font-size:80px;">👏</div><h1 style="color:#E2001A;">MERCI !</h1></div>""", unsafe_allow_html=True)
            elif not cfg["session_ouverte"]: 
                st.warning("⌛ Votes clos ou attente.")
            else:
                choix = st.multiselect("Top 3 :", cfg["candidats"])
                if len(choix) == 3 and st.button("VALIDER"):
                    vts = load_json(VOTES_FILE, {})
                    pts = cfg.get("points_ponderation", [5, 3, 1])
                    for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                    json.dump(vts, open(VOTES_FILE, "w"))
                    voters = load_json(VOTERS_FILE, [])
                    voters.append(st.session_state.user_id)
                    with open(VOTERS_FILE, "w") as f: json.dump(voters, f)
                    st.session_state["a_vote"] = True; st.rerun()
                elif len(choix) > 3: st.error("Max 3 !")

# --- 5. MUR SOCIAL ---
else:
    # CSS GLOBAL
    st.markdown("""
    <style>
        body, .stApp { background-color: black !important; } 
        [data-testid='stHeader'], footer { display: none !important; } 
        .block-container { padding-top: 2rem !important; }
        img { background-color: transparent !important; }
        
        /* Animation Bulles */
        @keyframes float {
            0% { transform: translateY(0px); opacity: 0; }
            10% { opacity: 1; }
            50% { transform: translateY(-20px); }
            100% { transform: translateY(0px); opacity: 1; }
        }
        .photo-bubble {
            border-radius: 50%;
            object-fit: cover;
            border: 4px solid #E2001A;
            box-shadow: 0 0 15px rgba(226, 0, 26, 0.5);
            animation: float 6s ease-in-out infinite;
            margin: 10px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    config = load_json(CONFIG_FILE, default_config)
    nb_p = len(load_json(PARTICIPANTS_FILE, []))
    
    # LOGO
    logo_html = ""
    if config.get("logo_b64"): 
        logo_html = f'<img src="data:image/png;base64,{config["logo_b64"]}" style="max-height:100px; margin-bottom:15px; display:block; margin-left:auto; margin-right:auto; background:transparent;">'

    # HEADER
    st.markdown(f"""
    <div style="text-align:center; color:white; background:transparent;">
    {logo_html}
    <h1 style="font-size:55px; font-weight:bold; text-transform:uppercase; margin:0; line-height:1.1;">{config["titre_mur"]}</h1>
    </div>
    """, unsafe_allow_html=True)

    # --- MODES D'AFFICHAGE ---
    
    # 1. ATTENTE
    if config["mode_affichage"] == "attente":
        st.markdown(f"""
        <div style="text-align:center; color:white; margin-top:80px;">
            <div style="{BADGE_CSS}">✨ BIENVENUE ✨</div>
            <h2 style="font-size:50px; margin-top:40px; font-weight:lighter;">L'événement va commencer...</h2>
        </div>
        """, unsafe_allow_html=True)

    # 2. PHOTOS LIVE (NOUVEAU MODE)
    elif config["mode_affichage"] == "photos_live":
        # QR Code pour rejoindre
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

        st.markdown(f'<div style="text-align:center;"><div style="{BADGE_CSS}">📸 MUR LIVE</div></div>', unsafe_allow_html=True)
        
        # Zone centrale (QR Code)
        st.markdown(f"""
        <div style="position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); z-index:100; text-align:center;">
            <div style="background:white; padding:10px; border-radius:15px; box-shadow: 0 0 50px rgba(255,255,255,0.2);">
                <img src="data:image/png;base64,{qr_b64}" width="200" style="display:block;">
                <p style="color:black; font-weight:bold; margin:0; font-size:20px;">PARTICIPEZ !</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Affichage des bulles
        photos = glob.glob(f"{LIVE_DIR}/*")
        # On prend les 20 dernières pour ne pas surcharger
        photos.sort(key=os.path.getmtime, reverse=True)
        recent_photos = photos[:24]

        if recent_photos:
            # Layout Masonry manuel en colonnes
            cols = st.columns(6)
            for i, photo_path in enumerate(recent_photos):
                with cols[i % 6]:
                    # Lecture image pour base64
                    with open(photo_path, "rb") as f:
                        b64_img = base64.b64encode(f.read()).decode()
                    # Affichage HTML rond
                    st.markdown(f"""
                    <img src="data:image/jpeg;base64,{b64_img}" class="photo-bubble" style="width:100%; aspect-ratio:1/1;">
                    """, unsafe_allow_html=True)

    # 3. VOTES
    elif config["mode_affichage"] == "votes" and not config["reveal_resultats"]:
        # Compteur visible ici
        st.markdown(f'<div style="text-align:center; margin-top:10px;"><div style="background:white; display:inline-block; padding:5px 20px; border-radius:20px; color:black; font-weight:bold;">👥 {nb_p} CONNECTÉS</div></div>', unsafe_allow_html=True)
        
        if config["session_ouverte"]:
            host = st.context.headers.get('host', 'localhost')
            qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            
            st.markdown(f'<div style="text-align:center;"><div style="{BADGE_CSS} animation:blink 1.5s infinite;">🚀 VOTES OUVERTS</div></div><style>@keyframes blink{{50%{{opacity:0.5;}}}}</style>', unsafe_allow_html=True)
            
            cands = config["candidats"]
            mid = (len(cands) + 1) // 2
            
            def get_html(lbl):
                img = '<span style="font-size:30px; margin-right:15px;">🎥</span>'
                if lbl in config.get("candidats_images", {}):
                    b64 = config["candidats_images"][lbl]
                    img = f'<img src="data:image/png;base64,{b64}" style="width:60px; height:60px; object-fit:cover; border-radius:10px; margin-right:15px; border:2px solid #E2001A;">'
                return f'<div style="background:#222; color:white; padding:10px; margin-bottom:12px; border-left:6px solid #E2001A; font-weight:bold; font-size:22px; display:flex; align-items:center;">{img}{lbl}</div>'

            st.markdown("<div style='margin-top:40px;'>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 0.7, 1])
            with c1:
                for c in cands[:mid]: st.markdown(get_html(c), unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div style="background:white; padding:4px; border-radius:10px; text-align:center; margin: 0 auto; width: fit-content;"><img src="data:image/png;base64,{qr_b64}" width="180" style="display:block;"><p style="color:black; font-weight:bold; margin-top:5px; margin-bottom:0; font-size:14px;">SCANNEZ</p></div>', unsafe_allow_html=True)
            with c3:
                for c in cands[mid:]: st.markdown(get_html(c), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            components.html(f"""<div style="text-align:center;color:white;background:black;height:100vh;"><div style="{BADGE_CSS} background:#333;">🏁 CLOS</div><div style="font-size:100px;margin-top:40px;">👏</div><h1 style="color:#E2001A;">MERCI !</h1></div>""", height=600)

    # 4. PODIUM
    elif config["reveal_resultats"]:
        diff = 10 - int(time.time() - config.get("timestamp_podium", 0))
        if diff > 0:
            st.markdown(f"""<div style="text-align:center; margin-top:80px;"><div style="font-size:250px; color:#E2001A; font-weight:bold;">{diff}</div></div>""", unsafe_allow_html=True)
            time.sleep(0.5); st.rerun()
        else:
            v_data = load_json(VOTES_FILE, {})
            valid = {k:v for k,v in v_data.items() if k in config["candidats"]}
            sorted_v = sorted(valid.items(), key=lambda x: x[1], reverse=True)[:3]
            st.markdown(f'<div style="text-align:center;"><div style="{BADGE_CSS}">🏆 PODIUM</div></div>', unsafe_allow_html=True)
            cols = st.columns(3)
            colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
            ranks = ["🥇", "🥈", "🥉"]
            for i, (name, score) in enumerate(sorted_v):
                img_p = ""
                if name in config.get("candidats_images", {}):
                     img_p = f'<img src="data:image/png;base64,{config["candidats_images"][name]}" style="width:120px; height:120px; border-radius:50%; border:4px solid {colors[i]}; display:block; margin:0 auto 15px auto;">'
                cols[i].markdown(f"""<div style="background:#1a1a1a; padding:30px; border:4px solid {colors[i]}; text-align:center; color:white; margin-top:30px; border-radius:20px;"><h2>{ranks[i]}</h2>{img_p}<h1>{name}</h1><p>{score} pts</p></div>""", unsafe_allow_html=True)
            components.html('<script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script><script>confetti({particleCount:100,spread:70,origin:{y:0.6}});</script>', height=0)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(5000, key="wall_ref")
    except: pass
