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

# --- CSS GLOBAL ---
st.markdown("""
<style>
    /* Supprime les marges par défaut */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }
    
    /* Boutons */
    button[kind="secondary"] { color: #333 !important; border-color: #333 !important; }
    button[kind="primary"] { color: white !important; background-color: #E2001A !important; border: none; }
    button[kind="primary"]:hover { background-color: #C20015 !important; }
    
    /* Login Box */
    .login-container {
        max-width: 400px; margin: 100px auto; padding: 40px;
        background: #f0f2f6; border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1); text-align: center; border: 1px solid #ddd;
    }
    .login-title { color: #E2001A; font-size: 24px; font-weight: bold; margin-bottom: 20px; text-transform: uppercase; }
    .stTextInput input { text-align: center; font-size: 18px; }
    
    /* Sidebar */
    section[data-testid="stSidebar"] button[kind="primary"] {
        background-color: #E2001A !important; width: 100%; border-radius: 5px; margin-bottom: 5px;
    }
    section[data-testid="stSidebar"] button[kind="secondary"] {
        background-color: #333333 !important; width: 100%; border-radius: 5px; margin-bottom: 5px; border: none !important; color: white !important;
    }
    
    /* Liens externes */
    a.custom-link-btn {
        display: block; text-align: center; padding: 12px; border-radius: 8px;
        text-decoration: none !important; font-weight: bold; margin-bottom: 10px;
        color: white !important; transition: transform 0.2s;
    }
    a.custom-link-btn:hover { transform: scale(1.02); }
    .btn-red { background-color: #E2001A; }
    .btn-blue { background-color: #2980b9; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATIONS ---
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

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")

def archive_current_session(name_suffix="AutoSave"):
    current_cfg = load_json(CONFIG_FILE, default_config)
    titre = current_cfg.get("titre_mur", "Session")
    safe_titre = sanitize_filename(titre)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder_name = f"{timestamp}_{safe_titre}_{name_suffix}"
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

def reset_app_data(init_mode="blank"):
    for f in [VOTES_FILE, VOTERS_FILE, PARTICIPANTS_FILE, DETAILED_VOTES_FILE]:
        if os.path.exists(f): os.remove(f)
    if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
    files = glob.glob(f"{LIVE_DIR}/*")
    for f in files: os.remove(f)
    if init_mode == "blank":
        st.session_state.config = copy.deepcopy(blank_config)
        st.session_state.config["session_id"] = str(uuid.uuid4())
        save_config()
    elif init_mode == "demo":
        st.session_state.config = copy.deepcopy(default_config)
        st.session_state.config["session_id"] = str(uuid.uuid4())
        save_config()

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

def get_file_info(filepath):
    try:
        ts = os.path.getmtime(filepath)
        return datetime.fromtimestamp(ts).strftime("%H:%M:%S")
    except: return "?"

def inject_visual_effect(effect_name, intensity, speed):
    if effect_name == "Aucun" or effect_name == "🎉 Confettis":
        components.html("<script>var old = window.parent.document.getElementById('effect-layer'); if(old) old.remove();</script>", height=0)
        return
    duration = max(3, 25 - (speed * 0.4)) 
    interval = int(5000 / (intensity + 1))
    js_code = f"""
    <script>
        var doc = window.parent.document;
        var layer = doc.getElementById('effect-layer');
        if(!layer) {{
            layer = doc.createElement('div');
            layer.id = 'effect-layer';
            layer.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:0;overflow:hidden;';
            doc.body.appendChild(layer);
        }}
        function createBalloon() {{
            var e = doc.createElement('div'); e.innerHTML = '🎈';
            e.style.cssText = 'position:absolute;bottom:-100px;left:'+Math.random()*100+'vw;font-size:'+(Math.random()*40+30)+'px;transition:bottom {duration}s linear;';
            layer.appendChild(e);
            setTimeout(() => {{ e.style.bottom = '110vh'; }}, 50); setTimeout(() => {{ e.remove(); }}, {duration * 1000});
        }}
        function createSnow() {{
            var e = doc.createElement('div'); e.innerHTML = '❄';
            e.style.cssText = 'position:absolute;top:-50px;left:'+Math.random()*100+'vw;color:white;font-size:'+(Math.random()*20+10)+'px;transition:top {duration}s linear;';
            layer.appendChild(e);
            setTimeout(() => {{ e.style.top = '110vh'; }}, 50); setTimeout(() => {{ e.remove(); }}, {duration * 1000});
        }}
    """
    if effect_name == "🎈 Ballons": js_code += f"if(!window.balloonInterval) window.balloonInterval = setInterval(createBalloon, {interval});"
    elif effect_name == "❄️ Neige": js_code += f"if(!window.snowInterval) window.snowInterval = setInterval(createSnow, {interval});"
    js_code += "</script>"
    components.html(js_code, height=0)

# --- GENERATEUR PDF SECURISÉ ---
if PDF_AVAILABLE:
    class PDFReport(FPDF):
        def header(self):
            if os.path.exists("temp_logo.png"):
                try: self.image("temp_logo.png", 10, 8, 33)
                except: pass
            
            self.set_font('Arial', 'B', 15)
            self.set_text_color(226, 0, 26)
            x_pos = 50 if os.path.exists("temp_logo.png") else 10
            self.set_xy(x_pos, 10)
            self.cell(0, 10, 'REGIE MASTER - RAPPORT OFFICIEL', 0, 1, 'C')
            self.ln(5)
            self.set_font('Arial', 'I', 10)
            self.set_text_color(100, 100, 100)
            self.cell(0, 5, f"Date du rapport : {datetime.now().strftime('%d/%m/%Y à %H:%M')}", 0, 1, 'R')
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def prepare_logo_file(logo_b64):
        if logo_b64:
            try:
                with open("temp_logo.png", "wb") as f:
                    f.write(base64.b64decode(logo_b64))
                return True
            except: return False
        return False

    def create_pdf_results(title, df, logo_b64=None, total_voters=0):
        try:
            has_logo = prepare_logo_file(logo_b64)
            pdf = PDFReport()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, txt=f"Résultats : {title}", ln=True, align='L')
            pdf.set_font("Arial", 'I', 11)
            pdf.cell(0, 10, txt=f"Nombre total de votants : {total_voters}", ln=True, align='L')
            pdf.ln(5)
            
            # CENTRAGE TABLEAU
            margin_left = 35
            pdf.set_fill_color(226, 0, 26)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", 'B', 12)
            pdf.set_x(margin_left)
            pdf.cell(100, 10, "Candidat", 1, 0, 'C', 1)
            pdf.cell(40, 10, "Points", 1, 1, 'C', 1)
            pdf.set_text_color(0, 0, 0)
            pdf.ln()
            
            pdf.set_font("Arial", size=12)
            for i, row in df.iterrows():
                pdf.set_x(margin_left)
                cand = str(row['Candidat']).encode('latin-1', 'replace').decode('latin-1')
                points = str(row['Points'])
                pdf.cell(100, 10, cand, 1, 0, 'C')
                pdf.cell(40, 10, points, 1, 1, 'C')
                pdf.ln()
                
            if has_logo and os.path.exists("temp_logo.png"): os.remove("temp_logo.png")
            return pdf.output(dest='S').encode('latin-1')
        except: return b"Erreur PDF"

    def create_pdf_audit(title, df, logo_b64=None):
        try:
            has_logo = prepare_logo_file(logo_b64)
            pdf = PDFReport()
            pdf.add_page()
            pdf.set_font("Arial", size=10)
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt=f"Audit Detaillé : {title}", ln=True, align='L')
            pdf.ln(5)
            
            cols = [str(c) for c in df.columns.tolist() if "Date" not in str(c)]
            w = 190 / max(1, len(cols))
            pdf.set_fill_color(50, 50, 50)
            pdf.set_text_color(255)
            for col in cols:
                c_txt = col.encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(w, 8, c_txt, 1, 0, 'C', 1)
            pdf.ln()
            
            pdf.set_text_color(0)
            for i, row in df.iterrows():
                for col in cols:
                    txt = str(row[col]).encode('latin-1', 'replace').decode('latin-1')
                    pdf.cell(w, 8, txt, 1, 0, 'C')
                pdf.ln()
                
            if has_logo and os.path.exists("temp_logo.png"): os.remove("temp_logo.png")
            return pdf.output(dest='S').encode('latin-1')
        except: return b"Erreur PDF"

# --- NAVIGATION VARS ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
is_blocked = st.query_params.get("blocked") == "true"
is_test_admin = st.query_params.get("test_admin") == "true"

# --- INIT SESSION ---
if "config" not in st.session_state:
    st.session_state.config = load_json(CONFIG_FILE, default_config)

# =========================================================
# 1. CONSOLE ADMIN
# =========================================================
if est_admin:
    st.markdown("""<style>.stApp { background-color: #ffffff !important; color: black !important; }</style>""", unsafe_allow_html=True)
    if "auth" not in st.session_state: st.session_state["auth"] = False
    
    if not st.session_state["auth"]:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown('<div class="login-container"><div class="login-title">🔒 ADMIN ACCESS</div>', unsafe_allow_html=True)
            pwd = st.text_input("Code de sécurité", type="password", label_visibility="collapsed")
            if st.button("ENTRER", use_container_width=True, type="primary"):
                if pwd == "ADMIN_LIVE_MASTER": st.session_state["auth"] = True; st.session_state["session_active"] = False; st.rerun()
                else: st.error("Code incorrect")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        if "session_active" not in st.session_state or not st.session_state["session_active"]:
            st.title("🗂️ GESTIONNAIRE DE SESSIONS")
            st.info("Avant d'accéder au pilotage, choisissez une session.")
            current_title = st.session_state.config.get("titre_mur", "Session Inconnue")
            c1, c2 = st.columns(2, gap="large")
            with c1:
                st.markdown("### 🚀 Continuer")
                st.write(f"Session : **{current_title}**")
                if st.button("OUVRIR LA SESSION", type="primary", use_container_width=True): st.session_state["session_active"] = True; st.rerun()
            with c2:
                st.markdown("### ✨ Créer")
                st.write("Nouvelle session vierge")
                if st.button("CRÉER NOUVELLE SESSION", type="primary", use_container_width=True):
                    archive_current_session("AutoSave"); reset_app_data(init_mode="blank"); st.session_state["session_active"] = True; st.success("Nouvelle session vierge prête !"); time.sleep(1); st.rerun()
            st.divider(); st.markdown("### 📚 Historique / Archives")
            archives = sorted([d for d in os.listdir(ARCHIVE_DIR) if os.path.isdir(os.path.join(ARCHIVE_DIR, d))], reverse=True)
            if not archives: st.caption("Aucune archive trouvée.")
            else:
                for arc in archives:
                    with st.expander(f"📁 {arc}"):
                        c_res, c_del = st.columns([3, 1])
                        if c_res.button(f"Restaurer {arc}", key=f"res_{arc}"):
                            archive_current_session("PreRestoreBackup"); restore_session_from_archive(arc); st.session_state.config = load_json(CONFIG_FILE, default_config); st.session_state["session_active"] = True; st.success("Session restaurée !"); time.sleep(1); st.rerun()
                        confirm = c_del.checkbox("Confirmer", key=f"chk_{arc}")
                        if c_del.button("🗑️", key=f"del_{arc}", disabled=not confirm): delete_archived_session(arc); st.rerun()
        else:
            cfg = st.session_state.config
            with st.sidebar:
                if st.button("⬅️ CHANGER DE SESSION"): st.session_state["session_active"] = False; st.rerun()
                st.divider(); 
                if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), use_container_width=True)
                st.header("MENU"); 
                if "admin_menu" not in st.session_state: st.session_state.admin_menu = "🔴 PILOTAGE LIVE"
                for m in ["🔴 PILOTAGE LIVE", "⚙️ CONFIG", "📸 MÉDIATHÈQUE", "📊 DATA"]:
                    if st.button(m, key=f"nav_{m}", type="primary" if st.session_state.admin_menu == m else "secondary", use_container_width=True): st.session_state.admin_menu = m; st.rerun()
                st.divider()
                st.markdown("""<a href="/" target="_blank" class="custom-link-btn btn-red">📺 OUVRIR MUR SOCIAL</a><a href="/?mode=vote&test_admin=true" target="_blank" class="custom-link-btn btn-blue">📱 TESTER MOBILE (ILLIMITÉ)</a>""", unsafe_allow_html=True)
                if st.button("🔓 DÉCONNEXION"): st.session_state["auth"] = False; st.session_state["session_active"] = False; st.rerun()

            if st.session_state.admin_menu == "🔴 PILOTAGE LIVE":
                st.title("🔴 PILOTAGE LIVE"); st.subheader("Séquenceur")
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
                st.markdown("---"); st.button("📸 MUR PHOTOS LIVE", use_container_width=True, type="primary" if cfg["mode_affichage"]=="photos_live" else "secondary", on_click=set_state, args=("photos_live", False, False))
                st.divider(); 
                with st.expander("🚨 ZONE DE DANGER"):
                    if st.button("🗑️ RESET DONNÉES (Session en cours)", type="primary"): reset_app_data(full_wipe=False); st.rerun()

            elif st.session_state.admin_menu == "⚙️ CONFIG":
                st.title("⚙️ CONFIGURATION"); t1, t2 = st.tabs(["Général", "Candidats & Images"])
                with t1:
                    new_t = st.text_input("Titre", value=cfg["titre_mur"])
                    if st.button("Sauver Titre"): st.session_state.config["titre_mur"] = new_t; save_config(); st.rerun()
                    upl = st.file_uploader("Logo (PNG Transparent)", type=["png", "jpg"])
                    if upl: st.session_state.config["logo_b64"] = process_logo(upl); save_config(); st.rerun()
                with t2:
                    st.subheader(f"Liste des participants ({len(cfg['candidats'])}/15)")
                    if len(cfg['candidats']) < 15:
                        c_add, c_btn = st.columns([4, 1])
                        new_cand = c_add.text_input("Nouveau participant", key="new_cand_input")
                        if c_btn.button("➕ Ajouter") and new_cand:
                            if new_cand.strip() not in cfg['candidats']: cfg['candidats'].append(new_cand.strip()); save_config(); st.rerun()
                            else: st.error("Existe déjà !")
                    st.divider()
                    candidates_to_remove = []
                    for i, cand in enumerate(cfg['candidats']):
                        c1, c2, c3 = st.columns([0.5, 3, 2])
                        with c1: 
                            if cand in cfg.get("candidats_images", {}): st.image(BytesIO(base64.b64decode(cfg["candidats_images"][cand])), width=40)
                        with c2:
                            new_name = st.text_input(f"Participant {i+1}", value=cand, key=f"edit_{i}", label_visibility="collapsed")
                            if new_name != cand and new_name:
                                cfg['candidats'][i] = new_name
                                if cand in cfg.get("candidats_images", {}): cfg["candidats_images"][new_name] = cfg["candidats_images"].pop(cand)
                                save_config(); st.rerun()
                        with c3:
                            col_up, col_del = st.columns([3, 1])
                            up_img = col_up.file_uploader(f"Img {cand}", type=["png", "jpg"], key=f"up_{i}", label_visibility="collapsed")
                            if up_img: st.session_state.config["candidats_images"][cand] = process_participant_image(up_img); save_config(); st.rerun()
                            if col_del.button("🗑️", key=f"del_{i}"): candidates_to_remove.append(cand)
                    if candidates_to_remove:
                        for c in candidates_to_remove: cfg['candidats'].remove(c); 
                        save_config(); st.rerun()

            elif st.session_state.admin_menu == "📸 MÉDIATHÈQUE":
                st.title("📸 MÉDIATHÈQUE"); st.subheader("🗑️ Zone de Danger")
                if st.button("🗑️ TOUT SUPPRIMER (Irréversible)", type="primary", use_container_width=True):
                    for f in glob.glob(f"{LIVE_DIR}/*"): os.remove(f)
                    st.success("Suppression OK"); time.sleep(1); st.rerun()
                st.divider(); st.subheader("📥 Exportation")
                files = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
                if not files: st.info("Aucune photo disponible.")
                else:
                    zip_all = BytesIO()
                    with zipfile.ZipFile(zip_all, "w") as zf:
                        for f in files: zf.write(f, arcname=os.path.basename(f))
                    st.download_button("⬇️ TOUT TÉLÉCHARGER (ZIP)", data=zip_all.getvalue(), file_name="photos_live.zip", mime="application/zip", type="secondary", use_container_width=True)
                    st.write(f"**Sélectionnez les photos ({len(files)} au total) :**")
                    cols = st.columns(5); new_selection = []
                    for i, f in enumerate(files):
                        with cols[i % 5]:
                            st.image(f, use_container_width=True)
                            if st.checkbox(f"Sel. {i+1}", key=f"chk_{os.path.basename(f)}"): new_selection.append(f)
                    if new_selection:
                        zip_sel = BytesIO()
                        with zipfile.ZipFile(zip_sel, "w") as zf:
                            for f in new_selection: zf.write(f, arcname=os.path.basename(f))
                        st.download_button("⬇️ TÉLÉCHARGER LA SÉLECTION (ZIP)", data=zip_sel.getvalue(), file_name="selection.zip", mime="application/zip", type="secondary", use_container_width=True)

            elif st.session_state.admin_menu == "📊 DATA":
                st.title("📊 DONNÉES & RÉSULTATS")
                votes = load_json(VOTES_FILE, {}); detailed_data = load_json(DETAILED_VOTES_FILE, [])
                voters_count = len(set([d['Utilisateur'] for d in detailed_data])) if detailed_data else 0
                all_cands = {c: 0 for c in cfg["candidats"]}; all_cands.update(votes)
                df_totals = pd.DataFrame(list(all_cands.items()), columns=['Candidat', 'Points']).sort_values(by='Points', ascending=False)
                st.subheader("Classement")
                # MODIF: Graphique Fixe
                c = alt.Chart(df_totals).mark_bar(color="#E2001A").encode(x=alt.X('Points'), y=alt.Y('Candidat', sort='-x'), text='Points').properties(height=400)
                st.altair_chart(c + c.mark_text(align='left', dx=2), use_container_width=True)
                st.dataframe(df_totals, use_container_width=True)
                c1, c2 = st.columns(2)
                c1.download_button("📥 Résultats (CSV)", data=df_totals.to_csv(index=False, sep=";", encoding='utf-8-sig').encode('utf-8-sig'), file_name="resultats.csv", mime="text/csv", use_container_width=True)
                if PDF_AVAILABLE: c2.download_button("📄 Résultats (PDF)", data=create_pdf_results(cfg['titre_mur'], df_totals, cfg.get("logo_b64"), voters_count), file_name="resultats.pdf", mime="application/pdf", use_container_width=True)
                st.divider(); st.subheader("Audit Détaillé")
                if detailed_data:
                    df_detail = pd.DataFrame(detailed_data); st.dataframe(df_detail, use_container_width=True)
                    c3, c4 = st.columns(2)
                    c3.download_button("📥 Audit Complet (CSV)", data=df_detail.to_csv(index=False, sep=";", encoding='utf-8-sig').encode('utf-8-sig'), file_name="audit_votes.csv", mime="text/csv", use_container_width=True)
                    if PDF_AVAILABLE: c4.download_button("📄 Audit (PDF)", data=create_pdf_audit(cfg['titre_mur'], df_detail, cfg.get("logo_b64")), file_name="audit.pdf", mime="application/pdf", use_container_width=True)
                else: st.info("Aucun vote.")

# =========================================================
# 2. APPLICATION MOBILE
# =========================================================
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, default_config)
    st.markdown("""<style>.stApp {background-color:black !important; color:white !important;} [data-testid='stHeader'] {display:none;} .block-container {padding:1rem !important;}</style>""", unsafe_allow_html=True)
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
        else: st.info("⚠️ MODE TEST ADMIN")
        
    if "user_pseudo" not in st.session_state:
        st.subheader("Identification")
        if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), width=100)
        pseudo = st.text_input("Veuillez entrer votre prénom ou Pseudo :")
        if st.button("ENTRER", type="primary", use_container_width=True) and pseudo:
            st.session_state.user_pseudo = pseudo.strip(); parts = load_json(PARTICIPANTS_FILE, []); parts.append(pseudo.strip()); save_json(PARTICIPANTS_FILE, parts); st.rerun()
    else:
        if cfg["mode_affichage"] == "photos_live":
            st.info("📸 ENVOYER UNE PHOTO")
            up_key = f"uploader_{st.session_state.cam_reset_id}"; cam_key = f"camera_{st.session_state.cam_reset_id}"
            uploaded_file = st.file_uploader("Choisir dans la galerie", type=['png', 'jpg', 'jpeg'], key=up_key)
            cam_file = st.camera_input("Prendre une photo", key=cam_key)
            final_file = uploaded_file if uploaded_file else cam_file
            if final_file:
                fname = f"live_{uuid.uuid4().hex}_{int(time.time())}.jpg"
                with open(os.path.join(LIVE_DIR, fname), "wb") as f: f.write(final_file.getbuffer())
                st.success("Photo envoyée !"); st.session_state.cam_reset_id += 1; time.sleep(1); st.rerun()
        
        elif (cfg["mode_affichage"] == "votes" and (cfg["session_ouverte"] or is_test_admin)):
            st.write(f"Bonjour **{st.session_state.user_pseudo}**")
            if not st.session_state.rules_accepted:
                st.info("⚠️ **RÈGLES DU VOTE**"); st.markdown("1. Sélectionnez **3 vidéos**.\n2. 🥇 1er = **5 pts**\n3. 🥈 2ème = **3 pts**\n4. 🥉 3ème = **1 pt**\n\n**Vote unique et définitif.**")
                if st.button("J'AI COMPRIS, JE VOTE !", type="primary", use_container_width=True): st.session_state.rules_accepted = True; st.rerun()
            else:
                choix = st.multiselect("Vos 3 vidéos préférées :", cfg["candidats"], max_selections=3, key="widget_choix")
                if len(choix) == 3:
                    if st.button("VALIDER (DÉFINITIF)", type="primary", use_container_width=True):
                        vts = load_json(VOTES_FILE, {}); pts = cfg.get("points_ponderation", [5, 3, 1])
                        for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                        save_json(VOTES_FILE, vts)
                        details = load_json(DETAILED_VOTES_FILE, [])
                        details.append({"Utilisateur": st.session_state.user_pseudo, "Choix 1 (5pts)": choix[0], "Choix 2 (3pts)": choix[1], "Choix 3 (1pt)": choix[2], "Date": datetime.now().strftime("%H:%M:%S")})
                        save_json(DETAILED_VOTES_FILE, details)
                        st.session_state.vote_success = True; st.balloons()
                        st.markdown("""<div style='text-align:center; margin-top:50px; padding:20px;'><h1 style='color:#E2001A;'>MERCI !</h1><h2 style='color:white;'>Vote enregistré.</h2><br><div style='font-size:80px;'>✅</div></div>""", unsafe_allow_html=True)
                        if not is_test_admin: components.html("""<script>localStorage.setItem('HAS_VOTED_2026', 'true');</script>""", height=0); st.stop()
                        else: st.button("🔄 Voter à nouveau (RAZ)", on_click=reset_vote_callback, type="primary"); st.stop()
        
        elif is_test_admin and cfg["mode_affichage"] == "votes":
             st.write(f"Bonjour **{st.session_state.user_pseudo}** (Mode Test Force)")
             choix = st.multiselect("Vos 3 vidéos préférées :", cfg["candidats"], max_selections=3, key="widget_choix_force")
             if len(choix) == 3:
                if st.button("VALIDER (MODE TEST)", type="primary"):
                    vts = load_json(VOTES_FILE, {}); pts = cfg.get("points_ponderation", [5, 3, 1])
                    for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                    save_json(VOTES_FILE, vts); st.balloons(); st.success("Vote Test OK"); st.button("🔄 Voter à nouveau (RAZ)", on_click=reset_vote_callback, type="primary"); st.stop()
        else: st.info("⏳ En attente...")

# =========================================================
# 3. MUR SOCIAL
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    cfg = load_json(CONFIG_FILE, default_config)
    refresh_rate = 5000 if (cfg.get("mode_affichage") == "votes" and cfg.get("reveal_resultats")) else 4000
    st_autorefresh(interval=refresh_rate, key="wall_refresh")
    
    # MODIF: Fond Noir + Masquage Header
    st.markdown("""
    <style>
        body, .stApp { background-color: black !important; font-family: 'Arial', sans-serif; overflow: hidden !important; }
        [data-testid='stHeader'] { display: none; }
        .block-container { padding: 0 !important; max-width: 100% !important; margin: 0 !important; }
        .social-header { position: fixed; top: 0; left: 0; width: 100%; height: 12vh; background: #E2001A; display: flex; align-items: center; justify-content: center; z-index: 5000; border-bottom: 5px solid white; }
        .social-title { color: white; font-size: 40px; font-weight: bold; margin: 0; text-transform: uppercase; }
        .vote-cta { text-align: center; color: #E2001A; font-size: 35px; font-weight: 900; margin-top: 15px; animation: blink 2s infinite; text-transform: uppercase; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .cand-row { display: flex; align-items: center; justify-content: flex-start; margin-bottom: 10px; background: rgba(255,255,255,0.08); padding: 8px 15px; border-radius: 50px; width: 100%; max-width: 350px; height: 70px; margin: 0 auto 10px auto; }
        .cand-img { width: 55px; height: 55px; border-radius: 50%; object-fit: cover; border: 3px solid #E2001A; margin-right: 15px; }
        .cand-name { color: white; font-size: 20px; font-weight: 600; margin: 0; white-space: nowrap; }
        
        /* MODIF: Centrage vertical et horizontal strict */
        .full-screen-center { position:fixed; top:0; left:0; width:100vw; height:100vh; display:flex; flex-direction:column; justify-content:center; align-items:center; z-index: 2; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f'<div class="social-header"><h1 class="social-title">{cfg["titre_mur"]}</h1></div>', unsafe_allow_html=True)
    mode = cfg.get("mode_affichage")
    effects = cfg.get("screen_effects", {})
    effect_name = effects.get("attente" if mode=="attente" else "podium", "Aucun")
    inject_visual_effect(effect_name, 25, 15)

    ph = st.empty()
    
    # --- MURS ---
    # Je rétablis le COMPONENTS.HTML uniquement là où c'est critique (animation podium/photo), 
    # et ST.MARKDOWN là où vous préfériez le rendu "texte".
    # Pour éviter le bandeau blanc, j'ai ajouté ".block-container { padding: 0... }" dans le CSS ci-dessus.

    if mode == "attente":
        # UTILISATION COMPONENTS pour centrage parfait sans marge
        logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="width:450px; margin-bottom:30px;">' if cfg.get("logo_b64") else ""
        components.html(f"""
        <html><body style="background:black;margin:0;height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
            {logo_html}
            <h1 style='color:white; font-family:Arial; font-size:100px; margin:0; font-weight:bold;'>BIENVENUE</h1>
        </body></html>""", height=900)

    elif mode == "votes":
        if cfg.get("reveal_resultats"):
            # PODIUM (VOTRE CODE INITIAL QUI MARCHAIT)
            v_data = load_json(VOTES_FILE, {}); scores = sorted(list(set(v_data.values())), reverse=True)
            s1 = scores[0] if len(scores)>0 else 0; s2 = scores[1] if len(scores)>1 else -1; s3 = scores[2] if len(scores)>2 else -1
            winners = [k for k,v in v_data.items() if v==s1]; finalists = [k for k,v in v_data.items() if v in scores[:3]]
            
            js_finalists = []; js_winners = []
            for name in finalists:
                img=None; 
                for c,i in cfg.get("candidats_images",{}).items():
                    if c.strip()==name.strip(): img=i; break
                js_finalists.append({'name':name, 'score':v_data[name], 'img':f"data:image/jpeg;base64,{img}" if img else ""})
            for name in winners:
                img=None; 
                for c,i in cfg.get("candidats_images",{}).items():
                    if c.strip()==name.strip(): img=i; break
                js_winners.append({'name':name, 'score':v_data[name], 'img':f"data:image/jpeg;base64,{img}" if img else ""})
                
            ts_start = cfg.get("timestamp_podium", 0) * 1000
            logo_data = cfg.get("logo_b64", "")
            
            components.html(f"""
            <html><head><style>
                body {{ background:transparent; font-family:Arial; overflow:hidden; margin:0; width:100vw; height:100vh; display:flex; justify-content:center; align-items:center; }}
                .wrapper {{ text-align:center; width:100%; display:flex; flex-direction:column; justify-content:center; align-items:center; height:100vh; }}
                .logo-img {{ width:300px; margin-bottom:20px; object-fit:contain; }}
                .countdown {{ font-size:150px; color:#E2001A; font-weight:bold; text-shadow:0 0 20px black; margin:20px 0; }}
                .title {{ color:white; font-size:50px; font-weight:bold; margin-bottom:20px; }}
                .grid {{ display:flex; justify-content:center; align-items:flex-end; gap:30px; width:95%; flex-wrap:wrap; }}
                .card {{ background:rgba(255,255,255,0.1); padding:20px; border-radius:20px; width:200px; text-align:center; color:white; }}
                .card img {{ width:120px; height:120px; border-radius:50%; object-fit:cover; border:4px solid white; }}
                .winner-card {{ background:rgba(20,20,20,0.95); border:6px solid #FFD700; padding:40px; border-radius:40px; width:350px; text-align:center; box-shadow:0 0 60px #FFD700; }}
                .winner-card img {{ width:180px; height:180px; border-radius:50%; object-fit:cover; border:6px solid white; }}
            </style></head><body>
                <div id="screen-suspense" class="wrapper" style="display:none;">
                    {f'<img src="data:image/png;base64,{logo_data}" class="logo-img">' if logo_data else ''}
                    <div class="title">LES FINALISTES...</div><div id="timer" class="countdown">10</div><div class="grid" id="finalists-grid"></div>
                </div>
                <div id="screen-winner" class="wrapper" style="display:none;">
                    {f'<img src="data:image/png;base64,{logo_data}" class="logo-img">' if logo_data else ''}
                    <div class="grid" id="winners-grid"></div>
                </div>
                <script>
                    const finalists={json.dumps(js_finalists)}; const winners={json.dumps(js_winners)}; const startTime={ts_start};
                    const fGrid=document.getElementById('finalists-grid');
                    finalists.forEach(f=>{{ fGrid.innerHTML+=`<div class="card">${{f.img?`<img src="${{f.img}}">`:`<div style="font-size:50px">🏆</div>`}}<h3>${{f.name}}</h3><h4>${{f.score}} pts</h4></div>` }});
                    const wGrid=document.getElementById('winners-grid');
                    winners.forEach(w=>{{ wGrid.innerHTML+=`<div class="winner-card"><div style="font-size:60px">🥇</div>${{w.img?`<img src="${{w.img}}">`:`<div style="font-size:80px">🏆</div>`}}<h1>${{w.name}}</h1><h2>VAINQUEUR</h2><h3>${{w.score}} pts</h3></div>` }});
                    setInterval(()=>{{
                        const el=(Date.now()-startTime)/1000;
                        if(el<10){{ document.getElementById('screen-suspense').style.display='flex'; document.getElementById('screen-winner').style.display='none'; document.getElementById('timer').innerText=Math.ceil(10-el); }}
                        else{{ document.getElementById('screen-suspense').style.display='none'; document.getElementById('screen-winner').style.display='flex'; }}
                    }},100);
                </script>
            </body></html>
            """, height=850, scrolling=False)

        elif cfg.get("session_ouverte"):
            # VOTE ON (VOTRE CODE INITIAL)
            with ph.container():
                cands = cfg.get("candidats", [])
                imgs = cfg.get("candidats_images", {})
                mid = (len(cands) + 1) // 2
                left_list, right_list = cands[:mid], cands[mid:]
                c_left, c_center, c_right = st.columns([1, 1, 1])
                with c_left:
                    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
                    for c in left_list:
                        if c in imgs: html = f"<div class='cand-row'><img src='data:image/png;base64,{imgs[c]}' class='cand-img'><span class='cand-name'>{c}</span></div>"
                        else: html = f"<div class='cand-row'><div style='width:55px;height:55px;border-radius:50%;background:black;border:3px solid #E2001A;display:flex;align-items:center;justify-content:center;margin-right:15px;'><span style='font-size:30px;'>🏆</span></div><span class='cand-name'>{c}</span></div>"
                        st.markdown(html, unsafe_allow_html=True)
                with c_center:
                    st.markdown("<div style='height:12vh'></div>", unsafe_allow_html=True)
                    if cfg.get("logo_b64"): st.markdown(f"<div style='text-align:center; width:100%; margin-bottom:20px;'><img src='data:image/png;base64,{cfg['logo_b64']}' style='width:350px;'></div>", unsafe_allow_html=True)
                    host = st.context.headers.get('host', 'localhost')
                    qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
                    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
                    st.markdown(f"<div style='text-align:center; width:100%;'><img src='data:image/png;base64,{qr_b64}' style='width:240px; border-radius:10px;'></div>", unsafe_allow_html=True)
                    st.markdown("<div class='vote-cta'>À VOS VOTES !</div>", unsafe_allow_html=True)
                    
                    # RETABLISSEMENT PARTICIPANTS (Ticker)
                    parts = load_json(PARTICIPANTS_FILE, [])
                    if parts:
                        tags_html = "".join([f"<span style='background:rgba(255,255,255,0.1);color:white;padding:5px 10px;border-radius:15px;border:1px solid #E2001A;margin:3px;display:inline-block;'>{p}</span>" for p in parts[-8:]])
                        st.markdown(f"<div style='text-align:center;margin-top:20px;'>{tags_html}</div>", unsafe_allow_html=True)

                with c_right:
                    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
                    for c in right_list:
                        if c in imgs: html = f"<div class='cand-row'><img src='data:image/png;base64,{imgs[c]}' class='cand-img'><span class='cand-name'>{c}</span></div>"
                        else: html = f"<div class='cand-row'><div style='width:55px;height:55px;border-radius:50%;background:black;border:3px solid #E2001A;display:flex;align-items:center;justify-content:center;margin-right:15px;'><span style='font-size:30px;'>🏆</span></div><span class='cand-name'>{c}</span></div>"
                        st.markdown(html, unsafe_allow_html=True)

        else:
            # VOTE OFF
            logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="width:300px; margin-bottom:30px;">' if cfg.get("logo_b64") else ""
            ph.markdown(f"<div class='full-screen-center'>{logo_html}<div style='border: 5px solid #E2001A; padding: 50px; border-radius: 40px; background: rgba(0,0,0,0.9);'><h1 style='color:#E2001A; font-size:70px; margin:0;'>VOTES CLÔTURÉS</h1></div></div>", unsafe_allow_html=True)

    elif mode == "photos_live":
        # PHOTOS LIVE (Correction JS accolades)
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        logo_data = cfg.get("logo_b64", "")
        photos = glob.glob(f"{LIVE_DIR}/*")
        if not photos: photos = []
        # Utilisation de simple quote pour le JSON stringifié pour éviter conflit f-string
        img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-40:]])
        
        center_html_content = f"""
            <div id='center-box' style='position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); z-index:100; text-align:center; background:rgba(0,0,0,0.85); padding:20px; border-radius:30px; border:2px solid #E2001A; width:340px; box-shadow:0 0 50px rgba(0,0,0,0.8);'>
                <h1 style='color:#E2001A; margin:0 0 15px 0; font-size:28px; font-weight:bold; text-transform:uppercase;'>MUR PHOTOS LIVE</h1>
                {f'<img src="data:image/png;base64,{logo_data}" style="width:180px; margin-bottom:15px;">' if logo_data else ''}
                <div style='background:white; padding:10px; border-radius:10px; display:inline-block;'>
                    <img src='data:image/png;base64,{qr_b64}' style='width:150px;'>
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
        </script>""", height=0)
