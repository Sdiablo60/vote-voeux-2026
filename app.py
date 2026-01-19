simport streamlit as st
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

# --- RECUPERATION PARAMETRES URL ---
qp = st.query_params
mode_url = qp.get("mode", "wall") 
admin_url = qp.get("admin", "false")
is_blocked = qp.get("blocked") == "true"
is_test_admin = qp.get("test_admin") == "true"

est_admin = (admin_url == "true")
# On est utilisateur SEULEMENT si c'est écrit "vote" explicitement
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

st.markdown("""
<style>
    /* === CSS GLOBAL (ADMIN & DÉFAUT) === */
    
    /* 1. Configuration de base : Fond Blanc pour l'Admin */
    .stApp {
        background-color: #FFFFFF;
        color: black;
    }
    
    /* 2. Masquer le menu hamburger et le footer Streamlit partout */
    [data-testid="stHeader"], footer, header { 
        display: none !important; 
        height: 0 !important;
        visibility: hidden !important;
    }

    /* 3. Style des Boutons (Commun) */
    button[kind="secondary"] { color: #333 !important; border-color: #333 !important; }
    button[kind="primary"] { color: white !important; background-color: #E2001A !important; border: none; }
    button[kind="primary"]:hover { background-color: #C20015 !important; }
    
    /* 4. Styles Admin Spécifiques (Cartes, Login, Sidebar) */
    .session-card { background-color: #f8f9fa; padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; border: 1px solid #ddd; margin-bottom: 20px; }
    .session-title { color: #E2001A; font-size: 24px; font-weight: 900; text-transform: uppercase; margin-bottom: 10px; }
    .login-container { max-width: 400px; margin: 100px auto; padding: 40px; background: #f8f9fa; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); text-align: center; border: 1px solid #ddd; }
    .login-title { color: #E2001A; font-size: 24px; font-weight: bold; margin-bottom: 20px; text-transform: uppercase; }
    .stTextInput input { text-align: center; font-size: 18px; }
    
    section[data-testid="stSidebar"] { background-color: #f0f2f6 !important; }
    section[data-testid="stSidebar"] button[kind="primary"] { background-color: #E2001A !important; width: 100%; border-radius: 5px; margin-bottom: 5px; }
    
    /* Cache les ascenseurs */
    ::-webkit-scrollbar { display: none; }
</style>
""", unsafe_allow_html=True)
# =========================================================
# 3. DONNEES & CONFIGURATIONS PAR DEFAUT
# =========================================================
blank_config = {
    "mode_affichage": "attente", 
    "titre_mur": "TITRE À DÉFINIR", 
    "session_ouverte": False, 
    "reveal_resultats": False,
    "timestamp_podium": 0,
    "logo_b64": None, 
    "candidats": [], 
    "candidats_images": {}, 
    "points_ponderation": [5, 3, 1],
    "effect_intensity": 25, 
    "effect_speed": 15, 
    "screen_effects": {"attente": "Aucun", "votes_open": "Aucun", "votes_closed": "Aucun", "podium": "Aucun", "photos_live": "Aucun"},
    "session_id": ""
}

default_config = {
    "mode_affichage": "attente", 
    "titre_mur": "CONCOURS VIDÉO 2026", 
    "session_ouverte": False, 
    "reveal_resultats": False,
    "timestamp_podium": 0,
    "logo_b64": None,
    "candidats": ["BU PAX", "BU FRET", "BU B2B", "RH", "IT", "DPMI", "FINANCES", "AO", "QSSE", "DIRECTION"],
    "candidats_images": {}, 
    "points_ponderation": [5, 3, 1],
    "effect_intensity": 25, 
    "effect_speed": 15, 
    "screen_effects": {"attente": "Aucun", "votes_open": "Aucun", "votes_closed": "Aucun", "podium": "Aucun", "photos_live": "Aucun"},
    "session_id": str(uuid.uuid4())
}

default_users = {
    "admin": {"pwd": "ADMIN_LIVE_MASTER", "role": "Super Admin", "perms": ["all"]}
}

# =========================================================
# 4. FONCTIONS UTILITAIRES
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
                content = f.read().strip()
                if not content: return default
                return json.loads(content)
        except: return default
    return default

def save_json(file, data):
    try:
        safe_data = clean_for_json(data)
        with open(str(file), "w", encoding='utf-8') as f:
            json.dump(safe_data, f, ensure_ascii=False, indent=4)
    except Exception as e: print(f"Erreur Save: {e}")

def save_config():
    save_json(CONFIG_FILE, st.session_state.config)

def reset_app_data(init_mode="blank", preserve_config=False):
    for f in [VOTES_FILE, VOTERS_FILE, PARTICIPANTS_FILE, DETAILED_VOTES_FILE]:
        if os.path.exists(f): os.remove(f)
    files = glob.glob(f"{LIVE_DIR}/*")
    for f in files: os.remove(f)
    if not preserve_config:
        if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
        if init_mode == "blank": st.session_state.config = copy.deepcopy(blank_config)
        elif init_mode == "demo": st.session_state.config = copy.deepcopy(default_config)
    
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
    live_archive = os.path.join(archive_path, "galerie_live_users")
    if os.path.exists(LIVE_DIR): shutil.copytree(LIVE_DIR, live_archive)
    return folder_name

def restore_session_from_archive(folder_name):
    source_path = os.path.join(ARCHIVE_DIR, folder_name)
    reset_app_data(init_mode="none")
    for f in [VOTES_FILE, CONFIG_FILE, VOTERS_FILE, PARTICIPANTS_FILE, DETAILED_VOTES_FILE]:
        src_f = os.path.join(source_path, f)
        if os.path.exists(src_f): shutil.copy2(src_f, ".")
    src_live = os.path.join(source_path, "galerie_live_users")
    if os.path.exists(src_live):
        if os.path.exists(LIVE_DIR): shutil.rmtree(LIVE_DIR)
        shutil.copytree(src_live, LIVE_DIR)

def delete_archived_session(folder_name):
    path = os.path.join(ARCHIVE_DIR, folder_name)
    if os.path.exists(path): shutil.rmtree(path)

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")

def process_logo(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        img.thumbnail((600, 600), Image.Resampling.BICUBIC)
        buf = BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return base64.b64encode(buf.getvalue()).decode()
    except: return None

def process_participant_image(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        if img.mode != "RGB": img = img.convert("RGB")
        img.thumbnail((300, 300), Image.Resampling.BICUBIC)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=60, optimize=True)
        return base64.b64encode(buf.getvalue()).decode()
    except: return None

def inject_visual_effect(effect_name, intensity, speed):
    if effect_name == "Aucun":
        components.html("<script>var old = window.parent.document.getElementById('effect-layer'); if(old) old.remove();</script>", height=0)
        return
    pass 

def set_state(mode, open_s, reveal):
    st.session_state.config["mode_affichage"] = mode
    st.session_state.config["session_ouverte"] = open_s
    st.session_state.config["reveal_resultats"] = reveal
    if reveal: st.session_state.config["timestamp_podium"] = time.time()
    save_config()

def reset_vote_callback():
    st.session_state.vote_success = False
    if "widget_choix" in st.session_state: st.session_state.widget_choix = []
    if "widget_choix_force" in st.session_state: st.session_state.widget_choix_force = []

# --- STATS ---
def get_advanced_stats():
    details = load_json(DETAILED_VOTES_FILE, [])
    vote_counts = {}
    rank_dist = {}
    unique_voters = set()
    for record in details:
        unique_voters.add(record.get('Utilisateur'))
        for idx, k in enumerate(["Choix 1 (5pts)", "Choix 2 (3pts)", "Choix 3 (1pt)"]):
            cand = record.get(k)
            if cand:
                vote_counts[cand] = vote_counts.get(cand, 0) + 1
                if cand not in rank_dist: rank_dist[cand] = {1:0, 2:0, 3:0}
                rank_dist[cand][idx+1] += 1
    return vote_counts, len(unique_voters), rank_dist

if PDF_AVAILABLE:
    class PDFReport(FPDF):
        def header(self):
            if "logo_b64" in st.session_state.config and st.session_state.config["logo_b64"]:
                try:
                    logo_data = base64.b64decode(st.session_state.config["logo_b64"])
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                        tmp.write(logo_data)
                        tmp_path = tmp.name
                    self.image(tmp_path, 10, 8, 45) 
                    os.unlink(tmp_path) 
                except: pass
            self.set_font('Arial', 'B', 15)
            self.set_text_color(226, 0, 26)
            self.cell(50) 
            self.cell(0, 10, f"{st.session_state.config.get('titre_mur', 'Session')}", 0, 1, 'L')
            self.set_font('Arial', 'I', 10)
            self.set_text_color(100, 100, 100)
            self.cell(50)
            self.cell(0, 10, f"Rapport généré le: {datetime.now().strftime('%d/%m/%Y à %H:%M')}", 0, 1, 'L')
            self.ln(20)
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def draw_summary_box(pdf, nb_voters, nb_votes, total_points):
        pdf.set_fill_color(245, 245, 245)
        pdf.set_draw_color(200, 200, 200)
        pdf.rect(10, pdf.get_y(), 190, 15, 'DF') 
        pdf.set_y(pdf.get_y() + 4)
        pdf.set_font("Arial", 'B', 10)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(63, 8, f"TOTAL VOTANTS (UNIQUES): {nb_voters}", 0, 0, 'C')
        pdf.cell(63, 8, f"TOTAL VOTES: {nb_votes}", 0, 0, 'C')
        pdf.cell(63, 8, f"TOTAL POINTS DISTRIBUÉS: {total_points}", 0, 1, 'C')
        pdf.ln(12) 

    def create_pdf_results(title, df, nb_voters, total_points):
        pdf = PDFReport()
        pdf.add_page()
        pdf.set_auto_page_break(auto=False)
        nb_votes_total = df['Nb Votes'].sum()
        draw_summary_box(pdf, nb_voters, nb_votes_total, total_points)
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(0)
        pdf.cell(0, 8, txt="VISUALISATION ANALYTIQUE DES SCORES", ln=True, align='L')
        pdf.ln(1)
        max_points = df['Points'].max() if not df.empty else 1
        page_width = pdf.w - 2 * pdf.l_margin
        label_width = 50
        max_bar_width = page_width - label_width - 25
        bar_height = 3.0
        spacing = 1.5
        pdf.set_font("Arial", size=9)
        for i, row in df.iterrows():
            cand = str(row['Candidat']).encode('latin-1', 'replace').decode('latin-1')
            points = row['Points']
            pdf.set_text_color(0)
            pdf.cell(label_width, bar_height, cand, 0, 0, 'R')
            if max_points > 0: width = (points / max_points) * max_bar_width
            else: width = 0
            x_start = pdf.get_x() + 2
            y_start = pdf.get_y()
            pdf.set_fill_color(245, 245, 245)
            pdf.rect(x_start, y_start, max_bar_width, bar_height, 'F')
            pdf.set_fill_color(226, 0, 26) 
            if width > 0: pdf.rect(x_start, y_start, width, bar_height, 'F')
            pdf.set_xy(x_start + max_bar_width + 4, y_start)
            pdf.cell(20, bar_height, f"{points} pts", 0, 1, 'L')
            pdf.ln(bar_height + spacing)
        return pdf.output(dest='S').encode('latin-1')

# --- INIT SESSION ---
if "config" not in st.session_state:
    st.session_state.config = load_json(CONFIG_FILE, default_config)

# =========================================================
# 1. CONSOLE ADMIN
# =========================================================
if est_admin:
    
    if "auth" not in st.session_state: st.session_state["auth"] = False
    if "user_role" not in st.session_state: st.session_state["user_role"] = None
    if "user_perms" not in st.session_state: st.session_state["user_perms"] = []
    
    # Chargement DB Users
    users_db = load_json(USERS_FILE, default_users)
    if "admin" not in users_db: 
        users_db["admin"] = default_users["admin"]
        save_json(USERS_FILE, users_db)

    # --- ECRAN DE LOGIN ---
    if not st.session_state["auth"]:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown('<div class="login-container"><div class="login-title">🔒 ADMIN ACCESS</div>', unsafe_allow_html=True)
            username = st.text_input("Identifiant", label_visibility="collapsed", placeholder="Identifiant")
            pwd = st.text_input("Mot de passe", type="password", label_visibility="collapsed", placeholder="Mot de passe")
            
            if st.button("ENTRER", use_container_width=True, type="primary"):
                if username in users_db and users_db[username]["pwd"] == pwd:
                    st.session_state["auth"] = True
                    st.session_state["current_user"] = username
                    st.session_state["user_role"] = users_db[username].get("role", "Utilisateur")
                    st.session_state["user_perms"] = users_db[username].get("perms", [])
                    st.session_state["session_active"] = False 
                    st.rerun()
                else: st.error("Identifiants incorrects")
            st.markdown('</div>', unsafe_allow_html=True)
            
    else:
        # --- LOGIQUE PERMISSIONS ---
        perms = st.session_state["user_perms"]
        is_super_admin = "all" in perms
        
        # --- DASHBOARD SESSIONS ---
        if "session_active" not in st.session_state or not st.session_state["session_active"]:
            st.markdown("<br>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                st.markdown(f'<div class="session-card"><div class="session-title">🗂️ GESTIONNAIRE DE SESSIONS</div>', unsafe_allow_html=True)
                st.write(f"Connecté en tant que : **{st.session_state['user_role']}**")
                
                st.button(f"📂 OUVRIR : {st.session_state.config.get('titre_mur', 'Session')}", type="primary", use_container_width=True, on_click=lambda: st.session_state.update({"session_active": True}))
                
                if is_super_admin or "config" in perms:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.button("✨ CRÉER UNE NOUVELLE SESSION VIERGE", type="secondary", use_container_width=True, on_click=lambda: (archive_current_session(), reset_app_data("blank"), st.session_state.update({"session_active": True})))
                
                st.markdown('</div>', unsafe_allow_html=True) # Fin card
                
                st.divider()
                st.subheader("📦 Archives des sessions")
                archives = sorted([d for d in os.listdir(ARCHIVE_DIR) if os.path.isdir(os.path.join(ARCHIVE_DIR, d))], reverse=True)
                
                if not archives:
                    st.caption("Aucune archive disponible.")
                else:
                    for arc in archives:
                        # Affichage en mode liste propre
                        c_name, c_act = st.columns([3, 1])
                        c_name.text(f"📁 {arc}")
                        
                        sub_c1, sub_c2 = c_act.columns(2)
                        if sub_c1.button("♻️", key=f"res_{arc}", help="Restaurer"):
                             archive_current_session()
                             restore_session_from_archive(arc)
                             st.session_state.config = load_json(CONFIG_FILE, default_config)
                             st.session_state["session_active"] = True
                             st.toast("Session restaurée !")
                             time.sleep(1); st.rerun()
                        
                        if is_super_admin:
                             if sub_c2.button("🗑️", key=f"del_{arc}", help="Supprimer"):
                                  delete_archived_session(arc); st.rerun()
                        
        else:
            # --- INTERFACE ADMIN COMPLETE ---
            cfg = st.session_state.config
            with st.sidebar:
                if st.button("⬅️ CHANGER DE SESSION"):
                    st.session_state["session_active"] = False; st.rerun()
                st.divider()
                if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), use_container_width=True)
                st.header(f"MENU ({st.session_state['current_user']})")
                
                if "admin_menu" not in st.session_state: st.session_state.admin_menu = "🔴 PILOTAGE LIVE"

                if is_super_admin or "pilotage" in perms:
                    if st.button("🔴 PILOTAGE LIVE", type="primary" if st.session_state.admin_menu == "🔴 PILOTAGE LIVE" else "secondary"): 
                        st.session_state.admin_menu = "🔴 PILOTAGE LIVE"; st.rerun()
                
                if is_super_admin or "test_mobile" in perms:
                    if st.button("📱 TEST MOBILE", type="primary" if st.session_state.admin_menu == "📱 TEST MOBILE" else "secondary"): 
                        st.session_state.admin_menu = "📱 TEST MOBILE"; st.rerun()
                
                if is_super_admin or "config" in perms:
                    if st.button("⚙️ CONFIG", type="primary" if st.session_state.admin_menu == "⚙️ CONFIG" else "secondary"): 
                        st.session_state.admin_menu = "⚙️ CONFIG"; st.rerun()
                
                if is_super_admin or "mediatheque" in perms:
                    if st.button("📸 MÉDIATHÈQUE", type="primary" if st.session_state.admin_menu == "📸 MÉDIATHÈQUE" else "secondary"): 
                        st.session_state.admin_menu = "📸 MÉDIATHÈQUE"; st.rerun()
                
                if is_super_admin or "data" in perms:
                    if st.button("📊 DATA", type="primary" if st.session_state.admin_menu == "📊 DATA" else "secondary"): 
                        st.session_state.admin_menu = "📊 DATA"; st.rerun()
                
                if is_super_admin:
                    st.markdown("---")
                    if st.button("👥 UTILISATEURS", type="primary" if st.session_state.admin_menu == "👥 UTILISATEURS" else "secondary"): 
                        st.session_state.admin_menu = "👥 UTILISATEURS"; st.rerun()

                st.divider()
                # BOUTON MUR SOCIAL (FORCE MODE WALL)
                host_url = st.context.headers.get("host", "")
                st.markdown(f'<a href="https://{host_url}/?mode=wall" target="_blank" class="custom-link-btn btn-red">📺 OUVRIR MUR SOCIAL</a>', unsafe_allow_html=True)
                if st.button("🔓 DÉCONNEXION"): 
                    st.session_state["auth"] = False
                    st.session_state["session_active"] = False
                    st.rerun()

            menu = st.session_state.admin_menu

            if menu == "🔴 PILOTAGE LIVE" and (is_super_admin or "pilotage" in perms):
                st.title("🔴 PILOTAGE LIVE")
                st.subheader("Séquenceur")
                etat = "Inconnu"
                if cfg["mode_affichage"] == "attente": etat = "ACCUEIL"
                elif cfg["mode_affichage"] == "votes":
                    if cfg["reveal_resultats"]: etat = "PODIUM"
      elif cfg["session_ouverte"]:
            # === VOTES OUVERTS (LAYOUT IDENTIQUE CAPTURE : 3 COLONNES + INSTRUCTIONS) ===
            host = st.context.headers.get('host', 'localhost')
            qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            
            # 1. LOGO (Transdev)
            logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" class="logo-img">' if cfg.get("logo_b64") else ""
            
            # 2. MARQUEE (Derniers votes)
            recent_votes = load_json(DETAILED_VOTES_FILE, [])
            voter_names = [v['Utilisateur'] for v in recent_votes[-20:]][::-1]
            voter_string = " &nbsp;&nbsp;•&nbsp;&nbsp; ".join(voter_names) if voter_names else "En attente des premiers votes..."
            
            # 3. LISTES CANDIDATS (GAUCHE / DROITE)
            cands = cfg["candidats"]
            mid = (len(cands) + 1) // 2
            left_cands = cands[:mid]
            right_cands = cands[mid:]
            
            def gen_pill_html(clist, imgs):
                h = ""
                for c in clist:
                    # Avatar par défaut ou Image Custom
                    im_html = '<div class="default-avatar">👤</div>' 
                    if c in imgs: 
                        im_html = f'<img src="data:image/png;base64,{imgs[c]}" class="custom-avatar">'
                    
                    h += f"""
                    <div class="cand-pill">
                        <div class="pill-icon">{im_html}</div>
                        <div class="pill-name">{c}</div>
                    </div>
                    """
                return h
                
            left_html = gen_pill_html(left_cands, cfg.get("candidats_images", {}))
            right_html = gen_pill_html(right_cands, cfg.get("candidats_images", {}))

            # 4. RENDU HTML/CSS COMPLET
            components.html(f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700;900&display=swap');
                
                body {{ 
                    background-color: black; margin: 0; padding: 0; 
                    font-family: 'Roboto', sans-serif; overflow: hidden; height: 100vh;
                    display: flex; flex-direction: column;
                }}

                /* --- HEADER ROUGE --- */
                .header-top {{
                    background-color: #E2001A;
                    height: 8vh; width: 100%;
                    display: flex; align-items: center; justify-content: center;
                    border-bottom: 3px solid white;
                    z-index: 10;
                }}
                .header-title {{
                    color: white; font-weight: 900; font-size: 3vh; text-transform: uppercase; letter-spacing: 1px;
                }}

                /* --- MARQUEE ROUGE FONCÉ --- */
                .marquee-bar {{
                    background-color: #C20015; /* Rouge légèrement plus sombre */
                    height: 5vh; width: 100%;
                    display: flex; align-items: center;
                    color: white; font-weight: bold; font-size: 1.8vh;
                    overflow: hidden;
                    border-bottom: 1px solid #333;
                }}
                .marquee-label {{
                    background: #90000e; padding: 0 20px; height: 100%; 
                    display: flex; align-items: center; z-index: 2; white-space: nowrap;
                }}
                .marquee-text {{
                    display: inline-block; padding-left: 100%; animation: scroll 20s linear infinite; white-space: nowrap;
                }}
                @keyframes scroll {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}

                /* --- CONTENU PRINCIPAL (GRID 3 COLONNES) --- */
                .main-container {{
                    flex: 1; display: flex; width: 100%; height: 87vh;
                    align-items: center; justify-content: center;
                    padding-top: 2vh; box-sizing: border-box;
                }}
                .col-side {{ width: 25%; display: flex; flex-direction: column; justify-content: center; padding: 0 2vw; }}
                .col-center {{ width: 40%; display: flex; flex-direction: column; align-items: center; justify-content: center; }}

                /* --- ELEMENTS CENTRAUX --- */
                .logo-img {{ height: 8vh; margin-bottom: 1vh; }}
                .main-title {{ 
                    color: #E2001A; font-size: 6vh; font-weight: 900; margin: 0; 
                    text-transform: uppercase; text-shadow: 0 0 20px rgba(226,0,26,0.5);
                }}
                .sub-title {{ color: white; font-size: 2.5vh; margin: 0 0 2vh 0; font-weight: normal; }}
                
                .info-box {{
                    background-color: #1a1a1a; border: 1px solid #333;
                    border-radius: 15px; padding: 1.5vh 2vw;
                    text-align: center; color: #ccc; font-size: 1.8vh;
                    margin-bottom: 3vh; width: 80%;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.5);
                }}
                .info-highlight {{ color: white; font-weight: bold; margin-bottom: 5px; display: block; }}
                .warning-text {{ color: #ff4444; font-weight: bold; font-size: 1.6vh; margin-top: 5px; display: block; }}
                
                .qr-container {{
                    background: white; padding: 15px; border-radius: 20px;
                    box-shadow: 0 0 50px rgba(255,255,255,0.1);
                    animation: pulse-qr 3s infinite alternate;
                }}
                .qr-img {{ width: 22vh; height: 22vh; display: block; }}

                @keyframes pulse-qr {{ from {{ box-shadow: 0 0 20px rgba(255,255,255,0.1); }} to {{ box-shadow: 0 0 40px rgba(255,255,255,0.3); }} }}

                /* --- PILLS CANDIDATS --- */
                .cand-pill {{
                    background: #1e1e1e; /* Gris foncé comme sur l'image */
                    border-radius: 50px;
                    padding: 1vh 1vw; margin-bottom: 1.5vh;
                    display: flex; align-items: center;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                    border: 1px solid #2a2a2a;
                    transition: transform 0.2s;
                }}
                .cand-pill:hover {{ transform: scale(1.02); border-color: #E2001A; }}
                
                .pill-icon {{
                    width: 5vh; height: 5vh; border-radius: 50%; background: #2c2c2c;
                    display: flex; align-items: center; justify-content: center;
                    margin-right: 15px; overflow: hidden; flex-shrink: 0;
                }}
                .default-avatar {{ font-size: 3vh; }}
                .custom-avatar {{ width: 100%; height: 100%; object-fit: cover; }}
                
                .pill-name {{
                    color: white; font-weight: bold; font-size: 2vh; text-transform: uppercase;
                    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
                }}

            </style>
            </head>
            <body>
                <div class="header-top">
                    <div class="header-title">{cfg['titre_mur']}</div>
                </div>

                <div class="marquee-bar">
                    <div class="marquee-label">DERNIERS VOTES :</div>
                    <div style="flex:1; overflow:hidden; position:relative; height:100%;">
                        <div class="marquee-text">{voter_string}</div>
                    </div>
                </div>

                <div class="main-container">
                    <div class="col-side" style="align-items: flex-end;">
                        {left_html}
                    </div>

                    <div class="col-center">
                        {logo_html}
                        <h1 class="main-title">VOTES OUVERTS</h1>
                        <h3 class="sub-title">Scannez pour voter</h3>
                        
                        <div class="info-box">
                            <span class="info-highlight">3 choix par préférence :</span>
                            🥇 1er (5 pts) &nbsp;|&nbsp; 🥈 2ème (3 pts) &nbsp;|&nbsp; 🥉 3ème (1 pt)
                            <span class="warning-text">🚫 INTERDIT DE VOTER POUR SON ÉQUIPE</span>
                        </div>

                        <div class="qr-container">
                            <img src="data:image/png;base64,{qr_b64}" class="qr-img">
                        </div>
                    </div>

                    <div class="col-side" style="align-items: flex-start;">
                        {right_html}
                    </div>
                </div>
            </body>
            </html>
            """, height=980, scrolling=False)
            
        else:
            # VOTE FERMÉ (Attente avec Robot)
            logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="width:350px; margin-bottom:10px;">' if cfg.get("logo_b64") else ""
            html_code = f"""<!DOCTYPE html><html><head>{internal_css_base}</head><body>{js_config}
            <div id="safe-zone"></div>
            <div style='position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); z-index: 10; display:flex; flex-direction:column; align-items:center; justify-content:center; pointer-events: none;'>
                <div style='border: 5px solid #E2001A; padding: 40px; border-radius: 30px; background: rgba(0,0,0,0.85); max-width: 800px; text-align: center; box-shadow: 0 0 50px black;'>
                    {logo_html}
                    <h1 class="neon-title" style='font-size:60px; margin:0;'>MERCI !</h1>
                    <h2 style='color:white; font-size:35px; margin-top:20px; font-weight:normal; text-shadow: 0 0 10px black;'>Les votes sont clos.</h2>
                    <h3 style='color:#cccccc; font-size:25px; margin-top:10px; font-style:italic; text-shadow: 0 0 10px black;'>Veuillez patienter... Nous allons découvrir les GAGNANTS !</h3>
                </div>
            </div>
            <div id="robot-bubble" class="bubble" style="z-index: 20;">...</div>
            <div id="robot-container" style="z-index: 5; pointer-events: none;"></div>
            {import_map}<script type="module">{js_content}</script></body></html>"""
            components.html(html_code, height=1000, scrolling=False)

    elif mode == "photos_live":
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        logo_data = cfg.get("logo_b64", "")
        photos = glob.glob(f"{LIVE_DIR}/*")
        img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-40:]]) if photos else "[]"
        center_html_content = f"""<div id='center-box' style='position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); z-index:10; text-align:center; background:rgba(0,0,0,0.85); padding:20px; border-radius:30px; border:2px solid #E2001A; width:400px; box-shadow:0 0 50px rgba(0,0,0,0.8); pointer-events: none;'><h1 class="neon-title" style='font-size:28px; margin:0 0 15px 0;'>MUR PHOTOS LIVE</h1>{f'<img src="data:image/png;base64,{logo_data}" style="width:350px; margin-bottom:10px;">' if logo_data else ''}<div style='background:white; padding:15px; border-radius:15px; display:inline-block;'><img src='data:image/png;base64,{qr_b64}' style='width:250px;'></div><h2 style='color:white; margin-top:15px; font-size:22px; font-family:Arial; line-height:1.3; text-shadow: 0 0 10px black;'>Partagez vos sourires<br>et vos moments forts !</h2></div>"""
        
        bubbles_script = f"""<script>setTimeout(function() {{ var container = document.createElement('div'); container.id = 'live-container'; container.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:1;overflow:hidden;background:transparent;pointer-events:none;'; document.body.appendChild(container); var centerDiv = document.createElement('div'); centerDiv.innerHTML = `{center_html_content}`; document.body.appendChild(centerDiv); const imgs = {img_js}; const bubbles = []; imgs.forEach((src, i) => {{ const bSize = Math.floor(Math.random() * 300) + 150; const el = document.createElement('img'); el.src = src; el.style.cssText = 'position:absolute; width:'+bSize+'px; height:'+bSize+'px; border-radius:50%; border:4px solid #E2001A; object-fit:cover; z-index:50; opacity:0.9;'; let x = Math.random() * (window.innerWidth - bSize); let y = Math.random() * (window.innerHeight - bSize); let angle = Math.random() * Math.PI * 2; let speed = 1.5 + Math.random() * 1.5; container.appendChild(el); bubbles.push({{el, x, y, vx: Math.cos(angle)*speed, vy: Math.sin(angle)*speed, size: bSize}}); }}); function animateBubbles() {{ bubbles.forEach(b => {{ b.x += b.vx; b.y += b.vy; if(b.x <= 0 || b.x + b.size >= window.innerWidth) b.vx *= -1; if(b.y <= 0 || b.y + b.size >= window.innerHeight) b.vy *= -1; b.el.style.transform = 'translate3d(' + b.x + 'px, ' + b.y + 'px, 0)'; }}); requestAnimationFrame(animateBubbles); }} animateBubbles(); }}, 500);</script>"""
        
        html_code = f"""<!DOCTYPE html><html><head>{internal_css_base}</head><body>{js_config}
        <div id="safe-zone"></div>
        <div id="robot-bubble" class="bubble" style="z-index: 20;">...</div>
        <div id="robot-container" style="z-index: 5; pointer-events: none;"></div>
        {import_map}<script type="module">{js_content}</script>{bubbles_script}</body></html>"""
        components.html(html_code, height=1000, scrolling=False)
    
    else:
        st.markdown(f"<div class='full-screen-center'><h1 style='color:white;'>EN ATTENTE...</h1></div>", unsafe_allow_html=True)
