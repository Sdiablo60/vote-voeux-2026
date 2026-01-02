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
# 1. CONSOLE ADMIN (STANDARD STREAMLIT - AUCUN CSS BLOQUANT)
# =========================================================
if est_admin:
    st.title("🎛️ CONSOLE RÉGIE")
    st.markdown("---")
    
    if "auth" not in st.session_state: st.session_state["auth"] = False
    if not st.session_state["auth"]:
        if st.text_input("Code", type="password") == "ADMIN_LIVE_MASTER":
            st.session_state["auth"] = True; st.rerun()
    else:
        cfg = st.session_state.config
        
        with st.sidebar:
            if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), use_container_width=True)
            st.header("MENU")
            menu = st.radio("Navigation", ["🔴 PILOTAGE LIVE", "⚙️ CONFIG", "📸 MÉDIATHÈQUE", "📊 DATA"])
            st.divider()
            if st.button("🔓 DÉCONNEXION"): st.session_state["auth"] = False; st.rerun()

        # RECHARGEMENT SYSTÉMATIQUE
        st.session_state.config = load_json(CONFIG_FILE, default_config)
        cfg = st.session_state.config

        if menu == "🔴 PILOTAGE LIVE":
            st.subheader("Contrôle du Direct")
            
            mode = cfg["mode_affichage"]
            open = cfg["session_ouverte"]
            reveal = cfg["reveal_resultats"]
            
            c1, c2, c3, c4 = st.columns(4)
            
            if c1.button("1. ACCUEIL", type="primary" if mode=="attente" else "secondary", use_container_width=True):
                cfg.update({"mode_affichage": "attente", "session_ouverte": False, "reveal_resultats": False})
                save_config(); st.rerun()
                
            if c2.button("2. VOTES ON", type="primary" if (mode=="votes" and open) else "secondary", use_container_width=True):
                cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False})
                save_config(); st.rerun()
                
            if c3.button("3. VOTES OFF", type="primary" if (mode=="votes" and not open and not reveal) else "secondary", use_container_width=True):
                cfg.update({"mode_affichage": "votes", "session_ouverte": False, "reveal_resultats": False})
                save_config(); st.rerun()
                
            if c4.button("4. PODIUM", type="primary" if reveal else "secondary", use_container_width=True):
                cfg.update({"mode_affichage": "votes", "reveal_resultats": True, "session_ouverte": False})
                cfg["timestamp_podium"] = time.time()
                save_config(); st.rerun()

            st.markdown("---")
            if st.button("5. 📸 MUR PHOTOS LIVE", type="primary" if mode=="photos_live" else "secondary", use_container_width=True):
                cfg.update({"mode_affichage": "photos_live", "session_ouverte": False, "reveal_resultats": False})
                save_config(); st.rerun()

            st.divider()
            with st.expander("🚨 ZONE DE DANGER"):
                if st.button("🗑️ RESET TOTAL", type="primary"):
                    for f in [VOTES_FILE, VOTERS_FILE, PARTICIPANTS_FILE, DETAILED_VOTES_FILE]:
                        if os.path.exists(f): os.remove(f)
                    cfg["session_id"] = str(uuid.uuid4())
                    save_config()
                    st.success("RESET EFFECTUÉ"); time.sleep(1); st.rerun()

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
# 2. APPLICATION MOBILE (SÉCURISÉE)
# =========================================================
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, default_config)
    st.markdown("<style>.stApp {background-color:black; color:white;} [data-testid='stHeader'] {display:none;}</style>", unsafe_allow_html=True)
    
    if "vote_just_done" not in st.session_state: st.session_state.vote_just_done = False

    curr_sess = cfg.get("session_id", "init")
    components.html(f"""<script>
        var sS = "{curr_sess}";
        var lS = localStorage.getItem('VOTE_SID');
        if(lS !== sS) {{ localStorage.removeItem('VOTE_DONE'); localStorage.setItem('VOTE_SID', sS); 
           if(window.parent.location.href.includes('blocked=true')) window.parent.location.href = window.parent.location.href.replace('&blocked=true','');
        }}
    </script>""", height=0)

    if is_blocked or st.session_state.vote_just_done:
        st.balloons()
        st.markdown("<div style='text-align:center; margin-top:50px;'><h1 style='color:#E2001A;'>MERCI !</h1><p>Vote enregistré.</p></div>", unsafe_allow_html=True)
        st.stop()

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
            st.info("📸 Mur Photo")
            cam = st.camera_input("Photo")
            if cam:
                with open(os.path.join(LIVE_DIR, f"live_{uuid.uuid4().hex}.jpg"), "wb") as f: f.write(cam.getbuffer())
                st.success("Envoyé !"); time.sleep(1); st.rerun()
        elif cfg["mode_affichage"] == "votes" and cfg["session_ouverte"]:
            st.write(f"Bonjour **{st.session_state.user_pseudo}**")
            choix = st.multiselect("3 Choix :", cfg["candidats"], max_selections=3)
            if len(choix) == 3:
                if st.button("VALIDER (DÉFINITIF)", type="primary", use_container_width=True):
                    voters = load_json(VOTERS_FILE, [])
                    if st.session_state.user_pseudo.upper() in [v.upper() for v in voters]: st.error("Déjà voté !")
                    else:
                        vts = load_json(VOTES_FILE, {})
                        pts = cfg.get("points_ponderation", [5, 3, 1])
                        for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                        save_json(VOTES_FILE, vts)
                        voters.append(st.session_state.user_pseudo); save_json(VOTERS_FILE, voters)
                        st.session_state.vote_just_done = True
                        components.html("""<script>localStorage.setItem('VOTE_DONE', 'true'); window.parent.location.href += '&blocked=true';</script>""", height=0)
                        st.rerun()
        else: st.info("⏳ Attente...")

# =========================================================
# 3. MUR SOCIAL (DESIGN DEMANDÉ)
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2000, key="wall_refresh")
    cfg = load_json(CONFIG_FILE, default_config)
    
    st.markdown("""
    <style>
        body, .stApp { background-color: black !important; font-family: 'Arial', sans-serif; overflow: hidden; }
        [data-testid='stHeader'] { display: none; }
        
        .social-header { position: fixed; top: 0; left: 0; width: 100%; height: 12vh; background: #E2001A; display: flex; align-items: center; justify-content: center; z-index: 100; border-bottom: 5px solid white; }
        .social-title { color: white; font-size: 40px; font-weight: bold; margin: 0; text-transform: uppercase; }
        
        /* GAUCHE : VOTANTS */
        .voters-column { position: fixed; top: 15vh; left: 20px; width: 220px; bottom: 20px; display: flex; flex-direction: column; justify-content: flex-start; overflow: hidden; }
        .user-tag { background: rgba(255,255,255,0.15); color: #EEE; border-radius: 10px; padding: 8px; margin-bottom: 5px; font-size: 16px; border-left: 4px solid #E2001A; text-align: center; }
        
        /* DROITE : LISTES */
        .list-container { position: absolute; top: 15vh; left: 260px; right: 20px; display: flex; justify-content: center; align-items: flex-start; gap: 30px; }
        .col-list { width: 35%; display: flex; flex-direction: column; }
        .cand-row { display: flex; align-items: center; margin-bottom: 10px; background: rgba(255,255,255,0.08); padding: 5px 15px; border-radius: 50px; width: 100%; height: 60px; }
        .cand-img { width: 50px; height: 50px; border-radius: 50%; object-fit: cover; border: 2px solid #E2001A; }
        .cand-name { color: white; font-size: 20px; font-weight: 600; margin: 0 15px; white-space: nowrap; }
        .row-left { flex-direction: row; justify-content: flex-end; text-align: right; }
        .row-right { flex-direction: row; justify-content: flex-start; text-align: left; }
        
        .qr-center { display:flex; flex-direction:column; align-items:center; justify-content:center; margin-top: 20px; }
        .qr-logo { width: 200px; margin-bottom: 20px; object-fit: contain; }
        
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
        tags = "".join([f"<div class='user-tag'>{p}</div>" for p in reversed(parts[-15:])])
        st.markdown(f'<div class="voters-column">{tags}</div>', unsafe_allow_html=True)

    if mode == "attente":
        st.markdown("<div style='position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); text-align:center;'><h1 style='color:white; font-size:100px;'>BIENVENUE</h1><h2 style='color:#AAA; font-size:40px;'>Veuillez patienter...</h2></div>", unsafe_allow_html=True)

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
                    if name in cfg.get("candidats_images", {}): img = f'<img src="data:image/png;base64,{cfg["candidats_images"][name]}" style="width:100px; height:100px; border-radius:50%; object-fit:cover; margin-bottom:20px;">'
                    suspense_html += f'<div class="suspense-card">{img}<h2 style="color:white">{name}</h2></div>'
                st.markdown(f'<div class="suspense-container">{suspense_html}</div>', unsafe_allow_html=True)
                st.markdown("<h1 style='position:fixed; bottom:10%; width:100%; text-align:center; color:#E2001A; font-size:50px;'>LE VAINQUEUR EST...</h1>", unsafe_allow_html=True)
                time.sleep(1); st.rerun()
            else:
                if sorted_v:
                    winner, pts = sorted_v[0]
                    img = ""
                    if winner in cfg.get("candidats_images", {}): img = f'<img src="data:image/png;base64,{cfg["candidats_images"][winner]}" style="width:150px; height:150px; border-radius:50%; border:5px solid white; object-fit:cover; margin-bottom:20px;">'
                    st.markdown(f"""<div class="winner-card"><div style="font-size:80px;">🏆</div>{img}<h1 style="color:white; font-size:50px; margin:10px 0;">{winner}</h1><h2 style="color:#FFD700; font-size:30px;">VAINQUEUR</h2><h3 style="color:#CCC;">{pts} points</h3></div>""", unsafe_allow_html=True)
                    inject_visual_effect("🎉 Confettis", 50, 20)

        elif cfg.get("session_ouverte"):
            cands = cfg.get("candidats", [])
            imgs = cfg.get("candidats_images", {})
            mid = (len(cands) + 1) // 2
            left_list, right_list = cands[:mid], cands[mid:]
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
            logo_qr = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" class="qr-logo">' if cfg.get("logo_b64") else ""

            st.markdown(f"""<div class="list-container"><div class="col-list">{html_left}</div><div class="qr-center">{logo_qr}<div style="background:white; padding:10px; border-radius:15px; border:5px solid #E2001A;"><img src="data:image/png;base64,{qr_b64}" width="200"></div><h2 style="color:white; margin-top:10px; font-size:24px;">SCANNEZ !</h2></div><div class="col-list">{html_right}</div></div>""", unsafe_allow_html=True)
        else:
            st.markdown("<div style='position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); text-align:center; border: 5px solid #E2001A; padding: 50px; border-radius: 30px; background: rgba(0,0,0,0.8);'><h1 style='color:#E2001A; font-size:60px;'>VOTES CLÔTURÉS</h1></div>", unsafe_allow_html=True)

    elif mode == "photos_live":
        photos = glob.glob(f"{LIVE_DIR}/*")
        if photos:
            img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-30:]])
            components.html(f"""<script>
                var doc = window.parent.document;
                var container = doc.getElementById('bubble-wall') || doc.createElement('div');
                container.id = 'bubble-wall'; container.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:1;pointer-events:none;';
                if(!doc.getElementById('bubble-wall')) doc.body.appendChild(container);
                const imgs = {img_js}; const bubbles = []; const bSize = 200;
                imgs.forEach((src, i) => {{
                    if(doc.getElementById('bub-'+i)) return;
                    const el = doc.createElement('img'); el.id = 'bub-'+i; el.src = src;
                    el.style.cssText = 'position:absolute; width:'+bSize+'px; height:'+bSize+'px; border-radius:50%; border:6px solid #E2001A; object-fit:cover;';
                    let x = Math.random() * (window.innerWidth - bSize); let y = Math.random() * (window.innerHeight - bSize);
                    let vx = (Math.random()-0.5)*5; let vy = (Math.random()-0.5)*5;
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
