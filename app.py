import streamlit as st
import os, glob, base64, qrcode, json, time, uuid, threading, zipfile, shutil, textwrap
import pandas as pd
from io import BytesIO
from PIL import Image
from datetime import datetime
import streamlit.components.v1 as components

# --- GESTION PDF & ALTAIR (IMPORTATIONS CRITIQUES) ---
try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

try:
    import altair as alt
    HAS_ALTAIR = True
except ImportError:
    HAS_ALTAIR = False

# --- 1. CONFIGURATION & LOCKING ---
st.set_page_config(page_title="Régie Master - Pôle Aéroportuaire", layout="wide", initial_sidebar_state="collapsed")
lock = threading.Lock() 

# Dossiers et fichiers de données
GALLERY_DIR, ADMIN_DIR, LIVE_DIR = "galerie_images", "galerie_admin", "galerie_live_users"
VOTES_FILE, PARTICIPANTS_FILE, CONFIG_FILE, VOTERS_FILE, DETAILED_VOTES_FILE = "votes.json", "participants.json", "config_mur.json", "voters.json", "detailed_votes.json"

for d in [GALLERY_DIR, ADMIN_DIR, LIVE_DIR]:
    if not os.path.exists(d): os.makedirs(d)

# Injection CSS Global pour stabiliser l'interface et éviter le clignotement
st.markdown("""
    <style>
        header {visibility: hidden;}
        [data-testid="stHeader"] {display:none;}
        .fixed-header {
            position: fixed; top: 0; left: 0; width: 100%; height: 70px;
            background-color: #1E1E1E; z-index: 999999;
            display: flex; align-items: center; justify-content: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-bottom: 2px solid #E2001A;
        }
        .header-title { color: white; font-size: 24px; font-weight: bold; text-transform: uppercase; font-family: sans-serif; }
        .header-logo {
            position: absolute; right: 20px; top: 5px; height: 60px; width: 120px;
            background-size: contain; background-repeat: no-repeat; background-position: right center;
        }
        .main .block-container { padding-top: 80px !important; }
        .user-tag { display: inline-block; background: rgba(226, 0, 26, 0.4); color: white; border-radius: 20px; padding: 5px 15px; margin: 5px; font-size: 18px; border: 1px solid white; }
    </style>
""", unsafe_allow_html=True)

# --- 2. FONCTIONS DE PERSISTENCE SÉCURISÉES ---
def load_json(file, default):
    if os.path.exists(file):
        with lock:
            try:
                with open(file, "r", encoding='utf-8') as f: return json.load(f)
            except: return default
    return default

def save_json(file, data):
    with lock:
        with open(file, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

def process_image_upload(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        if img.mode != "RGBA": img = img.convert("RGBA")
        img.thumbnail((300, 300))
        buffered = BytesIO()
        img.save(buffered, format="PNG") 
        return base64.b64encode(buffered.getvalue()).decode()
    except: return None

def save_live_photo(uploaded_file):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(LIVE_DIR, f"live_{timestamp}_{uuid.uuid4().hex[:6]}.jpg")
        img = Image.open(uploaded_file).convert("RGB")
        img.thumbnail((800, 800)) 
        img.save(filepath, "JPEG", quality=80, optimize=True)
        return True
    except: return False

def generate_pdf_report(dataframe, title):
    if not HAS_FPDF: return None
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15); self.cell(0, 10, title, 0, 1, 'C'); self.ln(10)
        def footer(self):
            self.set_y(-15); self.set_font('Arial', 'I', 8); self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", size=10)
    for col in dataframe.columns: pdf.cell(40, 10, str(col), 1)
    pdf.ln()
    for _, row in dataframe.iterrows():
        for val in row: pdf.cell(40, 10, str(val), 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 3. INITIALISATION ---
DEFAULT_CANDIDATS = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCES", "Service AO", "Service QSSE", "DIRECTION POLE"]
if "config" not in st.session_state:
    st.session_state.config = load_json(CONFIG_FILE, {
        "mode_affichage": "attente", "titre_mur": "CONCOURS VIDÉO PÔLE AÉROPORTUAIRE",
        "session_ouverte": False, "reveal_resultats": False, "timestamp_podium": 0,
        "logo_b64": None, "candidats": DEFAULT_CANDIDATS, "candidats_images": {},
        "effect_intensity": 25, "effect_speed": 25,
        "screen_effects": {"attente": "Aucun", "votes_open": "Aucun", "podium": "🎉 Confettis", "photos_live": "Aucun"}
    })

# --- 4. ROUTAGE ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
is_blocked = st.query_params.get("blocked") == "true"

# =========================================================
# 1. CONSOLE ADMIN
# =========================================================
if est_admin:
    logo_b64 = st.session_state.config.get("logo_b64")
    logo_style = f"background-image: url('data:image/png;base64,{logo_b64}');" if logo_b64 else ""
    st.markdown(f'<div class="fixed-header"><div class="header-title">Console Admin Gestion des Votes</div><div class="header-logo" style="{logo_style}"></div></div>', unsafe_allow_html=True)

    if "auth" not in st.session_state: st.session_state["auth"] = False
    if not st.session_state["auth"]:
        pwd = st.text_input("Code Régie", type="password")
        if pwd == "ADMIN_LIVE_MASTER": st.session_state["auth"] = True; st.rerun()
    else:
        with st.sidebar:
            st.title("🎛️ RÉGIE")
            menu = st.radio("Menu", ["🔴 PILOTAGE LIVE", "⚙️ Paramétrage", "📸 Médiathèque", "📊 Data"])
            if st.button("🔓 Déconnexion"): st.session_state["auth"] = False; st.rerun()

        if menu == "🔴 PILOTAGE LIVE":
            cfg = st.session_state.config
            c1, c2, c3, c4 = st.columns(4)
            if c1.button("🏠 ACCUEIL", use_container_width=True):
                cfg.update({"mode_affichage": "attente", "session_ouverte": False, "reveal_resultats": False})
                save_json(CONFIG_FILE, cfg); st.rerun()
            if c2.button("🗳️ VOTES ON", use_container_width=True):
                cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False})
                save_json(CONFIG_FILE, cfg); st.rerun()
            if c3.button("🔒 VOTES OFF", use_container_width=True):
                cfg["session_ouverte"] = False; save_json(CONFIG_FILE, cfg); st.rerun()
            if c4.button("🏆 PODIUM", use_container_width=True):
                cfg.update({"mode_affichage": "votes", "reveal_resultats": True, "timestamp_podium": time.time()})
                save_json(CONFIG_FILE, cfg); st.rerun()
            
            st.divider()
            if st.button("📸 ACTIVER MUR PHOTOS LIVE", use_container_width=True):
                cfg.update({"mode_affichage": "photos_live", "session_ouverte": False})
                save_json(CONFIG_FILE, cfg); st.rerun()

        elif menu == "⚙️ Paramétrage":
            cfg = st.session_state.config
            st.subheader("Configuration Générale")
            cfg["titre_mur"] = st.text_input("Titre Événement", cfg["titre_mur"])
            logo = st.file_uploader("Logo (PNG)", type=["png"])
            if logo: cfg["logo_b64"] = process_image_upload(logo)
            
            st.subheader("Gestion des Candidats")
            df = pd.DataFrame(cfg["candidats"], columns=["Candidat"])
            edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            if st.button("💾 Sauvegarder Candidats"):
                cfg["candidats"] = edited["Candidat"].tolist()
                save_json(CONFIG_FILE, cfg); st.rerun()

        elif menu == "📸 Médiathèque":
            st.header("📸 Gestion des Photos")
            photos = glob.glob(f"{LIVE_DIR}/*")
            if photos:
                zip_buf = BytesIO()
                with zipfile.ZipFile(zip_buf, "w") as zf:
                    for f in photos: zf.write(f, os.path.basename(f))
                st.download_button("📥 Télécharger ZIP", data=zip_buf.getvalue(), file_name="photos.zip")
                if st.button("🗑️ TOUT SUPPRIMER", type="primary"):
                    for f in photos: os.remove(f)
                    st.rerun()
                cols = st.columns(6)
                for i, f in enumerate(photos):
                    with cols[i%6]:
                        st.image(f)
                        if st.button("Suppr", key=f): os.remove(f); st.rerun()

        elif menu == "📊 Data":
            st.header("📊 Statistiques")
            vts = load_json(VOTES_FILE, {})
            if vts:
                df = pd.DataFrame(list(vts.items()), columns=["Service", "Points"]).sort_values("Points", ascending=False)
                st.dataframe(df, use_container_width=True)
                if HAS_ALTAIR: st.altair_chart(alt.Chart(df).mark_bar().encode(x="Points", y=alt.Y("Service", sort="-x")), use_container_width=True)
                det = load_json(DETAILED_VOTES_FILE, [])
                if det and HAS_FPDF:
                    pdf = generate_pdf_report(pd.DataFrame(det), "Détail des votes")
                    st.download_button("📥 Rapport PDF", pdf, "votes.pdf")

# =========================================================
# 2. APPLICATION MOBILE
# =========================================================
elif est_utilisateur:
    st.markdown("<style>.stApp {background:black; color:white;} [data-testid='stHeader'] {display:none;}</style>", unsafe_allow_html=True)
    if not is_blocked: components.html("<script>if(localStorage.getItem('voted26')) { window.parent.location.href += '&blocked=true'; }</script>", height=0)
    
    if is_blocked: st.error("⛔ Déjà voté !")
    elif "user_pseudo" not in st.session_state:
        pseudo = st.text_input("Ton Prénom")
        if st.button("ENTRER") and pseudo:
            st.session_state.user_pseudo = pseudo
            parts = load_json(PARTICIPANTS_FILE, [])
            parts.append(pseudo); save_json(PARTICIPANTS_FILE, parts); st.rerun()
    else:
        cfg = load_json(CONFIG_FILE, st.session_state.config)
        if cfg["mode_affichage"] == "photos_live":
            cam = st.camera_input("Photo !")
            if cam and save_live_photo(cam): st.success("Transmis !")
        elif cfg["session_ouverte"]:
            if "choix" not in st.session_state: st.session_state.choix = []
            cols = st.columns(2)
            for i, c in enumerate(cfg["candidats"]):
                with cols[i%2]:
                    sel = c in st.session_state.choix
                    if st.button(f"{'⭐' if sel else '⚪'} {c}", key=f"m_{i}", use_container_width=True):
                        if sel: st.session_state.choix.remove(c)
                        elif len(st.session_state.choix) < 3: st.session_state.choix.append(c)
                        st.rerun()
            if len(st.session_state.choix) == 3:
                if st.button("🚀 VALIDER", type="primary", use_container_width=True):
                    vts = load_json(VOTES_FILE, {})
                    for c, p in zip(st.session_state.choix, [5, 3, 1]): vts[c] = vts.get(c, 0) + p
                    save_json(VOTES_FILE, vts)
                    components.html("<script>localStorage.setItem('voted26', 'true'); window.parent.location.reload();</script>", height=0)

# =========================================================
# 3. MUR SOCIAL (AFFICHAGE PUBLIC)
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=3000, key="wall")
    cfg = load_json(CONFIG_FILE, st.session_state.config)
    if cfg["mode_affichage"] != "photos_live": components.html("<script>var c = window.parent.document.getElementById('live-bubble-container'); if(c) c.remove();</script>", height=0)
    
    st.markdown(f"<div style='background:#E2001A; color:white; text-align:center; padding:20px; border-bottom:5px solid white;'><h1>{cfg['titre_mur']}</h1></div>", unsafe_allow_html=True)
    
    if cfg["mode_affichage"] == "attente":
        st.markdown("<br><h1 style='text-align:center; color:white; font-size:80px;'>BIENVENUE</h1>", unsafe_allow_html=True)
        parts = load_json(PARTICIPANTS_FILE, [])
        st.markdown(f"<div style='text-align:center;'>{''.join([f'<span class=\"user-tag\">{p}</span>' for p in parts[-20:]])}</div>", unsafe_allow_html=True)
    elif cfg["mode_affichage"] == "votes" and not cfg["reveal_resultats"]:
        c1, c2, c3 = st.columns([1,1,1])
        with c2:
            qr = qrcode.make(f"http://{st.context.headers.get('host', 'localhost')}/?mode=vote")
            buf = BytesIO(); qr.save(buf, format="PNG")
            st.image(buf, caption="SCANNEZ POUR VOTER", use_container_width=True)
    elif cfg["reveal_resultats"]:
        vts = load_json(VOTES_FILE, {})
        res = sorted(vts.items(), key=lambda x: x[1], reverse=True)[:3]
        if res: st.markdown(f"<div style='text-align:center; margin-top:80px;'><h1 style='font-size:100px; color:#FFD700;'>🏆 {res[0][0]}</h1></div>", unsafe_allow_html=True)
    elif cfg["mode_affichage"] == "photos_live":
        photos = glob.glob(f"{LIVE_DIR}/*")
        if photos:
            img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-15:]])
            components.html(f"<script>var doc = window.parent.document; var cont = doc.getElementById('live-bubble-container') || doc.createElement('div'); cont.id='live-bubble-container'; cont.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:1;'; if(!doc.getElementById('live-bubble-container')) doc.body.appendChild(cont); cont.innerHTML=''; {img_js}.forEach(src => {{ var el = doc.createElement('img'); el.src=src; el.style.cssText='position:absolute; width:180px; height:180px; border-radius:50%; border:5px solid #E2001A; object-fit:cover;'; el.style.left=Math.random()*80+'vw'; el.style.top=Math.random()*80+'vh'; cont.appendChild(el); }});</script>", height=0)
