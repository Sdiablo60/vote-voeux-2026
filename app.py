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

# TENTATIVE D'IMPORT DE FPDF
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# SECURITE PIL
Image.MAX_IMAGE_PIXELS = None 

# --- CONFIGURATION ---
st.set_page_config(page_title="Régie Master", layout="wide", initial_sidebar_state="expanded")

# Dossiers & Fichiers
LIVE_DIR = "galerie_live_users"
ARCHIVE_DIR = "_archives_sessions"
VOTES_FILE = "votes.json"
CONFIG_FILE = "config_mur.json"
VOTERS_FILE = "voters.json"
PARTICIPANTS_FILE = "participants.json"
DETAILED_VOTES_FILE = "detailed_votes.json"

# --- INIT DOSSIERS ---
for d in [LIVE_DIR, ARCHIVE_DIR]:
    os.makedirs(d, exist_ok=True)

# --- CSS COMMUN (BOUTONS & LOGIN & FOND BLANC) ---
st.markdown("""
<style>
    /* 1. FOND GLOBAL BLANC (Appliqué par défaut partout) */
    .stApp {
        background-color: #FFFFFF !important;
    }
    
    /* 2. STOP SCROLLING ULTIME (Global) */
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
    
    /* Liens externes */
    .custom-link-btn {
        display: block; text-align: center; padding: 12px; border-radius: 8px;
        text-decoration: none !important; font-weight: bold; margin-bottom: 10px;
        color: white !important; transition: transform 0.2s;
    }
    .custom-link-btn:hover { transform: scale(1.02); }
    .btn-red { background-color: #E2001A; }
    .btn-blue { background-color: #2980b9; }

    /* Header Social (Caché pour l'admin) */
    .social-header { display: none; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION VIERGE ---
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

# --- CONFIGURATION DEMO ---
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

# --- FONCTIONS ---
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
    else: save_config()

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

# --- TRAITEMENT IMAGES ---
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

def reset_vote_callback():
    st.session_state.vote_success = False
    if "widget_choix" in st.session_state: st.session_state.widget_choix = []
    if "widget_choix_force" in st.session_state: st.session_state.widget_choix_force = []

# --- ACTIONS ---
def set_state(mode, open_s, reveal):
    st.session_state.config["mode_affichage"] = mode
    st.session_state.config["session_ouverte"] = open_s
    st.session_state.config["reveal_resultats"] = reveal
    if reveal: st.session_state.config["timestamp_podium"] = time.time()
    save_config()

def inject_visual_effect(effect_name, intensity, speed):
    if effect_name == "Aucun":
        components.html("<script>var old = window.parent.document.getElementById('effect-layer'); if(old) old.remove();</script>", height=0)
        return
    # Note: Effects are handled inside the wall logic mostly now, but kept here for compatibility
    pass 

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

# --- PDF GENERATOR ---
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

# --- NAVIGATION VARS ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
# INIT SESSION
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
        cfg = st.session_state.config
        with st.sidebar:
            if st.button("⬅️ CHANGER DE SESSION"): st.session_state["session_active"] = False; st.rerun()
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
            
            st.divider()
            st.markdown(f'<a href="/" target="_blank" class="custom-link-btn btn-red">📺 OUVRIR MUR SOCIAL</a>', unsafe_allow_html=True)
            if st.button("🔓 DÉCONNEXION"): st.session_state["auth"] = False; st.rerun()

        menu = st.session_state.admin_menu

        if menu == "🔴 PILOTAGE LIVE":
            st.title("🔴 PILOTAGE LIVE")
            st.info(f"État actuel : {cfg['mode_affichage']}")
            c1, c2, c3, c4 = st.columns(4)
            c1.button("🏠 ACCUEIL", on_click=set_state, args=("attente", False, False))
            c2.button("🗳️ VOTES ON", on_click=set_state, args=("votes", True, False))
            c3.button("🔒 VOTES OFF", on_click=set_state, args=("votes", False, False))
            c4.button("🏆 PODIUM", on_click=set_state, args=("votes", False, True))
            st.markdown("---")
            st.button("📸 PHOTOS LIVE", on_click=set_state, args=("photos_live", False, False))
            with st.expander("🚨 ZONE DE DANGER"):
                if st.button("🗑️ RESET DONNÉES", type="primary"): 
                    reset_app_data(preserve_config=True)
                    st.success("Reset OK"); time.sleep(1); st.rerun()

        elif menu == "⚙️ CONFIG":
            st.title("⚙️ CONFIGURATION")
            t1, t2 = st.tabs(["Général", "Candidats"])
            with t1:
                new_t = st.text_input("Titre", value=cfg["titre_mur"])
                if st.button("Sauver Titre"): st.session_state.config["titre_mur"] = new_t; save_config(); st.rerun()
                upl = st.file_uploader("Logo", type=["png", "jpg"])
                if upl:
                    p = process_logo(upl)
                    if p: st.session_state.config["logo_b64"] = p; save_config(); st.rerun()
            with t2:
                c_add, c_btn = st.columns([4, 1])
                new_c = c_add.text_input("Nouveau")
                if c_btn.button("➕") and new_c: cfg['candidats'].append(new_c); save_config(); st.rerun()
                for c in cfg['candidats']:
                    c1, c2 = st.columns([4,1])
                    c1.write(c)
                    if c2.button("🗑️", key=c): cfg['candidats'].remove(c); save_config(); st.rerun()
        
        elif menu == "📸 MÉDIATHÈQUE":
            st.title("📸 MÉDIATHÈQUE")
            files = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
            if files:
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for f in files: zf.write(f, arcname=os.path.basename(f))
                st.download_button("📥 TOUT TÉLÉCHARGER", data=zip_buffer.getvalue(), file_name="galerie.zip", mime="application/zip")
            st.image([f for f in files[:20]], width=100) # Preview simple
            if st.button("🗑️ TOUT SUPPRIMER", type="primary"):
                for f in files: os.remove(f)
                st.rerun()

        elif menu == "📊 DATA":
            st.title("📊 DONNÉES")
            votes = load_json(VOTES_FILE, {})
            vote_counts, nb_voters, rank_dist = get_advanced_stats()
            data = [{"Candidat": c, "Points": votes.get(c, 0), "Votes": vote_counts.get(c, 0)} for c in cfg["candidats"]]
            df = pd.DataFrame(data).sort_values("Points", ascending=False)
            st.dataframe(df, hide_index=True, use_container_width=True)
            if PDF_AVAILABLE:
                st.download_button("📄 RAPPORT PDF", data=create_pdf_results(cfg['titre_mur'], df, nb_voters, df['Points'].sum()), file_name="rapport.pdf")

# =========================================================
# 2. APPLICATION MOBILE (Vote)
# =========================================================
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, default_config)
    st.markdown("<style>.stApp {background-color:black !important; color:white;}</style>", unsafe_allow_html=True)
    
    if "user_pseudo" not in st.session_state:
        st.subheader("Identification")
        pseudo = st.text_input("Votre Prénom")
        if st.button("Valider") and pseudo:
            st.session_state.user_pseudo = pseudo
            parts = load_json(PARTICIPANTS_FILE, [])
            parts.append(pseudo)
            save_json(PARTICIPANTS_FILE, parts)
            st.rerun()
    else:
        if cfg["mode_affichage"] == "photos_live":
            st.info("📸 ENVOYER UNE PHOTO")
            up = st.file_uploader("Photo", type=['png','jpg'])
            cam = st.camera_input("Camera")
            if up or cam:
                f = up if up else cam
                with open(os.path.join(LIVE_DIR, f"live_{int(time.time())}.jpg"), "wb") as w: w.write(f.getbuffer())
                st.success("Envoyé !")
                time.sleep(2); st.rerun()
        
        elif cfg["session_ouverte"]:
            st.write(f"Bonjour {st.session_state.user_pseudo}")
            if not st.session_state.get("vote_success"):
                choix = st.multiselect("Vos 3 vidéos :", cfg["candidats"], max_selections=3)
                if len(choix) == 3 and st.button("Voter"):
                    vts = load_json(VOTES_FILE, {})
                    pts = [5, 3, 1]
                    for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                    save_json(VOTES_FILE, vts)
                    details = load_json(DETAILED_VOTES_FILE, [])
                    details.append({"Utilisateur": st.session_state.user_pseudo, "Choix": choix})
                    save_json(DETAILED_VOTES_FILE, details)
                    st.session_state.vote_success = True
                    st.rerun()
            else:
                st.success("Merci ! Vote enregistré.")
        else:
            st.info("Les votes sont fermés.")

# =========================================================
# 3. MUR SOCIAL (Podium & Affichage)
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    cfg = load_json(CONFIG_FILE, default_config)
    st_autorefresh(interval=4000, key="wall_refresh")
    
    st.markdown(f'<div class="social-header"><h1 class="social-title">{cfg["titre_mur"]}</h1></div>', unsafe_allow_html=True)
    
    mode = cfg.get("mode_affichage")
    
    # ------------------ ACCUEIL ------------------
    if mode == "attente":
        st.markdown("""<style>.stApp {background-color:black !important;}</style>""", unsafe_allow_html=True)
        logo = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="width:400px;">' if cfg.get("logo_b64") else ""
        st.markdown(f"""
        <div style="height:88vh; margin-top:12vh; display:flex; flex-direction:column; justify-content:center; align-items:center; background:black;">
            {logo}
            <h1 style="color:white; font-size:80px; margin-top:30px;">BIENVENUE</h1>
        </div>
        """, unsafe_allow_html=True)

    # ------------------ PODIUM (VERSION 32 - COMPOSANT ISOLE) ------------------
    elif mode == "votes" and cfg.get("reveal_resultats"):
        st.markdown("""<style>.stApp {background-color:black !important;}</style>""", unsafe_allow_html=True)
        v_data = load_json(VOTES_FILE, {})
        c_imgs = cfg.get("candidats_images", {})
        if not v_data: v_data = {"Personne": 0}
        
        scores = sorted(list(set(v_data.values())), reverse=True)
        s1 = scores[0] if len(scores) > 0 else -1
        s2 = scores[1] if len(scores) > 1 else -1
        s3 = scores[2] if len(scores) > 2 else -1
        
        rank1 = [c for c, s in v_data.items() if s == s1]
        rank2 = [c for c, s in v_data.items() if s == s2]
        rank3 = [c for c, s in v_data.items() if s == s3]

        txt_intro = "NOUS ALLONS DÉCOUVRIR MAINTENANT LES FINALISTES DE CE CONCOURS"
        txt_3 = "ILS SONT PLUSIEURS À LA 3ÈME PLACE !" if len(rank3) > 1 else "À LA TROISIÈME PLACE..."
        txt_2 = "EX-AEQUO À LA DEUXIÈME PLACE !" if len(rank2) > 1 else "À LA DEUXIÈME PLACE..."
        txt_1 = "LES GRANDS VAINQUEURS SONT..." if len(rank1) > 1 else "ET LE GRAND VAINQUEUR EST..."

        def get_html_cards(cands, score, medal):
            html = ""
            for c in cands:
                img = f"data:image/png;base64,{c_imgs[c]}" if c in c_imgs else ""
                img_tag = f"<img src='{img}' class='p-img'>" if img else f"<div style='font-size:50px'>{medal}</div>"
                html += f"""<div class="p-card">{img_tag}<div class="p-name">{c}</div><div class="p-score">{score} pts</div></div>"""
            return html

        h1 = get_html_cards(rank1, s1, "🥇")
        h2 = get_html_cards(rank2, s2, "🥈")
        h3 = get_html_cards(rank3, s3, "🥉")

        components.html(f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; background-color: black; font-family: Arial, sans-serif; }}
            .podium-container {{
                display: flex; flex-direction: column; width: 100vw; height: 100vh;
                justify-content: flex-end; align-items: center;
                padding-bottom: 20px; box-sizing: border-box; padding-top: 12vh;
            }}
            .rank-row {{
                display: flex; flex-direction: row; justify-content: center; align-items: flex-end;
                width: 100%; opacity: 0; transform: translateY(30px); transition: opacity 1s ease, transform 1s ease;
            }}
            .visible {{ opacity: 1 !important; transform: translateY(0) !important; }}
            #row-1 {{ order: 1; margin-bottom: 40px; z-index: 10; }} 
            #row-2 {{ order: 2; margin-bottom: 20px; z-index: 5; }}  
            #row-3 {{ order: 3; margin-bottom: 0px; z-index: 1; }}   
            .p-card {{
                background: rgba(255,255,255,0.1); border-radius: 15px; padding: 15px; margin: 0 10px;
                text-align: center; border: 2px solid rgba(255,255,255,0.2); color: white; min-width: 180px;
                display: flex; flex-direction: column; align-items: center;
            }}
            #row-1 .p-card {{ border-color: #FFD700; background: rgba(20,20,20,0.9); box-shadow: 0 0 50px rgba(255, 215, 0, 0.4); transform: scale(1.2); }}
            #row-2 .p-card {{ border-color: #C0C0C0; transform: scale(1.0); }}
            #row-3 .p-card {{ border-color: #CD7F32; transform: scale(0.9); }}
            .p-img {{ width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 3px solid white; margin-bottom: 10px; }}
            #row-1 .p-img {{ width: 120px; height: 120px; border-color: #FFD700; }}
            .p-name {{ font-weight: bold; font-size: 18px; text-transform: uppercase; margin-bottom: 5px; }}
            #row-1 .p-name {{ font-size: 26px; color: #FFD700; }}
            .p-score {{ font-size: 14px; color: #ddd; }}
            .overlay {{
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0,0,0,0.9); display: flex; flex-direction: column; justify-content: center; align-items: center;
                z-index: 9999; transition: opacity 0.5s;
            }}
            .txt-msg {{ color: white; font-size: 40px; font-weight: bold; text-align: center; text-transform: uppercase; margin: 20px; }}
            .txt-num {{ color: #E2001A; font-size: 120px; font-weight: 900; }}
        </style>
        </head>
        <body>
            <div id="overlay" class="overlay"><div id="msg" class="txt-msg"></div><div id="num" class="txt-num"></div></div>
            <audio id="sound" src="https://www.soundjay.com/human/sounds/applause-01.mp3"></audio>
            <div class="podium-container">
                <div id="row-1" class="rank-row">{h1}</div>
                <div id="row-2" class="rank-row">{h2}</div>
                <div id="row-3" class="rank-row">{h3}</div>
            </div>
            <script>
                const wait = (ms) => new Promise(r => setTimeout(r, ms));
                const ov = document.getElementById('overlay');
                const msg = document.getElementById('msg');
                const num = document.getElementById('num');
                const r1 = document.getElementById('row-1');
                const r2 = document.getElementById('row-2');
                const r3 = document.getElementById('row-3');
                
                async function count(sec, text, dark=false) {{
                    ov.style.backgroundColor = dark ? 'black' : 'rgba(0,0,0,0.7)';
                    ov.style.display = 'flex'; ov.style.opacity = '1'; msg.innerText = text;
                    for(let i=sec; i>0; i--) {{ num.innerText = i; await wait(1000); }}
                    ov.style.opacity = '0'; await wait(500); ov.style.display = 'none';
                }}
                async function start() {{
                    await count(5, "{txt_intro}", true);
                    if(r3.innerHTML.trim() !== "") {{ await count(4, "{txt_3}"); r3.classList.add('visible'); await wait(2000); }}
                    if(r2.innerHTML.trim() !== "") {{ await count(4, "{txt_2}"); r2.classList.add('visible'); await wait(2000); }}
                    if(r1.innerHTML.trim() !== "") {{ await count(6, "{txt_1}"); r1.classList.add('visible'); 
                        var script = document.createElement('script');
                        script.src = "https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js";
                        script.onload = () => {{ setInterval(() => confetti({{particleCount: 50, spread: 100, origin: {{y:0.6}}}}), 500); }};
                        document.body.appendChild(script);
                        try {{ document.getElementById('sound').play(); }} catch(e){{}}
                    }}
                }}
                window.onload = start;
            </script>
        </body>
        </html>
        """, height=900, scrolling=False)

    # ------------------ MODE VOTE OUVERT (AVEC COMPTEUR + TAGS) ------------------
    elif mode == "votes" and cfg["session_ouverte"]:
        st.markdown("""<style>.stApp {background-color:black !important;}</style>""", unsafe_allow_html=True)
        
        # 1. LOAD PARTICIPANTS
        participants = load_json(PARTICIPANTS_FILE, [])
        nb_total = len(participants)
        last_participants = participants[-24:][::-1] # Last 24, reversed (newest first)

        # 2. GENERATE TAGS HTML
        tags_html = "".join([f"<span style='display:inline-block; padding:5px 12px; margin:4px; border:1px solid #E2001A; border-radius:20px; background:rgba(255,255,255,0.1); color:white; font-size:14px;'>{p}</span>" for p in last_participants])

        # 3. DISPLAY HEADER (COUNTER + TAGS)
        st.markdown(f"""
        <div style="margin-top:10vh; text-align:center; width:100%; margin-bottom:20px;">
            <div style="color:#E2001A; font-size:26px; font-weight:bold; margin-bottom:10px; text-transform:uppercase;">
                👥 {nb_total} PARTICIPANTS EN LICE
            </div>
            <div style="width:90%; margin:0 auto; line-height:1.5;">
                {tags_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 4. STANDARD COLUMNS DISPLAY
        cands = cfg.get("candidats", [])
        imgs = cfg.get("candidats_images", {})
        mid = (len(cands) + 1) // 2
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        logo_html = f"<img src='data:image/png;base64,{cfg['logo_b64']}' style='width:250px; margin-bottom:20px;'>" if cfg.get("logo_b64") else ""
        
        def make_col_html(clist):
            h = ""
            for c in clist:
                im = f"<img src='data:image/png;base64,{imgs[c]}' class='cand-img'>" if c in imgs else "<div class='cand-img' style='background:black;'>🏆</div>"
                h += f"<div class='cand-row'>{im}<span class='cand-name'>{c}</span></div>"
            return h

        css = """<style>
            .vote-container { display: flex; justify-content: space-between; align-items: flex-start; width: 100vw; height: 65vh; padding: 0 20px; box-sizing: border-box; }
            .col-participants { flex: 1; display: flex; flex-direction: column; align-items: center; }
            .col-center { flex: 0 0 400px; display: flex; flex-direction: column; align-items: center; padding-top: 10px; }
            .cand-row { width: 90%; max-width: 400px; background: rgba(255,255,255,0.1); backdrop-filter: blur(5px); margin-bottom:10px; padding:8px 15px; border-radius:50px; display:flex; align-items:center; }
            .cand-img { width:55px; height:55px; border-radius:50%; object-fit:cover; border:3px solid #E2001A; margin-right:15px; }
            .cand-name { color:white; font-size:20px; font-weight:600; }
        </style>"""
        
        full_html = css + f"""
        <div class='vote-container'>
            <div class='col-participants'>{make_col_html(cands[:mid])}</div>
            <div class='col-center'>{logo_html}
                <div style='background: white; padding: 15px; border-radius: 15px; box-shadow: 0 0 30px rgba(226,0,26,0.5);'>
                    <img src='data:image/png;base64,{qr_b64}' style='width: 250px; display:block;'>
                </div>
                <div class='vote-cta'>À VOS VOTES !</div>
            </div>
            <div class='col-participants'>{make_col_html(cands[mid:])}</div>
        </div>
        """
        st.markdown(full_html, unsafe_allow_html=True)

    elif mode == "photos_live":
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        logo_data = cfg.get("logo_b64", "")
        photos = glob.glob(f"{LIVE_DIR}/*")
        img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-40:]]) if photos else "[]"
        
        components.html(f"""
        <style>body {{ background: black; overflow: hidden; }}</style>
        <div id='center-box' style='position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); z-index:100; text-align:center; background:rgba(0,0,0,0.85); padding:20px; border-radius:30px; border:2px solid #E2001A; width:340px; box-shadow:0 0 50px rgba(0,0,0,0.8);'>
            <h1 style='color:#E2001A; margin:0 0 15px 0; font-size:28px; font-weight:bold; font-family:Arial;'>MUR PHOTOS LIVE</h1>
            {f'<img src="data:image/png;base64,{logo_data}" style="width:180px; margin-bottom:15px;">' if logo_data else ''}
            <div style='background:white; padding:10px; border-radius:10px; display:inline-block;'><img src='data:image/png;base64,{qr_b64}' style='width:150px;'></div>
        </div>
        <script>
            const imgs = {img_js}; const bubbles = [];
            imgs.forEach(src => {{
                const el = document.createElement('img'); el.src = src;
                const size = Math.random() * 100 + 60;
                el.style.cssText = `position:absolute; width:${{size}}px; height:${{size}}px; border-radius:50%; border:4px solid #E2001A; object-fit:cover;`;
                document.body.appendChild(el);
                bubbles.push({{el, x: Math.random()*window.innerWidth, y: Math.random()*window.innerHeight, vx: (Math.random()-0.5)*2, vy: (Math.random()-0.5)*2}});
            }});
            function animate() {{
                bubbles.forEach(b => {{
                    b.x += b.vx; b.y += b.vy;
                    if(b.x < 0 || b.x > window.innerWidth) b.vx *= -1;
                    if(b.y < 0 || b.y > window.innerHeight) b.vy *= -1;
                    b.el.style.transform = `translate(${{b.x}}px, ${{b.y}}px)`;
                }});
                requestAnimationFrame(animate);
            }}
            animate();
        </script>
        """, height=900)

    else:
        st.markdown(f"<div class='full-screen-center'><h1 style='color:white;'>EN ATTENTE...</h1></div>", unsafe_allow_html=True)
