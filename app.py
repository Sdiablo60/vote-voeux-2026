import streamlit as st
import os, glob, base64, qrcode, json, random, pandas as pd
from io import BytesIO
import streamlit.components.v1 as components
import time
from PIL import Image
from datetime import datetime
import zipfile

# --- 1. CONFIGURATION & FICHIERS ---
st.set_page_config(page_title="Régie Master - Pôle Aéroportuaire", layout="wide")

GALLERY_DIR, ADMIN_DIR = "galerie_images", "galerie_admin"
LIVE_DIR = "galerie_live_users"
VOTES_FILE, PARTICIPANTS_FILE, CONFIG_FILE, VOTERS_FILE = "votes.json", "participants.json", "config_mur.json", "voters.json"

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

if "refresh_id" not in st.session_state: st.session_state.refresh_id = 0
if "cam_reset_id" not in st.session_state: st.session_state.cam_reset_id = 0

# Sécurités structure
if "candidats" not in st.session_state.config: st.session_state.config["candidats"] = DEFAULT_CANDIDATS
if "candidats_images" not in st.session_state.config: st.session_state.config["candidats_images"] = {}
if "points_ponderation" not in st.session_state.config: st.session_state.config["points_ponderation"] = [5, 3, 1]

BADGE_CSS = "margin-top:20px; background:#E2001A; display:inline-block; padding:10px 30px; border-radius:10px; font-size:22px; font-weight:bold; border:2px solid white; color:white;"

# --- FONCTIONS CRITIQUES ---

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(st.session_state.config, f)

def force_refresh():
    st.session_state.refresh_id += 1
    save_config()

def process_image_upload(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        if img.mode != "RGBA": img = img.convert("RGBA")
        img.thumbnail((300, 300))
        buffered = BytesIO()
        img.save(buffered, format="PNG") 
        return base64.b64encode(buffered.getvalue()).decode().replace('\n', '')
    except: return None

def save_live_photo(uploaded_file):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"live_{timestamp}_{random.randint(100,999)}.jpg"
        filepath = os.path.join(LIVE_DIR, filename)
        
        img = Image.open(uploaded_file)
        try: # Rotation EXIF
            from PIL import ExifTags
            if hasattr(img, '_getexif'):
                exif = img._getexif()
                if exif:
                    for orientation in ExifTags.TAGS.keys():
                        if ExifTags.TAGS[orientation] == 'Orientation': break
                    if exif.get(orientation) == 3: img = img.rotate(180, expand=True)
                    elif exif.get(orientation) == 6: img = img.rotate(270, expand=True)
                    elif exif.get(orientation) == 8: img = img.rotate(90, expand=True)
        except: pass

        img = img.convert("RGB")
        img.thumbnail((500, 500)) 
        img.save(filepath, "JPEG", quality=85)
        return True
    except Exception as e:
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
            menu = st.radio("Navigation :", ["🔴 PILOTAGE LIVE", "⚙️ Paramétrage", "📸 Médiathèque (Export)", "📊 Data & Exports"], label_visibility="collapsed")
            st.markdown("---")
            if st.button("🔓 Déconnexion", use_container_width=True):
                st.session_state["auth"] = False
                st.rerun()

        # --- CONTENU ---
        if menu == "🔴 PILOTAGE LIVE":
            st.title("🔴 COCKPIT LIVE")
            
            st.subheader("1️⃣ Séquenceur")
            c1, c2, c3, c4 = st.columns(4)
            cfg = st.session_state.config
            m, vo, re = cfg["mode_affichage"], cfg["session_ouverte"], cfg["reveal_resultats"]

            if c1.button("1. ACCUEIL", use_container_width=True, type="primary" if m=="attente" else "secondary"):
                cfg.update({"mode_affichage": "attente", "session_ouverte": False, "reveal_resultats": False}); force_refresh(); st.rerun()
            if c2.button("2. VOTES ON", use_container_width=True, type="primary" if (m=="votes" and vo) else "secondary"):
                cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False}); force_refresh(); st.rerun()
            if c3.button("3. VOTES OFF", use_container_width=True, type="primary" if (m=="votes" and not vo and not re) else "secondary"):
                cfg.update({"session_ouverte": False}); force_refresh(); st.rerun()
            if c4.button("4. PODIUM", use_container_width=True, type="primary" if re else "secondary"):
                cfg.update({"mode_affichage": "votes", "reveal_resultats": True, "session_ouverte": False, "timestamp_podium": time.time()}); force_refresh(); st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
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
                    if st.button("♻️ VIDER LES VOTES", use_container_width=True, help="Remet tout à 0"):
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
                    st.info("Efface les scores ou les photos live.")

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
                    base = alt.Chart(df).encode(x=alt.X('Points', axis=None), y=alt.Y('Candidat', sort='-x', axis=alt.Axis(labelFontSize=14, title=None)))
                    bars = base.mark_bar().encode(color=alt.Color('Color', scale=None))
                    text = base.mark_text(align='left', baseline='middle', dx=3).encode(text='Points')
                    st.altair_chart((bars + text).properties(height=500).configure_view(strokeWidth=0), use_container_width=True)
                else: st.info("Aucun vote actif.")
            else: st.info("En attente de votes...")

        elif menu == "⚙️ Paramétrage":
            st.title("⚙️ Paramétrage")
            t1, t2 = st.tabs(["Identité", "Gestion Questions"])
            with t1:
                new_t = st.text_input("Titre", value=st.session_state.config["titre_mur"], key=f"titre_{st.session_state.refresh_id}")
                if new_t != st.session_state.config["titre_mur"]:
                    if st.button("Sauver Titre"):
                        st.session_state.config["titre_mur"] = new_t; force_refresh(); st.rerun()
                up_l = st.file_uploader("Logo", type=["png", "jpg"])
                if up_l:
                    b64 = process_image_upload(up_l)
                    if b64:
                        st.session_state.config["logo_b64"] = b64; force_refresh(); st.success("Logo chargé !"); st.rerun()
                if st.session_state.config.get("logo_b64"):
                    st.markdown(f'<img src="data:image/png;base64,{st.session_state.config["logo_b64"]}" width="150" style="background:gray; padding:10px;">', unsafe_allow_html=True)
            with t2:
                st.subheader("📋 Liste des Questions")
                current_list = st.session_state.config["candidats"]
                df_cands = pd.DataFrame(current_list, columns=["Nom du Candidat"])
                edited_df = st.data_editor(df_cands, num_rows="dynamic", use_container_width=True, key="editor_cands")
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

        # --- MÉDIATHÈQUE AVEC DOUBLE VUE ---
        elif menu == "📸 Médiathèque (Export)":
            st.title("📸 Médiathèque & Export")
            
            files = glob.glob(f"{LIVE_DIR}/*")
            files.sort(key=os.path.getmtime, reverse=True)
            
            # 1. ZONE EXPORT
            st.markdown("### 📤 Exportation")
            if not files:
                st.warning("Aucune photo.")
            else:
                col_ex_all, col_ex_sel = st.columns(2)
                with col_ex_all:
                    zip_buffer_all = BytesIO()
                    with zipfile.ZipFile(zip_buffer_all, "w") as zf:
                        for f in files: zf.write(f, os.path.basename(f))
                    st.download_button(
                        label=f"📥 TÉLÉCHARGER TOUT ({len(files)} photos)",
                        data=zip_buffer_all.getvalue(),
                        file_name=f"photos_live_tout_{int(time.time())}.zip",
                        mime="application/zip", use_container_width=True, type="primary"
                    )

            st.divider()
            
            # 2. SÉLECTEUR DE VUE
            st.markdown("### 🖼️ Galerie")
            view_mode = st.radio("Mode d'affichage :", ["▦ Grille (Aperçu)", "☰ Liste (Détail & Gestion)"], horizontal=True, label_visibility="collapsed")
            
            if files:
                selected_files = []
                
                # --- VUE GRILLE (5 COLONNES) ---
                if "Grille" in view_mode:
                    cols = st.columns(6)
                    for i, f in enumerate(files):
                        with cols[i%6]:
                            st.image(f, use_container_width=True)
                            if st.checkbox("Select", key=f"sel_g_{i}", label_visibility="collapsed"):
                                selected_files.append(f)
                            if st.button("🗑️", key=f"del_g_{i}"):
                                os.remove(f); st.rerun()

                # --- VUE LISTE (DÉTAILLÉE) ---
                else:
                    # Bouton "Tout sélectionner" (Simulation visuelle)
                    if st.checkbox("Tout sélectionner pour export/suppression"):
                        selected_files = files
                    
                    st.markdown("---")
                    for i, f in enumerate(files):
                        c1, c2, c3, c4 = st.columns([0.5, 0.5, 3, 1], vertical_alignment="center")
                        
                        # Miniature
                        with c1:
                            st.image(f, width=50)
                        
                        # Checkbox
                        with c2:
                            if f in selected_files:
                                st.checkbox("✅", value=True, key=f"sel_l_d_{i}", disabled=True)
                            else:
                                if st.checkbox("✅", key=f"sel_l_{i}", label_visibility="collapsed"):
                                    selected_files.append(f)
                        
                        # Infos fichier
                        with c3:
                            ts = os.path.getmtime(f)
                            dt_str = datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                            st.write(f"**{os.path.basename(f)}** | 🕒 {dt_str}")
                        
                        # Delete
                        with c4:
                            if st.button("🗑️ Suppr.", key=f"del_l_{i}"):
                                os.remove(f); st.rerun()

                # 3. EXPORT SÉLECTION
                if selected_files:
                    st.markdown("---")
                    st.success(f"{len(selected_files)} photos sélectionnées.")
                    zip_buffer_sel = BytesIO()
                    with zipfile.ZipFile(zip_buffer_sel, "w") as zf:
                        for f in selected_files: zf.write(f, os.path.basename(f))
                    st.download_button(
                        label="📥 TÉLÉCHARGER SÉLECTION (.ZIP)",
                        data=zip_buffer_sel.getvalue(),
                        file_name=f"photos_live_selection_{int(time.time())}.zip",
                        mime="application/zip", type="primary"
                    )
            else:
                st.info("Vide.")

        elif menu == "📊 Data & Exports":
            if st.button("RESET TOUT"):
                 for f in [VOTES_FILE, PARTICIPANTS_FILE, VOTERS_FILE]:
                     if os.path.exists(f): os.remove(f)
                 for f in glob.glob(f"{LIVE_DIR}/*"): os.remove(f)
                 st.success("Reset complet !"); st.rerun()

# --- 4. UTILISATEUR (MOBILE) ---
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, default_config)
    
    st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }
        .stApp { background-color: black !important; color: white !important; }
        [data-testid="stHeader"] { display: none !important; }
        h1 { font-size: 1.5rem !important; text-align: center; margin-bottom: 0.5rem !important; }
        .stTabs [data-baseweb="tab-list"] { justify-content: center; }
        div[data-testid="stCameraInput"] button { width: 100%; }
    </style>
    """, unsafe_allow_html=True)
    
    if "participant_recorded" not in st.session_state:
        parts = load_json(PARTICIPANTS_FILE, [])
        parts.append(time.time())
        with open(PARTICIPANTS_FILE, "w") as f: json.dump(parts, f)
        st.session_state["participant_recorded"] = True

    if cfg["mode_affichage"] == "photos_live":
        st.markdown("<h1 style='color:#E2001A;'>📸 MUR PHOTO LIVE</h1>", unsafe_allow_html=True)
        if cfg.get("logo_b64"):
            st.markdown(f'<div style="text-align:center; margin-bottom:10px;"><img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:60px; width:auto;"></div>', unsafe_allow_html=True)
        
        tab_native, tab_web = st.tabs(["📱 Téléphone", "💻 Webcam"])
        
        with tab_native:
            photo_native = st.file_uploader("Prendre une photo", type=["png", "jpg", "jpeg"], key=f"upl_{st.session_state.cam_reset_id}", label_visibility="collapsed")
            if photo_native:
                if save_live_photo(photo_native):
                    st.balloons()
                    st.toast("✅ Envoyé !", icon="🚀")
                    st.session_state.cam_reset_id += 1
                    time.sleep(1.5); st.rerun()
        
        with tab_web:
            photo_web = st.camera_input("Photo", key=f"cam_{st.session_state.cam_reset_id}", label_visibility="collapsed")
            if photo_web:
                if save_live_photo(photo_web):
                    st.toast("✅ Envoyé !", icon="🚀")
                    st.session_state.cam_reset_id += 1
                    time.sleep(0.5); st.rerun()

    else:
        st.title("🗳️ Vote Transdev")
        if cfg.get("logo_b64"):
            st.markdown(f'<div style="text-align:center; margin-bottom:20px;"><img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:80px; width:auto;"></div>', unsafe_allow_html=True)

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
    st.markdown("""
    <style>
        body, .stApp { background-color: black !important; } 
        [data-testid='stHeader'], footer { display: none !important; } 
        .block-container { padding-top: 2rem !important; }
        img { background-color: transparent !important; }
    </style>
    """, unsafe_allow_html=True)
    
    config = load_json(CONFIG_FILE, default_config)
    nb_p = len(load_json(PARTICIPANTS_FILE, []))
    
    logo_html = ""
    if config.get("logo_b64"): 
        logo_html = f'<img src="data:image/png;base64,{config["logo_b64"]}" style="max-height:100px; margin-bottom:15px; display:block; margin-left:auto; margin-right:auto; background:transparent;">'

    if config["mode_affichage"] != "photos_live":
        st.markdown(f'<div style="text-align:center; color:white; background:transparent;">{logo_html}<h1 style="font-size:55px; font-weight:bold; text-transform:uppercase; margin:0; line-height:1.1;">{config["titre_mur"]}</h1></div>', unsafe_allow_html=True)

    if config["mode_affichage"] == "attente":
        st.markdown(f"""<div style="text-align:center; color:white; margin-top:80px;"><div style="{BADGE_CSS}">✨ BIENVENUE ✨</div><h2 style="font-size:50px; margin-top:40px; font-weight:lighter;">L'événement va commencer...</h2></div>""", unsafe_allow_html=True)

    elif config["mode_affichage"] == "photos_live":
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

        st.markdown(f"""
        <div style="position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); z-index:9999; display:flex; flex-direction:column; align-items:center; gap:25px;">
            <div style="margin-bottom:10px;">{logo_html}</div>
            <div style="background:white; padding:20px; border-radius:25px; box-shadow: 0 0 60px rgba(0,0,0,0.8);">
                <img src="data:image/png;base64,{qr_b64}" width="160" style="display:block;">
            </div>
            <div style="background: #E2001A; color: white; padding: 15px 40px; border-radius: 50px; font-weight: bold; font-size: 26px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-transform: uppercase; white-space: nowrap; border: 2px solid white;">
                📸 PRENEZ AUTANT DE PHOTOS QUE VOUS VOULEZ !
            </div>
        </div>
        """, unsafe_allow_html=True)

        photos = glob.glob(f"{LIVE_DIR}/*")
        photos.sort(key=os.path.getmtime, reverse=True)
        recent_photos = photos[:40] 

        img_array_js = []
        for photo_path in recent_photos:
            with open(photo_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                img_array_js.append(f"data:image/jpeg;base64,{b64}")
        js_img_list = json.dumps(img_array_js)

        components.html(f"""
        <html>
        <head>
            <style>
                body {{ margin: 0; overflow: hidden; background: transparent; }}
                .bubble {{
                    position: absolute;
                    border-radius: 50%;
                    border: 4px solid #E2001A;
                    box-shadow: 0 0 20px rgba(226, 0, 26, 0.5);
                    object-fit: cover;
                    will-change: transform;
                }}
            </style>
        </head>
        <body>
            <div id="container"></div>
            <script>
                const images = {js_img_list};
                const container = document.getElementById('container');
                const bubbles = [];
                const speed = 2.5;
                const centerX_min = window.innerWidth * 0.35;
                const centerX_max = window.innerWidth * 0.65;
                const centerY_min = window.innerHeight * 0.30;
                const centerY_max = window.innerHeight * 0.70;

                images.forEach((src, index) => {{
                    const img = document.createElement('img');
                    img.src = src;
                    img.className = 'bubble';
                    const size = 80 + Math.random() * 150;
                    let startX, startY;
                    do {{
                        startX = Math.random() * (window.innerWidth - 150);
                        startY = Math.random() * (window.innerHeight - 150);
                    }} while (startX > centerX_min && startX < centerX_max && startY > centerY_min && startY < centerY_max);

                    const bubble = {{
                        element: img,
                        x: startX,
                        y: startY,
                        vx: (Math.random() - 0.5) * speed * 2,
                        vy: (Math.random() - 0.5) * speed * 2,
                        size: size
                    }};
                    img.style.width = bubble.size + 'px';
                    img.style.height = bubble.size + 'px';
                    container.appendChild(img);
                    bubbles.push(bubble);
                }});

                function animate() {{
                    const w = window.innerWidth;
                    const h = window.innerHeight;
                    bubbles.forEach(b => {{
                        b.x += b.vx;
                        b.y += b.vy;
                        if (b.x <= 0 || b.x + b.size >= w) b.vx *= -1;
                        if (b.y <= 0 || b.y + b.size >= h) b.vy *= -1;
                        if (b.x + b.size > centerX_min && b.x < centerX_max && 
                            b.y + b.size > centerY_min && b.y < centerY_max) {{
                            const centerX = (centerX_min + centerX_max) / 2;
                            if (b.x < centerX) b.vx = -Math.abs(b.vx); 
                            else b.vx = Math.abs(b.vx);
                        }}
                        b.element.style.transform = `translate(${{b.x}}px, ${{b.y}}px)`;
                    }});
                    requestAnimationFrame(animate);
                }}
                animate();
            </script>
        </body>
        </html>
        """, height=900)

    elif config["mode_affichage"] == "votes" and not config["reveal_resultats"]:
        st.markdown(f'<div style="text-align:center; margin-top:10px;"><div style="background:white; display:inline-block; padding:5px 20px; border-radius:20px; color:black; font-weight:bold;">👥 {nb_p} CONNECTÉS</div></div>', unsafe_allow_html=True)
        if config["session_ouverte"]:
            host = st.context.headers.get('host', 'localhost')
            qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            st.markdown(f'<div style="text-align:center;"><div style="{BADGE_CSS} animation:blink 1.5s infinite;">🚀 VOTES OUVERTS</div></div>', unsafe_allow_html=True)
            cands = config["candidats"]
            mid = (len(cands) + 1) // 2
            def get_item_html(label):
                img_html = '<span style="font-size:30px; margin-right:15px;">🎥</span>'
                if label in config.get("candidats_images", {}):
                    b64 = config["candidats_images"][label]
                    img_html = f'<img src="data:image/png;base64,{b64}" style="width:60px; height:60px; object-fit:cover; border-radius:10px; margin-right:15px; border:2px solid #E2001A;">'
                return f'<div style="background:#222; color:white; padding:10px; margin-bottom:12px; border-left:6px solid #E2001A; font-weight:bold; font-size:22px; display:flex; align-items:center;">{img_html}{label}</div>'
            st.markdown("<div style='margin-top:40px;'>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 0.7, 1])
            with c1:
                for c in cands[:mid]: st.markdown(get_item_html(c), unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div style="background:white; padding:4px; border-radius:10px; text-align:center; margin: 0 auto; width: fit-content;"><img src="data:image/png;base64,{qr_b64}" width="180" style="display:block;"><p style="color:black; font-weight:bold; margin-top:5px; margin-bottom:0; font-size:14px;">SCANNEZ</p></div>', unsafe_allow_html=True)
            with c3:
                for c in cands[mid:]: st.markdown(get_item_html(c), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            components.html(f"""<div style="text-align:center;color:white;background:black;height:100vh;"><div style="{BADGE_CSS} background:#333;">🏁 CLOS</div><div style="font-size:100px;margin-top:40px;">👏</div><h1 style="color:#E2001A;">MERCI !</h1></div>""", height=600)

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
            ranks = ["🥇", "🥈", "🥉"]
            colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
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
