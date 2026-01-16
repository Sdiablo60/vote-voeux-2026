import streamlit as st
import os
import glob
import base64
import qrcode
import json
import time
import uuid
import textwrap
import zipfile
import shutil
from io import BytesIO
import streamlit.components.v1 as components
from PIL import Image
from datetime import datetime
import pandas as pd
import random
import altair as alt
import copy
import re
import tempfile

# =========================================================
# 1. IMPORTS & CONFIGURATION INITIALE
# =========================================================

try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

Image.MAX_IMAGE_PIXELS = None 

st.set_page_config(
    page_title="Régie Master",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- RECUPERATION PARAMETRES URL (SECURISÉ) ---
qp = st.query_params
mode_url = qp.get("mode", "wall") 
admin_url = qp.get("admin", "false")
is_blocked = qp.get("blocked") == "true"
is_test_admin = qp.get("test_admin") == "true"

est_admin = (admin_url == "true")
est_utilisateur = (mode_url == "vote")

# DOSSIERS & FICHIERS
LIVE_DIR = "galerie_live_users"
ARCHIVE_DIR = "_archives_sessions"
VOTES_FILE = "votes.json"
CONFIG_FILE = "config_mur.json"
VOTERS_FILE = "voters.json"
PARTICIPANTS_FILE = "participants.json"
DETAILED_VOTES_FILE = "detailed_votes.json"
USERS_FILE = "users.json"

for d in [LIVE_DIR, ARCHIVE_DIR]:
    os.makedirs(d, exist_ok=True)

# =========================================================
# 2. CSS GLOBAL (DESIGN AMÉLIORÉ)
# =========================================================
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; color: black; }
    
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
    
    .social-header { 
        position: fixed; top: 0; left: 0; width: 100%; height: 12vh; 
        background: #E2001A !important; display: flex; align-items: center; 
        justify-content: center; z-index: 999999 !important; border-bottom: 5px solid white; 
    }
    .social-title { 
        color: white !important; font-size: 40px !important; 
        font-weight: bold; margin: 0; text-transform: uppercase; 
    }

    html, body, [data-testid="stAppViewContainer"] {
        overflow: hidden !important; height: 100vh !important; 
        width: 100vw !important; margin: 0 !important; padding: 0 !important;
    }
    
    ::-webkit-scrollbar { display: none; }
    
    button[kind="secondary"] { color: #333 !important; border-color: #333 !important; }
    button[kind="primary"] { color: white !important; background-color: #E2001A !important; border: none; }
    button[kind="primary"]:hover { background-color: #C20015 !important; }
    
    .session-card {
        background-color: #f8f9fa; padding: 30px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center;
        border: 1px solid #ddd; margin-bottom: 20px;
    }
    .session-title {
        color: #E2001A; font-size: 24px; font-weight: 900;
        text-transform: uppercase; margin-bottom: 10px;
    }
    
    .login-container {
        max-width: 400px; margin: 100px auto; padding: 40px;
        background: #f8f9fa; border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1); text-align: center; border: 1px solid #ddd;
    }
    .login-title { 
        color: #E2001A; font-size: 24px; font-weight: bold; 
        margin-bottom: 20px; text-transform: uppercase; 
    }
    
    section[data-testid="stSidebar"] { background-color: #f0f2f6 !important; }
    section[data-testid="stSidebar"] button[kind="primary"] {
        background-color: #E2001A !important; width: 100%; border-radius: 5px; margin-bottom: 5px;
    }
    
    a.custom-link-btn {
        display: block !important; text-align: center !important; 
        padding: 12px 20px !important; border-radius: 8px !important; 
        text-decoration: none !important; font-weight: bold !important; 
        margin-bottom: 10px !important; color: white !important; 
        transition: transform 0.2s !important; width: 100% !important; 
        box-sizing: border-box !important; line-height: 1.5 !important; 
    }
    a.custom-link-btn:hover { transform: scale(1.02); opacity: 0.9; }
    .btn-red { background-color: #E2001A !important; }
    
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] { background-color: white !important; }
    li[role="option"] { color: black !important; background-color: white !important; }
    div[data-baseweb="select"] div { color: black !important; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 3. DONNEES & CONFIGURATIONS
# =========================================================
blank_config = {
    "mode_affichage": "attente", "titre_mur": "TITRE À DÉFINIR", 
    "session_ouverte": False, "reveal_resultats": False, "timestamp_podium": 0,
    "logo_b64": None, "candidats": [], "candidats_images": {}, 
    "points_ponderation": [5, 3, 1], "session_id": ""
}

default_config = {
    "mode_affichage": "attente", "titre_mur": "CONCOURS VIDÉO 2026", 
    "session_ouverte": False, "reveal_resultats": False, "timestamp_podium": 0,
    "logo_b64": None, 
    "candidats": ["BU PAX", "BU FRET", "BU B2B", "RH", "IT", "DPMI", "FINANCES", "AO", "QSSE", "DIRECTION"],
    "candidats_images": {}, "points_ponderation": [5, 3, 1], "session_id": str(uuid.uuid4())
}

default_users = { "admin": {"pwd": "ADMIN_LIVE_MASTER", "role": "Super Admin", "perms": ["all"]} }

# =========================================================
# 4. FONCTIONS UTILITAIRES & MOTEUR PDF
# =========================================================
def clean_for_json(data):
    if isinstance(data, dict): return {k: clean_for_json(v) for k, v in data.items()}
    elif isinstance(data, list): return [clean_for_json(v) for v in data]
    elif isinstance(data, (str, int, float, bool, type(None))): return data
    else: return str(data)

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding='utf-8') as f:
                return json.loads(f.read().strip() or "{}")
        except: return default
    return default

def save_json(file, data):
    try:
        with open(str(file), "w", encoding='utf-8') as f:
            json.dump(clean_for_json(data), f, ensure_ascii=False, indent=4)
    except: pass

def save_config(): save_json(CONFIG_FILE, st.session_state.config)

def reset_app_data(init_mode="blank", preserve_config=False):
    for f in [VOTES_FILE, VOTERS_FILE, PARTICIPANTS_FILE, DETAILED_VOTES_FILE]:
        if os.path.exists(f): os.remove(f)
    for f in glob.glob(f"{LIVE_DIR}/*"): os.remove(f)
    if not preserve_config:
        if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
        st.session_state.config = copy.deepcopy(blank_config if init_mode == "blank" else default_config)
    st.session_state.config["session_id"] = str(uuid.uuid4())
    save_config()

def archive_current_session():
    current_cfg = load_json(CONFIG_FILE, default_config)
    titre = current_cfg.get("titre_mur", "Session")
    safe_titre = re.sub(r'[\\/*?:"<>|]', "", titre).replace(" ", "_")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder_name = f"{timestamp}_{safe_titre}"
    archive_path = os.path.join(ARCHIVE_DIR, folder_name)
    os.makedirs(archive_path, exist_ok=True)
    for f in [VOTES_FILE, CONFIG_FILE, VOTERS_FILE, PARTICIPANTS_FILE, DETAILED_VOTES_FILE]:
        if os.path.exists(f): shutil.copy2(f, archive_path)
    if os.path.exists(LIVE_DIR): shutil.copytree(LIVE_DIR, os.path.join(archive_path, "galerie_live_users"))
    return folder_name

def restore_session_from_archive(folder_name):
    source_path = os.path.join(ARCHIVE_DIR, folder_name)
    reset_app_data(init_mode="none")
    for f in [VOTES_FILE, CONFIG_FILE, VOTERS_FILE, PARTICIPANTS_FILE, DETAILED_VOTES_FILE]:
        src_f = os.path.join(source_path, f)
        if os.path.exists(src_f): shutil.copy2(src_f, ".")
    if os.path.exists(os.path.join(source_path, "galerie_live_users")):
        if os.path.exists(LIVE_DIR): shutil.rmtree(LIVE_DIR)
        shutil.copytree(os.path.join(source_path, "galerie_live_users"), LIVE_DIR)

def delete_archived_session(folder_name):
    path = os.path.join(ARCHIVE_DIR, folder_name)
    if os.path.exists(path): shutil.rmtree(path)

def process_logo(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        img.thumbnail((600, 600)); buf = BytesIO(); img.save(buf, format="PNG"); return base64.b64encode(buf.getvalue()).decode()
    except: return None

def process_participant_image(uploaded_file):
    try:
        img = Image.open(uploaded_file).convert("RGB"); img.thumbnail((300, 300)); buf = BytesIO(); img.save(buf, format="JPEG", quality=60); return base64.b64encode(buf.getvalue()).decode()
    except: return None

def set_state(mode, open_s, reveal):
    st.session_state.config.update({"mode_affichage": mode, "session_ouverte": open_s, "reveal_resultats": reveal})
    if reveal: st.session_state.config["timestamp_podium"] = time.time()
    save_config()

def reset_vote_callback():
    st.session_state.vote_success = False
    if "widget_choix" in st.session_state: st.session_state.widget_choix = []

def get_advanced_stats():
    details = load_json(DETAILED_VOTES_FILE, [])
    vote_counts = {}; rank_dist = {}; unique_voters = set()
    for record in details:
        unique_voters.add(record.get('Utilisateur'))
        for idx, k in enumerate(["Choix 1", "Choix 2", "Choix 3"]):
            cand = record.get(k)
            if cand:
                vote_counts[cand] = vote_counts.get(cand, 0) + 1
                if cand not in rank_dist: rank_dist[cand] = {1:0, 2:0, 3:0}
                rank_dist[cand][idx+1] += 1
    return vote_counts, len(unique_voters), rank_dist

# --- PDF GENERATOR (LE RETOUR) ---
if PDF_AVAILABLE:
    class PDFReport(FPDF):
        def header(self):
            if "logo_b64" in st.session_state.config and st.session_state.config["logo_b64"]:
                try:
                    logo_data = base64.b64decode(st.session_state.config["logo_b64"])
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                        tmp.write(logo_data); tmp_path = tmp.name
                    self.image(tmp_path, 10, 8, 45); os.unlink(tmp_path)
                except: pass
            self.set_font('Arial', 'B', 15); self.set_text_color(226, 0, 26)
            self.cell(50); self.cell(0, 10, f"{st.session_state.config.get('titre_mur', 'Session')}", 0, 1, 'L')
            self.ln(20)
        def footer(self):
            self.set_y(-15); self.set_font('Arial', 'I', 8); self.set_text_color(128)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def create_pdf_results(title, df, nb_voters, total_points):
        pdf = PDFReport(); pdf.add_page()
        pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0)
        pdf.cell(0, 8, txt="RESULTATS", ln=True, align='L'); pdf.ln(5)
        max_points = df['Points'].max() if not df.empty else 1
        for i, row in df.iterrows():
            cand = str(row['Candidat']).encode('latin-1', 'replace').decode('latin-1')
            points = row['Points']
            pdf.cell(50, 8, cand, 0, 0, 'R')
            width = (points / max_points) * 100
            pdf.set_fill_color(226, 0, 26); pdf.rect(pdf.get_x()+2, pdf.get_y(), width, 5, 'F')
            pdf.set_xy(pdf.get_x() + 110, pdf.get_y()); pdf.cell(20, 8, f"{points} pts", 0, 1, 'L')
            pdf.ln(8)
        return pdf.output(dest='S').encode('latin-1')

# --- INIT SESSION ---
if "config" not in st.session_state:
    st.session_state.config = load_json(CONFIG_FILE, default_config)

# =========================================================
# 1. CONSOLE ADMIN
# =========================================================
if est_admin:
    if "auth" not in st.session_state: st.session_state["auth"] = False
    users_db = load_json(USERS_FILE, default_users)
    if "admin" not in users_db: users_db["admin"] = default_users["admin"]; save_json(USERS_FILE, users_db)

    if not st.session_state["auth"]:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown('<div class="login-container"><div class="login-title">🔒 ADMIN ACCESS</div>', unsafe_allow_html=True)
            u = st.text_input("Identifiant", label_visibility="collapsed")
            p = st.text_input("Mot de passe", type="password", label_visibility="collapsed")
            if st.button("ENTRER", type="primary", use_container_width=True):
                if u in users_db and users_db[u]["pwd"] == p:
                    st.session_state.update({"auth": True, "current_user": u, "user_role": users_db[u].get("role", "User"), "user_perms": users_db[u].get("perms", []), "session_active": False})
                    st.rerun()
                else: st.error("Erreur")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        perms = st.session_state["user_perms"]
        is_super_admin = "all" in perms
        
        if "session_active" not in st.session_state or not st.session_state["session_active"]:
            st.markdown("<br>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                st.markdown(f'<div class="session-card"><div class="session-title">🗂️ GESTIONNAIRE DE SESSIONS</div>', unsafe_allow_html=True)
                st.button(f"📂 OUVRIR : {st.session_state.config.get('titre_mur', 'Session')}", type="primary", use_container_width=True, on_click=lambda: st.session_state.update({"session_active": True}))
                if is_super_admin or "config" in perms:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.button("✨ CRÉER UNE NOUVELLE SESSION VIERGE", type="secondary", use_container_width=True, on_click=lambda: (archive_current_session(), reset_app_data("blank"), st.session_state.update({"session_active": True})))
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.divider()
                st.subheader("📦 Archives")
                archives = sorted([d for d in os.listdir(ARCHIVE_DIR) if os.path.isdir(os.path.join(ARCHIVE_DIR, d))], reverse=True)
                if not archives: st.caption("Aucune archive.")
                for arc in archives:
                    c_name, c_act = st.columns([3, 1])
                    c_name.text(f"📁 {arc}")
                    c_r, c_d = c_act.columns(2)
                    if c_r.button("♻️", key=f"r_{arc}"):
                        archive_current_session(); restore_session_from_archive(arc)
                        st.session_state.config = load_json(CONFIG_FILE, default_config); st.session_state["session_active"] = True; st.rerun()
                    if is_super_admin and c_d.button("🗑️", key=f"d_{arc}"): delete_archived_session(arc); st.rerun()
        else:
            cfg = st.session_state.config
            with st.sidebar:
                if st.button("⬅️ CHANGER DE SESSION"): st.session_state["session_active"] = False; st.rerun()
                st.divider()
                if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), use_container_width=True)
                st.header(f"MENU ({st.session_state['current_user']})")
                
                if "admin_menu" not in st.session_state: st.session_state.admin_menu = "🔴 PILOTAGE LIVE"
                
                # MENU
                menu_items = [("🔴 PILOTAGE LIVE", "pilotage"), ("📱 TEST MOBILE", "test_mobile"), ("⚙️ CONFIG", "config"), ("📸 MÉDIATHÈQUE", "mediatheque"), ("📊 DATA", "data")]
                for label, perm in menu_items:
                    if is_super_admin or perm in perms:
                        if st.button(label, type="primary" if st.session_state.admin_menu == label else "secondary"): st.session_state.admin_menu = label; st.rerun()
                
                if is_super_admin:
                    st.markdown("---")
                    if st.button("👥 UTILISATEURS", type="primary" if st.session_state.admin_menu == "👥 UTILISATEURS" else "secondary"): st.session_state.admin_menu = "👥 UTILISATEURS"; st.rerun()

                st.divider()
                # BOUTON MUR SOCIAL (FORCE MODE WALL)
                host_url = st.context.headers.get("host", "")
                st.markdown(f'<a href="https://{host_url}/?mode=wall" target="_blank" class="custom-link-btn btn-red">📺 OUVRIR MUR SOCIAL</a>', unsafe_allow_html=True)
                if st.button("🔓 DÉCONNEXION"): st.session_state["auth"] = False; st.session_state["session_active"] = False; st.rerun()

            menu = st.session_state.admin_menu

            if menu == "🔴 PILOTAGE LIVE":
                st.title("🔴 PILOTAGE LIVE")
                st.subheader(f"État : {cfg['mode_affichage'].upper()}")
                c1, c2, c3, c4 = st.columns(4)
                c1.button("🏠 ACCUEIL", type="primary" if cfg["mode_affichage"]=="attente" else "secondary", use_container_width=True, on_click=set_state, args=("attente", False, False))
                c2.button("🗳️ VOTES ON", type="primary" if (cfg["mode_affichage"]=="votes" and cfg["session_ouverte"]) else "secondary", use_container_width=True, on_click=set_state, args=("votes", True, False))
                c3.button("🔒 VOTES OFF", type="primary" if (cfg["mode_affichage"]=="votes" and not cfg["session_ouverte"] and not cfg["reveal_resultats"]) else "secondary", use_container_width=True, on_click=set_state, args=("votes", False, False))
                c4.button("🏆 PODIUM", type="primary" if cfg["reveal_resultats"] else "secondary", use_container_width=True, on_click=set_state, args=("votes", False, True))
                st.markdown("---")
                st.button("📸 MUR PHOTOS LIVE", type="primary" if cfg["mode_affichage"]=="photos_live" else "secondary", use_container_width=True, on_click=set_state, args=("photos_live", False, False))
                
                if is_super_admin:
                    st.divider()
                    if st.button("🗑️ RESET DONNÉES (Session en cours)", type="primary"): reset_app_data(preserve_config=True); st.success("Reset OK"); time.sleep(1); st.rerun()

            elif menu == "📸 MÉDIATHÈQUE":
                st.title("📸 MÉDIATHÈQUE")
                files = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
                if not files: st.info("Vide.")
                else:
                    if "selected_images" not in st.session_state: st.session_state.selected_images = []
                    c1, c2 = st.columns(2)
                    # ZIP ALL
                    zip_all = BytesIO()
                    with zipfile.ZipFile(zip_all, "w") as z:
                        for f in files: z.write(f, os.path.basename(f))
                    c1.download_button("📥 TOUT TÉLÉCHARGER", data=zip_all.getvalue(), file_name="all.zip", mime="application/zip", use_container_width=True)
                    
                    # ZIP SELECT
                    if st.session_state.selected_images:
                        zip_sel = BytesIO()
                        with zipfile.ZipFile(zip_sel, "w") as z:
                            for f in st.session_state.selected_images: z.write(f, os.path.basename(f))
                        c2.download_button(f"📥 SÉLECTION ({len(st.session_state.selected_images)})", data=zip_sel.getvalue(), file_name="selection.zip", mime="application/zip", use_container_width=True, type="primary")
                    
                    st.divider()
                    cols = st.columns(5)
                    for i, f in enumerate(files):
                        with cols[i%5]:
                            st.image(f, use_container_width=True)
                            sel = st.checkbox("Select", key=f"s_{f}", value=(f in st.session_state.selected_images), label_visibility="collapsed")
                            if sel and f not in st.session_state.selected_images: st.session_state.selected_images.append(f)
                            elif not sel and f in st.session_state.selected_images: st.session_state.selected_images.remove(f)

            elif menu == "📱 TEST MOBILE":
                st.title("TEST MOBILE")
                st.markdown(f'<a href="/?mode=vote&test_admin=true" target="_blank">Ouvrir Simulateur</a>', unsafe_allow_html=True)
                if st.button("Générer 10 votes aléatoires"):
                    v = load_json(VOTES_FILE, {}); d = load_json(DETAILED_VOTES_FILE, [])
                    for _ in range(10):
                        ch = random.sample(cfg["candidats"], 3)
                        for x, p in zip(ch, [5,3,1]): v[x] = v.get(x,0)+p
                        d.append({"Utilisateur": "Bot", "Choix 1": ch[0], "Choix 2": ch[1], "Choix 3": ch[2]})
                    save_json(VOTES_FILE, v); save_json(DETAILED_VOTES_FILE, d); st.success("Fait!")

            elif menu == "⚙️ CONFIG":
                st.title("CONFIG")
                t1, t2 = st.tabs(["Général", "Candidats"])
                with t1:
                    new_t = st.text_input("Titre", value=cfg["titre_mur"])
                    if st.button("Sauver"): cfg["titre_mur"] = new_t; save_config(); st.rerun()
                    upl = st.file_uploader("Logo", type=["png","jpg"])
                    if upl: 
                        b64 = process_logo(upl)
                        if b64: cfg["logo_b64"] = b64; save_config(); st.rerun()
                with t2:
                    st.subheader(f"Candidats ({len(cfg['candidats'])})")
                    c_a, c_b = st.columns([4,1])
                    new_c = c_a.text_input("Nouveau")
                    if c_b.button("Ajouter") and new_c: cfg['candidats'].append(new_c); save_config(); st.rerun()
                    
                    to_remove = []
                    for i, cand in enumerate(cfg['candidats']):
                        c1, c2, c3 = st.columns([0.5, 3, 2])
                        with c1: 
                            if cand in cfg.get("candidats_images",{}): st.image(BytesIO(base64.b64decode(cfg["candidats_images"][cand])), width=40)
                        with c2: st.write(cand)
                        with c3: 
                            u = st.file_uploader(f"Img {i}", key=f"u_{i}", label_visibility="collapsed")
                            if u: 
                                p = process_participant_image(u)
                                if p: cfg["candidats_images"][cand] = p; save_config(); st.rerun()
                            if st.button("🗑️", key=f"d_{i}"): to_remove.append(cand)
                    if to_remove: 
                        for c in to_remove: cfg['candidats'].remove(c)
                        save_config(); st.rerun()

            elif menu == "📊 DATA":
                st.title("DATA")
                vote_counts, nb_unique_voters, rank_dist = get_advanced_stats()
                v = load_json(VOTES_FILE, {})
                df = pd.DataFrame([{"Candidat": k, "Points": v} for k,v in v.items()]).sort_values("Points", ascending=False)
                st.table(df)
                
                if PDF_AVAILABLE:
                    st.download_button("📄 Rapport PDF", data=create_pdf_results(cfg['titre_mur'], df, nb_unique_voters, df['Points'].sum()), file_name="Rapport.pdf", mime="application/pdf")

# =========================================================
# 2. APPLICATION MOBILE
# =========================================================
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, default_config)
    st.markdown("""<style>.stApp {background-color:black !important; color:white !important;}</style>""", unsafe_allow_html=True)
    
    if cfg["mode_affichage"] == "photos_live":
        if "user_pseudo" not in st.session_state: st.session_state.user_pseudo = "Anonyme"
    elif cfg["mode_affichage"] == "votes":
        if "user_pseudo" in st.session_state and st.session_state.user_pseudo == "Anonyme": del st.session_state["user_pseudo"]; st.rerun()

    if "user_pseudo" not in st.session_state:
        st.subheader("Identification")
        pseudo = st.text_input("Votre prénom :")
        if st.button("ENTRER", type="primary") and pseudo:
            st.session_state.user_pseudo = pseudo.strip(); st.rerun()
    else:
        if cfg["mode_affichage"] == "photos_live":
            st.info("📸 ENVOYER UNE PHOTO")
            up = st.file_uploader("Galerie", type=['png','jpg'])
            cam = st.camera_input("Camera")
            f = up if up else cam
            if f:
                with open(os.path.join(LIVE_DIR, f"live_{uuid.uuid4().hex}.jpg"), "wb") as o: o.write(f.getbuffer())
                st.success("Envoyé !"); time.sleep(1); st.rerun()
        elif cfg["mode_affichage"] == "votes" and (cfg["session_ouverte"] or is_test_admin):
            if st.session_state.vote_success: st.success("Vote enregistré !"); st.stop()
            choix = st.multiselect("3 choix :", cfg["candidats"], max_selections=3)
            if len(choix)==3 and st.button("VALIDER"):
                v = load_json(VOTES_FILE, {}); d = load_json(DETAILED_VOTES_FILE, [])
                for x,p in zip(choix, [5,3,1]): v[x] = v.get(x,0)+p
                d.append({"Utilisateur": st.session_state.user_pseudo, "Choix 1": choix[0], "Choix 2": choix[1], "Choix 3": choix[2]})
                save_json(VOTES_FILE, v); save_json(DETAILED_VOTES_FILE, d); st.session_state.vote_success = True; st.rerun()
        else: st.info("En attente...")

# =========================================================
# 3. MUR SOCIAL
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    cfg = load_json(CONFIG_FILE, default_config)
    st_autorefresh(interval=4000)
    st.markdown("""<style>.stApp { background-color: black !important; color: white !important; }</style>""", unsafe_allow_html=True)
    st.markdown(f'<div class="social-header"><h1 class="social-title">{cfg["titre_mur"]}</h1></div>', unsafe_allow_html=True)
    
    mode = cfg.get("mode_affichage")
    
    # --- CHARGEMENT JS ET CSS ---
    try:
        with open("style.css", "r", encoding="utf-8") as f: css = f.read()
        with open("robot.js", "r", encoding="utf-8") as f: js = f.read()
    except: css=""; js=""

    # --- CONFIG ROBOT ---
    robot_mode = "attente"
    if mode == "votes" and not cfg["session_ouverte"] and not cfg["reveal_resultats"]: robot_mode = "vote_off"
    elif mode == "photos_live": robot_mode = "photos"
    
    js_config = f"<script>window.robotConfig = {{ mode: '{robot_mode}', titre: '{cfg['titre_mur'].replace('\'','\\\'')}' }};</script>"
    
    # IMPORT MAP (Pour que le robot fonctionne)
    imp = '<script type="importmap">{ "imports": { "three": "https://unpkg.com/three@0.160.0/build/three.module.js" } }</script>'

    if mode == "attente":
        logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="width:300px; margin-bottom:20px;">' if cfg.get("logo_b64") else ""
        html = f"""<!DOCTYPE html><html><head><style>body{{margin:0;background:black;overflow:hidden;width:100vw;height:100vh;}}{css}</style></head>
        <body>{js_config}<div id="welcome-text" style="position:absolute;top:20%;width:100%;text-align:center;color:white;font-family:Arial;font-weight:bold;font-size:60px;">{logo_html}<br>BIENVENUE</div><div id="robot-bubble" class="bubble">...</div><div id="robot-container"></div>{imp}<script type="module">{js}</script></body></html>"""
        components.html(html, height=1000)

    elif mode == "votes":
        if cfg.get("reveal_resultats"):
            # PODIUM LOGIQUE
            v = load_json(VOTES_FILE, {})
            # ... (Logique podium ici, simplifiée pour l'affichage)
            components.html(f"""<div style="color:white;text-align:center;font-size:50px;">🏆 PODIUM 🏆<br>(Affichage à compléter selon design)</div>""", height=900)
        elif cfg["session_ouverte"]:
            host = st.context.headers.get('host', 'localhost')
            qr = qrcode.make(f"https://{host}/?mode=vote"); buf = BytesIO(); qr.save(buf, format="PNG"); b64 = base64.b64encode(buf.getvalue()).decode()
            logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="width:200px;">' if cfg.get("logo_b64") else ""
            components.html(f"""<div style="text-align:center;color:white;font-family:Arial;">{logo_html}<h1>VOTES OUVERTS</h1><img src="data:image/png;base64,{b64}" width="400"><p>Scannez pour voter !</p></div>""", height=900)
        else:
            # VOTE OFF AVEC ROBOT
            overlay = f"<div style='position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);z-index:10;text-align:center;background:rgba(0,0,0,0.8);padding:40px;border-radius:20px;border:4px solid #E2001A;'><h1>MERCI !</h1><h2>Votes clos.</h2></div>"
            html = f"""<!DOCTYPE html><html><head><style>body{{margin:0;background:black;overflow:hidden;}}{css}</style></head>
            <body>{js_config}{overlay}<div id="robot-bubble" class="bubble">...</div><div id="robot-container"></div>{imp}<script type="module">{js}</script></body></html>"""
            components.html(html, height=1000)

    elif mode == "photos_live":
        # PHOTOS LIVE AVEC ROBOT EN FOND
        photos = glob.glob(f"{LIVE_DIR}/*"); img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f,'rb').read()).decode()}" for f in photos[-30:]]) if photos else "[]"
        bubbles = f"""<script>setTimeout(()=>{{
            var c=document.createElement('div');c.style.cssText='position:fixed;top:0;left:0;width:100%;height:100%;z-index:5;pointer-events:none;';document.body.appendChild(c);
            var imgs={img_js}; imgs.forEach(src=>{{
                var el=document.createElement('img');el.src=src;
                el.style.cssText='position:absolute;width:200px;height:200px;border-radius:50%;border:3px solid gold;object-fit:cover;opacity:0.9;left:'+Math.random()*90+'%;top:'+Math.random()*90+'%';
                c.appendChild(el);
            }});
        }}, 500);</script>"""
        html = f"""<!DOCTYPE html><html><head><style>body{{margin:0;background:black;overflow:hidden;}}{css}</style></head>
        <body>{js_config}<div id="robot-bubble" class="bubble">...</div><div id="robot-container"></div>{imp}<script type="module">{js}</script>{bubbles}</body></html>"""
        components.html(html, height=1000)
