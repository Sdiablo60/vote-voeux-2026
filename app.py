import streamlit as st
import os, glob, base64, qrcode, json, random, pandas as pd
from io import BytesIO
import streamlit.components.v1 as components
import time
from PIL import Image
from datetime import datetime
import zipfile
import uuid
import textwrap
import shutil
import threading

# --- GESTION PDF & ALTAIR ---
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

# --- 1. CONFIGURATION ET CONSTANTES ---
st.set_page_config(page_title="Régie Master - Pôle Aéroportuaire", layout="wide", initial_sidebar_state="collapsed")
lock = threading.Lock() 

# Dossiers de stockage
GALLERY_DIR, ADMIN_DIR, LIVE_DIR = "galerie_images", "galerie_admin", "galerie_live_users"
VOTES_FILE = "votes.json"
PARTICIPANTS_FILE = "participants.json"
CONFIG_FILE = "config_mur.json"
VOTERS_FILE = "voters.json"
DETAILED_VOTES_FILE = "detailed_votes.json"

for d in [GALLERY_DIR, ADMIN_DIR, LIVE_DIR]:
    if not os.path.exists(d): os.makedirs(d)

# Configuration par défaut
DEFAULT_CANDIDATS = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCES", "Service AO", "Service QSSE", "DIRECTION POLE"]

default_config = {
    "mode_affichage": "attente", 
    "titre_mur": "CONCOURS VIDÉO PÔLE AÉROPORTUAIRE", 
    "session_ouverte": False, 
    "reveal_resultats": False,
    "timestamp_podium": 0,
    "logo_b64": None,
    "candidats": DEFAULT_CANDIDATS,
    "candidats_images": {}, 
    "points_ponderation": [5, 3, 1],
    "session_id": "session_init_001",
    "effect_intensity": 25, 
    "effect_speed": 25,      
    "screen_effects": {"attente": "Aucun", "votes_open": "Aucun", "votes_closed": "Aucun", "podium": "🎉 Confettis", "photos_live": "Aucun"}
}

# --- 2. INJECTION CSS (POUR ÉVITER LE CLIGNOTEMENT) ---
st.markdown("""
    <style>
        /* Stabilisation du Header Admin */
        .fixed-header {
            position: fixed; top: 0; left: 0; width: 100%; height: 70px;
            background-color: #1E1E1E; z-index: 9999;
            display: flex; align-items: center; justify-content: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-bottom: 2px solid #E2001A;
        }
        .header-title { color: white; font-size: 24px; font-weight: bold; text-transform: uppercase; font-family: sans-serif; }
        .header-logo {
            position: absolute; right: 20px; top: 5px; height: 60px; width: 120px;
            background-size: contain; background-repeat: no-repeat; background-position: right center;
        }
        /* Ajustement du contenu pour ne pas être caché par le header fixe */
        .main .block-container { padding-top: 60px !important; }
        [data-testid="stHeader"] { display:none; }
    </style>
""", unsafe_allow_html=True)

# --- 3. UTILITAIRES DE PERSISTANCE ---
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
        unique_id = uuid.uuid4().hex[:6]
        filename = f"live_{timestamp}_{unique_id}.jpg"
        filepath = os.path.join(LIVE_DIR, filename)
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
    cols = dataframe.columns.tolist(); col_width = 190 / len(cols)
    pdf.set_fill_color(200, 220, 255)
    for col in cols: pdf.cell(col_width, 10, str(col), 1, 0, 'C', 1)
    pdf.ln(); pdf.set_fill_color(255, 255, 255)
    for index, row in dataframe.iterrows():
        for col in cols: pdf.cell(col_width, 10, str(row[col]), 1, 0, 'C')
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1', 'replace')

def inject_visual_effect(effect_name, intensity, speed):
    if effect_name == "Aucun":
        components.html("<script>var old = window.parent.document.getElementById('effect-layer'); if(old) old.remove();</script>", height=0)
        return
    duration = max(2, 20 - (speed * 0.35))
    interval = int(4000 / (intensity + 5))
    js_code = f"""<script>
        var doc = window.parent.document;
        var layer = doc.getElementById('effect-layer');
        if(!layer) {{
            layer = doc.createElement('div'); layer.id = 'effect-layer';
            layer.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:0;overflow:hidden;';
            doc.body.appendChild(layer);
        }}
        function createParticle(char) {{
            var e = doc.createElement('div'); e.innerHTML = char;
            e.style.cssText = 'position:absolute;top:-50px;left:'+Math.random()*100+'vw;font-size:'+(Math.random()*30+20)+'px;transition:top {duration}s linear;';
            layer.appendChild(e);
            setTimeout(() => {{ e.style.top = '110vh'; }}, 50); 
            setTimeout(() => {{ e.remove(); }}, {duration * 1000});
        }}
    """
    if effect_name == "🎈 Ballons": js_code += f"setInterval(() => createParticle('🎈'), {interval});"
    elif effect_name == "❄️ Neige": js_code += f"setInterval(() => createParticle('❄️'), {interval});"
    elif effect_name == "🎉 Confettis":
        js_code += f"""
        var s = doc.createElement('script'); s.src = "https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js";
        s.onload = () => {{
            function fire() {{ window.parent.confetti({{ particleCount: {max(1, int(intensity))}, angle: 90, spread: 80, origin: {{ x: Math.random(), y: -0.1 }} }}); setTimeout(fire, {max(500, 2000 - (speed * 30))}); }}
            fire();
        }}; doc.body.appendChild(s);
        """
    js_code += "</script>"
    components.html(js_code, height=0)

# --- 4. INITIALISATION DE LA SESSION ---
if "config" not in st.session_state: st.session_state.config = load_json(CONFIG_FILE, default_config)
if "session_id" not in st.session_state.config: st.session_state.config["session_id"] = str(int(time.time()))
if "my_uuid" not in st.session_state: st.session_state.my_uuid = str(uuid.uuid4())
if "cam_reset_id" not in st.session_state: st.session_state.cam_reset_id = 0
if "a_vote" not in st.session_state: st.session_state.a_vote = False
if "rules_accepted" not in st.session_state: st.session_state.rules_accepted = False

# --- 5. NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
is_blocked = st.query_params.get("blocked") == "true"

# =========================================================
# 1. CONSOLE ADMIN
# =========================================================
if est_admin:
    # Header statique pour éviter le clignotement
    logo_b64 = st.session_state.config.get("logo_b64")
    logo_html = f"background-image: url('data:image/png;base64,{logo_b64}');" if logo_b64 else ""
    st.markdown(f"""
        <div class="fixed-header">
            <div class="header-title">Console Admin Gestion des Votes</div>
            <div class="header-logo" style="{logo_html}"></div>
        </div>
    """, unsafe_allow_html=True)

    if "auth" not in st.session_state: st.session_state["auth"] = False
    if not st.session_state["auth"]:
        st.markdown("<br><br><h2 style='text-align:center;'>🔐 Connexion Régie</h2>", unsafe_allow_html=True)
        col_c, col_p, col_d = st.columns([1,2,1])
        with col_p:
            pwd = st.text_input("Code d'accès", type="password")
            if pwd == "ADMIN_LIVE_MASTER": st.session_state["auth"] = True; st.rerun()
    else:
        with st.sidebar:
            st.title("🎛️ MENU")
            menu = st.radio("Pilotage", ["🔴 DIRECT", "⚙️ CONFIG", "📸 MÉDIA", "📊 DATA"])
            st.divider()
            st.markdown(f"[📺 Voir le Mur Social](/?v={time.time()})")
        
        if menu == "🔴 DIRECT":
            st.header("🔴 Pilotage Temps Réel")
            cfg = st.session_state.config
            c1, c2, c3, c4 = st.columns(4)
            
            if c1.button("🏠 ACCUEIL", use_container_width=True, type="primary" if cfg["mode_affichage"]=="attente" else "secondary"):
                cfg.update({"mode_affichage": "attente", "session_ouverte": False, "reveal_resultats": False})
                save_json(CONFIG_FILE, cfg); st.rerun()
            if c2.button("🗳️ VOTES ON", use_container_width=True, type="primary" if cfg["session_ouverte"] else "secondary"):
                cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False})
                save_json(CONFIG_FILE, cfg); st.rerun()
            if c3.button("🔒 VOTES OFF", use_container_width=True):
                cfg["session_ouverte"] = False; save_json(CONFIG_FILE, cfg); st.rerun()
            if c4.button("🏆 PODIUM", use_container_width=True, type="primary" if cfg["reveal_resultats"] else "secondary"):
                cfg.update({"mode_affichage": "votes", "reveal_resultats": True, "timestamp_podium": time.time()})
                save_json(CONFIG_FILE, cfg); st.rerun()
            
            st.divider()
            if st.button("📸 MUR PHOTOS LIVE", use_container_width=True, type="primary" if cfg["mode_affichage"]=="photos_live" else "secondary"):
                cfg.update({"mode_affichage": "photos_live", "session_ouverte": False})
                save_json(CONFIG_FILE, cfg); st.rerun()

        elif menu == "⚙️ CONFIG":
            st.header("⚙️ Paramètres")
            cfg = st.session_state.config
            cfg["titre_mur"] = st.text_input("Titre de l'événement", cfg["titre_mur"])
            logo = st.file_uploader("Modifier Logo (PNG)", type=["png"])
            if logo: cfg["logo_b64"] = process_image_upload(logo)
            
            st.subheader("Candidats")
            df = pd.DataFrame(cfg["candidats"], columns=["Nom"])
            edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            if st.button("💾 Sauvegarder"):
                cfg["candidats"] = edited["Nom"].tolist()
                save_json(CONFIG_FILE, cfg); st.rerun()

        elif menu == "📸 MÉDIA":
            st.header("📸 Galerie Live")
            photos = glob.glob(f"{LIVE_DIR}/*")
            if not photos: st.info("Aucune photo.")
            else:
                if st.button("🗑️ Vider Galerie", type="primary"):
                    for f in photos: os.remove(f)
                    st.rerun()
                cols = st.columns(5)
                for i, f in enumerate(photos):
                    with cols[i%5]:
                        st.image(f, use_container_width=True)
                        if st.button("Suppr", key=f): os.remove(f); st.rerun()

        elif menu == "📊 DATA":
            st.header("📊 Résultats des Votes")
            vts = load_json(VOTES_FILE, {})
            if vts:
                df = pd.DataFrame(list(vts.items()), columns=["Service", "Points"]).sort_values("Points", ascending=False)
                st.dataframe(df, use_container_width=True)
                if HAS_ALTAIR:
                    chart = alt.Chart(df).mark_bar().encode(x="Points", y=alt.Y("Service", sort="-x"), color="Points")
                    st.altair_chart(chart, use_container_width=True)
                det_votes = load_json(DETAILED_VOTES_FILE, [])
                if det_votes and HAS_FPDF:
                    pdf = generate_pdf_report(pd.DataFrame(det_votes), "Détail des votes")
                    st.download_button("📥 PDF Report", data=pdf, file_name="votes.pdf")

# =========================================================
# 2. APPLICATION MOBILE
# =========================================================
elif est_utilisateur:
    st.markdown("<style>.stApp {background: black; color: white;} [data-testid='stHeader'] {display:none;}</style>", unsafe_allow_html=True)
    cfg = load_json(CONFIG_FILE, default_config)
    
    if not is_blocked:
        components.html("<script>if(localStorage.getItem('voted_2026')) { window.parent.location.href += '&blocked=true'; }</script>", height=0)
    
    if is_blocked:
        st.error("⛔ Participation enregistrée. Merci !")
        st.stop()

    if "user_pseudo" not in st.session_state:
        st.title("👋 Bienvenue")
        pseudo = st.text_input("Ton Prénom")
        if st.button("ENTRER", use_container_width=True) and pseudo:
            st.session_state.user_pseudo = pseudo
            parts = load_json(PARTICIPANTS_FILE, [])
            if not isinstance(parts, list): parts = []
            parts.append(pseudo); save_json(PARTICIPANTS_FILE, parts)
            st.rerun()
    else:
        if cfg["mode_affichage"] == "photos_live":
            st.header("📸 Partage Photo")
            cam = st.camera_input("Smile !")
            if cam and save_live_photo(cam): st.success("Photo transmise !")
        elif cfg["session_ouverte"]:
            st.subheader("Votez pour vos 3 favoris")
            if "choix" not in st.session_state: st.session_state.choix = []
            cols = st.columns(2)
            for i, cand in enumerate(cfg["candidats"]):
                with cols[i%2]:
                    sel = cand in st.session_state.choix
                    if st.button(f"{'⭐' if sel else '⚪'} {cand}", key=f"m_{i}", use_container_width=True):
                        if sel: st.session_state.choix.remove(cand)
                        elif len(st.session_state.choix) < 3: st.session_state.choix.append(cand)
                        st.rerun()
            if len(st.session_state.choix) == 3:
                if st.button("🚀 VALIDER VOTRE VOTE", type="primary", use_container_width=True):
                    vts = load_json(VOTES_FILE, {})
                    for c, p in zip(st.session_state.choix, [5, 3, 1]): vts[c] = vts.get(c, 0) + p
                    save_json(VOTES_FILE, vts)
                    components.html("<script>localStorage.setItem('voted_2026', 'true'); window.parent.location.reload();</script>", height=0)
        else:
            st.info("⏳ En attente du lancement...")

# =========================================================
# 3. MUR SOCIAL (AFFICHAGE PUBLIC)
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=3000, key="wall_refresh")
    cfg = load_json(CONFIG_FILE, default_config)
    
    # Nettoyage CSS/JS
    if cfg["mode_affichage"] != "photos_live":
        components.html("<script>var c = window.parent.document.getElementById('live-bubble-container'); if(c) c.remove();</script>", height=0)

    st.markdown(f"<div style='background: #E2001A; color: white; text-align: center; padding: 25px; border-bottom: 5px solid white;'><h1>{cfg['titre_mur']}</h1></div>", unsafe_allow_html=True)
    inject_visual_effect(cfg["screen_effects"].get(cfg["mode_affichage"], "Aucun"), cfg["effect_intensity"], cfg["effect_speed"])

    if cfg["mode_affichage"] == "attente":
        st.markdown("<br><br><h1 style='text-align:center; color:white; font-size:100px;'>BIENVENUE</h1>", unsafe_allow_html=True)
        parts = load_json(PARTICIPANTS_FILE, [])
        if parts:
            tags = "".join([f"<span style='background:#333; color:white; padding:10px 20px; border-radius:30px; margin:10px; display:inline-block; border:1px solid white;'>{p}</span>" for p in parts[-20:]])
            st.markdown(f"<div style='text-align:center; margin-top:50px;'>{tags}</div>", unsafe_allow_html=True)

    elif cfg["mode_affichage"] == "votes":
        if not cfg["reveal_resultats"]:
            c1, c2, c3 = st.columns([1, 1, 1])
            with c2:
                host = st.context.headers.get('host', 'localhost')
                qr = qrcode.make(f"http://{host}/?mode=vote")
                buf = BytesIO(); qr.save(buf, format="PNG")
                st.image(buf, caption="SCANNEZ POUR VOTER", use_container_width=True)
        else:
            vts = load_json(VOTES_FILE, {})
            res = sorted(vts.items(), key=lambda x: x[1], reverse=True)[:3]
            if res:
                winner, score = res[0]
                st.markdown(f"<div style='text-align:center; margin-top:80px;'><h1 style='font-size:120px; color:#FFD700;'>🏆 {winner}</h1><h2 style='color:white; font-size:50px;'>{score} POINTS</h2></div>", unsafe_allow_html=True)

    elif cfg["mode_affichage"] == "photos_live":
        photos = glob.glob(f"{LIVE_DIR}/*")
        if photos:
            img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-20:]])
            components.html(f"""
                <script>
                var doc = window.parent.document;
                var cont = doc.getElementById('live-bubble-container') || doc.createElement('div');
                cont.id = 'live-bubble-container'; cont.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:1;';
                if(!doc.getElementById('live-bubble-container')) doc.body.appendChild(cont);
                cont.innerHTML = '';
                var imgs = {img_js};
                imgs.forEach(src => {{
                    var el = doc.createElement('img'); el.src = src;
                    el.style.cssText = 'position:absolute; width:180px; height:180px; border-radius:50%; border:5px solid #E2001A; object-fit:cover; transition: 5s linear;';
                    el.style.left = Math.random()*80+'vw'; el.style.top = Math.random()*80+'vh';
                    cont.appendChild(el);
                }});
                </script>
            """, height=0)
