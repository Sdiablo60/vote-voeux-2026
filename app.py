import streamlit as st
import os, glob, base64, qrcode, json, random, pandas as pd
from io import BytesIO
import streamlit.components.v1 as components
import time
from PIL import Image
from datetime import datetime
import zipfile
import uuid

# --- 1. CONFIGURATION & FICHIERS ---
st.set_page_config(page_title="Régie Master - Pôle Aéroportuaire", layout="wide")

GALLERY_DIR, ADMIN_DIR = "galerie_images", "galerie_admin"
LIVE_DIR = "galerie_live_users"
VOTES_FILE, PARTICIPANTS_FILE, CONFIG_FILE, VOTERS_FILE, DETAILED_VOTES_FILE = "votes.json", "participants.json", "config_mur.json", "voters.json", "detailed_votes.json"

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
    "points_ponderation": [5, 3, 1],
    "session_id": "session_init_001"
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

if "session_id" not in st.session_state.config:
    st.session_state.config["session_id"] = str(int(time.time()))

if "my_uuid" not in st.session_state:
    st.session_state.my_uuid = str(uuid.uuid4())

if "refresh_id" not in st.session_state: st.session_state.refresh_id = 0
if "cam_reset_id" not in st.session_state: st.session_state.cam_reset_id = 0
if "confirm_delete" not in st.session_state: st.session_state.confirm_delete = False

# Variables User
if "user_id" not in st.session_state: st.session_state.user_id = None
if "a_vote" not in st.session_state: st.session_state.a_vote = False
if "rules_accepted" not in st.session_state: st.session_state.rules_accepted = False

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
        try:
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

def update_presence(is_active_user=False):
    presence_data = load_json(PARTICIPANTS_FILE, {})
    if isinstance(presence_data, list): presence_data = {}
    now = time.time()
    clean_data = {uid: ts for uid, ts in presence_data.items() if now - ts < 10} 
    if is_active_user:
        clean_data[st.session_state.my_uuid] = now
    with open(PARTICIPANTS_FILE, "w") as f:
        json.dump(clean_data, f)
    return len(clean_data)

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
            st.markdown("""<a href="/" target="_blank" style="text-decoration:none;"><div style="background-color: #E2001A; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 20px; border: 1px solid white; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">📺 OUVRIR LE MUR SOCIAL ⧉</div></a>""", unsafe_allow_html=True)
            st.markdown("---")
            menu = st.radio("Navigation :", ["🔴 PILOTAGE LIVE", "⚙️ Paramétrage", "📸 Médiathèque (Gestion)", "📊 Data & Exports"], label_visibility="collapsed")
            st.markdown("---")
            if st.button("🔓 Déconnexion", use_container_width=True):
                st.session_state["auth"] = False
                st.rerun()

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
                        for f in [VOTES_FILE, PARTICIPANTS_FILE, VOTERS_FILE, DETAILED_VOTES_FILE]:
                            if os.path.exists(f): os.remove(f)
                        st.session_state.config["session_id"] = str(int(time.time()))
                        save_config()
                        st.toast("✅ Session entièrement réinitialisée !")
                        time.sleep(1); st.rerun()
                    if st.button("🗑️ VIDER PHOTOS LIVE", use_container_width=True):
                        files = glob.glob(f"{LIVE_DIR}/*")
                        for f in files: os.remove(f)
                        st.toast("✅ Galerie Live vidée !")
                        time.sleep(1); st.rerun()
                with col_info: st.info("Efface les scores ou les photos live.")

            st.markdown("---")
            st.subheader("2️⃣ Monitoring")
            
            # KPI
            voters_list = load_json(VOTERS_FILE, [])
            st.metric("👥 Participants Validés", len(voters_list))
            
            # --- LOG DETAILLE (AVEC TOGGLE) ---
            st.markdown("##### 🕵️‍♂️ Détail des votes (Live)")
            
            # LE SWITCH D'AFFICHAGE/MASQUAGE
            show_details = st.toggle("👁️ Afficher le tableau des votants", value=False)
            
            if show_details:
                detailed_votes = load_json(DETAILED_VOTES_FILE, [])
                if detailed_votes:
                    df_details = pd.DataFrame(detailed_votes)
                    if not df_details.empty:
                        st.dataframe(
                            df_details, 
                            use_container_width=True, 
                            hide_index=True,
                            column_config={
                                "timestamp": "Heure",
                                "user": "Pseudo / Nom",
                                "choix_1": "🥇 1er Choix",
                                "choix_2": "🥈 2ème Choix",
                                "choix_3": "🥉 3ème Choix"
                            }
                        )
                else:
                    st.info("Aucun vote détaillé enregistré pour le moment.")

            st.markdown("---")
            
            # GRAPHIQUE
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                valid = {k:v for k,v in v_data.items() if k in cfg["candidats"]}
                if valid:
                    import altair as alt
                    df = pd.DataFrame(list(valid.items()), columns=['Candidat', 'Points'])
                    df = df.sort_values('Points', ascending=False).reset_index(drop=True)
                    df['Rang'] = df.index + 1
                    def get_color(rank): return '#FFD700' if rank == 1 else '#C0C0C0' if rank == 2 else '#CD7F32' if rank == 3 else '#E2001A'
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
                    if st.button("Sauver Titre"): st.session_state.config["titre_mur"] = new_t; force_refresh(); st.rerun()
                up_l = st.file_uploader("Logo", type=["png", "jpg"])
                if up_l:
                    b64 = process_image_upload(up_l)
                    if b64: st.session_state.config["logo_b64"] = b64; force_refresh(); st.success("Logo chargé !"); st.rerun()
                if st.session_state.config.get("logo_b64"): st.markdown(f'<img src="data:image/png;base64,{st.session_state.config["logo_b64"]}" width="150" style="background:gray; padding:10px;">', unsafe_allow_html=True)
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
                            if st.button("Supprimer"): del st.session_state.config["candidats_images"][sel]; save_config(); st.rerun()
                        else: st.info("Aucune image")
                    with c2:
                        up = st.file_uploader(f"Image pour {sel}", type=["png", "jpg"])
                        if up:
                            b64 = process_image_upload(up)
                            if b64: st.session_state.config["candidats_images"][sel] = b64; save_config(); st.rerun()

        elif menu == "📸 Médiathèque (Gestion)":
            st.markdown("""<style>div[data-testid="stButton"] button[key="btn_download"] { background-color: #007bff; color: white; border-color: #007bff; } div[data-testid="stButton"] button[key="btn_download"]:hover { background-color: #0056b3; border-color: #0056b3; } div[data-testid="stButton"] button[key="btn_delete"] { background-color: #dc3545; color: white; border-color: #dc3545; } div[data-testid="stButton"] button[key="btn_delete"]:hover { background-color: #a71d2a; border-color: #a71d2a; }</style>""", unsafe_allow_html=True)
            st.title("📸 Médiathèque & Export")
            files = glob.glob(f"{LIVE_DIR}/*"); files.sort(key=os.path.getmtime, reverse=True)
            st.markdown("### 🛠️ Outils de Gestion")
            
            if not files: st.warning("Aucune photo.")
            else:
                c_sel_all, c_dl, c_del = st.columns([1, 1.5, 1.5], vertical_alignment="center")
                with c_sel_all: select_all = st.checkbox("✅ Tout sélectionner", value=False)
                
                with c_dl:
                    if select_all:
                        zip_buffer = BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w") as zf:
                            for f in files: zf.write(f, os.path.basename(f))
                        st.download_button(label=f"📥 TÉLÉCHARGER TOUT ({len(files)})", data=zip_buffer.getvalue(), file_name=f"photos_full_{int(time.time())}.zip", mime="application/zip", use_container_width=True, key="btn_download")
                    else: st.caption("Cochez 'Tout sélectionner' ou utilisez la liste.")

                with c_del:
                    if select_all:
                        if st.button(f"🗑️ SUPPRIMER TOUT ({len(files)})", use_container_width=True, key="btn_delete"): st.session_state.confirm_delete = True
                    else: st.caption("Sélectionnez tout pour suppression de masse.")

                if st.session_state.confirm_delete:
                    st.error("⚠️ ATTENTION : SUPPRESSION DÉFINITIVE !")
                    col_conf_1, col_conf_2 = st.columns(2)
                    if col_conf_1.button("✅ OUI, TOUT EFFACER"):
                        for f in files: os.remove(f)
                        st.session_state.confirm_delete = False; st.success("Galerie vidée !"); time.sleep(1); st.rerun()
                    if col_conf_2.button("❌ ANNULER"): st.session_state.confirm_delete = False; st.rerun()

                st.divider()
                view_mode = st.radio("Affichage :", ["▦ Grille", "☰ Liste Détaillée"], horizontal=True, label_visibility="collapsed")
                
                if "Grille" in view_mode:
                    cols = st.columns(6)
                    for i, f in enumerate(files):
                        with cols[i%6]:
                            st.image(f, use_container_width=True)
                            if st.button("🗑️", key=f"del_g_{i}"): os.remove(f); st.rerun()
                else:
                    manual_selection = []
                    st.write("Sélection manuelle :")
                    h1, h2, h3, h4 = st.columns([0.5, 0.5, 3, 1]); h1.write("**Img**"); h2.write("**Sel**"); h3.write("**Infos**"); h4.write("**Action**")
                    st.markdown("---")
                    for i, f in enumerate(files):
                        c1, c2, c3, c4 = st.columns([0.5, 0.5, 3, 1], vertical_alignment="center")
                        with c1: st.image(f, width=50)
                        with c2: 
                            if st.checkbox("", key=f"sel_man_{i}", label_visibility="collapsed"): manual_selection.append(f)
                        with c3: st.write(f"**{os.path.basename(f)}**")
                        with c4:
                            if st.button("🗑️", key=f"del_l_{i}"): os.remove(f); st.rerun()
                    if manual_selection:
                        st.markdown("---")
                        zip_man = BytesIO()
                        with zipfile.ZipFile(zip_man, "w") as zf:
                            for f in manual_selection: zf.write(f, os.path.basename(f))
                        st.download_button("📥 Télécharger la sélection", data=zip_man.getvalue(), file_name="selection.zip", mime="application/zip")

        elif menu == "📊 Data & Exports":
            st.title("📊 Data & Exports")
            st.subheader("1️⃣ Export des Résultats")
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                valid = {k:v for k,v in v_data.items() if k in st.session_state.config["candidats"]}
                if valid:
                    df = pd.DataFrame(list(valid.items()), columns=['Candidat', 'Points']).sort_values('Points', ascending=False)
                    st.dataframe(df, hide_index=True, use_container_width=True)
                    st.download_button(label="📥 Télécharger CSV", data=df.to_csv(index=False).encode('utf-8'), file_name=f"resultats_{int(time.time())}.csv", mime="text/csv", type="primary")
                else: st.info("Aucun vote valide.")
            else: st.info("Aucun vote.")
            st.divider()
            
            st.subheader("2️⃣ Export Log Détaillé")
            detailed_votes = load_json(DETAILED_VOTES_FILE, [])
            if detailed_votes:
                df_det = pd.DataFrame(detailed_votes)
                st.download_button(label="📥 Télécharger Log Complet CSV", data=df_det.to_csv(index=False).encode('utf-8'), file_name=f"log_votes_complet_{int(time.time())}.csv", mime="text/csv")
            else: st.info("Pas de log détaillé.")

            st.divider()
            st.subheader("⚠️ Réinitialisation")
            st.markdown("""<div style="border: 1px solid red; padding: 15px; border-radius: 5px; background-color: #fff5f5; color: #8b0000;"><strong>ATTENTION :</strong> Efface TOUTES les données.</div><br>""", unsafe_allow_html=True)
            if st.button("🔥 RESET TOUT", type="primary"):
                 for f in [VOTES_FILE, PARTICIPANTS_FILE, VOTERS_FILE, DETAILED_VOTES_FILE]:
                     if os.path.exists(f): os.remove(f)
                 for f in glob.glob(f"{LIVE_DIR}/*"): os.remove(f)
                 st.session_state.config["session_id"] = str(int(time.time()))
                 save_config()
                 st.success("✅ Reset OK ! Session renouvelée."); time.sleep(1); st.rerun()

# --- 4. UTILISATEUR (MOBILE) ---
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, default_config)
    current_session = cfg.get("session_id", "v1")
    ls_key = f"vote_record_{current_session}"

    st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }
        .stApp { background-color: black !important; color: white !important; visibility: hidden; } /* CACHÉ PAR DÉFAUT */
        [data-testid="stHeader"] { display: none !important; }
        h1 { font-size: 1.5rem !important; text-align: center; margin-bottom: 0.5rem !important; }
        .stTabs [data-baseweb="tab-list"] { justify-content: center; }
        div[data-testid="stCameraInput"] button { width: 100%; }
        .stMultiSelect div[data-baseweb="select"] { border: 4px solid white !important; border-radius: 12px !important; box-shadow: 0 0 15px rgba(255, 255, 255, 0.3) !important; }
        .stMultiSelect div[data-baseweb="tag"] { background-color: #E2001A !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)
    
    if cfg["mode_affichage"] != "photos_live": 
        components.html(f"""
        <script>
            var voted = localStorage.getItem('{ls_key}');
            if (voted === 'true') {{
                var overlay = document.createElement('div');
                overlay.style.position = 'fixed'; overlay.style.top = '0'; overlay.style.left = '0';
                overlay.style.width = '100%'; overlay.style.height = '100%';
                overlay.style.backgroundColor = 'rgba(0,0,0,0.95)'; overlay.style.zIndex = '2147483647';
                overlay.style.display = 'flex'; overlay.style.flexDirection = 'column';
                overlay.style.justifyContent = 'center'; overlay.style.alignItems = 'center';
                overlay.style.color = 'white'; overlay.style.fontFamily = 'sans-serif'; overlay.style.textAlign = 'center';
                overlay.innerHTML = '<h1 style="font-size:4rem; margin:0;">🚫</h1><h2 style="color:#E2001A; margin-top:20px;">Vote Déjà Enregistré</h2><p style="font-size:1.2rem;">Vous avez déjà soumis votre participation.</p>';
                window.parent.document.body.appendChild(overlay);
                var app = window.parent.document.querySelector('.stApp');
                if (app) app.style.filter = 'blur(10px)';
            }} else {{
                window.parent.document.querySelector('.stApp').style.visibility = 'visible';
            }}
        </script>
        """, height=0)
    else:
        components.html("""<script>window.parent.document.querySelector('.stApp').style.visibility = 'visible';</script>""", height=0)

    if cfg["mode_affichage"] == "photos_live":
        st.markdown("<h1 style='color:#E2001A;'>📸 MUR PHOTO LIVE</h1>", unsafe_allow_html=True)
        if cfg.get("logo_b64"): st.markdown(f'<div style="text-align:center; margin-bottom:10px;"><img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:60px; width:auto;"></div>', unsafe_allow_html=True)
        
        tab_native, tab_web = st.tabs(["📱 Téléphone", "💻 Webcam"])
        with tab_native:
            photo_native = st.file_uploader("Prendre une photo", type=["png", "jpg", "jpeg"], key=f"upl_{st.session_state.cam_reset_id}", label_visibility="collapsed")
            if photo_native:
                if save_live_photo(photo_native): st.balloons(); st.toast("✅ Envoyé !", icon="🚀"); st.session_state.cam_reset_id += 1; time.sleep(1.5); st.rerun()
        with tab_web:
            photo_web = st.camera_input("Photo", key=f"cam_{st.session_state.cam_reset_id}", label_visibility="collapsed")
            if photo_web:
                if save_live_photo(photo_web): st.toast("✅ Envoyé !", icon="🚀"); st.session_state.cam_reset_id += 1; time.sleep(0.5); st.rerun()

    else:
        if st.session_state.get("a_vote", False):
            st.balloons()
            st.markdown("""<div style="text-align:center; padding-top:50px;"><div style="font-size:80px;">✅</div><h1 style="color:#E2001A;">Vote Enregistré !</h1><p>Merci d'avoir participé.</p></div>""", unsafe_allow_html=True)
        
        elif not cfg["session_ouverte"]:
            st.title("🗳️ Vote Transdev")
            if cfg.get("logo_b64"): st.markdown(f'<div style="text-align:center; margin-bottom:20px;"><img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:80px; width:auto;"></div>', unsafe_allow_html=True)
            st.warning("⌛ Votes clos ou attente.")
            
        else:
            st.title("🗳️ Vote Transdev")
            if cfg.get("logo_b64"): st.markdown(f'<div style="text-align:center; margin-bottom:20px;"><img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:80px; width:auto;"></div>', unsafe_allow_html=True)
            
            if not st.session_state.user_id:
                nom = st.text_input("Votre Pseudo / Nom :")
                if st.button("Commencer"):
                    if len(nom) > 2:
                        clean_id = nom.strip().lower()
                        voters = load_json(VOTERS_FILE, [])
                        if clean_id in voters: st.error("Ce nom a déjà voté.")
                        else: st.session_state.user_id = clean_id; st.rerun()
                    else: st.warning("Nom invalide.")
            
            elif not st.session_state.rules_accepted:
                st.markdown("""<div style="background:#222; padding:20px; border-radius:10px; border:2px solid #E2001A; margin-bottom:20px;">
                <h3 style="color:#E2001A; margin-top:0;">📜 RÈGLES DU JEU</h3>
                <ul><li>Vous ne pouvez voter qu'<strong>UNE SEULE FOIS</strong>.</li><li>Vous devez sélectionner <strong>3 CHOIX</strong>.</li></ul>
                <hr style="border-color:#555;"><h3 style="color:white; margin-top:10px;">🏆 PONDÉRATION</h3>""", unsafe_allow_html=True)
                pts = cfg.get("points_ponderation", [5, 3, 1])
                st.markdown(f"""* 🥇 **1er Choix :** {pts[0]} Points\n* 🥈 **2ème Choix :** {pts[1]} Points\n* 🥉 **3ème Choix :** {pts[2]} Points</div>""", unsafe_allow_html=True)
                if st.button("✅ J'AI COMPRIS, PASSER AU VOTE", type="primary", use_container_width=True):
                    st.session_state.rules_accepted = True; st.rerun()

            else:
                choix = st.multiselect("Sélectionnez vos 3 favoris :", cfg["candidats"])
                if len(choix) == 3 and st.button("VALIDER MON VOTE", type="primary", use_container_width=True):
                    vts = load_json(VOTES_FILE, {})
                    pts = cfg.get("points_ponderation", [5, 3, 1])
                    for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                    json.dump(vts, open(VOTES_FILE, "w"))
                    
                    voters = load_json(VOTERS_FILE, [])
                    voters.append(st.session_state.user_id)
                    with open(VOTERS_FILE, "w") as f: json.dump(voters, f)
                    
                    details = load_json(DETAILED_VOTES_FILE, [])
                    details.append({
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "user": st.session_state.user_id,
                        "choix_1": choix[0], "choix_2": choix[1], "choix_3": choix[2]
                    })
                    with open(DETAILED_VOTES_FILE, "w") as f: json.dump(details, f)
                    
                    st.session_state["a_vote"] = True
                    components.html(f"""<script>localStorage.setItem('{ls_key}', 'true'); location.reload();</script>""", height=0)
                    time.sleep(1)
                elif len(choix) > 3: st.error("⚠️ 3 choix maximum !")
                elif len(choix) > 0 and len(choix) < 3: st.warning(f"Encore {3-len(choix)} choix.")

# --- 5. MUR SOCIAL ---
else:
    st.markdown("""
    <style>
        body, .stApp { background-color: black !important; overflow: hidden; height: 100vh; } 
        [data-testid='stHeader'], footer { display: none !important; } 
        .block-container { padding-top: 1rem !important; padding-bottom: 0 !important; max-width: 98% !important; }
        
        .participant-badge {
            display: inline-block;
            background: rgba(255, 255, 255, 0.1);
            color: #ccc;
            border: 1px solid #444;
            border-radius: 15px;
            padding: 4px 12px;
            margin: 4px;
            font-size: 14px;
            font-weight: bold;
            white-space: nowrap;
        }
        
        .badges-container {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            max-height: 25vh; 
            overflow-y: auto;
            margin-top: 10px;
            padding: 10px;
            scrollbar-width: none; 
        }
        .badges-container::-webkit-scrollbar { display: none; }
    </style>
    """, unsafe_allow_html=True)
    
    config = load_json(CONFIG_FILE, default_config)
    voters_list = load_json(VOTERS_FILE, [])
    nb_p = len(voters_list)
    
    logo_html = ""
    if config.get("logo_b64"): 
        logo_html = f'<img src="data:image/png;base64,{config["logo_b64"]}" style="max-height:80px; display:block; margin: 0 auto 10px auto;">'

    if config["mode_affichage"] != "photos_live":
        st.markdown(f'<div style="text-align:center; color:white;">{logo_html}<h1 style="font-size:40px; font-weight:bold; text-transform:uppercase; margin:0; line-height:1.1;">{config["titre_mur"]}</h1></div>', unsafe_allow_html=True)

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

        photos = glob.glob(f"{LIVE_DIR}/*"); photos.sort(key=os.path.getmtime, reverse=True); recent_photos = photos[:40] 
        img_array_js = []
        for photo_path in recent_photos:
            with open(photo_path, "rb") as f: b64 = base64.b64encode(f.read()).decode(); img_array_js.append(f"data:image/jpeg;base64,{b64}")
        js_img_list = json.dumps(img_array_js)

        components.html(f"""
        <html><head><style>body {{ margin: 0; overflow: hidden; background: transparent; }} .bubble {{ position: absolute; border-radius: 50%; border: 4px solid #E2001A; box-shadow: 0 0 20px rgba(226, 0, 26, 0.5); object-fit: cover; will-change: transform; }}</style></head>
        <body><div id="container"></div><script>
            const images = {js_img_list}; const container = document.getElementById('container'); const bubbles = []; const speed = 2.5;
            const centerX_min = window.innerWidth * 0.35; const centerX_max = window.innerWidth * 0.65; const centerY_min = window.innerHeight * 0.30; const centerY_max = window.innerHeight * 0.70;
            images.forEach((src, index) => {{
                const img = document.createElement('img'); img.src = src; img.className = 'bubble'; const size = 80 + Math.random() * 150;
                let startX, startY;
                do {{ startX = Math.random() * (window.innerWidth - 150); startY = Math.random() * (window.innerHeight - 150); }} while (startX > centerX_min && startX < centerX_max && startY > centerY_min && startY < centerY_max);
                const bubble = {{ element: img, x: startX, y: startY, vx: (Math.random() - 0.5) * speed * 2, vy: (Math.random() - 0.5) * speed * 2, size: size }};
                img.style.width = bubble.size + 'px'; img.style.height = bubble.size + 'px'; container.appendChild(img); bubbles.push(bubble);
            }});
            function animate() {{
                const w = window.innerWidth; const h = window.innerHeight;
                bubbles.forEach(b => {{
                    b.x += b.vx; b.y += b.vy;
                    if (b.x <= 0 || b.x + b.size >= w) b.vx *= -1; if (b.y <= 0 || b.y + b.size >= h) b.vy *= -1;
                    if (b.x + b.size > centerX_min && b.x < centerX_max && b.y + b.size > centerY_min && b.y < centerY_max) {{ const centerX = (centerX_min + centerX_max) / 2; if (b.x < centerX) b.vx = -Math.abs(b.vx); else b.vx = Math.abs(b.vx); }}
                    b.element.style.transform = `translate(${{b.x}}px, ${{b.y}}px)`;
                }}); requestAnimationFrame(animate);
            }} animate();
        </script></body></html>
        """, height=900)

    elif config["mode_affichage"] == "votes" and not config["reveal_resultats"]:
        st.markdown(f'<div style="text-align:center; margin-top:5px; margin-bottom:5px;"><div style="background:white; display:inline-block; padding:2px 15px; border-radius:15px; color:black; font-weight:bold; font-size:16px;">👥 {nb_p} PARTICIPANTS</div></div>', unsafe_allow_html=True)
        
        if voters_list:
            badges_html = "".join([f'<div class="participant-badge">{v}</div>' for v in voters_list[::-1]])
            st.markdown(f'<div class="badges-container">{badges_html}</div>', unsafe_allow_html=True)

        if config["session_ouverte"]:
            host = st.context.headers.get('host', 'localhost')
            qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            
            cands = config["candidats"]
            mid = (len(cands) + 1) // 2
            
            def get_item_html(label):
                img_html = '<span style="font-size:30px; margin-right:15px;">🎥</span>'
                if label in config.get("candidats_images", {}):
                    b64 = config["candidats_images"][label]
                    img_html = f'<img src="data:image/png;base64,{b64}" style="width:50px; height:50px; object-fit:cover; border-radius:8px; margin-right:10px; border:2px solid #E2001A;">'
                return f'<div style="background:#222; color:white; padding:8px; margin-bottom:8px; border-left:4px solid #E2001A; font-weight:bold; font-size:18px; display:flex; align-items:center;">{img_html}{label}</div>'
            
            st.markdown("<div style='margin-top:20px;'>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 0.6, 1])
            with c1:
                for c in cands[:mid]: st.markdown(get_item_html(c), unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div style="background:white; padding:4px; border-radius:10px; text-align:center; margin: 0 auto; width: fit-content;"><img src="data:image/png;base64,{qr_b64}" width="160" style="display:block;"><p style="color:black; font-weight:bold; margin-top:5px; margin-bottom:0; font-size:14px;">SCANNEZ</p></div>', unsafe_allow_html=True)
                st.markdown(f'<div style="text-align:center; margin-top:15px;"><div style="{BADGE_CSS} animation:blink 1.5s infinite; font-size:18px; padding:8px 20px;">🚀 VOTES OUVERTS</div></div>', unsafe_allow_html=True)
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
