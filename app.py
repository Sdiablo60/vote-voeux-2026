import streamlit as st
import os, glob, base64, qrcode, json, time, uuid, textwrap, zipfile, shutil
from io import BytesIO
import streamlit.components.v1 as components
from PIL import Image
from datetime import datetime
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Régie Master", layout="wide", initial_sidebar_state="collapsed")

# Dossiers & Fichiers
LIVE_DIR = "galerie_live_users"
VOTES_FILE = "votes.json"
CONFIG_FILE = "config_mur.json"
VOTERS_FILE = "voters.json" # Liste des prénoms
PARTICIPANTS_FILE = "participants.json" # Liste pour l'affichage (tags)

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
    "effect_speed": 15, # Ralenti par défaut
    "screen_effects": {"attente": "Aucun", "votes_open": "Aucun", "votes_closed": "Aucun", "podium": "🎉 Confettis", "photos_live": "Aucun"},
    "session_id": str(uuid.uuid4()) # Identifiant unique de l'élection (change au Reset)
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
    if effect_name == "Aucun":
        components.html("<script>var old = window.parent.document.getElementById('effect-layer'); if(old) old.remove();</script>", height=0)
        return

    # Ajustement vitesse (plus la valeur speed est basse, plus c'est lent ?) 
    # Ici on inverse : Speed haut = Rapide. Speed bas = Lent.
    # On ralentit globalement l'animation
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

# --- INIT SESSION ---
if "config" not in st.session_state: st.session_state.config = load_json(CONFIG_FILE, default_config)

# --- NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
is_blocked = st.query_params.get("blocked") == "true"

# =========================================================
# 1. CONSOLE ADMIN (BOUTONS ACTIFS & IMAGES)
# =========================================================
if est_admin:
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
    <div class="fixed-header"><div class="header-title">CONSOLE RÉGIE</div><div class="header-logo"></div></div>
    """, unsafe_allow_html=True)
    
    if "auth" not in st.session_state: st.session_state["auth"] = False
    if not st.session_state["auth"]:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.text_input("Code Admin", type="password") == "ADMIN_LIVE_MASTER":
                st.session_state["auth"] = True; st.rerun()
    else:
        with st.sidebar:
            st.title("🎛️ PILOTAGE")
            menu = st.radio("Menu", ["🔴 PILOTAGE LIVE", "⚙️ Paramétrage", "📸 Médiathèque"])
            if st.button("🔓 Déconnexion"): st.session_state["auth"] = False; st.rerun()

        cfg = st.session_state.config

        if menu == "🔴 PILOTAGE LIVE":
            st.subheader("Séquenceur")
            
            # --- DETERMINER LE BOUTON ACTIF (Visuel) ---
            mode = cfg["mode_affichage"]
            open = cfg["session_ouverte"]
            reveal = cfg["reveal_resultats"]
            
            type_accueil = "primary" if mode == "attente" else "secondary"
            type_on = "primary" if (mode == "votes" and open) else "secondary"
            type_off = "primary" if (mode == "votes" and not open and not reveal) else "secondary"
            type_podium = "primary" if reveal else "secondary"
            type_photo = "primary" if mode == "photos_live" else "secondary"

            c1, c2, c3, c4 = st.columns(4)
            if c1.button("1. ACCUEIL", type=type_accueil, use_container_width=True):
                cfg.update({"mode_affichage": "attente", "session_ouverte": False, "reveal_resultats": False})
                save_config(); st.rerun()
                
            if c2.button("2. VOTES ON", type=type_on, use_container_width=True):
                cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False})
                save_config(); st.rerun()
                
            if c3.button("3. VOTES OFF", type=type_off, use_container_width=True):
                cfg.update({"mode_affichage": "votes", "session_ouverte": False, "reveal_resultats": False})
                save_config(); st.rerun()
                
            if c4.button("4. PODIUM", type=type_podium, use_container_width=True):
                cfg.update({"mode_affichage": "votes", "reveal_resultats": True, "session_ouverte": False})
                cfg["timestamp_podium"] = time.time() # Reset chrono suspense
                save_config(); st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("5. 📸 MUR PHOTOS LIVE", type=type_photo, use_container_width=True):
                cfg.update({"mode_affichage": "photos_live", "session_ouverte": False, "reveal_resultats": False})
                save_config(); st.rerun()

            st.divider()
            with st.expander("🚨 ZONE DE DANGER (Reset)"):
                st.warning("Ceci effacera tous les votes et permettra aux téléphones de revoter.")
                if st.button("🗑️ RESET TOTAL & DÉBLOQUER TÉLÉPHONES", type="primary"):
                    for f in [VOTES_FILE, VOTERS_FILE, PARTICIPANTS_FILE]:
                        if os.path.exists(f): os.remove(f)
                    
                    # CHANGEMENT DE SESSION ID POUR DEBLOQUER LES TELEPHONES
                    cfg["session_id"] = str(uuid.uuid4())
                    save_config()
                    
                    st.success("Système réinitialisé !"); time.sleep(1); st.rerun()

        elif menu == "⚙️ Paramétrage":
            st.subheader("Candidats & Images")
            
            # Affichage de la liste avec Images
            for i, c in enumerate(cfg["candidats"]):
                col_img, col_info = st.columns([1, 4])
                with col_img:
                    # AFFICHAGE DE L'IMAGE
                    if c in cfg.get("candidats_images", {}):
                        st.image(BytesIO(base64.b64decode(cfg["candidats_images"][c])), width=80)
                    else:
                        st.markdown("🚫 *Pas d'image*")
                
                with col_info:
                    st.write(f"**{c}**")
                    up = st.file_uploader(f"Modifier image pour {c}", key=f"u_{i}", label_visibility="collapsed")
                    if up:
                        cfg.setdefault("candidats_images", {})[c] = process_image(up)
                        save_config(); st.rerun()
                st.divider()

        elif menu == "📸 Médiathèque":
            st.subheader("Photos Live")
            files = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
            if st.button("🗑️ TOUT VIDER"):
                for f in files: os.remove(f)
                st.rerun()
            cols = st.columns(4)
            for i, f in enumerate(files):
                with cols[i%4]:
                    st.image(f)

# =========================================================
# 2. APPLICATION MOBILE (FIX BLOCAGE & SESSION ID)
# =========================================================
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, default_config)
    st.markdown("<style>.stApp {background-color:black; color:white;} [data-testid='stHeader'] {display:none;}</style>", unsafe_allow_html=True)
    
    # SYSTEME DE VERROUILLAGE INTELLIGENT
    # On stocke l'ID de session. Si l'ID change (Reset Admin), on autorise à nouveau.
    current_session = cfg.get("session_id", "init")
    
    components.html(f"""<script>
        const serverSession = "{current_session}";
        const localSession = localStorage.getItem('VOTE_SESSION_ID');
        
        // Si la session a changé (Reset Admin), on nettoie le blocage
        if (localSession !== serverSession) {{
            localStorage.removeItem('VOTE_BLOCKED');
            localStorage.setItem('VOTE_SESSION_ID', serverSession);
            // On recharge pour appliquer le déblocage si on était bloqué
            if(window.parent.location.href.includes('blocked=true')) {{
                 window.parent.location.href = window.parent.location.href.replace('&blocked=true', '');
            }}
        }} else {{
            // Si même session et marqué bloqué, on redirige
            if(localStorage.getItem('VOTE_BLOCKED')) {{
                if(!window.parent.location.href.includes('blocked=true')) {{
                    window.parent.location.href = window.parent.location.href + '&blocked=true';
                }}
            }}
        }}
    </script>""", height=0)

    if is_blocked:
        st.balloons()
        st.markdown("<div style='text-align:center; margin-top:100px;'><h1>✅ VOTE ENREGISTRÉ</h1><p>Merci pour votre participation.</p></div>", unsafe_allow_html=True)
        st.stop()

    if "user_pseudo" not in st.session_state:
        st.subheader("Identification")
        if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), width=100)
        pseudo = st.text_input("Votre Prénom :")
        if st.button("ENTRER", type="primary", use_container_width=True) and pseudo:
            # Vérification serveur stricte en plus du localStorage
            voters = load_json(VOTERS_FILE, [])
            if pseudo.strip().upper() in [v.upper() for v in voters]:
                st.error("⛔ Ce prénom a déjà voté pour cette session.")
            else:
                st.session_state.user_pseudo = pseudo.strip()
                # On l'ajoute à la liste des participants pour l'affichage (Tag)
                parts = load_json(PARTICIPANTS_FILE, [])
                if pseudo.strip() not in parts:
                    parts.append(pseudo.strip())
                    save_json(PARTICIPANTS_FILE, parts)
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
                    # Double check
                    voters = load_json(VOTERS_FILE, [])
                    if st.session_state.user_pseudo.upper() in [v.upper() for v in voters]:
                        st.error("Déjà voté !"); time.sleep(2); st.rerun()

                    vts = load_json(VOTES_FILE, {})
                    pts = cfg.get("points_ponderation", [5, 3, 1])
                    for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                    save_json(VOTES_FILE, vts)
                    
                    voters.append(st.session_state.user_pseudo)
                    save_json(VOTERS_FILE, voters)
                    
                    # Marquage LocalStorage liée à la session
                    components.html(f"""<script>
                        localStorage.setItem('VOTE_BLOCKED', 'true');
                        localStorage.setItem('VOTE_SESSION_ID', '{cfg.get("session_id")}');
                        window.parent.location.href = window.parent.location.href + '&blocked=true';
                    </script>""", height=0)
        else:
            st.info("⏳ Les votes sont actuellement fermés.")
            st.markdown("Attendez l'ouverture de la session par la régie.")

# =========================================================
# 3. MUR SOCIAL (CORRECTIONS VISUELLES & LOGIQUES)
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2000, key="wall_refresh")
    cfg = load_json(CONFIG_FILE, default_config)
    
    st.markdown(f"""
    <style>
        body, .stApp {{ background-color: black !important; overflow: hidden; font-family: 'Arial', sans-serif; }} 
        [data-testid='stHeader'] {{ display: none; }}
        
        /* HEADER */
        .social-header {{ position: fixed; top: 0; left: 0; width: 100%; height: 12vh; background: #E2001A; display: flex; align-items: center; justify-content: center; z-index: 5000; border-bottom: 5px solid white; }}
        .social-title {{ color: white; font-size: 45px; font-weight: bold; margin: 0; text-transform: uppercase; }}
        
        /* LISTE DES VOTANTS (TAGS) */
        .tags-marquee {{
            position: absolute; top: 13vh; width: 100%; height: 8vh;
            display: flex; justify-content: center; align-items: center; flex-wrap: wrap; overflow: hidden;
        }}
        .user-tag {{ 
            display: inline-block; background: rgba(255,255,255,0.15); color: #EEE; 
            border-radius: 15px; padding: 2px 10px; margin: 2px; font-size: 14px; border: 1px solid #555;
        }}
        
        /* LISTE CANDIDATS REMONTÉE ET COMPACTÉE */
        .list-container {{ position: absolute; top: 22vh; width: 100%; display: flex; justify-content: center; gap: 20px; }}
        .col-list {{ width: 38%; display: flex; flex-direction: column; }}
        
        .cand-row {{ 
            display: flex; align-items: center; margin-bottom: 8px; /* Espacement réduit */
            background: rgba(255,255,255,0.08); padding: 5px 15px; /* Padding réduit */
            border-radius: 40px; width: 100%; height: 55px; /* Hauteur fixe */
        }}
        .cand-img {{ width: 45px; height: 45px; border-radius: 50%; object-fit: cover; border: 2px solid #E2001A; }}
        .cand-name {{ color: white; font-size: 18px; font-weight: 600; margin: 0 10px; white-space: nowrap; }}
        
        /* MIROIR GAUCHE */
        .row-left {{ flex-direction: row; justify-content: flex-end; text-align: right; }}
        
        /* MIROIR DROITE */
        .row-right {{ flex-direction: row; justify-content: flex-start; text-align: left; }}
        
        /* QR BOX AVEC LOGO */
        .qr-center {{ display:flex; flex-direction:column; align-items:center; justify-content:center; margin-top: 0px; }}
        .qr-logo {{ width: 80px; margin-bottom: 10px; }}
        
        /* PODIUM CENTRÉ */
        .winner-card {{ 
            position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); 
            width: 500px; background: rgba(15,15,15,0.98); border: 10px solid #FFD700; 
            border-radius: 50px; padding: 40px; text-align: center; z-index: 1000;
            box-shadow: 0 0 80px #FFD700;
        }}
        
        /* SUSPENSE CARDS */
        .suspense-container {{ 
            position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
            display: flex; gap: 30px; z-index: 1000;
        }}
        .suspense-card {{
            width: 250px; height: 300px; background: rgba(255,255,255,0.05); border: 2px solid #555;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            border-radius: 20px; animation: pulse 1s infinite;
        }}
        @keyframes pulse {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.02); }} 100% {{ transform: scale(1); }} }}
        
    </style>
    <div class="social-header"><h1 class="social-title">{cfg['titre_mur']}</h1></div>
    """, unsafe_allow_html=True)

    mode = cfg.get("mode_affichage")
    
    # Barre des votants (Tags) visible si Votes ON ou OFF
    if mode == "votes":
        parts = load_json(PARTICIPANTS_FILE, [])
        # On affiche les 70 derniers pour remplir l'espace
        tags_html = "".join([f"<span class='user-tag'>{p}</span>" for p in parts[-80:]])
        st.markdown(f'<div class="tags-marquee">{tags_html}</div>', unsafe_allow_html=True)

    # GESTION EFFETS
    key_eff = "attente"
    if mode == "photos_live": key_eff = "photos_live"
    elif cfg.get("reveal_resultats"): key_eff = "podium"
    elif mode == "votes": key_eff = "votes_open" if cfg.get("session_ouverte") else "votes_closed"
    inject_visual_effect(cfg["screen_effects"].get(key_eff, "Aucun"), cfg.get("effect_intensity", 25), cfg.get("effect_speed", 15))

    if mode == "attente":
        st.markdown("""
        <div style='position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); text-align:center;'>
            <h1 style='color:white; font-size:100px; margin:0;'>BIENVENUE</h1>
            <h2 style='color:#AAA; font-size:40px; margin-top:20px;'>L'événement va commencer dans quelques instants...</h2>
        </div>
        """, unsafe_allow_html=True)

    elif mode == "votes":
        # 1. PODIUM (RESULTATS)
        if cfg.get("reveal_resultats"):
            v_data = load_json(VOTES_FILE, {})
            # Tri des scores
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)
            
            # Temps écoulé depuis le clic "Podium"
            elapsed = time.time() - cfg.get("timestamp_podium", 0)
            
            if elapsed < 6.0:
                # PHASE 1 : SUSPENSE (Affiche les 3 premiers sans dire qui a gagné)
                top3 = sorted_v[:3]
                suspense_html = ""
                for name, score in top3:
                    img = ""
                    if name in cfg.get("candidats_images", {}):
                         img = f'<img src="data:image/png;base64,{cfg["candidats_images"][name]}" style="width:100px; height:100px; border-radius:50%; object-fit:cover; margin-bottom:20px;">'
                    suspense_html += f'<div class="suspense-card">{img}<h2 style="color:white">{name}</h2></div>'
                
                st.markdown(f'<div class="suspense-container">{suspense_html}</div>', unsafe_allow_html=True)
                st.markdown("<h1 style='position:fixed; bottom:10%; width:100%; text-align:center; color:#E2001A; font-size:50px;'>LE VAINQUEUR EST...</h1>", unsafe_allow_html=True)
                time.sleep(1); st.rerun()
            
            else:
                # PHASE 2 : VAINQUEUR
                if sorted_v:
                    winner, pts = sorted_v[0]
                    img_html = ""
                    if winner in cfg.get("candidats_images", {}):
                        img_html = f'<img src="data:image/png;base64,{cfg["candidats_images"][winner]}" style="width:150px; height:150px; border-radius:50%; border:5px solid white; object-fit:cover; margin-bottom:20px;">'
                    
                    st.markdown(f"""
                    <div class="winner-card">
                        <div style="font-size:80px;">🏆</div>
                        {img_html}
                        <h1 style="color:white; font-size:50px; margin:10px 0;">{winner}</h1>
                        <h2 style="color:#FFD700; font-size:30px;">VAINQUEUR</h2>
                        <h3 style="color:#CCC; margin-top:10px;">Avec {pts} points</h3>
                    </div>""", unsafe_allow_html=True)

        # 2. SESSION OUVERTE (LISTES CANDIDATS)
        elif cfg.get("session_ouverte"):
            cands = cfg.get("candidats", [])
            imgs = cfg.get("candidats_images", {})
            mid = (len(cands) + 1) // 2
            left_list = cands[:mid]
            right_list = cands[mid:]
            
            # GAUCHE : [Photo] [Texte] (CSS row-left pousse à droite)
            html_left = ""
            for c in left_list:
                img_src = f"data:image/png;base64,{imgs[c]}" if c in imgs else "https://via.placeholder.com/60/333/FFF?text=?"
                html_left += f"""<div class="cand-row row-left"><img src="{img_src}" class="cand-img"><span class="cand-name">{c}</span></div>"""

            # DROITE : [Photo] [Texte] (CSS row-right pousse à gauche)
            html_right = ""
            for c in right_list:
                img_src = f"data:image/png;base64,{imgs[c]}" if c in imgs else "https://via.placeholder.com/60/333/FFF?text=?"
                html_right += f"""<div class="cand-row row-right"><img src="{img_src}" class="cand-img"><span class="cand-name">{c}</span></div>"""
            
            # LOGO + QR
            host = st.context.headers.get('host', 'localhost')
            qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            
            logo_qr = ""
            if cfg.get("logo_b64"):
                logo_qr = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" class="qr-logo">'

            st.markdown(f"""
            <div class="list-container">
                <div class="col-list">{html_left}</div>
                <div class="qr-center">
                    {logo_qr}
                    <div style="background:white; padding:10px; border-radius:15px; border:5px solid #E2001A;">
                        <img src="data:image/png;base64,{qr_b64}" width="200">
                    </div>
                    <h2 style="color:white; margin-top:10px; font-size:24px;">SCANNEZ !</h2>
                </div>
                <div class="col-list">{html_right}</div>
            </div>
            """, unsafe_allow_html=True)
            
        # 3. SESSION FERMEE (VOTE OFF)
        else:
            st.markdown("""
            <div style='position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); text-align:center; border: 5px solid #E2001A; padding: 50px; border-radius: 30px; background: rgba(0,0,0,0.8);'>
                <h1 style='color:#E2001A; font-size:60px; margin:0;'>VOTES CLÔTURÉS</h1>
                <h2 style='color:white; font-size:30px; margin-top:20px;'>Merci de votre participation</h2>
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
