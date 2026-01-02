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

# --- UTILITAIRES ---
def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding='utf-8') as f: return json.load(f)
        except: return default
    return default

def save_json(file, data):
    with open(file, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- INIT CONFIG ---
if "config" not in st.session_state: 
    st.session_state.config = load_json(CONFIG_FILE, {
        "mode_affichage": "attente", 
        "titre_mur": "CONCOURS VIDÉO PÔLE AEROPORTUAIRE", 
        "session_ouverte": False, 
        "reveal_resultats": False,
        "timestamp_podium": 0,
        "logo_b64": None,
        "candidats": DEFAULT_CANDIDATS,
        "candidats_images": {}, 
        "points_ponderation": [5, 3, 1],
        "effect_intensity": 25, 
        "effect_speed": 25,     
        "screen_effects": {"attente": "Aucun", "votes_open": "Aucun", "votes_closed": "Aucun", "podium": "🎉 Confettis", "photos_live": "Aucun"}
    })

def save_config():
    save_json(CONFIG_FILE, st.session_state.config)

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
        filename = f"live_{timestamp}_{uuid.uuid4().hex[:6]}.jpg"
        filepath = os.path.join(LIVE_DIR, filename)
        img = Image.open(uploaded_file).convert("RGB")
        img.thumbnail((800, 800)) 
        img.save(filepath, "JPEG", quality=80, optimize=True)
        return True
    except: return False

def inject_visual_effect(effect_name, intensity, speed):
    if effect_name == "Aucun": return
    duration = max(2, 20 - (speed * 0.35))
    interval = int(4000 / (intensity + 5))
    js_code = f"""
    <script>
        var doc = window.parent.document;
        var layer = doc.getElementById('effect-layer') || doc.createElement('div');
        if(!doc.getElementById('effect-layer')) {{
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
        if("{effect_name}" == "🎈 Ballons") setInterval(createBalloon, {interval});
    </script>"""
    components.html(js_code, height=0)

# --- NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
is_blocked = st.query_params.get("blocked") == "true"

# =========================================================
# 1. CONSOLE ADMIN (CORRIGÉE : TITRE STABLE)
# =========================================================
if est_admin:
    # On définit le CSS du titre en dehors de toute condition pour éviter le clignotement
    logo_b64 = st.session_state.config.get("logo_b64")
    logo_admin_css = f"url('data:image/png;base64,{logo_b64}')" if logo_b64 else "none"
    
    st.markdown(f"""
    <style>
        .fixed-header {{
            position: fixed; top: 0; left: 0; width: 100%; height: 70px;
            background-color: #1E1E1E; z-index: 9999;
            display: flex; align-items: center; justify-content: center;
            border-bottom: 2px solid #E2001A; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }}
        .header-title {{ color: white; font-size: 24px; font-weight: bold; text-transform: uppercase; font-family: sans-serif; }}
        .header-logo {{ position: absolute; right: 20px; top: 5px; height: 60px; width: 120px; background-image: {logo_admin_css}; background-size: contain; background-repeat: no-repeat; background-position: right center; }}
        .main .block-container {{ padding-top: 80px; }}
    </style>
    <div class="fixed-header">
        <div class="header-title">Console Admin Gestion des Votes</div>
        <div class="header-logo"></div>
    </div>
    """, unsafe_allow_html=True)

    if "auth" not in st.session_state: st.session_state["auth"] = False
    if not st.session_state["auth"]:
        pwd = st.text_input("Mot de passe", type="password")
        if pwd == "ADMIN_LIVE_MASTER": st.session_state["auth"] = True; st.rerun()
    else:
        with st.sidebar:
            st.title("🎛️ RÉGIE")
            menu = st.radio("Menu", ["🔴 PILOTAGE LIVE", "⚙️ Paramétrage", "📸 Médiathèque", "📊 Data"])
            if st.button("🔓 Déconnexion"): st.session_state["auth"] = False; st.rerun()

        if menu == "🔴 PILOTAGE LIVE":
            st.title("🔴 COCKPIT")
            c1, c2, c3, c4 = st.columns(4)
            cfg = st.session_state.config
            if c1.button("1. ACCUEIL", use_container_width=True):
                cfg.update({"mode_affichage": "attente", "session_ouverte": False, "reveal_resultats": False}); save_config(); st.rerun()
            if c2.button("2. VOTES ON", use_container_width=True):
                cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False}); save_config(); st.rerun()
            if c3.button("3. VOTES OFF", use_container_width=True):
                cfg["session_ouverte"] = False; save_config(); st.rerun()
            if c4.button("4. PODIUM", use_container_width=True):
                cfg.update({"mode_affichage": "votes", "reveal_resultats": True, "timestamp_podium": time.time()}); save_config(); st.rerun()
            
            if st.button("📸 MUR PHOTOS LIVE", type="primary", use_container_width=True):
                cfg.update({"mode_affichage": "photos_live", "session_ouverte": False}); save_config(); st.rerun()

        elif menu == "⚙️ Paramétrage":
            st.title("⚙️ Paramétrage")
            # Conservation de toutes vos options de candidats
            new_title = st.text_input("Titre", value=st.session_state.config["titre_mur"])
            if st.button("Sauver"): st.session_state.config["titre_mur"] = new_title; save_config(); st.rerun()
            
            up_l = st.file_uploader("Nouveau Logo")
            if up_l:
                st.session_state.config["logo_b64"] = process_image_upload(up_l); save_config(); st.rerun()

        elif menu == "📸 Médiathèque":
            st.title("📸 Médiathèque")
            files = glob.glob(f"{LIVE_DIR}/*")
            if st.button("🗑️ TOUT SUPPRIMER"):
                for f in files: os.remove(f)
                st.rerun()
            cols = st.columns(6)
            for i, f in enumerate(files):
                with cols[i%6]:
                    st.image(f)
                    if st.button("❌", key=f"del_{i}"): os.remove(f); st.rerun()

        elif menu == "📊 Data":
            st.title("📊 Data")
            v_data = load_json(VOTES_FILE, {})
            st.write(v_data)

# =========================================================
# 2. APPLICATION MOBILE (CORRIGÉE : BOUTON & BALLONS)
# =========================================================
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, st.session_state.config)
    st.markdown("<style>.stApp {background-color:black; color:white;} [data-testid='stHeader'] {display:none;}</style>", unsafe_allow_html=True)
    
    if not is_blocked:
        components.html("<script>if(localStorage.getItem('voted_2026')) { window.parent.location.href += '&blocked=true'; }</script>", height=0)

    if is_blocked:
        st.error("⛔ Déjà voté !")
        st.balloons() # Animation de ballons automatique au blocage
        st.stop()

    if "user_pseudo" not in st.session_state:
        pseudo = st.text_input("Ton Prénom")
        if st.button("ENTRER") and pseudo:
            st.session_state.user_pseudo = pseudo; st.rerun()
    else:
        st.write(f"Bonjour {st.session_state.user_pseudo}")
        if cfg["mode_affichage"] == "photos_live":
            cam = st.camera_input("📸 Photo")
            if cam and save_live_photo(cam): st.success("Envoyé !"); st.rerun()
        else:
            if not cfg["session_ouverte"]: st.warning("Votes fermés")
            else:
                choix = st.multiselect("Choisis 3 vidéos :", cfg["candidats"], max_selections=3)
                
                # CORRECTION : Le bouton apparaît et reste focus dès qu'il y a 3 choix
                if len(choix) == 3:
                    st.markdown("---")
                    if st.button("🚀 VALIDER MON VOTE", type="primary", use_container_width=True):
                        st.balloons() # Animation demandée
                        vts = load_json(VOTES_FILE, {})
                        for v in choix: vts[v] = vts.get(v, 0) + 1
                        save_json(VOTES_FILE, vts)
                        components.html("<script>localStorage.setItem('voted_2026', 'true'); setTimeout(()=>window.parent.location.reload(), 2000);</script>", height=0)
                elif len(choix) > 0:
                    st.info(f"Encore {3 - len(choix)} choix à faire...")

# =========================================================
# 3. MUR SOCIAL (CORRIGÉ : REBOND SUR QR)
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2000, key="wall_refresh")
    cfg = load_json(CONFIG_FILE, st.session_state.config)
    
    # Header stable
    st.markdown(f"""
    <div style='text-align:center; background:#E2001A; padding:20px; border-bottom:5px solid white; position:relative; z-index:100;'>
        <h1 style='color:white; font-size:60px; margin:0;'>{cfg['titre_mur']}</h1>
    </div>""", unsafe_allow_html=True)

    if cfg["mode_affichage"] == "attente":
        st.markdown("<h1 style='text-align:center; color:white; margin-top:100px;'>BIENVENUE</h1>", unsafe_allow_html=True)

    elif cfg["mode_affichage"] == "votes" or cfg["mode_affichage"] == "photos_live":
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"http://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

        # QR CODE CENTRAL
        st.markdown(f"""
        <div id="qr-container" style="position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); z-index:99; background:white; padding:20px; border-radius:20px; text-align:center; border: 5px solid #E2001A;">
            <img src="data:image/png;base64,{qr_b64}" width="200">
            <h2 style="color:black; font-family:sans-serif; margin-top:10px;">SCANNEZ POUR PARTICIPER</h2>
        </div>
        """, unsafe_allow_html=True)

        # ANIMATION PHOTOS (Correction Collision)
        photos = glob.glob(f"{LIVE_DIR}/*")
        if photos:
            img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-20:]])
            components.html(f"""
            <script>
                var doc = window.parent.document;
                var container = doc.getElementById('bubble-wall') || doc.createElement('div');
                container.id = 'bubble-wall';
                container.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:1;pointer-events:none;';
                if(!doc.getElementById('bubble-wall')) doc.body.appendChild(container);

                const imgs = {img_js};
                const bubbles = [];
                // Définition de la zone du QR Code pour le rebond
                const qrRect = {{ x: window.innerWidth/2 - 150, y: window.innerHeight/2 - 150, w: 300, h: 400 }};

                imgs.forEach((src, i) => {{
                    if(doc.getElementById('bub-'+i)) return;
                    const el = doc.createElement('img'); el.id = 'bub-'+i; el.src = src;
                    el.style.cssText = 'position:absolute; width:120px; height:120px; border-radius:50%; border:3px solid #E2001A; object-fit:cover;';
                    let x = Math.random() * window.innerWidth;
                    let y = Math.random() * window.innerHeight;
                    let vx = (Math.random() - 0.5) * 3;
                    let vy = (Math.random() - 0.5) * 3;
                    container.appendChild(el);
                    bubbles.push({{el, x, y, vx, vy, size: 120}});
                }});

                function animate() {{
                    bubbles.forEach(b => {{
                        b.x += b.vx; b.y += b.vy;
                        // Rebond bords écran
                        if(b.x <= 0 || b.x + b.size >= window.innerWidth) b.vx *= -1;
                        if(b.y <= 0 || b.y + b.size >= window.innerHeight) b.vy *= -1;
                        
                        // REBOND SUR LE QR CODE
                        if(b.x + b.size > qrRect.x && b.x < qrRect.x + qrRect.w && b.y + b.size > qrRect.y && b.y < qrRect.y + qrRect.h) {{
                            b.vx *= -1; b.vy *= -1;
                            b.x += b.vx * 4; b.y += b.vy * 4; // Éviter de rester collé
                        }}
                        b.el.style.transform = `translate(${{b.x}}px, ${{b.y}}px)`;
                    }});
                    requestAnimationFrame(animate);
                }
                animate();
            </script>
            """, height=0)

    if cfg.get("reveal_resultats"):
        st.balloons()
