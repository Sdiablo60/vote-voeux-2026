import streamlit as st
import os, glob, base64, qrcode, json, time, uuid, textwrap, zipfile, shutil
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

# TENTATIVE D'IMPORT DE FPDF
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# SECURITE PIL
Image.MAX_IMAGE_PIXELS = None 

# CONFIGURATION PAGE
st.set_page_config(page_title="Régie Master", layout="wide", initial_sidebar_state="expanded")

# RECUPERATION PARAMETRES URL
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
is_blocked = st.query_params.get("blocked") == "true"
is_test_admin = st.query_params.get("test_admin") == "true"

# DOSSIERS & FICHIERS
LIVE_DIR = "galerie_live_users"
ARCHIVE_DIR = "_archives_sessions"
VOTES_FILE = "votes.json"
CONFIG_FILE = "config_mur.json"
VOTERS_FILE = "voters.json"
PARTICIPANTS_FILE = "participants.json"
DETAILED_VOTES_FILE = "detailed_votes.json"

for d in [LIVE_DIR, ARCHIVE_DIR]:
    os.makedirs(d, exist_ok=True)

# =========================================================
# 2. CSS GLOBAL (BASE ADMIN BLANCHE & STRUCTURE)
# =========================================================
st.markdown("""
<style>
    /* PAR DEFAUT : FOND BLANC (Pour l'Admin) */
    .stApp {
        background-color: #FFFFFF;
        color: black;
    }
    
    /* FIX DU HEADER ROUGE POUR EVITER LE CLIGNOTEMENT SUR LE MUR SOCIAL */
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
    
    .social-header { 
        position: fixed; top: 0; left: 0; width: 100%; height: 12vh; 
        background: #E2001A !important; 
        display: flex; align-items: center; justify-content: center; 
        z-index: 999999 !important; /* Priorité maximale */
        border-bottom: 5px solid white; 
    }
    .social-title { color: white !important; font-size: 40px !important; font-weight: bold; margin: 0; text-transform: uppercase; }

    /* STOP SCROLLING ULTIME (Global) */
    html, body, [data-testid="stAppViewContainer"] {
        overflow: hidden !important;
        height: 100vh !important;
        width: 100vw !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Cacher scrollbars */
    ::-webkit-scrollbar { display: none; }
    
    /* Boutons Généraux */
    button[kind="secondary"] { color: #333 !important; border-color: #333 !important; }
    button[kind="primary"] { color: white !important; background-color: #E2001A !important; border: none; }
    button[kind="primary"]:hover { background-color: #C20015 !important; }
    
    /* Login Box */
    .login-container {
        max-width: 400px; margin: 100px auto; padding: 40px;
        background: #f8f9fa; border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1); text-align: center; border: 1px solid #ddd;
    }
    .login-title { color: #E2001A; font-size: 24px; font-weight: bold; margin-bottom: 20px; text-transform: uppercase; }
    .stTextInput input { text-align: center; font-size: 18px; }
    
    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #f0f2f6 !important; }
    section[data-testid="stSidebar"] button[kind="primary"] {
        background-color: #E2001A !important; width: 100%; border-radius: 5px; margin-bottom: 5px;
    }
    section[data-testid="stSidebar"] button[kind="secondary"] {
        background-color: #333333 !important; width: 100%; border-radius: 5px; margin-bottom: 5px; border: none !important; color: white !important;
    }
    
    /* STYLE DES BOUTONS D'EXPORT */
    .blue-anim-btn button {
        background-color: #2980b9 !important;
        color: white !important;
        border: none !important;
        transition: all 0.3s ease !important;
        font-weight: bold !important;
    }
    .blue-anim-btn button:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 5px 15px rgba(41, 128, 185, 0.4) !important;
        background-color: #3498db !important;
    }

    /* LIENS ADMIN STYLÉS EN BOUTONS */
    a.custom-link-btn {
        display: block !important; 
        text-align: center !important; 
        padding: 12px 20px !important; 
        border-radius: 8px !important;
        text-decoration: none !important; 
        font-weight: bold !important; 
        margin-bottom: 10px !important;
        color: white !important; 
        transition: transform 0.2s !important;
        width: 100% !important;
        box-sizing: border-box !important;
        line-height: 1.5 !important;
    }
    a.custom-link-btn:hover { transform: scale(1.02); opacity: 0.9; }
    .btn-red { background-color: #E2001A !important; }
    .btn-blue { background-color: #2980b9 !important; }

    /* Header Social (Visible uniquement sur le Mur via HTML, caché ici pour Admin via JS si besoin, mais géré par le mode) */
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

# --- ACTIONS & VISUAL ---
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

# --- GENERATEUR PDF ---
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
        pdf.ln(6) 
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, txt="MATRICE DÉTAILLÉE DES RÉSULTATS", ln=True, align='L')
        pdf.ln(1)
        pdf.set_fill_color(50, 50, 50)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 9) 
        row_h = 5 
        pdf.cell(100, row_h, "Candidat", 1, 0, 'C', 1)
        pdf.cell(45, row_h, "Points Total", 1, 0, 'C', 1)
        pdf.cell(45, row_h, "Nb Votes", 1, 1, 'C', 1)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", size=8)
        fill = False
        pdf.ln()
        for i, row in df.iterrows():
            cand = str(row['Candidat']).encode('latin-1', 'replace').decode('latin-1')
            if fill: pdf.set_fill_color(245, 245, 245)
            else: pdf.set_fill_color(255, 255, 255)
            pdf.cell(100, row_h, cand, 1, 0, 'L', 1)
            pdf.cell(45, row_h, str(row['Points']), 1, 0, 'C', 1)
            pdf.cell(45, row_h, str(row['Nb Votes']), 1, 1, 'C', 1)
            fill = not fill
            pdf.ln()
        return pdf.output(dest='S').encode('latin-1')

    def create_pdf_distribution(title, rank_dist, nb_voters):
        pdf = PDFReport()
        pdf.add_page()
        draw_summary_box(pdf, nb_voters, "N/A", "N/A")
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, txt="ANALYSE DE LA RÉPARTITION DES RANGS", ln=True, align='L')
        pdf.ln(5)
        pdf.set_fill_color(50, 50, 50)
        pdf.set_text_color(255)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(80, 8, "Candidat", 1, 0, 'C', 1)
        pdf.cell(35, 8, "1ere Place (Or)", 1, 0, 'C', 1)
        pdf.cell(35, 8, "2eme Place (Arg)", 1, 0, 'C', 1)
        pdf.cell(35, 8, "3eme Place (Brz)", 1, 1, 'C', 1)
        pdf.set_text_color(0)
        pdf.set_font("Arial", size=10)
        fill = False
        pdf.ln()
        sorted_dist = sorted(rank_dist.items(), key=lambda x: x[1][1], reverse=True)
        for cand, ranks in sorted_dist:
            cand_txt = str(cand).encode('latin-1', 'replace').decode('latin-1')
            if fill: pdf.set_fill_color(245, 245, 245)
            else: pdf.set_fill_color(255, 255, 255)
            pdf.cell(80, 8, cand_txt, 1, 0, 'L', 1)
            pdf.cell(35, 8, str(ranks[1]), 1, 0, 'C', 1)
            pdf.cell(35, 8, str(ranks[2]), 1, 0, 'C', 1)
            pdf.cell(35, 8, str(ranks[3]), 1, 1, 'C', 1)
            fill = not fill
            pdf.ln()
        return pdf.output(dest='S').encode('latin-1')

    def create_pdf_audit(title, df, nb_voters):
        pdf = PDFReport()
        pdf.add_page()
        draw_summary_box(pdf, nb_voters, len(df), "N/A")
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, txt="JOURNAL D'AUDIT COMPLET", ln=True, align='L')
        pdf.ln(5)
        cols = df.columns.tolist() 
        col_w = 190 / len(cols)
        pdf.set_fill_color(50, 50, 50)
        pdf.set_text_color(255)
        pdf.set_font("Arial", 'B', 9)
        for col in cols:
            c_txt = str(col).encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(col_w, 8, c_txt, 1, 0, 'C', 1)
        pdf.ln()
        pdf.set_text_color(0)
        pdf.set_font("Arial", size=8)
        fill = False
        for i, row in df.iterrows():
            if fill: pdf.set_fill_color(245, 245, 245)
            else: pdf.set_fill_color(255, 255, 255)
            for col in cols:
                txt = str(row[col]).encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(col_w, 8, txt, 1, 0, 'C', 1)
            pdf.ln()
            fill = not fill
        return pdf.output(dest='S').encode('latin-1')

# --- INIT SESSION ---
if "config" not in st.session_state:
    st.session_state.config = load_json(CONFIG_FILE, default_config)

# =========================================================
# 1. CONSOLE ADMIN
# =========================================================
if est_admin:
    
    if "auth" not in st.session_state: st.session_state["auth"] = False
    
    if not st.session_state["auth"]:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown('<div class="login-container"><div class="login-title">🔒 ADMIN ACCESS</div>', unsafe_allow_html=True)
            pwd = st.text_input("Code de sécurité", type="password", label_visibility="collapsed")
            if st.button("ENTRER", use_container_width=True, type="primary"):
                if pwd == "ADMIN_LIVE_MASTER":
                    st.session_state["auth"] = True
                    st.session_state["session_active"] = False 
                    st.rerun()
                else: st.error("Code incorrect")
            st.markdown('</div>', unsafe_allow_html=True)
            
    else:
        if "session_active" not in st.session_state or not st.session_state["session_active"]:
            st.title("🗂️ GESTIONNAIRE DE SESSIONS")
            st.info("Avant d'accéder au pilotage, choisissez une session.")
            current_title = st.session_state.config.get("titre_mur", "Session Inconnue")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### 🚀 Continuer")
                if st.button(f"OUVRIR : {current_title}", type="primary", use_container_width=True):
                    st.session_state["session_active"] = True
                    st.rerun()
            with c2:
                st.markdown("### ✨ Créer")
                if st.button("CRÉER UNE NOUVELLE SESSION VIERGE", type="primary", use_container_width=True):
                    archive_current_session()
                    reset_app_data(init_mode="blank")
                    st.session_state["session_active"] = True
                    st.success("Nouvelle session vierge prête !")
                    time.sleep(1)
                    st.rerun()
            st.divider()
            st.markdown("### 📚 Historique / Archives")
            archives = sorted([d for d in os.listdir(ARCHIVE_DIR) if os.path.isdir(os.path.join(ARCHIVE_DIR, d))], reverse=True)
            if not archives: st.caption("Aucune archive trouvée.")
            else:
                for arc in archives:
                    with st.expander(f"📁 {arc}"):
                        c_res, c_del = st.columns([3, 1])
                        if c_res.button(f"Restaurer {arc}", key=f"res_{arc}"):
                            archive_current_session()
                            restore_session_from_archive(arc)
                            st.session_state.config = load_json(CONFIG_FILE, default_config)
                            st.session_state["session_active"] = True
                            st.success("Session restaurée !")
                            time.sleep(1); st.rerun()
                        confirm = c_del.checkbox("Confirmer", key=f"chk_{arc}")
                        if c_del.button("🗑️", key=f"del_{arc}", disabled=not confirm):
                            delete_archived_session(arc); st.rerun()
        else:
            cfg = st.session_state.config
            with st.sidebar:
                if st.button("⬅️ CHANGER DE SESSION"):
                    st.session_state["session_active"] = False; st.rerun()
                st.divider()
                if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), use_container_width=True)
                st.header("MENU")
                if "admin_menu" not in st.session_state: st.session_state.admin_menu = "🔴 PILOTAGE LIVE"
                
                if st.button("🔴 PILOTAGE LIVE", type="primary" if st.session_state.admin_menu == "🔴 PILOTAGE LIVE" else "secondary"): 
                    st.session_state.admin_menu = "🔴 PILOTAGE LIVE"; st.rerun()
                if st.button("⚙️ CONFIG", type="primary" if st.session_state.admin_menu == "⚙️ CONFIG" else "secondary"): 
                    st.session_state.admin_menu = "⚙️ CONFIG"; st.rerun()
                if st.button("📸 MÉDIATHÈQUE", type="primary" if st.session_state.admin_menu == "📸 MÉDIATHÈQUE" else "secondary"): 
                    st.session_state.admin_menu = "📸 MÉDIATHÈQUE"; st.rerun()
                if st.button("📊 DATA", type="primary" if st.session_state.admin_menu == "📊 DATA" else "secondary"): 
                    st.session_state.admin_menu = "📊 DATA"; st.rerun()
                
                menu = st.session_state.admin_menu
                st.divider()
                st.markdown("""
                    <a href="/" target="_blank" class="custom-link-btn btn-red">📺 OUVRIR MUR SOCIAL</a>
                    <a href="/?mode=vote&test_admin=true" target="_blank" class="custom-link-btn btn-blue">📱 TESTER MOBILE (ILLIMITÉ)</a>
                """, unsafe_allow_html=True)
                if st.button("🔓 DÉCONNEXION"): 
                    st.session_state["auth"] = False
                    st.session_state["session_active"] = False
                    st.rerun()

            if menu == "🔴 PILOTAGE LIVE":
                st.title("🔴 PILOTAGE LIVE")
                st.subheader("Séquenceur")
                etat = "Inconnu"
                if cfg["mode_affichage"] == "attente": etat = "ACCUEIL"
                elif cfg["mode_affichage"] == "votes":
                    if cfg["reveal_resultats"]: etat = "PODIUM"
                    elif cfg["session_ouverte"]: etat = "VOTES OUVERTS"
                    else: etat = "VOTES FERMÉS"
                elif cfg["mode_affichage"] == "photos_live": etat = "PHOTOS LIVE"
                st.info(f"État actuel : **{etat}**")
                c1, c2, c3, c4 = st.columns(4)
                c1.button("🏠 ACCUEIL", use_container_width=True, type="primary" if cfg["mode_affichage"]=="attente" else "secondary", on_click=set_state, args=("attente", False, False))
                c2.button("🗳️ VOTES ON", use_container_width=True, type="primary" if (cfg["mode_affichage"]=="votes" and cfg["session_ouverte"]) else "secondary", on_click=set_state, args=("votes", True, False))
                c3.button("🔒 VOTES OFF", use_container_width=True, type="primary" if (cfg["mode_affichage"]=="votes" and not cfg["session_ouverte"] and not cfg["reveal_resultats"]) else "secondary", on_click=set_state, args=("votes", False, False))
                c4.button("🏆 PODIUM", use_container_width=True, type="primary" if cfg["reveal_resultats"] else "secondary", on_click=set_state, args=("votes", False, True))
                st.markdown("---")
                st.button("📸 MUR PHOTOS LIVE", use_container_width=True, type="primary" if cfg["mode_affichage"]=="photos_live" else "secondary", on_click=set_state, args=("photos_live", False, False))
                st.divider()
                with st.expander("🚨 ZONE DE DANGER"):
                    st.write("Attention : Cela efface tous les votes et les photos, mais garde votre configuration (Candidats, Titre, Logo).")
                    if st.button("🗑️ RESET DONNÉES (Session en cours)", type="primary"): 
                        reset_app_data(preserve_config=True)
                        st.success("Données remises à zéro !")
                        time.sleep(1)
                        st.rerun()

            elif menu == "⚙️ CONFIG":
                st.title("⚙️ CONFIGURATION")
                t1, t2 = st.tabs(["Général", "Candidats & Images"])
                with t1:
                    if cfg["titre_mur"] == "TITRE À DÉFINIR": st.error("⚠️ Veuillez définir un titre")
                    new_t = st.text_input("Titre", value=cfg["titre_mur"])
                    if st.button("Sauver Titre"): st.session_state.config["titre_mur"] = new_t; save_config(); st.rerun()
                    upl = st.file_uploader("Logo (PNG Transparent)", type=["png", "jpg"])
                    if upl: 
                        processed_logo = process_logo(upl)
                        if processed_logo:
                            st.session_state.config["logo_b64"] = processed_logo
                            save_config(); st.rerun()
                with t2:
                    st.subheader(f"Liste des participants ({len(cfg['candidats'])}/15)")
                    if not cfg["candidats"]: st.error("⚠️ La liste est vide ! Ajoutez des participants pour commencer.")
                    if len(cfg['candidats']) < 15:
                        c_add, c_btn = st.columns([4, 1])
                        new_cand = c_add.text_input("Nouveau participant", key="new_cand_input")
                        if c_btn.button("➕ Ajouter") and new_cand:
                            if new_cand.strip() not in cfg['candidats']:
                                cfg['candidats'].append(new_cand.strip())
                                save_config(); st.rerun()
                            else: st.error("Existe déjà !")
                    else: st.warning("Maximum atteint.")
                    st.divider()
                    candidates_to_remove = []
                    for i, cand in enumerate(cfg['candidats']):
                        c1, c2, c3 = st.columns([0.5, 3, 2])
                        with c1:
                            if cand in cfg.get("candidats_images", {}): st.image(BytesIO(base64.b64decode(cfg["candidats_images"][cand])), width=40)
                            else: st.write("🚫")
                        with c2:
                            new_name = st.text_input(f"Participant {i+1}", value=cand, key=f"edit_{i}", label_visibility="collapsed")
                            if new_name != cand and new_name:
                                cfg['candidats'][i] = new_name
                                if cand in cfg.get("candidats_images", {}): cfg["candidats_images"][new_name] = cfg["candidats_images"].pop(cand)
                                save_config(); st.rerun()
                        with c3:
                            col_up, col_del = st.columns([3, 1])
                            up_img = col_up.file_uploader(f"Img {cand}", type=["png", "jpg"], key=f"up_{i}", label_visibility="collapsed")
                            if up_img: 
                                if "candidats_images" not in st.session_state.config: st.session_state.config["candidats_images"] = {}
                                processed = process_participant_image(up_img)
                                if processed:
                                    current_img = st.session_state.config["candidats_images"].get(cand)
                                    if processed != current_img:
                                        st.session_state.config["candidats_images"][cand] = processed
                                        save_config(); st.toast(f"✅ Image {cand} sauvegardée"); time.sleep(0.5); st.rerun()
                            if col_del.button("🗑️", key=f"del_{i}"): candidates_to_remove.append(cand)
                    if candidates_to_remove:
                        for c in candidates_to_remove:
                            cfg['candidats'].remove(c)
                            if c in cfg.get("candidats_images", {}): del cfg["candidats_images"][c]
                        save_config(); st.rerun()

            elif menu == "📸 MÉDIATHÈQUE":
                st.title("📸 MÉDIATHÈQUE")
                files = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
                
                # --- ACTIONS GLOBALES ---
                st.markdown("### 📤 Actions Export")
                
                c1, c2 = st.columns(2)
                
                # --- SÉLECTEUR DE VUE ---
                c_mode, c_vide = st.columns([2, 2])
                with c_mode:
                    mode_view = st.radio("Style d'affichage :", ["🖼️ Vignettes (Icônes)", "📄 Liste (Noms)"], horizontal=True, label_visibility="collapsed")
                
                with c1:
                    if files:
                        zip_buffer_all = BytesIO()
                        with zipfile.ZipFile(zip_buffer_all, "w") as zf:
                            # RENOMMAGE DES FICHIERS POUR L'EXPORT ZIP
                            export_date = datetime.now().strftime("%Y-%m-%d")
                            for idx, file_path in enumerate(files):
                                ext = os.path.splitext(file_path)[1]
                                new_name = f"photo_Live{idx+1:02d}_{export_date}{ext}"
                                zf.write(file_path, arcname=new_name)
                            
                        st.markdown('<div class="blue-anim-btn">', unsafe_allow_html=True)
                        st.download_button("📥 TÉLÉCHARGER TOUTE LA GALERIE (ZIP)", data=zip_buffer_all.getvalue(), file_name=f"galerie_complete_{int(time.time())}.zip", mime="application/zip", use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.button("📥 TÉLÉCHARGER TOUT (VIDE)", disabled=True, use_container_width=True)

                st.divider()
                
                if not files: st.info("Aucune photo.")
                else:
                    st.write("**Sélectionnez les photos :**")
                    
                    if mode_view == "🖼️ Vignettes (Icônes)":
                        cols = st.columns(8) # 8 colonnes pour faire petit
                    else:
                        cols = st.columns(5) # 5 colonnes pour la liste
                    
                    new_selection = []
                    
                    for i, f in enumerate(files):
                        col = cols[i % len(cols)]
                        with col:
                            # NOMMAGE "photo_Live01.jpg" POUR L'AFFICHAGE LISTE
                            ext = os.path.splitext(f)[1]
                            display_name = f"photo_Live{i+1:02d}{ext}"
                            
                            if mode_view == "🖼️ Vignettes (Icônes)":
                                st.image(f, use_container_width=True)
                                if st.checkbox("Sel.", key=f"chk_{os.path.basename(f)}"): new_selection.append(f)
                            else:
                                st.markdown(f"<div style='font-size:12px; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; font-family:monospace;'>📷 {display_name}</div>", unsafe_allow_html=True)
                                if st.checkbox("Sel.", key=f"chk_list_{os.path.basename(f)}"): new_selection.append(f)
                                st.markdown("---")
                    
                    st.write("---")
                    
                    with c2:
                        if new_selection:
                            zip_buffer_sel = BytesIO()
                            with zipfile.ZipFile(zip_buffer_sel, "w") as zf:
                                for idx, file_path in enumerate(new_selection): 
                                    ext = os.path.splitext(file_path)[1]
                                    export_date = datetime.now().strftime("%Y-%m-%d")
                                    new_name = f"selection_Live{idx+1:02d}_{export_date}{ext}"
                                    zf.write(file_path, arcname=new_name)
                            st.markdown('<div class="blue-anim-btn">', unsafe_allow_html=True)
                            st.download_button(f"📥 TÉLÉCHARGER SÉLECTION ({len(new_selection)})", data=zip_buffer_sel.getvalue(), file_name="selection.zip", mime="application/zip", use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        else:
                            st.button("📥 TÉLÉCHARGER SÉLECTION (0)", disabled=True, use_container_width=True)

                st.markdown("<br><br><br>", unsafe_allow_html=True)
                
                with st.expander("🚨 ZONE DE DANGER (SUPPRESSION TOTALE)"):
                    st.write("Attention, cette action est irréversible.")
                    if st.button("🗑️ TOUT SUPPRIMER DÉFINITIVEMENT", type="primary", use_container_width=True):
                        files = glob.glob(f"{LIVE_DIR}/*")
                        for f in files: os.remove(f)
                        st.success("Suppression OK"); time.sleep(1); st.rerun()

            elif menu == "📊 DATA":
                st.title("📊 DONNÉES & RÉSULTATS")
                
                # --- CALCULS DONNEES ---
                votes = load_json(VOTES_FILE, {})
                vote_counts, nb_unique_voters, rank_dist = get_advanced_stats()
                
                all_cands_data = []
                total_points_session = 0
                for c in cfg["candidats"]:
                    p = votes.get(c, 0)
                    total_points_session += p
                    all_cands_data.append({
                        "Candidat": c,
                        "Points": p,
                        "Nb Votes": vote_counts.get(c, 0)
                    })
                
                df_totals = pd.DataFrame(all_cands_data).sort_values(by='Points', ascending=False)
                
                # --- SECTION 1: RESULTATS ---
                st.subheader("🏆 Classement Général")
                c_chart, c_data = st.columns([1, 1]) 
                
                with c_chart:
                    chart = alt.Chart(df_totals).mark_bar(color="#E2001A").encode(
                        x=alt.X('Points'), 
                        y=alt.Y('Candidat', sort='-x'), 
                        tooltip=['Candidat', 'Points', 'Nb Votes']
                    ).properties(height=350) 
                    st.altair_chart(chart, use_container_width=True)
                
                with c_data:
                    st.dataframe(df_totals, height=350, use_container_width=True, hide_index=True)
                
                # Exports Résultats
                st.markdown("##### 📥 Exporter le Rapport de Résultats")
                c1, c2, c3 = st.columns(3)
                if PDF_AVAILABLE:
                    st.markdown('<div class="blue-anim-btn">', unsafe_allow_html=True)
                    c1.download_button("📄 Rés. + Graphique (PDF)", data=create_pdf_results(cfg['titre_mur'], df_totals, nb_unique_voters, total_points_session), file_name=f"Resultats_{sanitize_filename(cfg['titre_mur'])}.pdf", mime="application/pdf", use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="blue-anim-btn">', unsafe_allow_html=True)
                    c2.download_button("📄 Analyse Répartition (PDF)", data=create_pdf_distribution(cfg['titre_mur'], rank_dist, nb_unique_voters), file_name=f"Repartition_{sanitize_filename(cfg['titre_mur'])}.pdf", mime="application/pdf", use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="blue-anim-btn">', unsafe_allow_html=True)
                c3.download_button("📊 Données Résultats (CSV)", data=df_totals.to_csv(index=False).encode('utf-8'), file_name=f"Resultats_{sanitize_filename(cfg['titre_mur'])}.csv", mime="text/csv", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

                st.divider()

                # --- SECTION 2: AUDIT ---
                st.subheader("📝 Journal d'Audit (Détails des votes)")
                raw_details = load_json(DETAILED_VOTES_FILE, [])
                if raw_details:
                    df_audit = pd.DataFrame(raw_details)
                    if 'Date' in df_audit.columns:
                        df_audit = df_audit.drop(columns=['Date'])
                        
                    st.dataframe(df_audit, use_container_width=True, height=400)
                    
                    st.markdown("##### 📥 Exporter l'Audit")
                    c4, c5 = st.columns(2)
                    if PDF_AVAILABLE:
                        st.markdown('<div class="blue-anim-btn">', unsafe_allow_html=True)
                        c4.download_button("📄 Audit Détaillé (PDF)", data=create_pdf_audit(cfg['titre_mur'], df_audit, nb_unique_voters), file_name=f"Audit_{sanitize_filename(cfg['titre_mur'])}.pdf", mime="application/pdf", use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="blue-anim-btn">', unsafe_allow_html=True)
                    c5.download_button("📊 Audit Détaillé (CSV)", data=df_audit.to_csv(index=False).encode('utf-8'), file_name=f"Audit_{sanitize_filename(cfg['titre_mur'])}.csv", mime="text/csv", use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("Aucun vote enregistré pour le moment.")

# =========================================================
# 2. APPLICATION MOBILE (Vote)
# =========================================================
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, default_config)
    st.markdown("""
        <style>
            .stApp {background-color:black !important; color:white !important;} 
            [data-testid='stHeader'] {display:none;}
            .block-container {padding: 1rem !important;}
            h1, h2, h3, p, div, span, label { color: white !important; }
        </style>
    """, unsafe_allow_html=True)
    
    curr_sess = cfg.get("session_id", "init")
    if "vote_success" not in st.session_state: st.session_state.vote_success = False
    if "rules_accepted" not in st.session_state: st.session_state.rules_accepted = False
    if "cam_reset_id" not in st.session_state: st.session_state.cam_reset_id = 0

    if cfg["mode_affichage"] == "photos_live":
        if "user_pseudo" not in st.session_state or st.session_state.user_pseudo != "Anonyme": st.session_state.user_pseudo = "Anonyme"
    elif cfg["mode_affichage"] == "votes":
        if "user_pseudo" in st.session_state and st.session_state.user_pseudo == "Anonyme": del st.session_state["user_pseudo"]; st.rerun()

    if cfg["mode_affichage"] != "photos_live":
        if not is_test_admin:
            components.html(f"""<script>
                var sS = "{curr_sess}";
                var lS = localStorage.getItem('VOTE_SID_2026');
                if(lS !== sS) {{ localStorage.removeItem('HAS_VOTED_2026'); localStorage.setItem('VOTE_SID_2026', sS); if(window.parent.location.href.includes('blocked=true')) {{ window.parent.location.href = window.parent.location.href.replace('&blocked=true',''); }} }}
                if(localStorage.getItem('HAS_VOTED_2026') === 'true') {{ window.parent.document.body.innerHTML = '<div style="background:black;color:white;text-align:center;height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;"><h1 style="color:#E2001A;font-size:50px;">MERCI !</h1><h2>Vote déjà enregistré sur cet appareil.</h2></div>'; }}
            </script>""", height=0)
        else:
            st.info("⚠️ MODE TEST ADMIN : Votes illimités autorisés.")
        
    if "user_pseudo" not in st.session_state:
        st.subheader("Identification")
        if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), width=100)
        pseudo = st.text_input("Veuillez entrer votre prénom ou Pseudo :")
        if st.button("ENTRER", type="primary", use_container_width=True) and pseudo:
            st.session_state.user_pseudo = pseudo.strip()
            parts = load_json(PARTICIPANTS_FILE, [])
            parts.append(pseudo.strip())
            save_json(PARTICIPANTS_FILE, parts)
            st.rerun()
    else:
        if cfg["mode_affichage"] == "photos_live":
            st.info("📸 ENVOYER UNE PHOTO")
            up_key = f"uploader_{st.session_state.cam_reset_id}"
            cam_key = f"camera_{st.session_state.cam_reset_id}"
            uploaded_file = st.file_uploader("Choisir dans la galerie", type=['png', 'jpg', 'jpeg'], key=up_key)
            cam_file = st.camera_input("Prendre une photo", key=cam_key)
            final_file = uploaded_file if uploaded_file else cam_file
            if final_file:
                fname = f"live_{uuid.uuid4().hex}_{int(time.time())}.jpg"
                with open(os.path.join(LIVE_DIR, fname), "wb") as f: f.write(final_file.getbuffer())
                st.success("Photo envoyée !")
                st.session_state.cam_reset_id += 1; time.sleep(1); st.rerun()
        
        elif (cfg["mode_affichage"] == "votes" and (cfg["session_ouverte"] or is_test_admin)):
            st.write(f"Bonjour **{st.session_state.user_pseudo}**")
            if not st.session_state.rules_accepted:
                st.info("⚠️ **RÈGLES DU VOTE**")
                st.markdown("1. Sélectionnez **3 vidéos**.\n2. 🥇 1er = **5 pts**\n3. 🥈 2ème = **3 pts**\n4. 🥉 3ème = **1 pt**\n\n**Vote unique et définitif.**")
                if st.button("J'AI COMPRIS, JE VOTE !", type="primary", use_container_width=True): st.session_state.rules_accepted = True; st.rerun()
            else:
                choix = st.multiselect("Vos 3 vidéos préférées :", cfg["candidats"], max_selections=3, key="widget_choix")
                if len(choix) == 3:
                    if st.button("VALIDER (DÉFINITIF)", type="primary", use_container_width=True):
                        vts = load_json(VOTES_FILE, {})
                        pts = cfg.get("points_ponderation", [5, 3, 1])
                        for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                        save_json(VOTES_FILE, vts)
                        details = load_json(DETAILED_VOTES_FILE, [])
                        details.append({"Utilisateur": st.session_state.user_pseudo, "Choix 1 (5pts)": choix[0], "Choix 2 (3pts)": choix[1], "Choix 3 (1pt)": choix[2], "Date": datetime.now().strftime("%H:%M:%S")})
                        save_json(DETAILED_VOTES_FILE, details)
                        st.session_state.vote_success = True
                        st.balloons()
                        st.markdown("""<div style='text-align:center; margin-top:50px; padding:20px;'><h1 style='color:#E2001A;'>MERCI !</h1><h2 style='color:white;'>Vote enregistré.</h2><br><div style='font-size:80px;'>✅</div></div>""", unsafe_allow_html=True)
                        if not is_test_admin: components.html("""<script>localStorage.setItem('HAS_VOTED_2026', 'true');</script>""", height=0); st.stop()
                        else: st.button("🔄 Voter à nouveau (RAZ)", on_click=reset_vote_callback, type="primary"); st.stop()
        
        elif is_test_admin and cfg["mode_affichage"] == "votes":
             st.write(f"Bonjour **{st.session_state.user_pseudo}** (Mode Test Force)")
             choix = st.multiselect("Vos 3 vidéos préférées :", cfg["candidats"], max_selections=3, key="widget_choix_force")
             if len(choix) == 3:
                if st.button("VALIDER (MODE TEST)", type="primary"):
                    vts = load_json(VOTES_FILE, {})
                    pts = cfg.get("points_ponderation", [5, 3, 1])
                    for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                    save_json(VOTES_FILE, vts)
                    st.balloons()
                    st.success("Vote Test OK")
                    st.button("🔄 Voter à nouveau (RAZ)", on_click=reset_vote_callback, type="primary")
                    st.stop()
        else: st.info("⏳ En attente...")

# =========================================================
# 3. MUR SOCIAL
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    cfg = load_json(CONFIG_FILE, default_config)
    refresh_rate = 5000 if (cfg.get("mode_affichage") == "votes" and cfg.get("reveal_resultats")) else 4000
    st_autorefresh(interval=refresh_rate, key="wall_refresh")
    
    # --- CORRECTION FOND NOIR ---
    # On force le fond de l'application à être NOIR pour le Mur Social
    # Cela écrase la configuration blanche de l'Admin définie plus haut
    st.markdown("""
        <style>
            .stApp {
                background-color: black !important;
                color: white !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # HEADER ROUGE EN Z-INDEX MAXIMAL (FIXE)
    st.markdown(f'<div class="social-header"><h1 class="social-title">{cfg["titre_mur"]}</h1></div>', unsafe_allow_html=True)
    
    mode = cfg.get("mode_affichage")
    effects = cfg.get("screen_effects", {})
    effect_name = effects.get("attente" if mode=="attente" else "podium", "Aucun")
    inject_visual_effect(effect_name, 25, 15)

    ph = st.empty()
    
    if mode == "attente":
        try:
            with open("style.css", "r", encoding="utf-8") as f: css_content = f.read()
            with open("robot.js", "r", encoding="utf-8") as f: js_content = f.read()
        except FileNotFoundError:
            css_content = ""; js_content = "console.error('Fichiers manquants');"

        logo_img_tag = ""
        if cfg.get("logo_b64"):
            # MODIFICATION : Taille 350px, Marge 10px
            logo_img_tag = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="width:350px; margin-bottom:10px;">'

        # STRUCTURE ANTI-CLIGNOTEMENT: Texte dans le HTML de l'iframe + Fond noir forcé
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ margin: 0; padding: 0; background-color: black; overflow: hidden; width: 100vw; height: 100vh; }}
                {css_content}
                #welcome-text {{
                    position: absolute; top: 45%; left: 50%; transform: translate(-50%, -50%);
                    text-align: center; color: white; font-family: Arial, sans-serif; z-index: 5;
                    font-size: 70px; font-weight: 900; letter-spacing: 5px; pointer-events: none;
                }}
            </style>
        </head>
        <body>
            <div id="welcome-text">
                {logo_img_tag}<br>BIENVENUE
            </div>
            <div id="robot-bubble" class="bubble">...</div>
            <div id="robot-container"></div>
            
            <script type="importmap">
            {{ "imports": {{ "three": "https://unpkg.com/three@0.160.0/build/three.module.js" }} }}
            </script>
            <script type="module">
                {js_content}
            </script>
        </body>
        </html>
        """
        components.html(html_code, height=1000, scrolling=False)

    elif mode == "votes":
        if cfg.get("reveal_resultats"):
            # CHARGEMENT DES VOTES
            v_data = load_json(VOTES_FILE, {})
            c_imgs = cfg.get("candidats_images", {})
            if not v_data: v_data = {"Personne": 0}
            sorted_unique_scores = sorted(list(set(v_data.values())), reverse=True)
            
            s1 = sorted_unique_scores[0] if len(sorted_unique_scores) > 0 else 0
            rank1 = [c for c, s in v_data.items() if s == s1]
            
            s2 = sorted_unique_scores[1] if len(sorted_unique_scores) > 1 else 0
            rank2 = [c for c, s in v_data.items() if s == s2]
            
            s3 = sorted_unique_scores[2] if len(sorted_unique_scores) > 2 else 0
            rank3 = [c for c, s in v_data.items() if s == s3]
            
            def get_podium_html(cands, score, emoji):
                if not cands: return ""
                html = ""
                for c in cands:
                    if c in c_imgs:
                        img_src = f"data:image/png;base64,{c_imgs[c]}"
                        img_tag = f"<img src='{img_src}' class='p-img'>"
                    else:
                        img_tag = f"<div class='p-placeholder' style='background:#333; display:flex; justify-content:center; align-items:center; font-size:50px;'>{emoji}</div>"
                    html += f"<div class='p-card'>{img_tag}<div class='p-name'>{c}</div><div class='p-score'>{score} pts</div></div>"
                return html

            h1 = get_podium_html(rank1, s1, "🥇")
            h2 = get_podium_html(rank2, s2, "🥈")
            h3 = get_podium_html(rank3, s3, "🥉")
            
            # ATTENTION : DANS LE BLOC CI-DESSOUS (f-string), TOUTES LES ACCOLADES CSS/JS DOIVENT ÊTRE DOUBLÉES {{ }}
            # SEULES LES VARIABLES PYTHON {h1}, {s1}, etc. GARDENT DES ACCOLADES SIMPLES
            components.html(f"""
            <div id="intro-layer" class="intro-overlay">
                <div id="intro-txt" class="intro-text"></div>
                <div id="intro-num" class="intro-count"></div>
            </div>
            
            <audio id="applause-sound" preload="auto">
                <source src="https://www.soundjay.com/human/sounds/applause-01.mp3" type="audio/mpeg">
            </audio>

            <div class="podium-container">
                <div class="column-2">
                    <div class="winners-box rank-2" id="win-2">{h2}</div>
                    <div class="pedestal pedestal-2"><div class="rank-num">2</div></div>
                </div>

                <div class="column-1">
                    <div class="winners-box rank-1" id="win-1">{h1}</div>
                    <div class="pedestal pedestal-1"><div class="rank-num">1</div></div>
                </div>

                <div class="column-3">
                    <div class="winners-box rank-3" id="win-3">{h3}</div>
                    <div class="pedestal pedestal-3"><div class="rank-num">3</div></div>
                </div>
            </div>

            <script>
                const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));
                const layer = document.getElementById('intro-layer');
                const txt = document.getElementById('intro-txt');
                const num = document.getElementById('intro-num');
                const w1 = document.getElementById('win-1');
                const w2 = document.getElementById('win-2');
                const w3 = document.getElementById('win-3');
                const audio = document.getElementById('applause-sound');

                function startConfetti() {{
                    var script = document.createElement('script');
                    script.src = "https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js";
                    script.onload = () => {{
                        var duration = 15 * 1000;
                        var animationEnd = Date.now() + duration;
                        var defaults = {{ startVelocity: 30, spread: 360, ticks: 60, zIndex: 9999 }};
                        var random = (min, max) => Math.random() * (max - min) + min;
                        var interval = setInterval(function() {{
                            var timeLeft = animationEnd - Date.now();
                            if (timeLeft <= 0) {{ return clearInterval(interval); }}
                            var particleCount = 50 * (timeLeft / duration);
                            confetti(Object.assign({{}}, defaults, {{ particleCount, origin: {{ x: random(0.1, 0.3), y: Math.random() - 0.2 }} }}));
                            confetti(Object.assign({{}}, defaults, {{ particleCount, origin: {{ x: random(0.7, 0.9), y: Math.random() - 0.2 }} }}));
                        }}, 250);
                    }};
                    document.body.appendChild(script);
                }}

                async function countdown(seconds, message) {{
                    layer.style.display = 'flex';
                    layer.style.opacity = '1';
                    txt.innerText = message;
                    for(let i=seconds; i>0; i--) {{
                        num.innerText = i;
                        await wait(1000);
                    }}
                    layer.style.opacity = '0';
                    await wait(500); 
                    layer.style.display = 'none';
                }}

                async function runShow() {{
                    // 3ème place
                    await countdown(10, "EN TROISIÈME PLACE AVEC {s3} POINTS...");
                    w3.classList.add('visible');
                    
                    // 2ème place
                    await wait(2000);
                    await countdown(10, "EN SECONDE PLACE AVEC {s2} POINTS...");
                    w2.classList.add('visible');
                    
                    // 1ère place
                    await wait(2000);
                    await countdown(10, "ET ENFIN CELUI QUE TOUT LE MONDE ATTEND... LA PREMIÈRE PLACE AVEC {s1} POINTS...");
                    w1.classList.add('visible');

                    startConfetti();
                    try {{ audio.currentTime = 0; audio.play(); }} catch(e) {{ console.log("Audio play failed due to browser policy"); }}
                }}

                window.parent.document.body.style.backgroundColor = "black";
                runShow();
            </script>
            <style>
                body {{ margin: 0; overflow: hidden; background: black; }}
                
                .podium-container {{
                    position: absolute; bottom: 0; left: 0; width: 100%; height: 100vh;
                    display: flex; justify-content: center; align-items: flex-end;
                    padding-bottom: 20px;
                }}

                /* COLONNES FIXES */
                .column-2 {{ width: 25%; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; margin-right: -20px; z-index: 2; }}
                .column-1 {{ width: 30%; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; z-index: 3; }}
                .column-3 {{ width: 25%; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; margin-left: -20px; z-index: 2; }}

                /* CONTENEUR GAGNANTS (Au-dessus de la marche) - CORRECTION EMPILEMENT VERS LE HAUT */
                .winners-box {{
                    display: flex; 
                    flex-direction: row;        /* Alignement horizontal */
                    flex-wrap: wrap-reverse;    /* Le "wrap" se fait vers le HAUT */
                    justify-content: center;
                    align-items: flex-end;      /* Aligne le bas des cartes */
                    width: 100%;
                    max-width: 320px;           /* Largeur max pour forcer le retour à la ligne après 2 cartes */
                    margin: 0 auto;             /* Centrer dans la colonne */
                    padding-bottom: 0px;
                    opacity: 0; transform: translateY(50px) scale(0.8); /* Caché par défaut */
                    transition: all 1s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                    gap: 10px;
                }}
                .winners-box.visible {{ opacity: 1; transform: translateY(0) scale(1); }}

                /* MARCHES DU PODIUM (DESIGN IMAGE) */
                .pedestal {{
                    width: 100%;
                    background: linear-gradient(to bottom, #333, #000);
                    border-radius: 20px 20px 0 0;
                    box-shadow: 0 -5px 15px rgba(255,255,255,0.1);
                    display: flex; justify-content: center; align-items: center;
                    position: relative;
                }}
                /* Effet de brillance en haut */
                .pedestal::after {{
                    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 5px;
                    box-shadow: 0 0 15px currentColor;
                    border-radius: 20px 20px 0 0;
                }}

                .pedestal-1 {{ height: 350px; border-top: 3px solid #FFD700; color: #FFD700; }}
                .pedestal-2 {{ height: 220px; border-top: 3px solid #C0C0C0; color: #C0C0C0; }}
                .pedestal-3 {{ height: 150px; border-top: 3px solid #CD7F32; color: #CD7F32; }}

                .rank-num {{
                    font-size: 120px; font-weight: 900; font-family: 'Arial Black', sans-serif;
                    opacity: 0.2; /* Transparence pour incruster dans le fond */
                }}

                /* CARTES GAGNANTS (Compactes & Modernes) */
                .p-card {{ 
                    background: rgba(20,20,20,0.8); border-radius: 15px; padding: 10px; 
                    width: 130px; backdrop-filter: blur(5px); 
                    border: 1px solid rgba(255,255,255,0.3); 
                    display:flex; flex-direction:column; align-items:center; 
                    box-shadow: 0 5px 15px rgba(0,0,0,0.5);
                    margin-bottom: 10px; /* Espace entre les lignes */
                }}
                .rank-1 .p-card {{ border-color: #FFD700; background: rgba(40,30,0,0.9); transform: scale(1.1); margin-bottom: 15px; }}
                .rank-2 .p-card {{ border-color: #C0C0C0; }}
                .rank-3 .p-card {{ border-color: #CD7F32; }}

                .p-img, .p-placeholder {{ 
                    width: 70px; height: 70px; border-radius: 50%; 
                    object-fit: cover; border: 3px solid white; margin-bottom: 5px; 
                    display: flex; justify-content: center; align-items: center; 
                }}
                .rank-1 .p-img {{ width: 90px; height: 90px; border-color: #FFD700; }}

                .p-name {{ font-family: Arial; font-size: 14px; font-weight: bold; color: white; margin: 0; text-transform: uppercase; text-align: center; line-height: 1.1; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
                .rank-1 .p-name {{ color: #FFD700; font-size: 18px; }}
                .p-score {{ font-family: Arial; font-size: 12px; color: #ccc; margin-top: 2px; }}
                
                /* COUNTDOWN OVERLAY (TOP OF SCREEN) */
                .intro-overlay {{ 
                    position: fixed; top: 15vh; /* Juste sous le header rouge */
                    left: 0; width: 100vw; height: auto; 
                    z-index: 5000; 
                    display: flex; flex-direction: column; align-items: center; 
                    text-align: center; transition: opacity 0.5s; pointer-events: none; 
                }}
                .intro-text {{ color: white; font-family: Arial; font-size: 40px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; text-shadow: 0 0 20px black; }}
                .intro-count {{ color: #E2001A; font-family: Arial; font-size: 100px; font-weight: 900; margin-top: 10px; text-shadow: 0 0 20px black; }}
            </style>
            """, height=900, scrolling=False)

        else:
            # MODIFICATION : Taille 350px, Marge 10px
            logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="width:350px; margin-bottom:10px;">' if cfg.get("logo_b64") else ""
            ph.markdown(f"<div class='full-screen-center' style='position:fixed; top:0; left:0; width:100vw; height:100vh; display:flex; flex-direction:column; justify-content:center; align-items:center; z-index: 2;'><div style='display:flex; flex-direction:column; align-items:center; justify-content:center;'>{logo_html}<div style='border: 5px solid #E2001A; padding: 50px; border-radius: 40px; background: rgba(0,0,0,0.9);'><h1 style='color:#E2001A; font-size:70px; margin:0;'>VOTES CLÔTURÉS</h1></div></div></div>", unsafe_allow_html=True)

    elif mode == "photos_live":
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        logo_data = cfg.get("logo_b64", "")
        photos = glob.glob(f"{LIVE_DIR}/*")
        img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-40:]]) if photos else "[]"
        
        # MODIFICATION : Taille 350px, Marge 10px pour le logo
        center_html_content = f"""
            <div id='center-box' style='position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); z-index:100; text-align:center; background:rgba(0,0,0,0.85); padding:20px; border-radius:30px; border:2px solid #E2001A; width:400px; box-shadow:0 0 50px rgba(0,0,0,0.8);'>
                <h1 style='color:#E2001A; margin:0 0 15px 0; font-size:28px; font-weight:bold; text-transform:uppercase;'>MUR PHOTOS LIVE</h1>
                {f'<img src="data:image/png;base64,{logo_data}" style="width:350px; margin-bottom:10px;">' if logo_data else ''}
                <div style='background:white; padding:15px; border-radius:15px; display:inline-block;'>
                    <img src='data:image/png;base64,{qr_b64}' style='width:250px;'>
                </div>
                <h2 style='color:white; margin-top:15px; font-size:22px; font-family:Arial; line-height:1.3;'>Partagez vos sourires<br>et vos moments forts !</h2>
            </div>
        """
        components.html(f"""<script>
            var doc = window.parent.document;
            var existing = doc.getElementById('live-container');
            if(existing) existing.remove();
            var container = doc.createElement('div');
            container.id = 'live-container'; 
            container.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:1;overflow:hidden;background:transparent;';
            doc.body.appendChild(container);
            container.innerHTML = `{center_html_content}`;
            const imgs = {img_js}; const bubbles = [];
            const minSize = 60; const maxSize = 160;
            var screenW = window.innerWidth || 1920;
            var screenH = window.innerHeight || 1080;
            imgs.forEach((src, i) => {{
                const bSize = Math.floor(Math.random() * (maxSize - minSize + 1)) + minSize;
                const el = doc.createElement('img'); el.src = src;
                el.style.cssText = 'position:absolute; width:'+bSize+'px; height:'+bSize+'px; border-radius:50%; border:4px solid #E2001A; object-fit:cover; will-change:transform; z-index:50;';
                let x = Math.random() * (screenW - bSize);
                let y = Math.random() * (screenH - bSize);
                let angle = Math.random() * Math.PI * 2;
                let speed = 0.8 + Math.random() * 1.2;
                let vx = Math.cos(angle) * speed;
                let vy = Math.sin(angle) * speed;
                container.appendChild(el); 
                bubbles.push({{el, x: x, y: y, vx, vy, size: bSize}});
            }});
            function animate() {{
                screenW = window.innerWidth || 1920;
                screenH = window.innerHeight || 1080;
                bubbles.forEach(b => {{
                    b.x += b.vx; b.y += b.vy;
                    if(b.x <= 0) {{ b.x=0; b.vx *= -1; }}
                    if(b.x + b.size >= screenW) {{ b.x=screenW-b.size; b.vx *= -1; }}
                    if(b.y <= 0) {{ b.y=0; b.vy *= -1; }}
                    if(b.y + b.size >= screenH) {{ b.y=screenH-b.size; b.vy *= -1; }}
                    b.el.style.transform = 'translate3d(' + b.x + 'px, ' + b.y + 'px, 0)';
                }});
                requestAnimationFrame(animate);
            }}
            animate();
        </script>""", height=900)

    else:
        st.markdown(f"<div class='full-screen-center'><h1 style='color:white;'>EN ATTENTE...</h1></div>", unsafe_allow_html=True)

