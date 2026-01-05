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

# --- 1. IMPORTS & CONFIGURATION ---
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

Image.MAX_IMAGE_PIXELS = None 
st.set_page_config(page_title="Régie Master", layout="wide", initial_sidebar_state="expanded")

# --- 2. CONSTANTES & DOSSIERS ---
LIVE_DIR = "galerie_live_users"
ARCHIVE_DIR = "_archives_sessions"
VOTES_FILE = "votes.json"
CONFIG_FILE = "config_mur.json"
VOTERS_FILE = "voters.json"
PARTICIPANTS_FILE = "participants.json"
DETAILED_VOTES_FILE = "detailed_votes.json"

for d in [LIVE_DIR, ARCHIVE_DIR]: os.makedirs(d, exist_ok=True)

# --- 3. CSS GLOBAL (STRUCTURAL) ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 100% !important; }
    button[kind="secondary"] { color: #333 !important; border-color: #333 !important; }
    button[kind="primary"] { color: white !important; background-color: #E2001A !important; border: none; }
    button[kind="primary"]:hover { background-color: #C20015 !important; }
    .login-container { max-width: 400px; margin: 100px auto; padding: 40px; background: #f0f2f6; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); text-align: center; border: 1px solid #ddd; }
    .login-title { color: #E2001A; font-size: 24px; font-weight: bold; margin-bottom: 20px; text-transform: uppercase; }
    section[data-testid="stSidebar"] button[kind="primary"] { background-color: #E2001A !important; width: 100%; border-radius: 5px; margin-bottom: 5px; }
    section[data-testid="stSidebar"] button[kind="secondary"] { background-color: #333333 !important; width: 100%; border-radius: 5px; margin-bottom: 5px; border: none !important; color: white !important; }
    a.custom-link-btn { display: block; text-align: center; padding: 12px; border-radius: 8px; text-decoration: none !important; font-weight: bold; margin-bottom: 10px; color: white !important; transition: transform 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    a.custom-link-btn:hover { transform: scale(1.02); opacity: 0.9; text-decoration: none; }
    .btn-red { background-color: #E2001A !important; border: 1px solid #E2001A !important; }
    .btn-blue { background-color: #2980b9 !important; border: 1px solid #2980b9 !important; }
</style>
""", unsafe_allow_html=True)

# --- 4. DATA & MODELS ---
blank_config = { "mode_affichage": "attente", "titre_mur": "TITRE À DÉFINIR", "session_ouverte": False, "reveal_resultats": False, "timestamp_podium": 0, "logo_b64": None, "candidats": [], "candidats_images": {}, "points_ponderation": [5, 3, 1], "effect_intensity": 25, "effect_speed": 15, "screen_effects": {"attente": "Aucun", "votes_open": "Aucun", "votes_closed": "Aucun", "podium": "Aucun", "photos_live": "Aucun"}, "session_id": "" }
default_config = { "mode_affichage": "attente", "titre_mur": "CONCOURS VIDÉO 2026", "session_ouverte": False, "reveal_resultats": False, "timestamp_podium": 0, "logo_b64": None, "candidats": ["BU PAX", "BU FRET", "BU B2B", "RH", "IT", "DPMI", "FINANCES", "AO", "QSSE", "DIRECTION"], "candidats_images": {}, "points_ponderation": [5, 3, 1], "effect_intensity": 25, "effect_speed": 15, "screen_effects": {"attente": "Aucun", "votes_open": "Aucun", "votes_closed": "Aucun", "podium": "Aucun", "photos_live": "Aucun"}, "session_id": str(uuid.uuid4()) }

def clean_for_json(data):
    if isinstance(data, dict): return {k: clean_for_json(v) for k, v in data.items()}
    elif isinstance(data, list): return [clean_for_json(v) for v in data]
    else: return data

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding='utf-8') as f: return json.loads(f.read().strip())
        except: return default
    return default

def save_json(file, data):
    try:
        with open(str(file), "w", encoding='utf-8') as f: json.dump(clean_for_json(data), f, ensure_ascii=False, indent=4)
    except: pass

def save_config(): save_json(CONFIG_FILE, st.session_state.config)
def sanitize_filename(name): return re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")

def archive_current_session(name_suffix="AutoSave"):
    cfg = load_json(CONFIG_FILE, default_config); title = cfg.get("titre_mur", "Session")
    fname = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{sanitize_filename(title)}_{name_suffix}"
    path = os.path.join(ARCHIVE_DIR, fname); os.makedirs(path, exist_ok=True)
    for f in [VOTES_FILE, CONFIG_FILE, VOTERS_FILE, PARTICIPANTS_FILE, DETAILED_VOTES_FILE]:
        if os.path.exists(f): shutil.copy2(f, path)
    if os.path.exists(LIVE_DIR): shutil.copytree(LIVE_DIR, os.path.join(path, "galerie_live_users"))

def restore_session_from_archive(folder_name):
    path = os.path.join(ARCHIVE_DIR, folder_name); reset_app_data("none")
    for f in [VOTES_FILE, CONFIG_FILE, VOTERS_FILE, PARTICIPANTS_FILE, DETAILED_VOTES_FILE]:
        src = os.path.join(path, f)
        if os.path.exists(src): shutil.copy2(src, ".")
    src_live = os.path.join(path, "galerie_live_users")
    if os.path.exists(src_live): shutil.copytree(src_live, LIVE_DIR)

def delete_archived_session(folder_name):
    path = os.path.join(ARCHIVE_DIR, folder_name)
    if os.path.exists(path): shutil.rmtree(path)

def reset_app_data(init_mode="blank"):
    for f in [VOTES_FILE, VOTERS_FILE, PARTICIPANTS_FILE, DETAILED_VOTES_FILE]:
        if os.path.exists(f): os.remove(f)
    if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
    for f in glob.glob(f"{LIVE_DIR}/*"): os.remove(f)
    if init_mode == "blank": st.session_state.config = copy.deepcopy(blank_config); st.session_state.config["session_id"] = str(uuid.uuid4()); save_config()
    elif init_mode == "demo": st.session_state.config = copy.deepcopy(default_config); st.session_state.config["session_id"] = str(uuid.uuid4()); save_config()

def process_logo(upl):
    try:
        img = Image.open(upl); img.thumbnail((600, 600)); buf = BytesIO(); img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except: return None

def process_participant_image(upl):
    try:
        img = Image.open(upl).convert("RGB"); img.thumbnail((300, 300)); buf = BytesIO(); img.save(buf, format="JPEG")
        return base64.b64encode(buf.getvalue()).decode()
    except: return None

def set_state(mode, open_s, reveal):
    st.session_state.config["mode_affichage"] = mode; st.session_state.config["session_ouverte"] = open_s
    st.session_state.config["reveal_resultats"] = reveal
    if reveal: st.session_state.config["timestamp_podium"] = time.time()
    save_config()

def inject_visual_effect(name, intensity, speed):
    if name == "Aucun" or name == "🎉 Confettis":
        components.html("<script>var o=window.parent.document.getElementById('effect-layer');if(o)o.remove();</script>", height=0); return
    js = f"""<script>
    var d=window.parent.document, l=d.getElementById('effect-layer');
    if(!l){{l=d.createElement('div');l.id='effect-layer';l.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:0;overflow:hidden;';d.body.appendChild(l);}}
    function B(){{var e=d.createElement('div');e.innerHTML='🎈';e.style.cssText='position:absolute;bottom:-100px;left:'+Math.random()*100+'vw;font-size:'+(Math.random()*40+30)+'px;transition:bottom {max(3, 25-(speed*0.4))}s linear;';l.appendChild(e);setTimeout(()=>{{e.style.bottom='110vh'}},50);setTimeout(()=>{{e.remove()}},{max(3, 25-(speed*0.4))*1000});}}
    function S(){{var e=d.createElement('div');e.innerHTML='❄';e.style.cssText='position:absolute;top:-50px;left:'+Math.random()*100+'vw;color:white;font-size:'+(Math.random()*20+10)+'px;transition:top {max(3, 25-(speed*0.4))}s linear;';l.appendChild(e);setTimeout(()=>{{e.style.top='110vh'}},50);setTimeout(()=>{{e.remove()}},{max(3, 25-(speed*0.4))*1000});}}
    </script>"""
    if name == "🎈 Ballons": js += f"<script>if(!window.iB)window.iB=setInterval(B,{int(5000/(intensity+1))});</script>"
    elif name == "❄️ Neige": js += f"<script>if(!window.iS)window.iS=setInterval(S,{int(5000/(intensity+1))});</script>"
    components.html(js, height=0)

# --- 5. PDF GENERATOR ---
if PDF_AVAILABLE:
    class PDFReport(FPDF):
        def header(self):
            if os.path.exists("temp_logo.png"): self.image("temp_logo.png", 10, 8, 33)
            self.set_font('Arial', 'B', 15); self.set_text_color(226, 0, 26)
            self.set_xy(50 if os.path.exists("temp_logo.png") else 10, 10)
            self.cell(0, 10, 'REGIE MASTER - RAPPORT OFFICIEL', 0, 1, 'C'); self.ln(5)
            self.set_font('Arial', 'I', 10); self.set_text_color(100)
            self.cell(0, 10, f"Le {datetime.now().strftime('%d/%m/%Y a %H:%M')}", 0, 1, 'R'); self.ln(10)
        def footer(self):
            self.set_y(-15); self.set_font('Arial', 'I', 8); self.set_text_color(128); self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def prep_logo(b64):
        if b64: 
            try: 
                with open("temp_logo.png", "wb") as f: f.write(base64.b64decode(b64))
                return True
            except: pass
        return False

    def create_pdf_results(title, df, logo_data=None, total_voters=0):
        try:
            has_logo = prep_logo(logo_data)
            pdf = PDFReport(); pdf.add_page(); pdf.set_font("Arial", size=12); pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, txt=f"Résultats : {title}", ln=True, align='L')
            pdf.set_font("Arial", 'I', 11); pdf.cell(0, 10, txt=f"Nombre total de votants : {total_voters}", ln=True, align='L'); pdf.ln(5)
            pdf.set_fill_color(226, 0, 26); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 12); pdf.set_x(35)
            pdf.cell(100, 10, "Candidat", 1, 0, 'C', 1); pdf.cell(40, 10, "Points", 1, 1, 'C', 1); pdf.set_text_color(0, 0, 0); pdf.ln()
            pdf.set_font("Arial", size=12)
            for i, row in df.iterrows():
                pdf.set_x(35)
                cand = str(row['Candidat']).encode('latin-1', 'replace').decode('latin-1')
                points = str(row['Points'])
                pdf.cell(100, 10, cand, 1, 0, 'C'); pdf.cell(40, 10, points, 1, 1, 'C'); pdf.ln()
            if os.path.exists("temp_logo.png"): os.remove("temp_logo.png")
            return pdf.output(dest='S').encode('latin-1')
        except: return b"Erreur PDF"

    def create_pdf_audit(title, df, logo_data=None):
        try:
            has_logo = prep_logo(logo_data)
            pdf = PDFReport(); pdf.add_page(); pdf.set_font("Arial", size=10); pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt=f"Audit Détail : {title}", ln=True, align='L'); pdf.ln(5)
            cols = [str(c) for c in df.columns.tolist() if "Date" not in str(c)]
            w = 190 / max(1, len(cols)); pdf.set_fill_color(50, 50, 50); pdf.set_text_color(255)
            for col in cols:
                c_txt = col.encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(w, 8, c_txt, 1, 0, 'C', 1)
            pdf.ln(); pdf.set_text_color(0)
            for i, row in df.iterrows():
                for col in cols:
                    txt = str(row[col]).encode('latin-1', 'replace').decode('latin-1')
                    pdf.cell(w, 8, txt, 1, 0, 'C')
                pdf.ln()
            if os.path.exists("temp_logo.png"): os.remove("temp_logo.png")
            return pdf.output(dest='S').encode('latin-1')
        except: return b"Erreur PDF"

# --- INIT SESSION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
is_test_admin = st.query_params.get("test_admin") == "true"

if "config" not in st.session_state:
    st.session_state.config = load_json(CONFIG_FILE, default_config)

# ==============================================================================
#  ZONE 1 : CONSOLE ADMIN (SILO INDEPENDANT)
# ==============================================================================
def interface_admin():
    # Force Fond Blanc Admin
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
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### 🚀 Continuer")
                if st.button(f"OUVRIR : {current_title}", type="primary", use_container_width=True):
                    st.session_state["session_active"] = True
                    st.rerun()
            with c2:
                st.markdown("### ✨ Créer")
                new_name = st.text_input("Nom de la sauvegarde (Optionnel)", placeholder="Ex: Matin_10h")
                if st.button("CRÉER UNE NOUVELLE SESSION VIERGE", type="primary", use_container_width=True):
                    archive_current_session(new_name if new_name else "AutoSave")
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
                            archive_current_session("PreRestoreBackup")
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
                menu_options = ["🔴 PILOTAGE LIVE", "⚙️ CONFIG", "📸 MÉDIATHÈQUE", "📊 DATA"]
                for m in menu_options:
                    if st.session_state.admin_menu == m:
                        st.button(m, key=f"nav_{m}", type="primary", use_container_width=True)
                    else:
                        if st.button(m, key=f"nav_{m}", type="secondary", use_container_width=True):
                            st.session_state.admin_menu = m; st.rerun()
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
                c1, c2, c3, c4 = st.columns(4)
                c1.button("🏠 ACCUEIL", use_container_width=True, type="primary" if cfg["mode_affichage"]=="attente" else "secondary", on_click=set_state, args=("attente", False, False))
                c2.button("🗳️ VOTES ON", use_container_width=True, type="primary" if (cfg["mode_affichage"]=="votes" and cfg["session_ouverte"]) else "secondary", on_click=set_state, args=("votes", True, False))
                c3.button("🔒 VOTES OFF", use_container_width=True, type="primary" if (cfg["mode_affichage"]=="votes" and not cfg["session_ouverte"] and not cfg["reveal_resultats"]) else "secondary", on_click=set_state, args=("votes", False, False))
                c4.button("🏆 PODIUM", use_container_width=True, type="primary" if cfg["reveal_resultats"] else "secondary", on_click=set_state, args=("votes", False, True))
                st.markdown("---")
                st.button("📸 MUR PHOTOS LIVE", use_container_width=True, type="primary" if cfg["mode_affichage"]=="photos_live" else "secondary", on_click=set_state, args=("photos_live", False, False))
                st.divider()
                with st.expander("🚨 ZONE DE DANGER"):
                    if st.button("🗑️ RESET DONNÉES (Session en cours)", type="primary"): reset_app_data(full_wipe=False); st.rerun()

            elif menu == "⚙️ CONFIG":
                st.title("⚙️ CONFIGURATION")
                t1, t2 = st.tabs(["Général", "Candidats & Images"])
                with t1:
                    new_t = st.text_input("Titre", value=cfg["titre_mur"])
                    if st.button("Sauver Titre"): st.session_state.config["titre_mur"] = new_t; save_config(); st.rerun()
                    upl = st.file_uploader("Logo (PNG Transparent)", type=["png", "jpg"])
                    if upl: 
                        processed_logo = process_logo(upl)
                        if processed_logo: st.session_state.config["logo_b64"] = processed_logo; save_config(); st.rerun()
                with t2:
                    st.subheader(f"Liste des participants ({len(cfg['candidats'])}/15)")
                    if not cfg["candidats"]: st.error("⚠️ La liste est vide ! Ajoutez des participants pour commencer.")
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
                                processed = process_participant_image(up_img)
                                if processed: st.session_state.config["candidats_images"][cand] = processed; save_config(); st.toast(f"✅ Image {cand} sauvegardée"); time.sleep(0.5); st.rerun()
                            if col_del.button("🗑️", key=f"del_{i}"): candidates_to_remove.append(cand)
                    if candidates_to_remove:
                        for c in candidates_to_remove:
                            cfg['candidats'].remove(c)
                            if c in cfg.get("candidats_images", {}): del cfg["candidats_images"][c]
                        save_config(); st.rerun()

            elif menu == "📸 MÉDIATHÈQUE":
                st.title("📸 MÉDIATHÈQUE")
                st.subheader("🗑️ Zone de Danger")
                if st.button("🗑️ TOUT SUPPRIMER (Irréversible)", type="primary", use_container_width=True):
                    files = glob.glob(f"{LIVE_DIR}/*")
                    for f in files: os.remove(f)
                    st.success("Suppression OK"); time.sleep(1); st.rerun()
                
                st.divider()
                st.subheader("📥 Exportation")
                files = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
                
                if not files: st.info("Aucune photo disponible.")
                else:
                    zip_all = BytesIO()
                    with zipfile.ZipFile(zip_all, "w") as zf:
                        for idx, file_path in enumerate(files): 
                            ts = os.path.getmtime(file_path); date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                            new_name = f"Photo_Live{idx+1:02d}_{date_str}.jpg"
                            zf.write(file_path, arcname=new_name)
                    st.download_button("⬇️ TOUT TÉLÉCHARGER (ZIP)", data=zip_all.getvalue(), file_name=f"toutes_photos_live.zip", mime="application/zip", type="secondary", use_container_width=True)
                    
                    st.write(f"**Sélectionnez les photos ({len(files)} au total) :**")
                    cols = st.columns(5)
                    new_selection = []
                    for i, f in enumerate(files):
                        with cols[i % 5]:
                            st.image(f, use_container_width=True)
                            if st.checkbox(f"Sel. {i+1}", key=f"chk_{os.path.basename(f)}"): new_selection.append(f)
                    
                    if new_selection:
                        st.success(f"{len(new_selection)} photos sélectionnées")
                        zip_sel = BytesIO()
                        with zipfile.ZipFile(zip_sel, "w") as zf:
                            for idx, file_path in enumerate(new_selection): 
                                zf.write(file_path, arcname=os.path.basename(file_path))
                        st.download_button("⬇️ TÉLÉCHARGER LA SÉLECTION (ZIP)", data=zip_sel.getvalue(), file_name="selection.zip", mime="application/zip", type="secondary", use_container_width=True)

            elif menu == "📊 DATA":
                st.title("📊 DONNÉES & RÉSULTATS")
                votes = load_json(VOTES_FILE, {})
                detailed_data = load_json(DETAILED_VOTES_FILE, [])
                voters_count = len(set([d['Utilisateur'] for d in detailed_data])) if detailed_data else 0
                all_cands = {c: 0 for c in cfg["candidats"]}
                all_cands.update(votes)
                df_totals = pd.DataFrame(list(all_cands.items()), columns=['Candidat', 'Points']).sort_values(by='Points', ascending=False)
                
                st.subheader("Classement")
                chart = alt.Chart(df_totals).mark_bar(color="#E2001A").encode(
                    x=alt.X('Points'), 
                    y=alt.Y('Candidat', sort='-x'), 
                    tooltip=['Candidat', 'Points']
                ).properties(height=400)
                st.altair_chart(chart, use_container_width=True)
                st.dataframe(df_totals, use_container_width=True)
                
                c_ex1, c_ex2 = st.columns(2)
                c_ex1.download_button("📥 Résultats (CSV)", data=df_totals.to_csv(index=False, sep=";", encoding='utf-8-sig').encode('utf-8-sig'), file_name="resultats.csv", mime="text/csv", use_container_width=True)
                if PDF_AVAILABLE: 
                    c_ex2.download_button("📄 Résultats (PDF)", data=create_pdf_results(cfg['titre_mur'], df_totals, cfg.get("logo_b64"), voters_count), file_name="resultats.pdf", mime="application/pdf", use_container_width=True)
                
                st.divider()
                st.subheader("Audit Détaillé")
                if detailed_data:
                    df_detail = pd.DataFrame(detailed_data)
                    st.dataframe(df_detail, use_container_width=True)
                    c_au1, c_au2 = st.columns(2)
                    c_au1.download_button("📥 Audit Complet (CSV)", data=df_detail.to_csv(index=False, sep=";", encoding='utf-8-sig').encode('utf-8-sig'), file_name="audit_votes.csv", mime="text/csv", use_container_width=True)
                    if PDF_AVAILABLE: 
                        c_au2.download_button("📄 Audit (PDF)", data=create_pdf_audit(cfg['titre_mur'], df_detail, cfg.get("logo_b64")), file_name="audit.pdf", mime="application/pdf", use_container_width=True)
                else: st.info("Aucun vote enregistré.")

# ==============================================================================
#  ZONE 2 : INTERFACE MOBILE (SILO INDEPENDANT)
# ==============================================================================
def interface_mobile_vote():
    cfg = load_json(CONFIG_FILE, default_config)
    st.markdown("""<style>.stApp {background-color:black !important; color:white !important;} [data-testid='stHeader'] {display:none;} .block-container {padding: 1rem !important;}</style>""", unsafe_allow_html=True)
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

# ==============================================================================
#  ZONE 3 : INTERFACE MUR SOCIAL (SILO INDEPENDANT AVEC SOUS-FONCTIONS)
# ==============================================================================

# SOUS-FONCTION : ACCUEIL
def interface_mur_attente(cfg, logo_data, titre_text):
    html = f"""
    <html><body style="background:black;margin:0;height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;font-family:Arial;overflow:hidden;">
        <div style="position:fixed; top:30px; width:100%; text-align:center; z-index:1000;"><h1 style="color:#E2001A; font-family:Arial; font-weight:bold; font-size:50px; text-transform:uppercase; text-shadow: 0 0 10px rgba(0,0,0,0.5);">{titre_text}</h1></div>
        {f'<img src="data:image/png;base64,{logo_data}" style="width:450px;margin-bottom:30px;object-fit:contain;">' if logo_data else ''}
        <h1 style="color:white;font-size:100px;margin:0;font-weight:bold;">BIENVENUE</h1>
    </body></html>
    """
    components.html(html, height=1000)

# SOUS-FONCTION : VOTE OFF
def interface_mur_vote_off(cfg, logo_data, titre_text):
    html = f"""
    <html><body style="background:black;margin:0;height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;font-family:Arial;overflow:hidden;">
        <div style="position:fixed; top:30px; width:100%; text-align:center; z-index:1000;"><h1 style="color:#E2001A; font-family:Arial; font-weight:bold; font-size:50px; text-transform:uppercase; text-shadow: 0 0 10px rgba(0,0,0,0.5);">{titre_text}</h1></div>
        <div style="border:5px solid #E2001A; padding:60px; border-radius:40px; text-align:center;">
            {f'<img src="data:image/png;base64,{logo_data}" style="width:250px;margin-bottom:30px;object-fit:contain;">' if logo_data else ''}
            <h1 style="color:#E2001A;font-size:70px;margin:0;">VOTES CLÔTURÉS</h1>
        </div>
    </body></html>
    """
    components.html(html, height=1000)

# SOUS-FONCTION : VOTE ON (QR + PARTICIPANTS)
def interface_mur_vote_on(cfg, logo_data, titre_text):
    host = st.context.headers.get('host', 'localhost')
    qr = qrcode.make(f"https://{host}/?mode=vote"); buf=BytesIO(); qr.save(buf, format="PNG"); qrb64=base64.b64encode(buf.getvalue()).decode()
    parts = load_json(PARTICIPANTS_FILE, [])
    tags_html = "".join([f"<div style='background:rgba(255,255,255,0.1);color:white;padding:8px 15px;border-radius:20px;border:1px solid #E2001A;font-size:18px;margin:5px;display:inline-block;'>{p}</div>" for p in parts[-10:]])
    
    html = f"""
    <html><body style="background:black;margin:0;height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;font-family:Arial;overflow:hidden;">
        <div style="position:fixed; top:30px; width:100%; text-align:center; z-index:1000;"><h1 style="color:#E2001A; font-family:Arial; font-weight:bold; font-size:50px; text-transform:uppercase; text-shadow: 0 0 10px rgba(0,0,0,0.5);">{titre_text}</h1></div>
        {f'<img src="data:image/png;base64,{logo_data}" style="width:300px;margin-bottom:20px;object-fit:contain;">' if logo_data else ''}
        <div style="background:white;padding:25px;border-radius:25px;display:inline-block;margin-bottom:20px;">
            <img src="data:image/png;base64,{qrb64}" style="width:280px;">
        </div>
        <div style="color:#E2001A;font-size:50px;font-weight:bold;animation:blink 1s infinite;">À VOS VOTES !</div>
        <div style="margin-top:30px;max-width:90%;text-align:center;">{tags_html}</div>
        <style>@keyframes blink {{ 50% {{ opacity: 0; }} }}</style>
    </body></html>
    """
    components.html(html, height=1000)

# SOUS-FONCTION : PODIUM ANIMÉ
def interface_mur_podium(cfg, logo_data, titre_text):
    v_data = load_json(VOTES_FILE, {}); scores = sorted(list(set(v_data.values())), reverse=True)
    s1 = scores[0] if len(scores)>0 else 0; s2 = scores[1] if len(scores)>1 else -1; s3 = scores[2] if len(scores)>2 else -1
    
    def get_p(s):
        l=[]
        for k,v in v_data.items():
            if v==s:
                img = cfg["candidats_images"].get(k)
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
        .grid {{ display:flex; justify-content:center; align-items:flex-end; gap:30px; width:95%; flex-wrap:wrap; }}
        .card {{ background:rgba(255,255,255,0.1); padding:20px; border-radius:20px; width:220px; text-align:center; color:white; animation:pop 0.5s ease-out; }}
        .card img {{ width:120px; height:120px; border-radius:50%; border:3px solid white; object-fit:cover; }}
        .win {{ background:radial-gradient(circle, #333 0%, #111 100%); border:6px solid #FFD700; width:450px; padding:40px; box-shadow:0 0 80px #FFD700; text-align:center; animation:pulse 2s infinite; border-radius:40px; }}
        .win img {{ width:220px; height:220px; border-radius:50%; border:6px solid white; object-fit:cover; margin-bottom:20px; }}
        .win h1 {{ font-size:45px; margin:10px 0; color:white; }} .win h2 {{ font-size:30px; color:#FFD700; }}
        @keyframes pop {{ 0% {{ transform:scale(0); }} 100% {{ transform:scale(1); }} }}
        @keyframes pulse {{ 0% {{ transform:scale(1); }} 50% {{ transform:scale(1.05); }} 100% {{ transform:scale(1); }} }}
    </style></head><body>
        <div style="position:fixed;top:30px;width:100%;text-align:center;z-index:1000;"><h1 style="color:#E2001A;font-family:Arial;font-weight:bold;font-size:50px;text-transform:uppercase;">{titre_text}</h1></div>
        <div id="intro" style="display:none;text-align:center;">
            {f'<img src="data:image/png;base64,{logo_data}" class="logo">' if logo_data else ''}
            <div id="lbl" class="txt"></div><div id="cnt" class="count"></div>
        </div>
        <div id="final" style="display:none;flex-direction:column;align-items:center;">
            {f'<img src="data:image/png;base64,{logo_data}" class="logo">' if logo_data else ''}
            <div id="grid" class="grid"></div>
        </div>
        <script>
            const r1={json.dumps(r1)}, r2={json.dumps(r2)}, r3={json.dumps(r3)};
            const start = {ts_start};
            function card(p, rank) {{
                if(rank==1) return `<div class="win"><div style="font-size:60px">🥇</div>`+(p.i?`<img src="${{p.i}}">`:``)+`<h1>${{p.n}}</h1><h2>VAINQUEUR</h2><h3 style="color:#CCC">${{p.s}} pts</h3></div>`;
                return `<div class="card" style="border:4px solid ${{rank==2?'#C0C0C0':'#CD7F32'}}"><div style="font-size:40px">${{rank==2?'🥈':'🥉'}}</div>`+(p.i?`<img src="${{p.i}}">`:``)+`<h3>${{p.n}}</h3><h4>${{p.s}} pts</h4></div>`;
            }}
            setInterval(() => {{
                const el = (Date.now() - start)/1000;
                const intro = document.getElementById('intro');
                const final = document.getElementById('final');
                const lbl = document.getElementById('lbl');
                const cnt = document.getElementById('cnt');
                const grid = document.getElementById('grid');
                let showIntro = false; let txt = ""; let time = 0;
                if(el < 5) {{ showIntro=true; txt="LES 3èmes..."; time=5-el; }}
                else if(el < 12) {{
                    intro.style.display='none'; final.style.display='flex';
                    let h=""; r3.forEach(p=>h+=card(p,3)); grid.innerHTML=h;
                }}
                else if(el < 17) {{ showIntro=true; txt="LES 2nds..."; time=17-el; }}
                else if(el < 25) {{
                    intro.style.display='none'; final.style.display='flex';
                    let h=""; r3.forEach(p=>h+=card(p,3)); r2.forEach(p=>h+=card(p,2)); grid.innerHTML=h;
                }}
                else if(el < 30) {{ showIntro=true; txt="LE VAINQUEUR..."; time=30-el; }}
                else {{
                    intro.style.display='none'; final.style.display='flex';
                    let h=""; r1.forEach(p=>h+=card(p,1)); grid.innerHTML=h;
                }}
                if(showIntro) {{
                    final.style.display='none'; intro.style.display='block';
                    lbl.innerText=txt; cnt.innerText=Math.ceil(time);
                }}
            }}, 100);
        </script>
    </body></html>
    """, height=1000)

# SOUS-FONCTION : PHOTOS LIVE ANIMÉES (QR + TITRE)
def interface_mur_photos_live(cfg, logo_data, titre_text):
    photos = glob.glob(f"{LIVE_DIR}/*")
    js_imgs = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-40:]])
    host = st.context.headers.get('host', 'localhost')
    qr = qrcode.make(f"https://{host}/?mode=vote"); buf=BytesIO(); qr.save(buf, format="PNG"); qrb64=base64.b64encode(buf.getvalue()).decode()
    
    components.html(f"""
    <html><body style="background:black;margin:0;overflow:hidden;">
    <div style="position:fixed;top:30px;width:100%;text-align:center;z-index:1000;"><h1 style="color:#E2001A;font-family:Arial;font-weight:bold;font-size:50px;text-transform:uppercase;">{titre_text}</h1></div>
    <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;z-index:100;background:rgba(0,0,0,0.8);padding:30px;border-radius:30px;border:2px solid #E2001A;">
        <h1 style="color:#E2001A;margin:0;font-family:Arial;font-size:40px;">MUR PHOTOS LIVE</h1>
        {f'<img src="data:image/png;base64,{logo_data}" style="width:150px;margin-top:10px;">' if logo_data else ''}
         <div style="background:white;padding:10px;border-radius:10px;display:inline-block;margin-top:10px;">
            <img src="data:image/png;base64,{qrb64}" style="width:120px;">
        </div>
        <h2 style="color:white;font-family:Arial;margin-top:10px;">Partagez vos sourires !</h2>
    </div>
    <script>
        const imgs = {js_imgs};
        imgs.forEach(src => {{
            let img = document.createElement('img'); img.src = src;
            img.style.cssText = 'position:absolute;width:'+(Math.random()*150+100)+'px;border-radius:50%;border:4px solid #E2001A;object-fit:cover;';
            let x = Math.random()*window.innerWidth, y = Math.random()*window.innerHeight, dx = (Math.random()-0.5)*3, dy = (Math.random()-0.5)*3;
            document.body.appendChild(img);
            setInterval(() => {{
                x += dx; y += dy;
                if(x<0||x>window.innerWidth) dx*=-1; if(y<0||y>window.innerHeight) dy*=-1;
                img.style.transform = 'translate(' + x + 'px, ' + y + 'px)';
            }}, 20);
        }});
    </script>
    </body></html>
    """, height=1000)

# FONCTION ROUTEUR MUR SOCIAL
def interface_mur_social():
    from streamlit_autorefresh import st_autorefresh
    cfg = load_json(CONFIG_FILE, default_config)
    st_autorefresh(interval=4000, key="wall_refresh")
    
    st.markdown("""<style>.stApp { background-color: black !important; overflow: hidden !important; } [data-testid='stHeader'] { display: none; } .block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; margin-top: -100px !important; }</style>""", unsafe_allow_html=True)
    
    mode = cfg.get("mode_affichage")
    logo_data = cfg.get("logo_b64", "")
    titre_text = cfg.get("titre_mur", "")
    inject_visual_effect(cfg.get("screen_effects", {}).get("attente" if mode=="attente" else "podium", "Aucun"), 25, 15)

    if mode == "attente":
        interface_mur_attente(cfg, logo_data, titre_text)
    elif mode == "votes":
        if cfg.get("reveal_resultats"):
            interface_mur_podium(cfg, logo_data, titre_text)
        elif cfg.get("session_ouverte"):
            interface_mur_vote_on(cfg, logo_data, titre_text)
        else:
            interface_mur_vote_off(cfg, logo_data, titre_text)
    elif mode == "photos_live":
        interface_mur_photos_live(cfg, logo_data, titre_text)

# =========================================================
# ROUTEUR PRINCIPAL
# =========================================================
if est_admin:
    interface_admin()
elif est_utilisateur:
    interface_mobile_vote()
else:
    interface_mur_social()
