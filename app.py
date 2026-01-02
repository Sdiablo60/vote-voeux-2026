import streamlit as st
import os, glob, base64, qrcode, json, time, uuid, textwrap, zipfile, shutil
from io import BytesIO
import streamlit.components.v1 as components
from PIL import Image
from datetime import datetime
import pandas as pd

# --- GESTION DES LIBRAIRIES OPTIONNELLES ---
try:
    import altair as alt
    HAS_ALTAIR = True
except ImportError:
    HAS_ALTAIR = False

# --- CONFIGURATION ---
st.set_page_config(page_title="Régie Master", layout="wide", initial_sidebar_state="collapsed")

# Dossiers & Fichiers
LIVE_DIR = "galerie_live_users"
VOTES_FILE = "votes.json"
CONFIG_FILE = "config_mur.json"
VOTERS_FILE = "voters.json"
PARTICIPANTS_FILE = "participants.json"
DETAILED_VOTES_FILE = "detailed_votes.json"

for d in [LIVE_DIR]:
    if not os.path.exists(d): os.makedirs(d)

# --- CONFIG PAR DÉFAUT (Riche) ---
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
    "effect_speed": 25,      
    "screen_effects": {"attente": "Aucun", "votes_open": "Aucun", "votes_closed": "Aucun", "podium": "🎉 Confettis", "photos_live": "Aucun"}
}

# --- FONCTIONS UTILITAIRES ---
def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding='utf-8') as f: return json.load(f)
        except: return default
    return default

def save_json(file, data):
    with open(file, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

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
    """Gestionnaire d'effets visuels (Confettis, Neige, Ballons)"""
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

# --- INIT SESSION ---
if "config" not in st.session_state: st.session_state.config = load_json(CONFIG_FILE, default_config)
if "cam_reset_id" not in st.session_state: st.session_state.cam_reset_id = 0

# --- NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
is_blocked = st.query_params.get("blocked") == "true"

# =========================================================
# 1. CONSOLE ADMIN (AVEC FONCTIONS RESTAURÉES & ANTI-CLIGNOTEMENT)
# =========================================================
if est_admin:
    # CSS OPTIMISÉ POUR HEADER FIXE SANS CLIGNOTEMENT
    logo_css = ""
    if st.session_state.config.get("logo_b64"):
        logo_css = f"background-image: url('data:image/png;base64,{st.session_state.config['logo_b64']}');"

    st.markdown(f"""
    <style>
        .main .block-container {{ margin-top: 60px !important; padding-top: 20px !important; }}
        .fixed-header {{
            position: fixed; top: 0; left: 0; width: 100%; height: 70px;
            background-color: #1E1E1E; z-index: 100000;
            display: flex; align-items: center; justify-content: center;
            border-bottom: 3px solid #E2001A; transition: none !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }}
        .header-title {{ color: white; font-size: 24px; font-weight: 800; text-transform: uppercase; font-family: sans-serif; }}
        .header-logo {{
            position: absolute; right: 30px; top: 5px; height: 60px; width: 100px;
            background-size: contain; background-repeat: no-repeat; background-position: center; {logo_css}
        }}
        header[data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    <div class="fixed-header">
        <div class="header-title">CONSOLE RÉGIE</div>
        <div class="header-logo"></div>
    </div>
    """, unsafe_allow_html=True)
    
    if "auth" not in st.session_state: st.session_state["auth"] = False
    if not st.session_state["auth"]:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.text_input("Code Admin", type="password") == "ADMIN_LIVE_MASTER":
                st.session_state["auth"] = True; st.rerun()
    else:
        # MENU RESTAURÉ COMME AVANT
        with st.sidebar:
            st.title("🎛️ PILOTAGE")
            st.markdown("""<a href="/" target="_blank"><div style="background-color: #E2001A; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 10px;">📺 MUR SOCIAL</div></a>""", unsafe_allow_html=True)
            st.markdown("""<a href="/?mode=vote" target="_blank"><div style="background-color: #333; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 20px;">📱 VUE MOBILE</div></a>""", unsafe_allow_html=True)
            menu = st.radio("Menu", ["🔴 PILOTAGE LIVE", "⚙️ Paramétrage", "📸 Médiathèque", "📊 Data"])
            if st.button("🔓 Déconnexion"): st.session_state["auth"] = False; st.rerun()

        cfg = st.session_state.config

        # --- ONGLET 1 : PILOTAGE LIVE (Boutons Restaurés) ---
        if menu == "🔴 PILOTAGE LIVE":
            st.subheader("Séquenceur")
            c1, c2, c3, c4 = st.columns(4)
            m, vo, re = cfg["mode_affichage"], cfg["session_ouverte"], cfg["reveal_resultats"]

            # Boutons logiques
            if c1.button("1. ACCUEIL", type="primary" if m=="attente" else "secondary", use_container_width=True):
                cfg.update({"mode_affichage": "attente", "session_ouverte": False, "reveal_resultats": False})
                save_config(); st.rerun()
                
            if c2.button("2. VOTES ON", type="primary" if (m=="votes" and vo) else "secondary", use_container_width=True):
                cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False})
                save_config(); st.rerun()
                
            if c3.button("3. VOTES OFF", type="primary" if (m=="votes" and not vo and not re) else "secondary", use_container_width=True):
                cfg["session_ouverte"] = False
                save_config(); st.rerun()
                
            if c4.button("4. PODIUM", type="primary" if re else "secondary", use_container_width=True):
                cfg.update({"mode_affichage": "votes", "reveal_resultats": True, "session_ouverte": False})
                cfg["timestamp_podium"] = time.time()
                save_config(); st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("5. 📸 MUR PHOTOS LIVE", type="primary" if m=="photos_live" else "secondary", use_container_width=True):
                cfg.update({"mode_affichage": "photos_live", "session_ouverte": False, "reveal_resultats": False})
                save_config(); st.rerun()

            st.divider()
            st.subheader("📡 Contrôle des Effets")
            ce1, ce2 = st.columns(2)
            with ce1:
                intensity = st.slider("Densité", 0, 50, cfg.get("effect_intensity", 25))
                speed = st.slider("Vitesse", 0, 50, cfg.get("effect_speed", 25))
                if intensity != cfg.get("effect_intensity") or speed != cfg.get("effect_speed"):
                    cfg["effect_intensity"] = intensity; cfg["effect_speed"] = speed; save_config()
            
            with ce2:
                EFFS = ["Aucun", "🎈 Ballons", "❄️ Neige", "🎉 Confettis"]
                cfg["screen_effects"]["attente"] = st.selectbox("Effet Accueil", EFFS, index=EFFS.index(cfg["screen_effects"].get("attente","Aucun")))
                cfg["screen_effects"]["podium"] = st.selectbox("Effet Podium", EFFS, index=EFFS.index(cfg["screen_effects"].get("podium","🎉 Confettis")))
                if st.button("Sauver Effets"): save_config(); st.toast("Effets mis à jour")

            st.divider()
            with st.expander("🚨 ZONE DE DANGER"):
                if st.button("🗑️ RESET TOTAL (Votes + Photos + Votants)", type="primary"):
                    for f in [VOTES_FILE, VOTERS_FILE, PARTICIPANTS_FILE, DETAILED_VOTES_FILE]:
                        if os.path.exists(f): os.remove(f)
                    files = glob.glob(f"{LIVE_DIR}/*"); 
                    for f in files: os.remove(f)
                    st.success("Tout a été effacé !"); time.sleep(1); st.rerun()

        # --- ONGLET 2 : PARAMÉTRAGE ---
        elif menu == "⚙️ Paramétrage":
            t1, t2 = st.tabs(["Général", "Candidats & Images"])
            with t1:
                new_t = st.text_input("Titre", value=cfg["titre_mur"])
                if st.button("Sauver Titre"): cfg["titre_mur"] = new_t; save_config(); st.rerun()
                up_logo = st.file_uploader("Logo", type=["png", "jpg"])
                if up_logo: cfg["logo_b64"] = process_image(up_logo); save_config(); st.rerun()
            with t2:
                # Gestion simple des candidats
                for c in cfg["candidats"]:
                    c1, c2 = st.columns([3, 1])
                    with c1: st.write(f"**{c}**")
                    with c2:
                        up = st.file_uploader(f"Img {c}", key=f"u_{c}", label_visibility="collapsed")
                        if up:
                            cfg.setdefault("candidats_images", {})[c] = process_image(up)
                            save_config(); st.rerun()

        # --- ONGLET 3 : MÉDIATHÈQUE ---
        elif menu == "📸 Médiathèque":
            files = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
            if st.button("🗑️ TOUT VIDER"):
                for f in files: os.remove(f)
                st.rerun()
            
            cols = st.columns(4)
            for i, f in enumerate(files):
                with cols[i%4]:
                    st.image(f)
                    if st.button("Sup", key=f"d_{i}"): os.remove(f); st.rerun()

        # --- ONGLET 4 : DATA (RESTAURÉ) ---
        elif menu == "📊 Data":
            st.title("Données")
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                df = pd.DataFrame(list(v_data.items()), columns=['Candidat', 'Points']).sort_values('Points', ascending=False)
                st.dataframe(df, use_container_width=True)
                
                if HAS_ALTAIR:
                    chart = alt.Chart(df).mark_bar().encode(x='Points', y=alt.Y('Candidat', sort='-x'), color='Points')
                    st.altair_chart(chart, use_container_width=True)
            else:
                st.info("Pas encore de votes.")

# =========================================================
# 2. APPLICATION MOBILE (SÉCURITÉ RENFORCÉE)
# =========================================================
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, default_config)
    st.markdown("<style>.stApp {background-color:black; color:white;} [data-testid='stHeader'] {display:none;}</style>", unsafe_allow_html=True)
    
    # Check Sécurité Navigateur
    components.html("""<script>
        if(localStorage.getItem('VOTE_DONE_SECURE_V12')) {
            if(!window.parent.location.href.includes('blocked=true')) {
                window.parent.location.href = window.parent.location.href + '&blocked=true';
            }
        }
    </script>""", height=0)

    if is_blocked:
        st.balloons()
        st.markdown("<div style='text-align:center; margin-top:100px;'><h1>✅ VOTE VALIDÉ</h1><p>Merci !</p></div>", unsafe_allow_html=True)
        st.stop()

    if "user_pseudo" not in st.session_state:
        st.subheader("Identification")
        if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), width=100)
        pseudo = st.text_input("Votre Prénom :")
        if st.button("ENTRER", type="primary", use_container_width=True) and pseudo:
            voters = load_json(VOTERS_FILE, [])
            if pseudo.strip().upper() in [v.upper() for v in voters]:
                st.error("⛔ Ce prénom a déjà voté.")
            else:
                st.session_state.user_pseudo = pseudo.strip()
                st.rerun()
    else:
        if cfg["mode_affichage"] == "photos_live":
            st.info("📸 Mur Photo Ouvert")
            cam = st.camera_input("Photo")
            if cam:
                with open(os.path.join(LIVE_DIR, f"live_{uuid.uuid4().hex}.jpg"), "wb") as f: f.write(cam.getbuffer())
                st.success("Envoyé !"); time.sleep(1); st.rerun()
        
        elif cfg["mode_affichage"] == "votes" and cfg["session_ouverte"]:
            st.write(f"Bonjour **{st.session_state.user_pseudo}**")
            st.write("Sélectionnez vos 3 favoris :")
            choix = st.multiselect("Choix", cfg["candidats"], max_selections=3, label_visibility="collapsed")
            
            if len(choix) == 3:
                st.markdown("---")
                if st.button("🚀 VALIDER (DÉFINITIF)", type="primary", use_container_width=True):
                    # Vérif Serveur
                    voters = load_json(VOTERS_FILE, [])
                    if st.session_state.user_pseudo.upper() in [v.upper() for v in voters]:
                        st.error("Déjà voté !"); time.sleep(2); st.rerun()

                    # Enregistrement
                    vts = load_json(VOTES_FILE, {})
                    pts = cfg.get("points_ponderation", [5, 3, 1])
                    for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                    save_json(VOTES_FILE, vts)
                    
                    voters.append(st.session_state.user_pseudo)
                    save_json(VOTERS_FILE, voters)
                    
                    # Verrouillage Local
                    components.html("""<script>
                        localStorage.setItem('VOTE_DONE_SECURE_V12', 'true');
                        window.parent.location.href = window.parent.location.href + '&blocked=true';
                    </script>""", height=0)
        else:
            st.info("⏳ En attente de l'ouverture...")

# =========================================================
# 3. MUR SOCIAL (DESIGN MIROIR & PODIUM BAS)
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2000, key="wall_refresh")
    cfg = load_json(CONFIG_FILE, default_config)
    
    # CSS AVANCÉ : DESIGN MIROIR + PODIUM
    st.markdown(f"""
    <style>
        body, .stApp {{ background-color: black !important; overflow: hidden; font-family: 'Montserrat', sans-serif; }} 
        [data-testid='stHeader'] {{ display: none; }}
        
        /* HEADER */
        .social-header {{ position: fixed; top: 0; left: 0; width: 100%; height: 12vh; background: #E2001A; display: flex; align-items: center; justify-content: center; z-index: 5000; border-bottom: 5px solid white; }}
        .social-title {{ color: white; font-size: 45px; font-weight: bold; margin: 0; text-transform: uppercase; }}
        
        /* CANDIDATS ROW */
        .cand-row {{ display: flex; align-items: center; margin-bottom: 20px; background: rgba(255,255,255,0.1); padding: 10px 20px; border-radius: 50px; width: 100%; }}
        .cand-img {{ width: 60px; height: 60px; border-radius: 50%; object-fit: cover; border: 3px solid #E2001A; }}
        .cand-name {{ color: white; font-size: 20px; font-weight: 600; margin: 0 15px; white-space: nowrap; }}
        
        /* MIROIR GAUCHE : [Photo] [Texte] -> Aligné à Droite */
        .row-left {{ flex-direction: row; justify-content: flex-end; text-align: right; }}
        
        /* MIROIR DROITE : [Photo] [Texte] -> Aligné à Gauche */
        .row-right {{ flex-direction: row; justify-content: flex-start; text-align: left; }}
        
        .list-container {{ position: absolute; top: 18vh; width: 100%; display: flex; justify-content: center; gap: 40px; }}
        .col-list {{ width: 35%; display: flex; flex-direction: column; }}
        
        /* PODIUM BAS & PETIT */
        .winner-card {{ 
            position: fixed; top: 450px; left: 50%; transform: translateX(-50%); 
            width: 350px; background: rgba(15,15,15,0.95); border: 8px solid #FFD700; 
            border-radius: 40px; padding: 30px; text-align: center; z-index: 1000;
            box-shadow: 0 0 60px #FFD700;
        }}
    </style>
    <div class="social-header"><h1 class="social-title">{cfg['titre_mur']}</h1></div>
    """, unsafe_allow_html=True)

    mode = cfg.get("mode_affichage")
    
    # GESTION EFFETS
    key_eff = "attente"
    if mode == "photos_live": key_eff = "photos_live"
    elif cfg.get("reveal_resultats"): key_eff = "podium"
    elif mode == "votes": key_eff = "votes_open" if cfg.get("session_ouverte") else "votes_closed"
    inject_visual_effect(cfg["screen_effects"].get(key_eff, "Aucun"), cfg.get("effect_intensity", 25), cfg.get("effect_speed", 25))

    if mode == "attente":
        st.markdown("<h1 style='text-align:center; color:white; margin-top:40vh; font-size:80px;'>BIENVENUE</h1><h2 style='text-align:center; color:#AAA;'>Veuillez patienter...</h2>", unsafe_allow_html=True)

    elif mode == "votes":
        if cfg.get("reveal_resultats"):
            # PODIUM
            v_data = load_json(VOTES_FILE, {})
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)
            if sorted_v:
                winner, pts = sorted_v[0]
                img_html = ""
                if winner in cfg.get("candidats_images", {}):
                    img_html = f'<img src="data:image/png;base64,{cfg["candidats_images"][winner]}" style="width:120px; height:120px; border-radius:50%; border:3px solid white; object-fit:cover; margin-bottom:10px;">'
                
                st.markdown(f"""
                <div class="winner-card">
                    <div style="font-size:60px;">🏆</div>
                    {img_html}
                    <h1 style="color:white; font-size:40px; margin:10px 0;">{winner}</h1>
                    <h2 style="color:#FFD700; font-size:20px;">VAINQUEUR ({pts} pts)</h2>
                </div>""", unsafe_allow_html=True)
        else:
            # LISTE VOTES (MIROIR)
            cands = cfg.get("candidats", [])
            imgs = cfg.get("candidats_images", {})
            mid = (len(cands) + 1) // 2
            left_list = cands[:mid]
            right_list = cands[mid:]
            
            # GAUCHE : [Photo] [Texte] (CSS row-left les pousse à droite)
            html_left = ""
            for c in left_list:
                img_src = f"data:image/png;base64,{imgs[c]}" if c in imgs else "https://via.placeholder.com/60/333/FFF?text=?"
                html_left += f"""<div class="cand-row row-left"><img src="{img_src}" class="cand-img"><span class="cand-name">{c}</span></div>"""

            # DROITE : [Photo] [Texte] (CSS row-right les pousse à gauche)
            html_right = ""
            for c in right_list:
                img_src = f"data:image/png;base64,{imgs[c]}" if c in imgs else "https://via.placeholder.com/60/333/FFF?text=?"
                html_right += f"""<div class="cand-row row-right"><img src="{img_src}" class="cand-img"><span class="cand-name">{c}</span></div>"""
            
            host = st.context.headers.get('host', 'localhost')
            qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

            st.markdown(f"""
            <div class="list-container">
                <div class="col-list">{html_left}</div>
                <div style="display:flex; flex-direction:column; align-items:center; justify-content:center;">
                    <div style="background:white; padding:15px; border-radius:20px; border:5px solid #E2001A;">
                        <img src="data:image/png;base64,{qr_b64}" width="220">
                    </div>
                    <h2 style="color:white; margin-top:20px;">VOTEZ !</h2>
                </div>
                <div class="col-list">{html_right}</div>
            </div>
            """, unsafe_allow_html=True)

    elif mode == "photos_live":
        # MUR PHOTOS
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
