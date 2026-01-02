import streamlit as st
import os, glob, base64, qrcode, json, time, uuid, textwrap, zipfile, shutil
from io import BytesIO
import streamlit.components.v1 as components
from PIL import Image
from datetime import datetime
import pandas as pd
import random

# --- CONFIGURATION ---
st.set_page_config(page_title="Régie Master", layout="wide", initial_sidebar_state="expanded")

# Dossiers & Fichiers
LIVE_DIR = "galerie_live_users"
VOTES_FILE = "votes.json"
CONFIG_FILE = "config_mur.json"
VOTERS_FILE = "voters.json"
PARTICIPANTS_FILE = "participants.json"
DETAILED_VOTES_FILE = "detailed_votes.json"

for d in [LIVE_DIR]:
    if not os.path.exists(d): os.makedirs(d)

# --- CONFIG PAR DÉFAUT ---
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

# --- FONCTIONS UTILITAIRES ---
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

# --- CALLBACKS ADMIN ---
def set_state(mode, open_s, reveal):
    st.session_state.config["mode_affichage"] = mode
    st.session_state.config["session_ouverte"] = open_s
    st.session_state.config["reveal_resultats"] = reveal
    if reveal:
        st.session_state.config["timestamp_podium"] = time.time()
    save_config()

def reset_app_data():
    for f in [VOTES_FILE, VOTERS_FILE, PARTICIPANTS_FILE, DETAILED_VOTES_FILE]:
        if os.path.exists(f): os.remove(f)
    st.session_state.config["session_id"] = str(uuid.uuid4())
    save_config()
    st.toast("✅ RESET TOTAL EFFECTUÉ !", icon="🗑️")
    time.sleep(1)

def process_image(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        img.thumbnail((300, 300))
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except: return None

def inject_visual_effect(effect_name, intensity, speed):
    # Gestion des effets simples (Ballons/Neige)
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

# --- NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
is_blocked = st.query_params.get("blocked") == "true"

# --- INIT SESSION ---
if "config" not in st.session_state:
    st.session_state.config = load_json(CONFIG_FILE, default_config)

# =========================================================
# 1. CONSOLE ADMIN
# =========================================================
if est_admin:
    st.title("🎛️ CONSOLE RÉGIE")
    st.write("---")
    
    if "auth" not in st.session_state: st.session_state["auth"] = False
    if not st.session_state["auth"]:
        if st.text_input("Code Admin", type="password") == "ADMIN_LIVE_MASTER":
            st.session_state["auth"] = True; st.rerun()
    else:
        cfg = st.session_state.config
        with st.sidebar:
            if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), use_container_width=True)
            st.header("MENU")
            menu = st.radio("Navigation", ["🔴 PILOTAGE LIVE", "⚙️ CONFIG", "📸 MÉDIATHÈQUE", "📊 DATA"])
            st.divider()
            st.markdown("""<a href="/" target="_blank" style="display:block; text-align:center; background:#E2001A; color:white; padding:10px; border-radius:5px; text-decoration:none;">📺 OUVRIR MUR SOCIAL</a>""", unsafe_allow_html=True)
            st.markdown("""<a href="/?mode=vote" target="_blank" style="display:block; text-align:center; background:#333; color:white; padding:10px; border-radius:5px; text-decoration:none;">📱 TESTER MOBILE</a>""", unsafe_allow_html=True)
            if st.button("🔓 DÉCONNEXION"): st.session_state["auth"] = False; st.rerun()

        if menu == "🔴 PILOTAGE LIVE":
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
                if st.button("🗑️ RESET TOTAL", type="primary"):
                    reset_app_data()
                    st.rerun()

        elif menu == "⚙️ CONFIG":
            t1, t2 = st.tabs(["Général", "Candidats"])
            with t1:
                new_t = st.text_input("Titre", value=cfg["titre_mur"])
                if st.button("Sauver Titre"): st.session_state.config["titre_mur"] = new_t; save_config(); st.rerun()
                upl = st.file_uploader("Logo", type=["png", "jpg"])
                if upl: st.session_state.config["logo_b64"] = process_image(upl); save_config(); st.rerun()
            with t2:
                for i, c in enumerate(cfg["candidats"]):
                    c1, c2 = st.columns([1, 4])
                    with c1:
                        if c in cfg.get("candidats_images", {}): st.image(BytesIO(base64.b64decode(cfg["candidats_images"][c])), width=50)
                    with c2:
                        up = st.file_uploader(f"Image pour {c}", key=f"u_{i}")
                        if up: st.session_state.config.setdefault("candidats_images", {})[c] = process_image(up); save_config(); st.rerun()

        elif menu == "📸 MÉDIATHÈQUE":
            files = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
            if st.button("Tout supprimer"): 
                for f in files: os.remove(f)
                st.rerun()
            cols = st.columns(4)
            for i, f in enumerate(files):
                with cols[i%4]:
                    st.image(f)
                    if st.button("X", key=f"d_{i}"): os.remove(f); st.rerun()

        elif menu == "📊 DATA":
            st.json(load_json(VOTES_FILE, {}))

# =========================================================
# 2. APPLICATION MOBILE
# =========================================================
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, default_config)
    st.markdown("<style>.stApp {background-color:black; color:white;} [data-testid='stHeader'] {display:none;}</style>", unsafe_allow_html=True)
    
    curr_sess = cfg.get("session_id", "init")
    if "vote_success" not in st.session_state: st.session_state.vote_success = False

    # --- GARDIEN ---
    components.html(f"""<script>
        var sS = "{curr_sess}";
        var lS = localStorage.getItem('VOTE_SID_2026');
        if(lS !== sS) {{ 
            localStorage.removeItem('HAS_VOTED_2026'); 
            localStorage.setItem('VOTE_SID_2026', sS); 
            if(window.parent.location.href.includes('blocked=true')) {{
                window.parent.location.href = window.parent.location.href.replace('&blocked=true','');
            }}
        }}
        if(localStorage.getItem('HAS_VOTED_2026') === 'true') {{
            if(!window.parent.location.href.includes('blocked=true')) {{
                window.parent.location.href = window.parent.location.href + '&blocked=true';
            }}
        }}
    </script>""", height=0)

    # --- BLOQUÉ ---
    if is_blocked or st.session_state.vote_success:
        st.balloons()
        st.markdown("""
            <div style='text-align:center; margin-top:50px; padding:20px;'>
                <h1 style='color:#E2001A; font-size:40px;'>MERCI !</h1>
                <h2 style='color:white;'>Vote enregistré.</h2>
                <br><div style='font-size:80px;'>✅</div>
                <p style='color:#777; margin-top:20px;'>Un seul vote autorisé.</p>
            </div>
        """, unsafe_allow_html=True)
        components.html("""<script>localStorage.setItem('HAS_VOTED_2026', 'true');</script>""", height=0)
        st.stop()

    # --- FORMULAIRE ---
    if "user_pseudo" not in st.session_state:
        st.subheader("Identification")
        if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), width=100)
        pseudo = st.text_input("Veuillez entrer votre prénom ou Pseudo :")
        if st.button("ENTRER", type="primary", use_container_width=True) and pseudo:
            voters = load_json(VOTERS_FILE, [])
            if pseudo.strip().upper() in [v.upper() for v in voters]: st.error("Ce pseudo a déjà voté.")
            else:
                st.session_state.user_pseudo = pseudo.strip()
                parts = load_json(PARTICIPANTS_FILE, [])
                if pseudo.strip() not in parts: parts.append(pseudo.strip()); save_json(PARTICIPANTS_FILE, parts)
                st.rerun()
    else:
        if cfg["mode_affichage"] == "photos_live":
            st.info("📸 Envoie ta photo !")
            cam = st.camera_input("Photo")
            if cam:
                with open(os.path.join(LIVE_DIR, f"live_{uuid.uuid4().hex}.jpg"), "wb") as f: f.write(cam.getbuffer())
                st.success("Envoyé !"); time.sleep(1); st.rerun()
        
        elif cfg["mode_affichage"] == "votes" and cfg["session_ouverte"]:
            st.write(f"Bonjour **{st.session_state.user_pseudo}**")
            choix = st.multiselect("Choisis 3 vidéos :", cfg["candidats"], max_selections=3)
            if len(choix) == 3:
                if st.button("VALIDER (DÉFINITIF)", type="primary", use_container_width=True):
                    vts = load_json(VOTES_FILE, {})
                    pts = cfg.get("points_ponderation", [5, 3, 1])
                    for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                    save_json(VOTES_FILE, vts)
                    voters = load_json(VOTERS_FILE, [])
                    voters.append(st.session_state.user_pseudo); save_json(VOTERS_FILE, voters)
                    st.session_state.vote_success = True
                    st.rerun()
        else: st.info("⏳ En attente...")

# =========================================================
# 3. MUR SOCIAL
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2000, key="wall_refresh")
    cfg = load_json(CONFIG_FILE, default_config)
    
    st.markdown("""
    <style>
        body, .stApp { background-color: black !important; font-family: 'Arial', sans-serif; overflow: hidden; }
        [data-testid='stHeader'] { display: none; }
        .social-header { position: fixed; top: 0; left: 0; width: 100%; height: 12vh; background: #E2001A; display: flex; align-items: center; justify-content: center; z-index: 5000; border-bottom: 5px solid white; }
        .social-title { color: white; font-size: 40px; font-weight: bold; margin: 0; text-transform: uppercase; }
        
        .vote-cta { text-align: center; color: #E2001A; font-size: 30px; font-weight: 900; margin-bottom: 20px; animation: blink 2s infinite; text-transform: uppercase; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        
        /* ZONE DE TAGS FIXE */
        .voters-zone {
            position: fixed; top: 13vh; left: 0; width: 100vw; height: 8vh;
            display: flex; justify-content: center; align-items: center; gap: 15px;
            background: rgba(0,0,0,0.5); z-index: 100;
        }
        .user-tag { background: rgba(255,255,255,0.15); color: #FFF; padding: 5px 15px; border-radius: 20px; font-size: 18px; font-weight: bold; border: 1px solid #E2001A; white-space: nowrap; }

        /* CARTES CANDIDATS REDUITES */
        .cand-row { 
            display: flex; align-items: center; justify-content: flex-start;
            background: rgba(255,255,255,0.08); 
            padding: 8px 15px; 
            border-radius: 50px; 
            width: 100%; max-width: 320px; /* TAILLE REDUITE */
            height: 70px; margin: 0 auto 10px auto;
        }
        .cand-img { width: 55px; height: 55px; border-radius: 50%; object-fit: cover; border: 3px solid #E2001A; margin-right: 15px; }
        .cand-name { color: white; font-size: 20px; font-weight: 600; white-space: nowrap; }
        
        .winner-card { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 500px; background: rgba(15,15,15,0.98); border: 10px solid #FFD700; border-radius: 50px; padding: 40px; text-align: center; z-index: 1000; box-shadow: 0 0 80px #FFD700; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f'<div class="social-header"><h1 class="social-title">{cfg["titre_mur"]}</h1></div>', unsafe_allow_html=True)

    mode = cfg.get("mode_affichage")
    inject_visual_effect(cfg["screen_effects"].get("attente" if mode=="attente" else "podium", "Aucun"), 25, 15)

    # --- BANDEAU VOTANTS (TOUS LES ECRANS) ---
    parts = load_json(PARTICIPANTS_FILE, [])
    if parts and mode == "votes":
        tags_html = "".join([f"<span class='user-tag'>{p}</span>" for p in parts[-10:]])
        st.markdown(f'<div class="voters-zone">{tags_html}</div>', unsafe_allow_html=True)

    if mode == "attente":
        if cfg.get("logo_b64"): 
            st.markdown("<div style='position:fixed; top:20vh; left:50%; transform:translate(-50%,0);'>", unsafe_allow_html=True)
            st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), width=300)
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div style='position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); text-align:center;'><h1 style='color:white; font-size:100px;'>BIENVENUE</h1><h2 style='color:#AAA; font-size:40px;'>L'événement va commencer...</h2></div>", unsafe_allow_html=True)

    elif mode == "votes":
        if cfg.get("reveal_resultats"):
            if cfg.get("logo_b64"): 
                st.markdown("<div style='position:fixed; top:15vh; right:20px;'>", unsafe_allow_html=True)
                st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), width=150)
                st.markdown("</div>", unsafe_allow_html=True)
                
            v_data = load_json(VOTES_FILE, {})
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)
            if sorted_v:
                winner, pts = sorted_v[0]
                img = ""
                if winner in cfg.get("candidats_images", {}): img = f'<img src="data:image/png;base64,{cfg["candidats_images"][winner]}" style="width:180px; height:180px; border-radius:50%; border:6px solid white; object-fit:cover; margin-bottom:30px;">'
                st.markdown(f"""<div class="winner-card"><div style="font-size:100px;">🏆</div>{img}<h1 style="color:white; font-size:60px; margin:10px 0;">{winner}</h1><h2 style="color:#FFD700; font-size:40px;">VAINQUEUR</h2><h3 style="color:#CCC; font-size:25px;">Avec {pts} points</h3></div>""", unsafe_allow_html=True)

        elif cfg.get("session_ouverte"):
            cands = cfg.get("candidats", [])
            imgs = cfg.get("candidats_images", {})
            mid = (len(cands) + 1) // 2
            left_list, right_list = cands[:mid], cands[mid:]
            
            # --- STRUCTURE 3 COLONNES ---
            c_left, c_center, c_right = st.columns([1, 1, 1])
            
            with c_left:
                st.markdown("<br><br><br>", unsafe_allow_html=True)
                for c in left_list:
                    img_src = f"data:image/png;base64,{imgs[c]}" if c in imgs else "https://via.placeholder.com/60/333/FFF?text=?"
                    st.markdown(f"<div class='cand-row'><img src='{img_src}' class='cand-img'><span class='cand-name'>{c}</span></div>", unsafe_allow_html=True)
            
            with c_center:
                # MARGE TOP POUR DESCENDRE SOUS LE BANDEAU
                st.markdown("<div style='height:12vh'></div>", unsafe_allow_html=True)
                
                # 1. TEXTE (AU DESSUS)
                st.markdown("<div class='vote-cta'>À VOS VOTES !</div>", unsafe_allow_html=True)
                
                # 2. QR CODE (AU MILIEU)
                host = st.context.headers.get('host', 'localhost')
                qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
                
                # Cadre blanc autour du QR
                st.markdown("<div style='background:white; padding:15px; border-radius:20px; border:5px solid #E2001A; width:280px; margin:0 auto;'>", unsafe_allow_html=True)
                st.image(qr_buf, width=250)
                st.markdown("</div>", unsafe_allow_html=True)
                
                # 3. LOGO (EN DESSOUS)
                if cfg.get("logo_b64"): 
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), width=150)

            with c_right:
                st.markdown("<br><br><br>", unsafe_allow_html=True)
                for c in right_list:
                    img_src = f"data:image/png;base64,{imgs[c]}" if c in imgs else "https://via.placeholder.com/60/333/FFF?text=?"
                    st.markdown(f"<div class='cand-row'><img src='{img_src}' class='cand-img'><span class='cand-name'>{c}</span></div>", unsafe_allow_html=True)

        else:
            if cfg.get("logo_b64"): 
                st.markdown("<div style='position:fixed; top:20vh; left:50%; transform:translate(-50%,0);'>", unsafe_allow_html=True)
                st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), width=200)
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<div style='position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); text-align:center; border: 5px solid #E2001A; padding: 60px; border-radius: 40px; background: rgba(0,0,0,0.9);'><h1 style='color:#E2001A; font-size:70px; margin:0;'>VOTES CLÔTURÉS</h1></div>", unsafe_allow_html=True)

    elif mode == "photos_live":
        # --- MUR PHOTO (Réintégration Logo + QR + Bulles) ---
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        
        # LOGO & QR pour le script JS
        logo_data = cfg.get("logo_b64", "")
        
        photos = glob.glob(f"{LIVE_DIR}/*")
        if photos:
            img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-30:]])
            
            # HTML CENTRAL (QR + LOGO)
            center_html = f"""
            <div id='center-box' style='position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); z-index:10; text-align:center; background:rgba(0,0,0,0.7); padding:30px; border-radius:30px; border:3px solid #E2001A;'>
                <img src="data:image/png;base64,{logo_data}" style="width:150px; margin-bottom:20px; display:block; margin-left:auto; margin-right:auto;">
                <div style="background:white; padding:10px; border-radius:10px;">
                    <img src="data:image/png;base64,{qr_b64}" style="width:200px;">
                </div>
            </div>
            """
            st.markdown(center_html, unsafe_allow_html=True)

            components.html(f"""<script>
                var doc = window.parent.document;
                var container = doc.getElementById('bubble-wall') || doc.createElement('div');
                container.id = 'bubble-wall'; 
                container.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:1;pointer-events:none;';
                if(!doc.getElementById('bubble-wall')) doc.body.appendChild(container);
                
                const imgs = {img_js}; const bubbles = []; const bSize = 250;
                
                imgs.forEach((src, i) => {{
                    if(doc.getElementById('bub-'+i)) return;
                    const el = doc.createElement('img'); el.id = 'bub-'+i; el.src = src;
                    el.style.cssText = 'position:absolute; width:'+bSize+'px; height:'+bSize+'px; border-radius:50%; border:8px solid #E2001A; object-fit:cover;';
                    
                    let x = Math.random() * (window.innerWidth - bSize); 
                    let y = Math.random() * (window.innerHeight - bSize);
                    let vx = (Math.random()-0.5)*6; 
                    let vy = (Math.random()-0.5)*6;
                    
                    container.appendChild(el); bubbles.push({{el, x, y, vx, vy, size: bSize}});
                }});
                
                function animate() {{
                    // On récupère la boite centrale pour le rebond
                    var centerBox = doc.getElementById('center-box');
                    var rect = centerBox ? centerBox.getBoundingClientRect() : {{left:0, right:0, top:0, bottom:0}};
                    
                    bubbles.forEach(b => {{
                        b.x += b.vx; b.y += b.vy;
                        
                        // Rebond Bords Ecran
                        if(b.x <= 0 || b.x + b.size >= window.innerWidth) b.vx *= -1;
                        if(b.y <= 0 || b.y + b.size >= window.innerHeight) b.vy *= -1;
                        
                        // Rebond Boite Centrale (Approximatif)
                        if(centerBox && 
                           b.x + b.size > rect.left && b.x < rect.right && 
                           b.y + b.size > rect.top && b.y < rect.bottom) {{
                               b.vx *= -1; b.vy *= -1;
                        }}
                        
                        b.element.style.transform = `translate(${{b.x}}px, ${{b.y}}px)`;
                    }});
                    requestAnimationFrame(animate);
                }} animate();
            </script>""", height=0)
