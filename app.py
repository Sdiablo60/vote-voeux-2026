import streamlit as st
import os, glob, base64, qrcode, json, time, uuid, textwrap, zipfile, shutil
from io import BytesIO
import streamlit.components.v1 as components
from PIL import Image
from datetime import datetime
import pandas as pd

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
    "screen_effects": {"attente": "Aucun", "votes_open": "Aucun", "votes_closed": "Aucun", "podium": "🎉 Confettis", "photos_live": "Aucun"},
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

def process_image(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        img.thumbnail((300, 300))
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except: return None

def inject_visual_effect(effect_name, intensity, speed):
    if effect_name == "Aucun":
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
    elif effect_name == "🎉 Confettis":
        js_code += f"""
        if(!window.confettiLoaded) {{
            var s = doc.createElement('script'); s.src = "https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js";
            s.onload = function() {{
                function fire() {{ window.parent.confetti({{ particleCount: {max(1, int(intensity*1.5))}, angle: 90, spread: 100, origin: {{ x: Math.random(), y: -0.2 }}, gravity: 0.6, ticks: 600 }}); setTimeout(fire, {max(500, 3000 - (speed * 40))}); }}
                fire();
            }}; layer.appendChild(s); window.confettiLoaded = true;
        }}"""
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
# 1. CONSOLE ADMIN (INTERFACE STANDARD FIABLE)
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
            st.divider()
            if st.button("🔓 DÉCONNEXION"): st.session_state["auth"] = False; st.rerun()

        st.session_state.config = load_json(CONFIG_FILE, default_config)
        cfg = st.session_state.config

        if menu == "🔴 PILOTAGE LIVE":
            st.subheader("Contrôle du Direct")
            mode, open, reveal = cfg["mode_affichage"], cfg["session_ouverte"], cfg["reveal_resultats"]
            
            c1, c2, c3, c4 = st.columns(4)
            if c1.button("1. ACCUEIL", type="primary" if mode=="attente" else "secondary", use_container_width=True):
                cfg.update({"mode_affichage": "attente", "session_ouverte": False, "reveal_resultats": False}); save_config(); st.rerun()
            if c2.button("2. VOTES ON", type="primary" if (mode=="votes" and open) else "secondary", use_container_width=True):
                cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False}); save_config(); st.rerun()
            if c3.button("3. VOTES OFF", type="primary" if (mode=="votes" and not open and not reveal) else "secondary", use_container_width=True):
                cfg.update({"mode_affichage": "votes", "session_ouverte": False, "reveal_resultats": False}); save_config(); st.rerun()
            if c4.button("4. PODIUM", type="primary" if reveal else "secondary", use_container_width=True):
                cfg.update({"mode_affichage": "votes", "reveal_resultats": True, "session_ouverte": False}); cfg["timestamp_podium"] = time.time(); save_config(); st.rerun()

            st.markdown("---")
            if st.button("5. 📸 MUR PHOTOS LIVE", type="primary" if mode=="photos_live" else "secondary", use_container_width=True):
                cfg.update({"mode_affichage": "photos_live", "session_ouverte": False, "reveal_resultats": False}); save_config(); st.rerun()

            st.divider()
            with st.expander("🚨 ZONE DE DANGER"):
                if st.button("🗑️ RESET TOTAL", type="primary"):
                    for f in [VOTES_FILE, VOTERS_FILE, PARTICIPANTS_FILE, DETAILED_VOTES_FILE]:
                        if os.path.exists(f): os.remove(f)
                    cfg["session_id"] = str(uuid.uuid4())
                    save_config(); st.success("RESET EFFECTUÉ"); time.sleep(1); st.rerun()

        elif menu == "⚙️ CONFIG":
            t1, t2 = st.tabs(["Général", "Candidats"])
            with t1:
                new_t = st.text_input("Titre", value=cfg["titre_mur"])
                if st.button("Sauver Titre"): cfg["titre_mur"] = new_t; save_config(); st.rerun()
                upl = st.file_uploader("Logo", type=["png", "jpg"])
                if upl: cfg["logo_b64"] = process_image(upl); save_config(); st.rerun()
            with t2:
                for i, c in enumerate(cfg["candidats"]):
                    c1, c2 = st.columns([1, 4])
                    with c1:
                        if c in cfg.get("candidats_images", {}): st.image(BytesIO(base64.b64decode(cfg["candidats_images"][c])), width=50)
                    with c2:
                        up = st.file_uploader(f"Img {c}", key=f"u_{i}")
                        if up: cfg.setdefault("candidats_images", {})[c] = process_image(up); save_config(); st.rerun()

        elif menu == "📸 MÉDIATHÈQUE":
            files = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
            if st.button("Vider"):
                for f in files: os.remove(f); st.rerun()
            cols = st.columns(4)
            for i, f in enumerate(files):
                with cols[i%4]:
                    st.image(f)
                    if st.button("X", key=f"d_{i}"): os.remove(f); st.rerun()

        elif menu == "📊 DATA":
            st.json(load_json(VOTES_FILE, {}))

# =========================================================
# 2. APPLICATION MOBILE (SÉCURITÉ STRICTE)
# =========================================================
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, default_config)
    st.markdown("<style>.stApp {background-color:black; color:white;} [data-testid='stHeader'] {display:none;}</style>", unsafe_allow_html=True)
    
    if "vote_just_done" not in st.session_state: st.session_state.vote_just_done = False

    curr_sess = cfg.get("session_id", "init")
    
    # --- VIGILE JAVASCRIPT ---
    # C'est ce bloc qui empêche de revoter même si on change de pseudo
    components.html(f"""<script>
        const sS = "{curr_sess}";
        const lS = localStorage.getItem('VOTE_SID_SECURE');
        
        // Si nouvelle session admin (reset), on efface le cookie local
        if(lS !== sS) {{ 
            localStorage.removeItem('HAS_VOTED'); 
            localStorage.setItem('VOTE_SID_SECURE', sS); 
            if(window.parent.location.href.includes('blocked=true')) {{
                window.parent.location.href = window.parent.location.href.replace('&blocked=true','');
            }}
        }} else {{
            // Si même session ET cookie de vote présent -> On bloque tout
            if(localStorage.getItem('HAS_VOTED') === 'true') {{
                if(!window.parent.location.href.includes('blocked=true')) {{
                    window.parent.location.href = window.parent.location.href + '&blocked=true';
                }}
            }}
        }}
    </script>""", height=0)

    # PAGE BLOQUÉE
    if is_blocked or st.session_state.vote_just_done:
        st.balloons()
        st.markdown("""
            <div style='text-align:center; margin-top:50px; padding:20px;'>
                <h1 style='color:#E2001A; font-size:40px;'>MERCI !</h1>
                <h2 style='color:white;'>Vote bien reçu.</h2>
                <br><div style='font-size:80px;'>✅</div>
                <p style='color:#777; margin-top:20px;'>Un seul vote possible.</p>
            </div>
        """, unsafe_allow_html=True)
        st.stop()

    # FORMULAIRE
    if "user_pseudo" not in st.session_state:
        st.subheader("Identification")
        if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), width=100)
        pseudo = st.text_input("Veuillez entrer votre prénom ou Pseudo :")
        if st.button("ENTRER", type="primary", use_container_width=True) and pseudo:
            voters = load_json(VOTERS_FILE, [])
            if pseudo.strip().upper() in [v.upper() for v in voters]: st.error("Déjà utilisé.")
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
                    # Sauvegarde
                    vts = load_json(VOTES_FILE, {})
                    pts = cfg.get("points_ponderation", [5, 3, 1])
                    for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                    save_json(VOTES_FILE, vts)
                    voters = load_json(VOTERS_FILE, [])
                    voters.append(st.session_state.user_pseudo)
                    save_json(VOTERS_FILE, voters)
                    
                    # C'EST ICI QU'ON POSE LE COOKIE DÉFINITIF
                    st.session_state.vote_just_done = True
                    components.html("""<script>localStorage.setItem('HAS_VOTED', 'true'); window.parent.location.href += '&blocked=true';</script>""", height=0)
                    st.rerun()
        else:
            st.info("⏳ En attente de l'ouverture des votes...")

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
        
        .marquee-container { position: absolute; top: 13vh; width: 100%; height: 60px; overflow: hidden; white-space: nowrap; display: flex; align-items: center; background: rgba(255,255,255,0.05); border-bottom: 1px solid #333; z-index: 100; }
        .marquee-content { display: inline-block; animation: marquee 25s linear infinite; }
        .user-tag { display: inline-block; color: #FFF; font-size: 20px; font-weight: bold; margin-right: 40px; background: rgba(255,255,255,0.1); padding: 5px 15px; border-radius: 20px; }
        @keyframes marquee { 0% { transform: translate(100%, 0); } 100% { transform: translate(-100%, 0); } }
        
        .vote-cta { text-align: center; color: #E2001A; font-size: 30px; font-weight: 900; margin-top: 15px; animation: blink 2s infinite; text-transform: uppercase; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

        .list-container { position: absolute; top: 22vh; left: 20px; right: 20px; display: flex; justify-content: center; align-items: flex-start; gap: 40px; }
        .col-list { width: 35%; display: flex; flex-direction: column; }
        .cand-row { display: flex; align-items: center; margin-bottom: 10px; background: rgba(255,255,255,0.08); padding: 8px 20px; border-radius: 50px; width: 100%; height: 70px; }
        .cand-img { width: 55px; height: 55px; border-radius: 50%; object-fit: cover; border: 3px solid #E2001A; }
        .cand-name { color: white; font-size: 22px; font-weight: 600; margin: 0 15px; white-space: nowrap; }
        .row-left { flex-direction: row; justify-content: flex-end; text-align: right; }
        .row-right { flex-direction: row; justify-content: flex-start; text-align: left; }
        
        .qr-center { display:flex; flex-direction:column; align-items:center; justify-content:center; }
        .qr-logo { width: 220px; margin-bottom: 10px; object-fit: contain; }
        
        .winner-card { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 500px; background: rgba(15,15,15,0.98); border: 10px solid #FFD700; border-radius: 50px; padding: 40px; text-align: center; z-index: 1000; box-shadow: 0 0 80px #FFD700; }
        .suspense-container { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); display: flex; gap: 30px; z-index: 1000; }
        .suspense-card { width: 250px; height: 300px; background: rgba(255,255,255,0.05); border: 2px solid #555; display: flex; flex-direction: column; align-items: center; justify-content: center; border-radius: 20px; animation: pulse 1s infinite; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f'<div class="social-header"><h1 class="social-title">{cfg["titre_mur"]}</h1></div>', unsafe_allow_html=True)

    mode = cfg.get("mode_affichage")
    inject_visual_effect(cfg["screen_effects"].get("attente" if mode=="attente" else "podium", "Aucun"), 25, 15)

    if mode == "votes":
        parts = load_json(PARTICIPANTS_FILE, [])
        tags = "".join([f"<span class='user-tag'>{p}</span>" for p in parts])
        st.markdown(f'<div class="marquee-container"><div class="marquee-content">{tags}</div></div>', unsafe_allow_html=True)

    if mode == "attente":
        st.markdown("<div style='position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); text-align:center;'><h1 style='color:white; font-size:100px;'>BIENVENUE</h1><h2 style='color:#AAA; font-size:40px;'>L'événement va commencer...</h2></div>", unsafe_allow_html=True)

    elif mode == "votes":
        if cfg.get("reveal_resultats"):
            v_data = load_json(VOTES_FILE, {})
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)
            elapsed = time.time() - cfg.get("timestamp_podium", 0)
            
            if elapsed < 6.0:
                top3 = sorted_v[:3]
                suspense_html = ""
                for name, score in top3:
                    img = ""
                    if name in cfg.get("candidats_images", {}): img = f'<img src="data:image/png;base64,{cfg["candidats_images"][name]}" style="width:120px; height:120px; border-radius:50%; object-fit:cover; margin-bottom:30px; border:4px solid white;">'
                    suspense_html += f'<div class="suspense-card">{img}<h2 style="color:white; font-size:30px;">{name}</h2></div>'
                st.markdown(f'<div class="suspense-container">{suspense_html}</div>', unsafe_allow_html=True)
                st.markdown("<h1 style='position:fixed; bottom:10%; width:100%; text-align:center; color:#E2001A; font-size:60px; font-weight:bold;'>LE VAINQUEUR EST...</h1>", unsafe_allow_html=True)
                time.sleep(1); st.rerun()
            else:
                if sorted_v:
                    winner, pts = sorted_v[0]
                    img = ""
                    if winner in cfg.get("candidats_images", {}): img = f'<img src="data:image/png;base64,{cfg["candidats_images"][winner]}" style="width:180px; height:180px; border-radius:50%; border:6px solid white; object-fit:cover; margin-bottom:30px;">'
                    st.markdown(f"""<div class="winner-card"><div style="font-size:100px;">🏆</div>{img}<h1 style="color:white; font-size:60px; margin:10px 0;">{winner}</h1><h2 style="color:#FFD700; font-size:40px;">VAINQUEUR</h2><h3 style="color:#CCC; font-size:25px;">Avec {pts} points</h3></div>""", unsafe_allow_html=True)
                    inject_visual_effect("🎉 Confettis", 50, 20)

        elif cfg.get("session_ouverte"):
            cands = cfg.get("candidats", [])
            imgs = cfg.get("candidats_images", {})
            mid = (len(cands) + 1) // 2
            left_list, right_list = cands[:mid], cands[mid:]
            
            # --- CORRECTION BUG AFFICHAGE BLANC : Construction propre des chaînes HTML ---
            html_left = ""
            for c in left_list:
                img_src = f"data:image/png;base64,{imgs[c]}" if c in imgs else "https://via.placeholder.com/60/333/FFF?text=?"
                html_left += f"""<div class="cand-row row-left"><img src="{img_src}" class="cand-img"><span class="cand-name">{c}</span></div>"""
            
            html_right = ""
            for c in right_list:
                img_src = f"data:image/png;base64,{imgs[c]}" if c in imgs else "https://via.placeholder.com/60/333/FFF?text=?"
                html_right += f"""<div class="cand-row row-right"><img src="{img_src}" class="cand-img"><span class="cand-name">{c}</span></div>"""
            
            host = st.context.headers.get('host', 'localhost')
            qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            
            # Logos et QR séparés pour éviter le bug de f-string
            logo_img = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" class="qr-logo">' if cfg.get("logo_b64") else ""
            qr_img = f'<img src="data:image/png;base64,{qr_b64}" width="220">'

            final_html = f"""
            <div class="list-container">
                <div class="col-list">{html_left}</div>
                <div class="qr-center">
                    {logo_img}
                    <div style="background:white; padding:10px; border-radius:15px; border:5px solid #E2001A;">
                        {qr_img}
                    </div>
                    <div class="vote-cta">À VOS VOTES !</div>
                </div>
                <div class="col-list">{html_right}</div>
            </div>
            """
            st.markdown(final_html, unsafe_allow_html=True)
        else:
            st.markdown("<div style='position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); text-align:center; border: 5px solid #E2001A; padding: 60px; border-radius: 40px; background: rgba(0,0,0,0.9);'><h1 style='color:#E2001A; font-size:70px; margin:0;'>VOTES CLÔTURÉS</h1></div>", unsafe_allow_html=True)

    elif mode == "photos_live":
        photos = glob.glob(f"{LIVE_DIR}/*")
        if photos:
            img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-30:]])
            components.html(f"""<script>
                var doc = window.parent.document;
                var container = doc.getElementById('bubble-wall') || doc.createElement('div');
                container.id = 'bubble-wall'; container.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:1;pointer-events:none;';
                if(!doc.getElementById('bubble-wall')) doc.body.appendChild(container);
                const imgs = {img_js}; const bubbles = []; const bSize = 250;
                imgs.forEach((src, i) => {{
                    if(doc.getElementById('bub-'+i)) return;
                    const el = doc.createElement('img'); el.id = 'bub-'+i; el.src = src;
                    el.style.cssText = 'position:absolute; width:'+bSize+'px; height:'+bSize+'px; border-radius:50%; border:8px solid #E2001A; object-fit:cover;';
                    let x = Math.random() * (window.innerWidth - bSize); let y = Math.random() * (window.innerHeight - bSize);
                    let vx = (Math.random()-0.5)*4; let vy = (Math.random()-0.5)*4;
                    container.appendChild(el); bubbles.push({{el, x, y, vx, vy, size: bSize}});
                }});
                function animate() {{
                    bubbles.forEach(b => {{
                        b.x += b.vx; b.y += b.vy;
                        if(b.x <= 0 || b.x + b.size >= window.innerWidth) b.vx *= -1;
                        if(b.y <= 12 * window.innerHeight / 100 || b.y + b.size >= window.innerHeight) b.vy *= -1;
                        b.element.style.transform = `translate(${{b.x}}px, ${{b.y}}px)`;
                    }});
                    requestAnimationFrame(animate);
                }} animate();
            </script>""", height=0)
