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

# --- 1. CONFIGURATION & IMPORTS ---
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

Image.MAX_IMAGE_PIXELS = None 
st.set_page_config(page_title="Régie Master", layout="wide", initial_sidebar_state="expanded")

# Dossiers & Fichiers
LIVE_DIR = "galerie_live_users"
ARCHIVE_DIR = "_archives_sessions"
VOTES_FILE = "votes.json"
CONFIG_FILE = "config_mur.json"
VOTERS_FILE = "voters.json"
PARTICIPANTS_FILE = "participants.json"
DETAILED_VOTES_FILE = "detailed_votes.json"

for d in [LIVE_DIR, ARCHIVE_DIR]: os.makedirs(d, exist_ok=True)

# --- 2. CSS GLOBAL ---
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

# --- 3. CONFIGURATIONS PAR DEFAUT ---
blank_config = { "mode_affichage": "attente", "titre_mur": "TITRE À DÉFINIR", "session_ouverte": False, "reveal_resultats": False, "timestamp_podium": 0, "logo_b64": None, "candidats": [], "candidats_images": {}, "points_ponderation": [5, 3, 1], "effect_intensity": 25, "effect_speed": 15, "screen_effects": {"attente": "Aucun", "votes_open": "Aucun", "votes_closed": "Aucun", "podium": "Aucun", "photos_live": "Aucun"}, "session_id": "" }
default_config = { "mode_affichage": "attente", "titre_mur": "CONCOURS VIDÉO 2026", "session_ouverte": False, "reveal_resultats": False, "timestamp_podium": 0, "logo_b64": None, "candidats": ["BU PAX", "BU FRET", "BU B2B", "RH", "IT", "DPMI", "FINANCES", "AO", "QSSE", "DIRECTION"], "candidats_images": {}, "points_ponderation": [5, 3, 1], "effect_intensity": 25, "effect_speed": 15, "screen_effects": {"attente": "Aucun", "votes_open": "Aucun", "votes_closed": "Aucun", "podium": "Aucun", "photos_live": "Aucun"}, "session_id": str(uuid.uuid4()) }

# --- 4. FONCTIONS UTILITAIRES ---
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
    path = os.path.join(ARCHIVE_DIR, folder_name)
    reset_app_data("none")
    for f in [VOTES_FILE, CONFIG_FILE, VOTERS_FILE, PARTICIPANTS_FILE, DETAILED_VOTES_FILE]:
        src = os.path.join(path, f); 
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

    def create_pdf_res(title, df, logo=None, total=0):
        prep_logo(logo); pdf = PDFReport(); pdf.add_page(); pdf.set_font("Arial", size=12)
        pdf.set_font("Arial", 'B', 14); pdf.cell(0, 10, f"Resultats : {title}", ln=True)
        pdf.set_font("Arial", 'I', 11); pdf.cell(0, 10, f"Votants : {total}", ln=True); pdf.ln(5)
        pdf.set_fill_color(226, 0, 26); pdf.set_text_color(255); pdf.set_font("Arial", 'B', 12)
        pdf.set_x(35); pdf.cell(100, 10, "Candidat", 1, 0, 'C', 1); pdf.cell(40, 10, "Points", 1, 1, 'C', 1); pdf.ln()
        pdf.set_text_color(0); pdf.set_font("Arial", size=12)
        for i, r in df.iterrows():
            pdf.set_x(35); pdf.cell(100, 10, str(r['Candidat']).encode('latin-1','replace').decode('latin-1'), 1, 0, 'C')
            pdf.cell(40, 10, str(r['Points']), 1, 1, 'C'); pdf.ln()
        if os.path.exists("temp_logo.png"): os.remove("temp_logo.png")
        return pdf.output(dest='S').encode('latin-1')

    def create_pdf_aud(title, df, logo=None):
        prep_logo(logo); pdf = PDFReport(); pdf.add_page(); pdf.set_font("Arial", size=10)
        pdf.set_font("Arial", 'B', 14); pdf.cell(0, 10, f"Audit : {title}", ln=True); pdf.ln(5)
        cols = [c for c in df.columns if "Date" not in c]; w = 190//len(cols)
        pdf.set_fill_color(50, 50, 50); pdf.set_text_color(255)
        for c in cols: pdf.cell(w, 8, str(c).encode('latin-1','replace').decode('latin-1'), 1, 0, 'C', 1)
        pdf.ln(); pdf.set_text_color(0)
        for i, r in df.iterrows():
            for c in cols: pdf.cell(w, 8, str(r[c]).encode('latin-1','replace').decode('latin-1'), 1, 0, 'C')
            pdf.ln()
        if os.path.exists("temp_logo.png"): os.remove("temp_logo.png")
        return pdf.output(dest='S').encode('latin-1')

# --- 5. INITIALISATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
is_test_admin = st.query_params.get("test_admin") == "true"
if "config" not in st.session_state: st.session_state.config = load_json(CONFIG_FILE, default_config)

# =========================================================
# 6. FONCTION VIEW ADMIN (SILO)
# =========================================================
def view_admin():
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
            st.title("🗂️ GESTION SESSIONS")
            c1, c2 = st.columns(2, gap="large")
            with c1:
                st.info(f"Session : {st.session_state.config.get('titre_mur')}")
                if st.button("OUVRIR SESSION", type="primary", use_container_width=True): st.session_state["session_active"]=True; st.rerun()
            with c2:
                st.warning("Nouvelle session")
                if st.button("CRÉER VIERGE", type="primary", use_container_width=True):
                    archive_current_session("Auto"); reset_app_data("blank"); st.session_state["session_active"]=True; st.rerun()
            st.divider(); st.write("Archives :")
            for a in sorted([d for d in os.listdir(ARCHIVE_DIR) if os.path.isdir(os.path.join(ARCHIVE_DIR, d))], reverse=True):
                with st.expander(a):
                    c1, c2 = st.columns([3, 1])
                    if c1.button(f"Restaurer {a}", key=f"r_{a}"): archive_current_session("Back"); restore_session_from_archive(a); st.session_state.config = load_json(CONFIG_FILE, default_config); st.session_state["session_active"]=True; st.rerun()
                    if c2.button("🗑️", key=f"d_{a}"): delete_archived_session(a); st.rerun()
        else:
            cfg = st.session_state.config
            with st.sidebar:
                if st.button("⬅️ SESSIONS"): st.session_state["session_active"]=False; st.rerun()
                st.divider(); 
                if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), use_container_width=True)
                if "menu" not in st.session_state: st.session_state.menu = "🔴 PILOTAGE LIVE"
                for m in ["🔴 PILOTAGE LIVE", "⚙️ CONFIG", "📸 MÉDIATHÈQUE", "📊 DATA"]:
                    if st.button(m, type="primary" if st.session_state.menu==m else "secondary", use_container_width=True): st.session_state.menu=m; st.rerun()
                st.divider(); st.markdown("""<a href="/" target="_blank" class="custom-link-btn btn-red">📺 MUR SOCIAL</a><a href="/?mode=vote&test_admin=true" target="_blank" class="custom-link-btn btn-blue">📱 TEST MOBILE</a>""", unsafe_allow_html=True)
                if st.button("DÉCONNEXION"): st.session_state["auth"]=False; st.rerun()

            if st.session_state.menu == "🔴 PILOTAGE LIVE":
                st.title("🔴 PILOTAGE"); c1, c2, c3, c4 = st.columns(4)
                c1.button("🏠 ACCUEIL", type="primary" if cfg["mode_affichage"]=="attente" else "secondary", use_container_width=True, on_click=set_state, args=("attente", False, False))
                c2.button("🗳️ VOTES ON", type="primary" if (cfg["mode_affichage"]=="votes" and cfg["session_ouverte"]) else "secondary", use_container_width=True, on_click=set_state, args=("votes", True, False))
                c3.button("🔒 VOTES OFF", type="primary" if (cfg["mode_affichage"]=="votes" and not cfg["session_ouverte"] and not cfg["reveal_resultats"]) else "secondary", use_container_width=True, on_click=set_state, args=("votes", False, False))
                c4.button("🏆 PODIUM", type="primary" if cfg["reveal_resultats"] else "secondary", use_container_width=True, on_click=set_state, args=("votes", False, True))
                st.button("📸 PHOTOS LIVE", type="primary" if cfg["mode_affichage"]=="photos_live" else "secondary", use_container_width=True, on_click=set_state, args=("photos_live", False, False))
                with st.expander("Danger"):
                    if st.button("RESET DATA"): reset_app_data(full_wipe=False); st.rerun()

            elif st.session_state.menu == "⚙️ CONFIG":
                st.title("CONFIG"); t1, t2 = st.tabs(["Général", "Candidats"])
                with t1:
                    nt = st.text_input("Titre", cfg["titre_mur"])
                    if st.button("Save Titre"): st.session_state.config["titre_mur"]=nt; save_config(); st.rerun()
                    u = st.file_uploader("Logo")
                    if u: st.session_state.config["logo_b64"]=process_logo(u); save_config(); st.rerun()
                with t2:
                    n = st.text_input("Ajout Candidat")
                    if st.button("Ajouter") and n: cfg['candidats'].append(n); save_config(); st.rerun()
                    for i, c in enumerate(cfg['candidats']):
                        c1, c2, c3 = st.columns([0.5, 3, 2])
                        if c in cfg.get("candidats_images", {}): c1.image(BytesIO(base64.b64decode(cfg["candidats_images"][c])), width=40)
                        c2.text_input(f"C{i}", c, disabled=True)
                        ui = c3.file_uploader(f"I{i}", key=f"u{i}")
                        if ui: st.session_state.config["candidats_images"][c]=process_participant_image(ui); save_config(); st.rerun()
                        if c3.button("Del", key=f"d{i}"): cfg['candidats'].remove(c); save_config(); st.rerun()

            elif st.session_state.menu == "📸 MÉDIATHÈQUE":
                st.title("MÉDIATHÈQUE"); 
                if st.button("🗑️ TOUT SUPPRIMER", type="primary"): 
                    for f in glob.glob(f"{LIVE_DIR}/*"): os.remove(f)
                    st.success("Vide"); time.sleep(1); st.rerun()
                fs = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
                if fs:
                    z = BytesIO(); 
                    with zipfile.ZipFile(z, "w") as zf: 
                        for f in fs: zf.write(f, arcname=os.path.basename(f))
                    st.download_button("⬇️ ZIP TOUT", z.getvalue(), "photos.zip", "application/zip", type="secondary")
                    
                    st.write("Sélection :"); sel = []
                    cols = st.columns(5)
                    for i, f in enumerate(fs):
                        with cols[i%5]:
                            st.image(f)
                            if st.checkbox("Sel", key=f): sel.append(f)
                    if sel:
                        zs = BytesIO()
                        with zipfile.ZipFile(zs, "w") as zf:
                            for f in sel: zf.write(f, arcname=os.path.basename(f))
                        st.download_button("⬇️ ZIP SÉLECTION", zs.getvalue(), "selection.zip", "application/zip")
                else: st.info("Vide")

            elif st.session_state.menu == "📊 DATA":
                st.title("DATA"); v = load_json(VOTES_FILE, {}); ac = {c:0 for c in cfg["candidats"]}; ac.update(v)
                df = pd.DataFrame(list(ac.items()), columns=['Candidat','Points']).sort_values('Points', ascending=False)
                c = alt.Chart(df).mark_bar(color="#E2001A").encode(x='Points', y=alt.Y('Candidat', sort='-x'), text='Points').properties(height=400)
                st.altair_chart(c + c.mark_text(align='left', dx=2), use_container_width=True)
                st.dataframe(df, use_container_width=True)
                
                c1, c2 = st.columns(2)
                c1.download_button("CSV Résultats", df.to_csv(sep=";", encoding='utf-8-sig'), "res.csv", "text/csv")
                if PDF_AVAILABLE: c2.download_button("PDF Résultats", create_pdf_res(cfg['titre_mur'], df, cfg.get("logo_b64")), "res.pdf", "application/pdf")
                
                det = load_json(DETAILED_VOTES_FILE, [])
                if det:
                    dfd = pd.DataFrame(det); st.dataframe(dfd)
                    c3, c4 = st.columns(2)
                    c3.download_button("CSV Audit", dfd.to_csv(sep=";", encoding='utf-8-sig'), "audit.csv", "text/csv")
                    if PDF_AVAILABLE: c4.download_button("PDF Audit", create_pdf_aud(cfg['titre_mur'], dfd, cfg.get("logo_b64")), "audit.pdf", "application/pdf")

# =========================================================
# 7. FONCTION VIEW MOBILE (SILO)
# =========================================================
def view_mobile():
    cfg = load_json(CONFIG_FILE, default_config)
    st.markdown("""<style>.stApp {background-color:black !important; color:white !important;} [data-testid='stHeader'] {display:none;} .block-container {padding:1rem !important;}</style>""", unsafe_allow_html=True)
    if "user_pseudo" not in st.session_state:
        if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), width=100)
        p = st.text_input("Pseudo"); 
        if st.button("ENTRER", type="primary") and p: st.session_state.user_pseudo = p; ps=load_json(PARTICIPANTS_FILE, []); ps.append(p); save_json(PARTICIPANTS_FILE, ps); st.rerun()
    else:
        if cfg["mode_affichage"] == "photos_live":
            u = st.file_uploader("Photo", type=['jpg','png']); c = st.camera_input("Camera"); f = u if u else c
            if f: 
                with open(os.path.join(LIVE_DIR, f"live_{uuid.uuid4()}.jpg"), "wb") as o: o.write(f.getbuffer())
                st.success("Envoyé !"); time.sleep(1); st.rerun()
        elif cfg["mode_affichage"] == "votes" and (cfg["session_ouverte"] or is_test_admin):
            if "vote_success" not in st.session_state: st.session_state.vote_success = False
            if st.session_state.vote_success and not is_test_admin: st.info("Vote OK"); st.stop()
            chs = st.multiselect("3 Choix", cfg["candidats"], max_selections=3)
            if len(chs)==3 and st.button("VALIDER", type="primary"):
                v = load_json(VOTES_FILE, {}); 
                for c, p in zip(chs, [5,3,1]): v[c] = v.get(c,0)+p
                save_json(VOTES_FILE, v); d=load_json(DETAILED_VOTES_FILE, []); d.append({"Utilisateur": st.session_state.user_pseudo, "C1": chs[0], "C2": chs[1], "C3": chs[2]}); save_json(DETAILED_VOTES_FILE, d)
                st.session_state.vote_success=True; st.balloons(); st.rerun()
            if is_test_admin and st.session_state.vote_success: st.button("Re-Voter", on_click=reset_vote_callback)
        else: st.info("Attente...")

# =========================================================
# 8. FONCTION VIEW WALL (SILO AVEC SOUS-FONCTIONS)
# =========================================================
def view_wall():
    from streamlit_autorefresh import st_autorefresh
    cfg = load_json(CONFIG_FILE, default_config)
    st_autorefresh(interval=4000)
    st.markdown("""<style>.stApp { background-color: black !important; overflow: hidden !important; } [data-testid='stHeader'] { display: none; } .block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; margin-top: -100px !important; }</style>""", unsafe_allow_html=True)
    
    mode = cfg.get("mode_affichage")
    logo = cfg.get("logo_b64", "")
    titre = cfg.get("titre_mur", "")
    header = f"<div style='position:fixed;top:30px;width:100%;text-align:center;z-index:1000;'><h1 style='color:#E2001A;font-family:Arial;font-size:50px;font-weight:bold;text-transform:uppercase;text-shadow:0 0 10px rgba(0,0,0,0.5);'>{titre}</h1></div>"
    inject_visual_effect(cfg.get("screen_effects",{}).get("attente" if mode=="attente" else "podium", "Aucun"), 25, 15)

    if mode == "attente":
        components.html(f"""<html><body style="background:black;margin:0;height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;font-family:Arial;overflow:hidden;">
            {header}
            {f'<img src="data:image/png;base64,{logo}" style="width:450px;margin-bottom:30px;object-fit:contain;">' if logo else ''}
            <h1 style="color:white;font-size:100px;margin:0;font-weight:bold;">BIENVENUE</h1>
        </body></html>""", height=1000)

    elif mode == "votes" and not cfg["session_ouverte"] and not cfg["reveal_resultats"]:
        components.html(f"""<html><body style="background:black;margin:0;height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;font-family:Arial;overflow:hidden;">
            {header}
            <div style="border:5px solid #E2001A; padding:60px; border-radius:40px; text-align:center;">
                {f'<img src="data:image/png;base64,{logo}" style="width:250px;margin-bottom:30px;object-fit:contain;">' if logo else ''}
                <h1 style="color:#E2001A;font-size:70px;margin:0;">VOTES CLÔTURÉS</h1>
            </div>
        </body></html>""", height=1000)

    elif mode == "votes" and cfg["session_ouverte"]:
        host = st.context.headers.get('host', 'localhost'); qr = qrcode.make(f"https://{host}/?mode=vote"); buf=BytesIO(); qr.save(buf, format="PNG"); qrb64=base64.b64encode(buf.getvalue()).decode()
        parts = load_json(PARTICIPANTS_FILE, []); tags = "".join([f"<div style='background:rgba(255,255,255,0.1);color:white;padding:8px 15px;border-radius:20px;border:1px solid #E2001A;font-size:18px;margin:5px;display:inline-block;'>{p}</div>" for p in parts[-10:]])
        components.html(f"""<html><body style="background:black;margin:0;height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;font-family:Arial;overflow:hidden;">
            {header}
            {f'<img src="data:image/png;base64,{logo}" style="width:300px;margin-bottom:20px;object-fit:contain;">' if logo else ''}
            <div style="background:white;padding:25px;border-radius:25px;display:inline-block;margin-bottom:20px;"><img src="data:image/png;base64,{qrb64}" style="width:280px;"></div>
            <div style="color:#E2001A;font-size:50px;font-weight:bold;animation:blink 1s infinite;">À VOS VOTES !</div>
            <div style="margin-top:30px;max-width:90%;text-align:center;">{tags}</div>
            <style>@keyframes blink {{ 50% {{ opacity: 0; }} }}</style>
        </body></html>""", height=1000)

    elif mode == "votes" and cfg["reveal_resultats"]:
        v = load_json(VOTES_FILE, {}); sc = sorted(list(set(v.values())), reverse=True)
        s1 = sc[0] if sc else 0; s2 = sc[1] if len(sc)>1 else -1; s3 = sc[2] if len(sc)>2 else -1
        def gp(s): return [{'n':k, 's':v[k], 'i':f"data:image/jpeg;base64,{cfg['candidats_images'].get(k)}" if cfg['candidats_images'].get(k) else ""} for k in v if v[k]==s]
        r1, r2, r3 = gp(s1), gp(s2), gp(s3); ts = cfg.get("timestamp_podium", 0)*1000
        components.html(f"""<html><head><style>
            body {{ background:black; margin:0; height:100vh; display:flex; flex-direction:column; justify-content:center; align-items:center; font-family:Arial; overflow:hidden; }}
            .card {{ background:rgba(255,255,255,0.1); padding:20px; border-radius:20px; width:220px; text-align:center; color:white; animation:pop 0.5s ease-out; margin:10px; }}
            .card img {{ width:120px; height:120px; border-radius:50%; border:3px solid white; object-fit:cover; }}
            .win {{ background:radial-gradient(circle, #333 0%, #111 100%); border:6px solid #FFD700; width:450px; padding:40px; box-shadow:0 0 80px #FFD700; text-align:center; animation:pulse 2s infinite; border-radius:40px; }}
            .win img {{ width:220px; height:220px; border-radius:50%; border:6px solid white; object-fit:cover; margin-bottom:20px; }}
            .win h1 {{ font-size:45px; margin:10px 0; color:white; }} .win h2 {{ font-size:30px; color:#FFD700; }}
            @keyframes pop {{ 0% {{ transform:scale(0); }} 100% {{ transform:scale(1); }} }}
            @keyframes pulse {{ 0% {{ transform:scale(1); }} 50% {{ transform:scale(1.05); }} 100% {{ transform:scale(1); }} }}
            .count {{ color:#E2001A; font-size:120px; font-weight:bold; }}
        </style></head><body>
            {header}
            <div id="intro" style="display:none;text-align:center;">{f'<img src="data:image/png;base64,{logo}" style="width:300px;">' if logo else ''}<div id="lbl" style="color:white;font-size:40px;font-weight:bold;"></div><div id="cnt" class="count"></div></div>
            <div id="final" style="display:none;flex-direction:column;align-items:center;">{f'<img src="data:image/png;base64,{logo}" style="width:300px;margin-bottom:20px;">' if logo else ''}<div id="grid" style="display:flex;justify-content:center;align-items:flex-end;flex-wrap:wrap;"></div></div>
            <script>
                const r1={json.dumps(r1)}, r2={json.dumps(r2)}, r3={json.dumps(r3)}; const start={ts};
                function card(p,r){{ 
                    if(r==1) return `<div class="win"><div style="font-size:60px">🥇</div>`+(p.i?`<img src="${{p.i}}">`:``)+`<h1>${{p.n}}</h1><h2>VAINQUEUR</h2><h3>${{p.s}} pts</h3></div>`;
                    return `<div class="card" style="border:4px solid ${{r==2?'#C0C0C0':'#CD7F32'}}"><div style="font-size:40px">${{r==2?'🥈':'🥉'}}</div>`+(p.i?`<img src="${{p.i}}">`:``)+`<h3>${{p.n}}</h3><h4>${{p.s}} pts</h4></div>`;
                }}
                setInterval(()=>{{
                    const el=(Date.now()-start)/1000, i=document.getElementById('intro'), f=document.getElementById('final'), l=document.getElementById('lbl'), c=document.getElementById('cnt'), g=document.getElementById('grid');
                    let si=false, t="", ti=0;
                    if(el<5){{ si=true; t="LES 3èmes..."; ti=5-el; }}
                    else if(el<12){{ i.style.display='none'; f.style.display='flex'; let h=""; r3.forEach(p=>h+=card(p,3)); g.innerHTML=h; }}
                    else if(el<17){{ si=true; t="LES 2nds..."; ti=17-el; }}
                    else if(el<25){{ i.style.display='none'; f.style.display='flex'; let h=""; r3.forEach(p=>h+=card(p,3)); r2.forEach(p=>h+=card(p,2)); g.innerHTML=h; }}
                    else if(el<30){{ si=true; t="LE VAINQUEUR..."; ti=30-el; }}
                    else {{ i.style.display='none'; f.style.display='flex'; let h=""; r1.forEach(p=>h+=card(p,1)); g.innerHTML=h; }}
                    if(si){{ f.style.display='none'; i.style.display='block'; l.innerText=t; c.innerText=Math.ceil(ti); }}
                }},100);
            </script></body></html>""", height=1000)

    elif mode == "photos_live":
        host = st.context.headers.get('host', 'localhost'); qr = qrcode.make(f"https://{host}/?mode=vote"); buf=BytesIO(); qr.save(buf, format="PNG"); qrb64=base64.b64encode(buf.getvalue()).decode()
        photos = glob.glob(f"{LIVE_DIR}/*"); js_imgs = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-40:]])
        components.html(f"""<html><body style="background:black;margin:0;overflow:hidden;">
        {header}
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;z-index:100;background:rgba(0,0,0,0.8);padding:30px;border-radius:30px;border:2px solid #E2001A;">
            <h1 style="color:#E2001A;margin:0;font-family:Arial;font-size:40px;">MUR PHOTOS LIVE</h1>
            {f'<img src="data:image/png;base64,{logo}" style="width:150px;margin-top:10px;">' if logo else ''}
            <div style="background:white;padding:10px;border-radius:10px;display:inline-block;margin-top:10px;"><img src="data:image/png;base64,{qrb64}" style="width:120px;"></div>
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
        </script></body></html>""", height=1000)

# =========================================================
# ROUTEUR PRINCIPAL
# =========================================================
if est_admin:
    view_admin()
elif est_utilisateur:
    view_mobile()
else:
    view_wall()
