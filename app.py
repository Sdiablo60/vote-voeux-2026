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

# --- 1. CONFIGURATION & FICHIERS ---
st.set_page_config(page_title="Régie Master", layout="wide")

GALLERY_DIR, ADMIN_DIR, LIVE_DIR = "galerie_images", "galerie_admin", "galerie_live_users"
VOTES_FILE, PARTICIPANTS_FILE, CONFIG_FILE, VOTERS_FILE, DETAILED_VOTES_FILE = "votes.json", "participants.json", "config_mur.json", "voters.json", "detailed_votes.json"

for d in [GALLERY_DIR, ADMIN_DIR, LIVE_DIR]:
    if not os.path.exists(d): os.makedirs(d)

DEFAULT_CANDIDATS = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]

default_config = {
    "mode_affichage": "attente", 
    "titre_mur": "CONCOURS VIDÉO PÔLE AEROPORTUAIRE", 
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

# --- UTILITAIRES ---
def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r") as f: return json.load(f)
        except: return default
    return default

def render_html(html_code):
    """Nettoie le HTML pour affichage propre"""
    clean_code = textwrap.dedent(html_code).strip().replace("\n", " ")
    st.markdown(clean_code, unsafe_allow_html=True)

# --- INIT SESSION ---
if "config" not in st.session_state: st.session_state.config = load_json(CONFIG_FILE, default_config)
if "session_id" not in st.session_state.config: st.session_state.config["session_id"] = str(int(time.time()))
if "my_uuid" not in st.session_state: st.session_state.my_uuid = str(uuid.uuid4())
if "refresh_id" not in st.session_state: st.session_state.refresh_id = 0
if "cam_reset_id" not in st.session_state: st.session_state.cam_reset_id = 0
if "confirm_delete" not in st.session_state: st.session_state.confirm_delete = False
if "user_id" not in st.session_state: st.session_state.user_id = None
if "a_vote" not in st.session_state: st.session_state.a_vote = False
if "rules_accepted" not in st.session_state: st.session_state.rules_accepted = False
if "selected_photos" not in st.session_state: st.session_state.selected_photos = []

# --- LOGIQUE ---
def save_config():
    with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)

def force_refresh():
    st.session_state.refresh_id += 1; save_config()

def process_image_upload(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        img.thumbnail((300, 300))
        buffered = BytesIO()
        img.save(buffered, format="PNG") 
        return base64.b64encode(buffered.getvalue()).decode().replace('\n', '')
    except: return None

def save_live_photo(uploaded_file):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        filename = f"live_{timestamp}_{unique_id}.jpg"
        filepath = os.path.join(LIVE_DIR, filename)
        img = Image.open(uploaded_file)
        try: 
            from PIL import ExifTags
            if hasattr(img, '_getexif'):
                exif = img._getexif()
                if exif:
                    for orientation in ExifTags.TAGS.keys():
                        if ExifTags.TAGS[orientation] == 'Orientation': break
                    if exif.get(orientation) == 3: img = img.rotate(180, expand=True)
                    elif exif.get(orientation) == 6: img = img.rotate(270, expand=True)
                    elif exif.get(orientation) == 8: img = img.rotate(90, expand=True)
        except: pass
        img = img.convert("RGB")
        img.thumbnail((800, 800)) 
        img.save(filepath, "JPEG", quality=80, optimize=True)
        return True
    except: return False

def update_presence(is_active_user=False):
    presence_data = load_json(PARTICIPANTS_FILE, {})
    if isinstance(presence_data, list): presence_data = {}
    now = time.time()
    clean_data = {uid: ts for uid, ts in presence_data.items() if now - ts < 10} 
    if is_active_user: clean_data[st.session_state.my_uuid] = now
    with open(PARTICIPANTS_FILE, "w") as f: json.dump(clean_data, f)
    return len(clean_data)

def inject_visual_effect(effect_name, intensity, speed):
    if effect_name == "Aucun":
        components.html("<script>var old = window.parent.document.getElementById('effect-layer'); if(old) old.remove();</script>", height=0)
        return
    duration = max(2, 20 - (speed * 0.35))
    interval = int(4000 / (intensity + 5))
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
            e.style.cssText = 'position:absolute;bottom:-100px;left:'+Math.random()*100+'vw;font-size:'+(Math.random()*40+20)+'px;transition:bottom {duration}s linear;';
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
    elif effect_name == "🎉 Confettis":
        js_code += f"""
        if(!window.confettiLoaded) {{
            var s = doc.createElement('script'); s.src = "https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js";
            s.onload = function() {{
                function fire() {{ window.parent.confetti({{ particleCount: {max(1, int(intensity*1.5))}, angle: 90, spread: 100, origin: {{ x: Math.random(), y: -0.2 }}, gravity: 0.8, ticks: 400 }}); setTimeout(fire, {max(200, 2000 - (speed * 35))}); }}
                fire();
            }}; layer.appendChild(s); window.confettiLoaded = true;
        }}"""
    js_code += "</script>"
    components.html(js_code, height=0)

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
    for col in cols: pdf.cell(col_width, 10, str(col).encode('latin-1', 'replace').decode('latin-1'), 1, 0, 'C', 1)
    pdf.ln(); pdf.set_fill_color(255, 255, 255)
    for index, row in dataframe.iterrows():
        for col in cols: pdf.cell(col_width, 10, str(row[col]).encode('latin-1', 'replace').decode('latin-1'), 1, 0, 'C')
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
is_blocked = st.query_params.get("blocked") == "true"

# =========================================================
# 1. CONSOLE ADMIN (CORRECTION CLIGNOTEMENT)
# =========================================================
if est_admin:
    # On prépare le CSS et le HTML en une seule fois pour éviter le repeint
    logo_css = ""
    if st.session_state.config.get("logo_b64"):
        logo_css = f"background-image: url('data:image/png;base64,{st.session_state.config['logo_b64']}');"

    st.markdown(f"""
    <style>
        /* Bloquer le scroll sous la barre */
        .main .block-container {{ margin-top: 60px !important; padding-top: 20px !important; }}
        
        /* Header Fixe Optimisé */
        .fixed-header {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 70px;
            background-color: #1E1E1E;
            z-index: 100000; /* Très haut pour rester au dessus */
            display: flex;
            align-items: center;
            justify-content: center;
            border-bottom: 3px solid #E2001A;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5);
            transition: none !important; /* Empêche les animations de transition */
        }}
        
        .header-title {{
            color: white;
            font-size: 24px;
            font-weight: 800;
            text-transform: uppercase;
            font-family: 'Arial', sans-serif;
            letter-spacing: 1px;
        }}

        .header-logo {{
            position: absolute;
            right: 30px;
            top: 5px;
            height: 60px;
            width: 100px;
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
            {logo_css}
        }}
        
        /* Cacher le header natif Streamlit pour éviter les conflits */
        header[data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    
    <div class="fixed-header">
        <div class="header-title">ADMINISTRATION</div>
        <div class="header-logo"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # --- LOGIQUE D'AUTHENTIFICATION ---
    if "auth" not in st.session_state: st.session_state["auth"] = False
    
    if not st.session_state["auth"]:
        st.markdown("<br><br><br>", unsafe_allow_html=True) # Espacement
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.info("🔒 Accès sécurisé")
            if st.text_input("Code d'accès", type="password") == "ADMIN_LIVE_MASTER":
                st.session_state["auth"] = True; st.rerun()
    else:
        # --- MENU LATÉRAL ---
        with st.sidebar:
            st.title("🎛️ PILOTAGE")
            menu = st.radio("Navigation", ["🔴 LIVE", "⚙️ CONFIG", "📸 MÉDIATHÈQUE"], label_visibility="collapsed")
            st.divider()
            
            # Liens rapides
            st.markdown("""
            <div style='display:flex; gap:10px; flex-direction:column;'>
                <a href="/" target="_blank" style='text-decoration:none; background:#E2001A; color:white; padding:8px; border-radius:5px; text-align:center; font-weight:bold;'>📺 ECRAN GÉANT</a>
                <a href="/?mode=vote" target="_blank" style='text-decoration:none; background:#333; color:white; padding:8px; border-radius:5px; text-align:center;'>📱 TEST MOBILE</a>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔓 DÉCONNEXION"):
                st.session_state["auth"] = False; st.rerun()

        cfg = st.session_state.config

        # --- CONTENU DES ONGLETS ---
        if menu == "🔴 LIVE":
            st.subheader("🎮 Contrôle du Direct")
            
            # Indicateur d'état
            etat = "⚪ ATTENTE"
            if cfg["mode_affichage"] == "votes": etat = "🟢 VOTES OUVERTS" if cfg["session_ouverte"] else "🔴 VOTES CLOS"
            if cfg["reveal_resultats"]: etat = "🏆 PODIUM"
            if cfg["mode_affichage"] == "photos_live": etat = "📸 MUR PHOTOS"
            st.markdown(f"**État actuel :** `{etat}`")

            c1, c2, c3, c4 = st.columns(4)
            # Boutons d'action immédiate
            if c1.button("🏠 ACCUEIL"):
                cfg.update({"mode_affichage": "attente", "reveal_resultats": False, "session_ouverte": False})
                save_json(CONFIG_FILE, cfg); st.rerun()
                
            if c2.button("🗳️ OUVRIR VOTES"):
                cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False})
                save_json(CONFIG_FILE, cfg); st.rerun()
                
            if c3.button("🔒 FERMER VOTES"):
                cfg["session_ouverte"] = False
                save_json(CONFIG_FILE, cfg); st.rerun()
                
            if c4.button("🏆 PODIUM"):
                cfg.update({"mode_affichage": "votes", "reveal_resultats": True, "session_ouverte": False})
                save_json(CONFIG_FILE, cfg); st.rerun()
            
            st.markdown("---")
            if st.button("📸 BASCULER SUR MUR PHOTOS LIVE", type="primary", use_container_width=True):
                cfg.update({"mode_affichage": "photos_live"})
                save_json(CONFIG_FILE, cfg); st.rerun()
            
            st.markdown("---")
            with st.expander("🚨 Zone de Danger (Reset)"):
                if st.button("🗑️ TOUT EFFACER (Votes & Votants)"):
                    if os.path.exists(VOTES_FILE): os.remove(VOTES_FILE)
                    if os.path.exists(VOTERS_FILE): os.remove(VOTERS_FILE)
                    st.success("Système réinitialisé à zéro !")
                    time.sleep(1); st.rerun()

        elif menu == "⚙️ CONFIG":
            st.subheader("Paramètres de l'événement")
            t1, t2 = st.tabs(["Général", "Candidats"])
            
            with t1:
                new_title = st.text_input("Titre du Mur", value=cfg["titre_mur"])
                if st.button("Sauvegarder Titre"):
                    cfg["titre_mur"] = new_title; save_json(CONFIG_FILE, cfg); st.rerun()
                
                st.write("---")
                up_logo = st.file_uploader("Changer le Logo (Haut Droite)", type=["png", "jpg"])
                if up_logo:
                    cfg["logo_b64"] = process_image(up_logo)
                    save_json(CONFIG_FILE, cfg); st.rerun()

            with t2:
                for c in cfg["candidats"]:
                    c1, c2 = st.columns([3, 1])
                    with c1: st.write(f"**{c}**")
                    with c2:
                        up = st.file_uploader(f"Img {c}", key=f"u_{c}", label_visibility="collapsed")
                        if up:
                            cfg.setdefault("candidats_images", {})[c] = process_image(up)
                            save_json(CONFIG_FILE, cfg); st.rerun()

        elif menu == "📸 MÉDIATHÈQUE":
            st.subheader("Gestion des Photos Live")
            files = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
            
            if not files:
                st.info("Aucune photo reçue pour le moment.")
            else:
                cols = st.columns(4)
                for i, f in enumerate(files):
                    with cols[i%4]:
                        st.image(f, use_container_width=True)
                        if st.button("Supprimer", key=f"del_{i}"):
                            os.remove(f); st.rerun()

# =========================================================
# 2. APPLICATION MOBILE (UTILISATEUR)
# =========================================================
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, default_config)
    st.markdown("<style>.stApp {background-color:black; color:white;} [data-testid='stHeader'] {display:none;}</style>", unsafe_allow_html=True)
    
    if not is_blocked:
        components.html("""<script>if(localStorage.getItem('has_voted_session_v1')) {window.parent.location.href = window.parent.location.href + "&blocked=true";}</script>""", height=0)

    if is_blocked:
        st.error("⛔ Vous avez déjà voté.")
        st.markdown("<h3 style='text-align:center; color:white;'>Merci de votre participation !</h3>", unsafe_allow_html=True)
        st.stop()

    if "user_pseudo" not in st.session_state:
        st.title("👋 Bienvenue")
        if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), width=100)
        st.write("Pour participer, entrez votre prénom :")
        pseudo = st.text_input("Votre Pseudo", label_visibility="collapsed")
        if st.button("ENTRER", type="primary", use_container_width=True) and pseudo:
            st.session_state.user_pseudo = pseudo
            parts = load_json(PARTICIPANTS_FILE, [])
            if pseudo not in parts:
                parts.append(pseudo)
                with open(PARTICIPANTS_FILE, "w") as f: json.dump(parts, f)
            st.rerun()
            
    elif not st.session_state.rules_accepted and cfg.get("mode_affichage") != "photos_live":
        st.title("📜 Règles du vote")
        st.markdown("""<div style="background:#222; padding:15px; border-radius:10px; border:1px solid #E2001A;"><ul style="font-size:18px;"><li>Vous devez sélectionner <strong>3 candidats</strong>.</li><li>Le vote est <strong>unique</strong> et définitif.</li></ul><hr><h3 style="color:#E2001A">🏆 Pondération :</h3><ul style="font-size:18px;"><li>🥇 <strong>1er choix :</strong> 5 Points</li><li>🥈 <strong>2ème choix :</strong> 3 Points</li><li>🥉 <strong>3ème choix :</strong> 1 Point</li></ul></div>""", unsafe_allow_html=True)
        if st.button("✅ J'AI COMPRIS", type="primary", use_container_width=True):
            st.session_state.rules_accepted = True; st.rerun()
    
    else:
        st.markdown(f"#### Bonjour {st.session_state.user_pseudo} !")
        
        if cfg.get("mode_affichage") == "photos_live":
            st.info("📷 Le mur photo est ouvert !")
            tab1, tab2 = st.tabs(["📸 Prendre Photo", "🖼️ Galerie"])
            photo_to_save = None
            with tab1:
                cam = st.camera_input("Camera", key=f"cam_{st.session_state.cam_reset_id}", label_visibility="collapsed")
                if cam: photo_to_save = cam
            with tab2:
                upl = st.file_uploader("Importer", type=["png", "jpg", "jpeg"], key=f"up_{st.session_state.cam_reset_id}", label_visibility="collapsed")
                if upl: photo_to_save = upl
            if photo_to_save:
                if save_live_photo(photo_to_save): st.success("Envoyée !"); st.session_state.cam_reset_id += 1; time.sleep(1); st.rerun()
        else:
            if not cfg.get("session_ouverte"):
                st.warning("⏳ Les votes sont fermés pour le moment.")
            else:
                if st.session_state.get("a_vote"):
                    st.success("✅ Vote enregistré. Merci !")
                else:
                    st.write("Sélectionnez vos 3 favoris (Ordre : 1er, 2ème, 3ème) :")
                    choix = st.multiselect("Choix", cfg.get("candidats", []), label_visibility="collapsed")
                    if len(choix) == 3:
                        if st.button("VALIDER MES CHOIX (Définitif)", type="primary", use_container_width=True):
                            vts = load_json(VOTES_FILE, {})
                            pts = cfg.get("points_ponderation", [5, 3, 1])
                            for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                            json.dump(vts, open(VOTES_FILE, "w"))
                            voters = load_json(VOTERS_FILE, [])
                            voters.append(st.session_state.user_pseudo)
                            with open(VOTERS_FILE, "w") as f: json.dump(voters, f)
                            det = load_json(DETAILED_VOTES_FILE, [])
                            det.append({"user": st.session_state.user_pseudo, "choix_1": choix[0], "choix_2": choix[1], "choix_3": choix[2], "time": str(datetime.now())})
                            with open(DETAILED_VOTES_FILE, "w") as f: json.dump(det, f)
                            components.html("""<script>localStorage.setItem('has_voted_session_v1', 'true');</script>""", height=0)
                            st.session_state.a_vote = True; time.sleep(1); st.rerun()
                    elif len(choix) > 3: st.error("Maximum 3 choix !")

# =========================================================
# 3. MUR SOCIAL (CONSOLE SOCIALE)
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2000, key="wall_autorefresh")
    cfg = load_json(CONFIG_FILE, default_config)
    
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');
        body, .stApp { background-color: black !important; overflow: hidden; height: 100vh; font-family: 'Montserrat', sans-serif; } 
        [data-testid='stHeader'] { display: none !important; } 
        .block-container { padding: 0 !important; max-width: 100% !important; }
        .user-tag { display: inline-block; background: rgba(255, 255, 255, 0.2); color: white; border-radius: 20px; padding: 5px 15px; margin: 5px; font-size: 18px; }
        .cand-row { display: flex; align-items: center; margin-bottom: 2px; padding: 2px 5px; border-radius: 50px; background: rgba(0,0,0,0.3); } 
        .cand-name { color: white; font-size: 16px; margin: 0 10px; font-weight: 600; white-space: nowrap; }
        .placeholder-circle { width: 45px; height: 45px; border-radius: 50%; border: 1px dashed #666; background: #222; display: inline-block; }
        .cand-img { width: 45px; height: 45px; border-radius: 50%; object-fit: cover; border: 1px solid #E2001A; }
        .qr-box { background: white; padding: 5px; border-radius: 10px; display:inline-block; margin: 10px auto; }
        .social-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 50px; height: 12vh; border-bottom: 2px solid #333; }
        .social-title { font-size: 50px; font-weight: 700; color: #FFF; text-transform: uppercase; margin: 0; }
        .social-logo img { height: 100px; }
        .tags-container { height: 12vh; overflow: hidden; margin-top: 10px; text-align: center; display: flex; align-items: center; justify-content: center; flex-wrap: wrap; align-content: center; }
        .vote-off-box { border: 4px solid #E2001A; padding: 40px 80px; border-radius: 30px; background:rgba(0,0,0,0.8); text-align:center; max-width: 800px; }
        
        /* NOUVEAU STYLE PODIUM */
        .podium-suspense-card {
            width: 300px; height: 300px; background: rgba(255,255,255,0.05); border: 2px solid #555;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            border-radius: 20px; animation: pulse 1s infinite;
        }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.02); box-shadow: 0 0 20px rgba(255,255,255,0.1); } 100% { transform: scale(1); } }
        
        .winner-final-card {
            transform: scale(2); background: rgba(0,0,0,0.8); border: 5px solid #FFD700; padding: 40px; border-radius: 30px;
            box-shadow: 0 0 100px #FFD700; text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

    mode = cfg.get("mode_affichage")
    key_eff = "attente"
    if mode == "photos_live": key_eff = "photos_live"
    elif cfg.get("reveal_resultats"): key_eff = "podium"
    elif mode == "votes": key_eff = "votes_open" if cfg.get("session_ouverte") else "votes_closed"
    inject_visual_effect(cfg["screen_effects"].get(key_eff, "Aucun"), cfg.get("effect_intensity", 25), cfg.get("effect_speed", 25))

    logo_part = ""
    if cfg.get("logo_b64"): 
        logo_part = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:100px;">'

    header_html = f"""<div class="social-header"><h1 class="social-title">{cfg.get('titre_mur')}</h1><div class="social-logo">{logo_part}</div></div>"""
    
    parts = load_json(PARTICIPANTS_FILE, [])
    tags_list = "".join([f"<span class='user-tag'>{p}</span>" for p in parts[-15:]])
    tags_section = f"""<div class="tags-container">{tags_list}</div>"""

    # --- A. ACCUEIL ---
    if mode == "attente":
        render_html(f"""
        <div style="height: 100vh; display: flex; flex-direction: column;">
            {header_html}
            <div style="flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;">
                <h1 style="color:white; font-size:50px; margin-bottom: 20px;">Bonjour à toutes et tous, nous allons bientôt commencer...</h1>
                <h2 style="color:#CCC; font-size:30px;">Veuillez patienter...</h2>
            </div>
            {tags_section}
        </div>
        """)

    # --- B. VOTES ---
    elif mode == "votes":
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        
        if cfg.get("session_ouverte"):
            cands = cfg.get("candidats", [])
            mid = (len(cands) + 1) // 2
            
            def build_list(items, align="left"):
                h = ""
                for c in items:
                    img_html = '<div class="placeholder-circle"></div>'
                    if c in cfg.get("candidats_images", {}):
                        img_html = f'<img src="data:image/png;base64,{cfg["candidats_images"][c]}" class="cand-img">'
                    
                    if align == "right": content = f'<span class="cand-name">{c}</span>{img_html}'
                    else: content = f'{img_html}<span class="cand-name">{c}</span>'
                    
                    h += f'<div class="cand-row" style="justify-content: { "flex-end" if align == "right" else "flex-start" }">{content}</div>'
                return h

            col_g = build_list(cands[:mid], align="right")
            col_d = build_list(cands[mid:], align="left")
            
            render_html(f"""
            <div style="display:flex; flex-direction: column; height:98vh;">
                {header_html}
                {tags_section}
                <div style="display:flex; flex: 1; overflow: hidden; align-items: center;">
                    <div style="width:35%; padding:10px;">{col_g}</div>
                    <div style="width:30%; text-align:center;">
                        <div class="qr-box"><img src="data:image/png;base64,{qr_b64}" width="180"></div>
                        <h2 style="color:white; font-size: 20px; margin-top:5px;">SCANNEZ POUR VOTER</h2>
                    </div>
                    <div style="width:35%; padding:10px;">{col_d}</div>
                </div>
            </div>
            """)
        
        elif cfg.get("reveal_resultats"):
            # PODIUM LOGIC
            elapsed = time.time() - cfg.get("timestamp_podium", 0)
            
            if elapsed < 6.0:
                # PHASE SUSPENSE (6 sec)
                v_data = load_json(VOTES_FILE, {})
                sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)[:3]
                
                cards_html = ""
                for i, (name, score) in enumerate(sorted_v):
                    img = ""
                    if name in cfg.get("candidats_images", {}):
                        img = f'<img src="data:image/png;base64,{cfg["candidats_images"][name]}" style="width:150px; height:150px; border-radius:50%; object-fit:cover; border:3px solid white; margin-bottom:20px;">'
                    cards_html += f"""
                    <div class="podium-suspense-card">
                        {img}
                        <h2 style="color:white; margin:0;">{name}</h2>
                    </div>
                    """
                
                render_html(f"""
                <div style="height:100vh; display:flex; flex-direction:column;">
                    {header_html}
                    <div style="flex:1; display:flex; flex-direction:column; justify-content:center; align-items:center;">
                        <h1 style="color:white; margin-bottom:50px;">QUI SERA LE VAINQUEUR ?</h1>
                        <div style="display:flex; gap:30px;">
                            {cards_html}
                        </div>
                    </div>
                </div>
                """)
                time.sleep(1); st.rerun()
            
            else:
                # PHASE GAGNANT (Final)
                v_data = load_json(VOTES_FILE, {})
                sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)
                winner_name, winner_score = sorted_v[0] if sorted_v else ("?", 0)
                
                img_html = ""
                if winner_name in cfg.get("candidats_images", {}):
                    img_html = f'<img src="data:image/png;base64,{cfg["candidats_images"][winner_name]}" style="width:200px; height:200px; border-radius:50%; object-fit:cover; border:5px solid #FFD700; margin-bottom:20px;">'

                render_html(f"""
                <div style="height:100vh; display:flex; flex-direction:column;">
                    {header_html}
                    <div style="flex:1; display:flex; flex-direction:column; justify-content:center; align-items:center;">
                        <div class="winner-final-card">
                            <div style="font-size:80px; margin-bottom:10px;">🏆</div>
                            {img_html}
                            <h1 style="color:white; margin:0; font-size:50px;">{winner_name}</h1>
                            <h2 style="color:#FFD700; margin-top:20px;">FÉLICITATIONS !</h2>
                            <h3 style="color:#ccc;">{winner_score} Points</h3>
                        </div>
                    </div>
                </div>
                """)
                inject_visual_effect("🎉 Confettis", 50, 50)

        else:
            # Votes CLOS (Vote OFF)
            render_html(f"""
            <div style="height:100vh; display:flex; flex-direction:column;">
                {header_html}
                {tags_section}
                <div style="flex:1; display:flex; flex-direction:column; justify-content:center; align-items:center;">
                    <div class="vote-off-box">
                        <h1 style="color:#E2001A; font-size:40px; margin:0; font-family: 'Montserrat', sans-serif;">MERCI DE VOTRE PARTICIPATION</h1>
                        <h2 style="color:white; font-size:25px; margin-top:15px; font-weight:300;">LES VOTES SONT CLOS</h2>
                    </div>
                </div>
            </div>
            """)

    # --- C. PHOTOS LIVE ---
    elif mode == "photos_live":
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        
        logo_live = ""
        if cfg.get("logo_b64"):
            logo_live = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:150px; width:auto; display:block; margin: 0 auto 20px auto;">'
        
        render_html(f"""
        <div style="position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); z-index:999; display:flex; flex-direction:column; align-items:center; gap:20px;">
            {logo_live}
            <h1 style="color:white; font-size:60px; font-weight:bold; text-transform:uppercase; margin-bottom:20px; text-shadow: 0 0 10px rgba(0,0,0,0.5);">MUR PHOTOS LIVE</h1>
            <div style="background:white; padding:20px; border-radius:25px; box-shadow: 0 0 60px rgba(0,0,0,0.8);">
                <img src="data:image/png;base64,{qr_b64}" width="160" style="display:block;">
            </div>
            <div style="background: #E2001A; color: white; padding: 15px 40px; border-radius: 50px; font-weight: bold; font-size: 26px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-transform: uppercase; white-space: nowrap; border: 2px solid white;">
                📸 SCANNEZ POUR PARTICIPER
            </div>
        </div>
        """)
        
        photos = glob.glob(f"{LIVE_DIR}/*"); photos.sort(key=os.path.getmtime, reverse=True); recent_photos = photos[:40] 
        img_array_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in recent_photos])
        
        components.html(f"""<html><head><style>body {{ margin: 0; overflow: hidden; background: transparent; }} .bubble {{ position: absolute; border-radius: 50%; border: 4px solid #E2001A; box-shadow: 0 0 20px rgba(226, 0, 26, 0.5); object-fit: cover; will-change: transform; }}</style></head><body><div id="container"></div><script>
            var doc = window.parent.document;
            var containerId = 'live-bubble-container';
            var existingContainer = doc.getElementById(containerId);
            if (existingContainer) {{ existingContainer.innerHTML = ''; }} else {{
                existingContainer = doc.createElement('div'); existingContainer.id = containerId;
                existingContainer.style.position = 'fixed'; existingContainer.style.top = '0'; existingContainer.style.left = '0';
                existingContainer.style.width = '100vw'; existingContainer.style.height = '100vh';
                existingContainer.style.pointerEvents = 'none'; existingContainer.style.zIndex = '1';
                doc.body.appendChild(existingContainer);
            }}
            const images = {img_array_js}; const speed = 1.0; const bubbles = [];
            images.forEach((src) => {{ 
                const img = doc.createElement('img'); img.src = src; img.className = 'bubble'; 
                img.style.position = 'absolute'; img.style.borderRadius = '50%'; img.style.border = '4px solid #E2001A'; img.style.objectFit = 'cover';
                const size = 60 + Math.random() * 60; img.style.width = size + 'px'; img.style.height = size + 'px'; 
                let startX = Math.random() * (window.innerWidth - size); let startY = Math.random() * (window.innerHeight - size);
                let vx = (Math.random() - 0.5) * speed * 3; let vy = (Math.random() - 0.5) * speed * 3;
                const bubble = {{ element: img, x: startX, y: startY, vx: vx, vy: vy, size: size }}; 
                existingContainer.appendChild(img); bubbles.push(bubble); 
            }}); 
            function animate() {{ 
                const w = window.innerWidth; const h = window.innerHeight; 
                const centerX = w / 2; const centerY = h / 2; const safeZoneW = 400; const safeZoneH = 500; 
                bubbles.forEach(b => {{ 
                    b.x += b.vx; b.y += b.vy; 
                    if (b.x <= 0 || b.x + b.size >= w) b.vx *= -1; if (b.y <= 0 || b.y + b.size >= h) b.vy *= -1; 
                    if (b.x + b.size > centerX - safeZoneW/2 && b.x < centerX + safeZoneW/2 && b.y + b.size > centerY - safeZoneH/2 && b.y < centerY + safeZoneH/2) {{
                        if(Math.abs(b.x - centerX) > Math.abs(b.y - centerY)) b.vx *= -1; else b.vy *= -1;
                    }}
                    b.element.style.transform = `translate(${{b.x}}px, ${{b.y}}px)`; 
                }}); 
                requestAnimationFrame(animate); 
            }} 
            animate();
        </script></body></html>""", height=1000)

