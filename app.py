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

# --- CSS GLOBAL (STRUCTURAL) ---
st.markdown("""
<style>
    /* SUPPRESSION MARGES STREAMLIT */
    .block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
    header { visibility: hidden; }
    footer { visibility: hidden; }
    
    /* BOUTONS STANDARDS */
    button[kind="secondary"] { color: #333 !important; border-color: #333 !important; }
    button[kind="primary"] { color: white !important; background-color: #E2001A !important; border: none; }
    
    /* LOGIN BOX */
    .login-container {
        max-width: 400px; margin: 100px auto; padding: 40px;
        background: #f0f2f6; border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1); text-align: center; border: 1px solid #ddd;
    }
    .login-title { color: #E2001A; font-size: 24px; font-weight: bold; margin-bottom: 20px; text-transform: uppercase; }
    .stTextInput input { text-align: center; font-size: 18px; }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] button[kind="primary"] { background-color: #E2001A !important; width: 100%; margin-bottom: 5px; }
    section[data-testid="stSidebar"] button[kind="secondary"] { background-color: #333333 !important; width: 100%; margin-bottom: 5px; border: none !important; color: white !important; }
    
    /* LIENS EXTERNES */
    a.custom-link-btn {
        display: block !important; text-align: center !important; padding: 12px !important;
        border-radius: 8px !important; text-decoration: none !important; font-weight: bold !important;
        margin-bottom: 10px !important; color: white !important; transition: transform 0.2s !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
    }
    a.custom-link-btn:hover { transform: scale(1.02) !important; opacity: 0.9 !important; }
    .btn-red { background-color: #E2001A !important; }
    .btn-blue { background-color: #2980b9 !important; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATIONS ---
blank_config = {
    "mode_affichage": "attente", "titre_mur": "TITRE À DÉFINIR", 
    "session_ouverte": False, "reveal_resultats": False, "timestamp_podium": 0, "logo_b64": None, 
    "candidats": [], "candidats_images": {}, "points_ponderation": [5, 3, 1],
    "effect_intensity": 25, "effect_speed": 15, 
    "screen_effects": {"attente": "Aucun", "votes_open": "Aucun", "votes_closed": "Aucun", "podium": "Aucun", "photos_live": "Aucun"},
    "session_id": ""
}

default_config = {
    "mode_affichage": "attente", "titre_mur": "CONCOURS VIDÉO 2026", 
    "session_ouverte": False, "reveal_resultats": False, "timestamp_podium": 0, "logo_b64": None,
    "candidats": ["BU PAX", "BU FRET", "BU B2B", "RH", "IT", "DPMI", "FINANCES", "AO", "QSSE", "DIRECTION"],
    "candidats_images": {}, "points_ponderation": [5, 3, 1],
    "effect_intensity": 25, "effect_speed": 15, 
    "screen_effects": {"attente": "Aucun", "votes_open": "Aucun", "votes_closed": "Aucun", "podium": "Aucun", "photos_live": "Aucun"},
    "session_id": str(uuid.uuid4())
}

# --- FONCTIONS ---
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
        with open(str(file), "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e: print(f"Erreur Save: {e}")

def save_config(): save_json(CONFIG_FILE, st.session_state.config)

def sanitize_filename(name): return re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")

def archive_current_session():
    current_cfg = load_json(CONFIG_FILE, default_config)
    titre = current_cfg.get("titre_mur", "Session")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder_name = f"{timestamp}_{sanitize_filename(titre)}"
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

def process_logo(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        img.thumbnail((600, 600), Image.Resampling.BICUBIC)
        buf = BytesIO(); img.save(buf, format="PNG", optimize=True)
        return base64.b64encode(buf.getvalue()).decode()
    except: return None

def process_participant_image(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        if img.mode != "RGB": img = img.convert("RGB")
        img.thumbnail((300, 300), Image.Resampling.BICUBIC)
        buf = BytesIO(); img.save(buf, format="JPEG", quality=60, optimize=True)
        return base64.b64encode(buf.getvalue()).decode()
    except: return None

def reset_vote_callback():
    st.session_state.vote_success = False
    if "widget_choix" in st.session_state: st.session_state.widget_choix = []
    if "widget_choix_force" in st.session_state: st.session_state.widget_choix_force = []

def set_state(mode, open_s, reveal):
    st.session_state.config["mode_affichage"] = mode
    st.session_state.config["session_ouverte"] = open_s
    st.session_state.config["reveal_resultats"] = reveal
    if reveal: st.session_state.config["timestamp_podium"] = time.time()
    save_config()

def inject_visual_effect(effect_name, intensity, speed):
    if effect_name == "Aucun" or effect_name == "🎉 Confettis":
        components.html("<script>var old = window.parent.document.getElementById('effect-layer'); if(old) old.remove();</script>", height=0)
        return
    interval = int(5000 / (intensity + 1))
    js_code = f"""
    <script>
        var doc = window.parent.document;
        var layer = doc.getElementById('effect-layer');
        if(!layer) {{
            layer = doc.createElement('div'); layer.id = 'effect-layer';
            layer.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:0;overflow:hidden;';
            doc.body.appendChild(layer);
        }}
        function createBalloon() {{
            var e = doc.createElement('div'); e.innerHTML = '🎈';
            e.style.cssText = 'position:absolute;bottom:-100px;left:'+Math.random()*100+'vw;font-size:'+(Math.random()*40+30)+'px;transition:bottom 10s linear;';
            layer.appendChild(e); setTimeout(() => {{ e.remove(); }}, 10000);
            setTimeout(() => {{ e.style.bottom = '110vh'; }}, 50);
        }}
        function createSnow() {{
            var e = doc.createElement('div'); e.innerHTML = '❄';
            e.style.cssText = 'position:absolute;top:-50px;left:'+Math.random()*100+'vw;color:white;font-size:'+(Math.random()*20+10)+'px;transition:top 10s linear;';
            layer.appendChild(e); setTimeout(() => {{ e.remove(); }}, 10000);
            setTimeout(() => {{ e.style.top = '110vh'; }}, 50);
        }}
    """
    if effect_name == "🎈 Ballons": js_code += f"if(!window.balloonInterval) window.balloonInterval = setInterval(createBalloon, {interval});"
    elif effect_name == "❄️ Neige": js_code += f"if(!window.snowInterval) window.snowInterval = setInterval(createSnow, {interval});"
    js_code += "</script>"
    components.html(js_code, height=0)

if PDF_AVAILABLE:
    class PDFReport(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15); self.set_text_color(226, 0, 26)
            self.cell(0, 10, 'REGIE MASTER - RAPPORT OFFICIEL', 0, 1, 'C'); self.ln(5)
        def footer(self):
            self.set_y(-15); self.set_font('Arial', 'I', 8); self.set_text_color(128)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    def create_pdf_results(title, df):
        pdf = PDFReport(); pdf.add_page(); pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt=f"Resultats: {title}", ln=True, align='L'); pdf.ln(10)
        pdf.set_fill_color(226, 0, 26); pdf.set_text_color(255)
        pdf.cell(100, 10, "Candidat", 1, 0, 'C', 1); pdf.cell(40, 10, "Points", 1, 1, 'C', 1); pdf.ln()
        pdf.set_text_color(0)
        for i, row in df.iterrows():
            cand = str(row['Candidat']).encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(100, 10, cand, 1); pdf.cell(40, 10, str(row['Points']), 1, 1, 'C'); pdf.ln()
        return pdf.output(dest='S').encode('latin-1')
    def create_pdf_audit(title, df):
        pdf = PDFReport(); pdf.add_page(); pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt=f"Audit: {title}", ln=True, align='L'); pdf.ln(5)
        pdf.set_font("Arial", size=10)
        for i, row in df.iterrows():
            txt = " | ".join([str(x).encode('latin-1', 'replace').decode('latin-1') for x in row.values])
            pdf.cell(0, 8, txt, 1, 1)
        return pdf.output(dest='S').encode('latin-1')

# --- NAVIGATION VARS ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
is_test_admin = st.query_params.get("test_admin") == "true"

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
            pwd = st.text_input("Code", type="password", label_visibility="collapsed")
            if st.button("ENTRER", use_container_width=True, type="primary"):
                if pwd == "ADMIN_LIVE_MASTER": st.session_state["auth"] = True; st.session_state["session_active"] = False; st.rerun()
                else: st.error("Code incorrect")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        if "session_active" not in st.session_state or not st.session_state["session_active"]:
            st.title("🗂️ SESSIONS")
            curr_t = st.session_state.config.get("titre_mur", "Session")
            c1, c2 = st.columns(2)
            if c1.button(f"OUVRIR : {curr_t}", type="primary", use_container_width=True): st.session_state["session_active"] = True; st.rerun()
            new_n = c2.text_input("Nom save", placeholder="Optionnel")
            if c2.button("NOUVELLE SESSION VIERGE", type="primary", use_container_width=True):
                archive_current_session(); reset_app_data("blank"); st.session_state["session_active"] = True; st.rerun()
            
            st.divider(); st.write("Archives :")
            arcs = sorted([d for d in os.listdir(ARCHIVE_DIR) if os.path.isdir(os.path.join(ARCHIVE_DIR, d))], reverse=True)
            for a in arcs:
                with st.expander(f"📁 {a}"):
                    if st.button(f"Restaurer {a}"): archive_current_session(); restore_session_from_archive(a); st.session_state.config = load_json(CONFIG_FILE, default_config); st.session_state["session_active"] = True; st.rerun()
                    if st.button(f"Supprimer {a}"): delete_archived_session(a); st.rerun()
        else:
            cfg = st.session_state.config
            with st.sidebar:
                if st.button("⬅️ SESSIONS"): st.session_state["session_active"] = False; st.rerun()
                st.divider()
                if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), use_container_width=True)
                st.header("MENU")
                if "admin_menu" not in st.session_state: st.session_state.admin_menu = "🔴 PILOTAGE LIVE"
                for m in ["🔴 PILOTAGE LIVE", "⚙️ CONFIG", "📸 MÉDIATHÈQUE", "📊 DATA"]:
                    if st.button(m, type="primary" if st.session_state.admin_menu == m else "secondary", use_container_width=True): st.session_state.admin_menu = m; st.rerun()
                st.divider()
                st.markdown("""<a href="/" target="_blank" class="custom-link-btn btn-red">📺 OUVRIR MUR SOCIAL</a><a href="/?mode=vote&test_admin=true" target="_blank" class="custom-link-btn btn-blue">📱 TESTER MOBILE</a>""", unsafe_allow_html=True)
                if st.button("🔓 DÉCONNEXION"): st.session_state["auth"] = False; st.rerun()

            menu = st.session_state.admin_menu
            if menu == "🔴 PILOTAGE LIVE":
                st.title("🔴 PILOTAGE")
                c1, c2, c3, c4 = st.columns(4)
                c1.button("🏠 ACCUEIL", type="primary" if cfg["mode_affichage"]=="attente" else "secondary", use_container_width=True, on_click=set_state, args=("attente", False, False))
                c2.button("🗳️ VOTES ON", type="primary" if (cfg["mode_affichage"]=="votes" and cfg["session_ouverte"]) else "secondary", use_container_width=True, on_click=set_state, args=("votes", True, False))
                c3.button("🔒 VOTES OFF", type="primary" if (cfg["mode_affichage"]=="votes" and not cfg["session_ouverte"] and not cfg["reveal_resultats"]) else "secondary", use_container_width=True, on_click=set_state, args=("votes", False, False))
                c4.button("🏆 PODIUM", type="primary" if cfg["reveal_resultats"] else "secondary", use_container_width=True, on_click=set_state, args=("votes", False, True))
                st.markdown("---")
                st.button("📸 MUR PHOTOS LIVE", type="primary" if cfg["mode_affichage"]=="photos_live" else "secondary", use_container_width=True, on_click=set_state, args=("photos_live", False, False))

            elif menu == "⚙️ CONFIG":
                st.title("⚙️ CONFIGURATION")
                t1, t2 = st.tabs(["Général", "Participants"])
                with t1:
                    new_t = st.text_input("Titre", value=cfg["titre_mur"])
                    if st.button("Sauver Titre"): st.session_state.config["titre_mur"] = new_t; save_config(); st.rerun()
                    upl = st.file_uploader("Logo", type=["png","jpg"])
                    if upl: st.session_state.config["logo_b64"] = process_logo(upl); save_config(); st.rerun()
                with t2:
                    with st.form("add"):
                        c1, c2 = st.columns([4, 1])
                        new = c1.text_input("Nouveau")
                        if c2.form_submit_button("➕") and new: cfg['candidats'].append(new); save_config(); st.rerun()
                    for i, c in enumerate(cfg['candidats']):
                        c1, c2, c3 = st.columns([0.5, 3, 2])
                        if c in cfg.get("candidats_images", {}): c1.image(BytesIO(base64.b64decode(cfg["candidats_images"][c])), width=40)
                        c2.text_input(f"Nom {i}", value=c, key=f"n_{i}", disabled=True)
                        u = c3.file_uploader(f"Img {i}", type=["jpg","png"], key=f"u_{i}", label_visibility="collapsed")
                        if u: st.session_state.config["candidats_images"][c] = process_participant_image(u); save_config(); st.rerun()

            elif menu == "📸 MÉDIATHÈQUE":
                st.title("📸 MÉDIATHÈQUE")
                c1, c2 = st.columns(2)
                if c1.button("🗑️ TOUT SUPPRIMER", type="primary", use_container_width=True):
                    for f in glob.glob(f"{LIVE_DIR}/*"): os.remove(f)
                    st.rerun()
                files = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
                zip_b = BytesIO()
                with zipfile.ZipFile(zip_b, "w") as z:
                    for f in files: z.write(f, arcname=os.path.basename(f))
                c2.download_button("⬇️ TOUT TÉLÉCHARGER", data=zip_b.getvalue(), file_name="photos.zip", mime="application/zip", use_container_width=True)
                st.divider()
                cols = st.columns(5)
                for i, f in enumerate(files):
                    with cols[i%5]: st.image(f, use_container_width=True)

            elif menu == "📊 DATA":
                st.title("📊 DONNÉES")
                votes = load_json(VOTES_FILE, {})
                df = pd.DataFrame(list(votes.items()), columns=['Candidat', 'Points']).sort_values('Points', ascending=False)
                c = alt.Chart(df).mark_bar(color="#E2001A").encode(x='Points', y=alt.Y('Candidat', sort='-x'), text='Points')
                st.altair_chart(c.mark_bar() + c.mark_text(align='left', dx=2), use_container_width=True)
                st.dataframe(df, use_container_width=True)
                if PDF_AVAILABLE: st.download_button("📄 PDF", data=create_pdf_results(cfg['titre_mur'], df), file_name="res.pdf")

# =========================================================
# 2. APPLICATION MOBILE
# =========================================================
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, default_config)
    st.markdown("""<style>.stApp {background-color:black !important; color:white !important;} [data-testid='stHeader'] {display:none;} .block-container {padding:1rem !important;}</style>""", unsafe_allow_html=True)
    if "user_pseudo" not in st.session_state:
        if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), width=100)
        p = st.text_input("Pseudo"); 
        if st.button("ENTRER", type="primary") and p: st.session_state.user_pseudo = p; st.rerun()
    else:
        if cfg["mode_affichage"] == "photos_live":
            u = st.file_uploader("Photo", type=['jpg','png']); c = st.camera_input("Camera")
            if u or c:
                f = u if u else c
                with open(os.path.join(LIVE_DIR, f"live_{uuid.uuid4()}.jpg"), "wb") as o: o.write(f.getbuffer())
                st.success("Envoyé !"); time.sleep(1); st.rerun()
        elif cfg["mode_affichage"] == "votes" and (cfg["session_ouverte"] or is_test_admin):
            if "vote_success" not in st.session_state: st.session_state.vote_success = False
            if st.session_state.vote_success and not is_test_admin: st.info("Vote enregistré."); st.stop()
            chs = st.multiselect("3 choix", cfg["candidats"], max_selections=3)
            if len(chs)==3 and st.button("VALIDER", type="primary"):
                v = load_json(VOTES_FILE, {}); 
                for c, p in zip(chs, [5,3,1]): v[c] = v.get(c,0)+p
                save_json(VOTES_FILE, v); st.session_state.vote_success=True; st.balloons(); st.rerun()
            if is_test_admin and st.session_state.vote_success: st.button("Voter à nouveau", on_click=reset_vote_callback)
        else: st.info("En attente...")

# =========================================================
# 3. MUR SOCIAL (NOIR, NO SCROLL, CENTRÉ)
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    cfg = load_json(CONFIG_FILE, default_config)
    st_autorefresh(interval=4000)
    
    st.markdown("""
    <style>
        body, .stApp { background-color: black !important; overflow: hidden !important; }
        [data-testid='stHeader'] { display: none; }
        .block-container { padding: 0 !important; max-width: 100% !important; margin: 0 !important; }
    </style>
    """, unsafe_allow_html=True)
    
    mode = cfg.get("mode_affichage")
    logo = cfg.get("logo_b64", "")
    
    # --- 1. ACCUEIL (CENTRÉ PARFAIT) ---
    if mode == "attente":
        components.html(f"""
        <style>body{{background:black;margin:0;height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;overflow:hidden;}}</style>
        {f'<img src="data:image/png;base64,{logo}" style="width:400px;margin-bottom:30px;">' if logo else ''}
        <h1 style="color:white;font-family:Arial;font-size:80px;margin:0;">BIENVENUE</h1>
        """, height=900)

    # --- 2. VOTE OFF (CENTRÉ PARFAIT) ---
    elif mode == "votes" and not cfg["session_ouverte"] and not cfg["reveal_resultats"]:
        components.html(f"""
        <style>body{{background:black;margin:0;height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;overflow:hidden;}}</style>
        <div style="border:5px solid #E2001A; padding:50px; border-radius:30px; text-align:center;">
            {f'<img src="data:image/png;base64,{logo}" style="width:200px;margin-bottom:20px;">' if logo else ''}
            <h1 style="color:#E2001A;font-family:Arial;font-size:60px;margin:0;">VOTES CLÔTURÉS</h1>
        </div>
        """, height=900)

    # --- 3. VOTE ON (QR CODE) ---
    elif mode == "votes" and cfg["session_ouverte"]:
        host = st.context.headers.get('host', 'localhost')
        qr = qrcode.make(f"https://{host}/?mode=vote"); buf=BytesIO(); qr.save(buf, format="PNG"); qrb64=base64.b64encode(buf.getvalue()).decode()
        components.html(f"""
        <style>body{{background:black;margin:0;height:100vh;display:flex;justify-content:center;align-items:center;font-family:Arial;overflow:hidden;}}</style>
        <div style="text-align:center;">
            {f'<img src="data:image/png;base64,{logo}" style="width:300px;margin-bottom:30px;">' if logo else ''}
            <div style="background:white;padding:20px;border-radius:20px;display:inline-block;margin-bottom:20px;">
                <img src="data:image/png;base64,{qrb64}" style="width:250px;">
            </div>
            <div style="color:#E2001A;font-size:40px;font-weight:bold;animation:blink 1s infinite;">À VOS VOTES !</div>
        </div>
        <style>@keyframes blink {{ 50% {{ opacity: 0; }} }}</style>
        """, height=900)

    # --- 4. PODIUM (SÉQUENTIEL & CENTRÉ) ---
    elif mode == "votes" and cfg["reveal_resultats"]:
        v_data = load_json(VOTES_FILE, {})
        scores = sorted(list(set(v_data.values())), reverse=True)
        s1 = scores[0] if len(scores)>0 else 0; s2 = scores[1] if len(scores)>1 else -1; s3 = scores[2] if len(scores)>2 else -1
        
        def get_p(s): 
            l=[]; 
            for k,v in v_data.items():
                if v==s: 
                    img = cfg["candidats_images"].get(k); 
                    l.append({'n':k, 's':v, 'i': f"data:image/jpeg;base64,{img}" if img else ""})
            return l
            
        r1, r2, r3 = get_p(s1), get_p(s2), get_p(s3)
        ts_start = cfg.get("timestamp_podium", 0) * 1000
        
        components.html(f"""
        <html><head><style>
            body {{ background:black; margin:0; height:100vh; display:flex; flex-direction:column; justify-content:center; align-items:center; font-family:Arial; overflow:hidden; }}
            .logo {{ width:300px; margin-bottom:20px; object-fit:contain; }}
            .txt {{ color:white; font-size:40px; font-weight:bold; margin-bottom:10px; }}
            .count {{ color:#E2001A; font-size:120px; font-weight:bold; }}
            .grid {{ display:flex; justify-content:center; align-items:flex-end; gap:20px; }}
            .card {{ background:rgba(255,255,255,0.1); padding:15px; border-radius:15px; width:200px; text-align:center; color:white; }}
            .card img {{ width:100px; height:100px; border-radius:50%; border:3px solid white; object-fit:cover; }}
            .win {{ background:rgba(20,20,20,0.9); border:4px solid #FFD700; width:350px; padding:30px; box-shadow:0 0 50px #FFD700; }}
            .win img {{ width:180px; height:180px; border-radius:50%; border:5px solid white; object-fit:cover; margin-bottom:15px; }}
            .win h1 {{ font-size:35px; margin:5px 0; color:white; }}
        </style></head><body>
            <div id="intro" style="display:none;text-align:center;">
                {f'<img src="data:image/png;base64,{logo}" class="logo">' if logo else ''}
                <div id="lbl" class="txt"></div><div id="cnt" class="count"></div>
            </div>
            <div id="final" style="display:none;flex-direction:column;align-items:center;">
                {f'<img src="data:image/png;base64,{logo}" class="logo">' if logo else ''}
                <div id="grid" class="grid"></div>
            </div>
            <script>
                const r1={json.dumps(r1)}, r2={json.dumps(r2)}, r3={json.dumps(r3)};
                const start = {ts_start};
                
                function card(p, rank) {{
                    if(rank==1) return `<div class="win"><div style="font-size:50px">🥇</div>`+(p.i?`<img src="${{p.i}}">`:``)+`<h1>${{p.n}}</h1><h2 style="color:#FFD700">VAINQUEUR</h2><h3 style="color:#CCC">${{p.s}} pts</h3></div>`;
                    return `<div class="card"><div style="font-size:30px">${{rank==2?'🥈':'🥉'}}</div>`+(p.i?`<img src="${{p.i}}">`:``)+`<h3>${{p.n}}</h3><h4>${{p.s}} pts</h4></div>`;
                }}

                setInterval(() => {{
                    const el = (Date.now() - start)/1000;
                    const intro = document.getElementById('intro');
                    const final = document.getElementById('final');
                    const lbl = document.getElementById('lbl');
                    const cnt = document.getElementById('cnt');
                    const grid = document.getElementById('grid');
                    
                    let showIntro = false;
                    let txt = "";
                    let time = 0;
                    
                    // PHASE 1: 3eme (0-5s intro, 5-12s affiche)
                    if(el < 5) {{ showIntro=true; txt="LES 3èmes..."; time=5-el; }}
                    else if(el < 12) {{
                        intro.style.display='none'; final.style.display='flex';
                        let h=""; r3.forEach(p=>h+=card(p,3)); grid.innerHTML=h;
                    }}
                    // PHASE 2: 2eme (12-17s intro, 17-25s affiche 2+3)
                    else if(el < 17) {{ showIntro=true; txt="LES 2nds..."; time=17-el; }}
                    else if(el < 25) {{
                        intro.style.display='none'; final.style.display='flex';
                        let h=""; r3.forEach(p=>h+=card(p,3)); r2.forEach(p=>h+=card(p,2)); grid.innerHTML=h;
                    }}
                    // PHASE 3: 1er (25-30s intro, 30s+ affiche TOUT)
                    else if(el < 30) {{ showIntro=true; txt="LE VAINQUEUR..."; time=30-el; }}
                    else {{
                        intro.style.display='none'; final.style.display='flex';
                        let h=""; r2.forEach(p=>h+=card(p,2)); r1.forEach(p=>h+=card(p,1)); r3.forEach(p=>h+=card(p,3)); grid.innerHTML=h;
                    }}
                    
                    if(showIntro) {{
                        final.style.display='none'; intro.style.display='block';
                        lbl.innerText=txt; cnt.innerText=Math.ceil(time);
                    }}
                }}, 100);
            </script>
        </body></html>
        """, height=900)

    # --- 5. PHOTOS LIVE (ANIMATION) ---
    elif mode == "photos_live":
        photos = glob.glob(f"{LIVE_DIR}/*")
        js_imgs = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-40:]])
        components.html(f"""
        <style>body{{background:black;margin:0;overflow:hidden;}}</style>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;z-index:100;background:rgba(0,0,0,0.8);padding:30px;border-radius:30px;border:2px solid #E2001A;">
            <h1 style="color:#E2001A;margin:0;font-family:Arial;">PHOTOS LIVE</h1>
            {f'<img src="data:image/png;base64,{logo}" style="width:150px;margin-top:10px;">' if logo else ''}
        </div>
        <script>
            const imgs = {js_imgs};
            imgs.forEach(src => {{
                let img = document.createElement('img'); img.src = src;
                img.style.cssText = 'position:absolute;width:'+(Math.random()*100+80)+'px;border-radius:50%;border:3px solid #E2001A;';
                let x = Math.random()*window.innerWidth, y = Math.random()*window.innerHeight, dx = (Math.random()-0.5)*2, dy = (Math.random()-0.5)*2;
                document.body.appendChild(img);
                setInterval(() => {{
                    x += dx; y += dy;
                    if(x<0||x>window.innerWidth) dx*=-1; if(y<0||y>window.innerHeight) dy*=-1;
                    img.style.transform = `translate(${3}{x}px, ${3}{y}px)`;
                }}, 20);
            }});
        </script>
        """, height=900)
