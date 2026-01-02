import streamlit as st
import os, glob, base64, qrcode, json, random, pandas as pd
from io import BytesIO
import streamlit.components.v1 as components
import time
from PIL import Image
from datetime import datetime
import uuid
import textwrap

# --- 1. CONFIGURATION ---
# Utilisation d'un ID de session unique pour forcer le rafraîchissement du cache navigateur
if "session_ui_id" not in st.session_state:
    st.session_state.session_ui_id = str(uuid.uuid4())[:8]

st.set_page_config(page_title="Régie Master", layout="wide", initial_sidebar_state="collapsed")

GALLERY_DIR, LIVE_DIR = "galerie_images", "galerie_live_users"
VOTES_FILE, CONFIG_FILE, VOTERS_FILE = "votes.json", "config_mur.json", "voters.json"

for d in [GALLERY_DIR, LIVE_DIR]:
    if not os.path.exists(d): os.makedirs(d)

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
        "logo_b64": None,
        "candidats": ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI", "FINANCES", "AO", "QSSE", "DIRECTION"],
        "screen_effects": {"attente": "Aucun", "podium": "🎉 Confettis"}
    })

# --- NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
is_blocked = st.query_params.get("blocked") == "true"

# =========================================================
# 1. CONSOLE ADMIN
# =========================================================
if est_admin:
    st.markdown(f"""
    <style>
        .fixed-header {{ position: fixed; top: 0; left: 0; width: 100%; height: 70px; background: #1E1E1E; z-index: 10000; display: flex; align-items: center; justify-content: center; border-bottom: 3px solid #E2001A; }}
        .header-title {{ color: white; font-size: 22px; font-weight: bold; text-transform: uppercase; }}
        .main .block-container {{ padding-top: 100px; }}
    </style>
    <div class="fixed-header"><div class="header-title">Console Admin Gestion des Votes</div></div>
    """, unsafe_allow_html=True)

    if "auth" not in st.session_state: st.session_state["auth"] = False
    if not st.session_state["auth"]:
        pwd = st.text_input("Code Secret", type="password")
        if pwd == "ADMIN_LIVE_MASTER": st.session_state["auth"] = True; st.rerun()
    else:
        with st.sidebar:
            menu = st.radio("Menu", ["🔴 PILOTAGE LIVE", "📸 MÉDIATHÈQUE"])
        
        if menu == "🔴 PILOTAGE LIVE":
            cfg = st.session_state.config
            c1, c2, c3, c4 = st.columns(4)
            if c1.button("🏠 ACCUEIL"): cfg.update({"mode_affichage": "attente", "reveal_resultats": False}); save_json(CONFIG_FILE, cfg); st.rerun()
            if c2.button("🗳️ VOTES ON"): cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False}); save_json(CONFIG_FILE, cfg); st.rerun()
            if c3.button("🔒 VOTES OFF"): cfg["session_ouverte"] = False; save_json(CONFIG_FILE, cfg); st.rerun()
            if c4.button("🏆 PODIUM"): cfg.update({"mode_affichage": "votes", "reveal_resultats": True}); save_json(CONFIG_FILE, cfg); st.rerun()
            st.button("📸 MUR PHOTOS LIVE", on_click=lambda: cfg.update({"mode_affichage": "photos_live"}))

        elif menu == "📸 MÉDIATHÈQUE":
            st.title("Médiathèque")
            files = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
            cols = st.columns(4)
            for i, f in enumerate(files):
                with cols[i%4]:
                    st.image(f)
                    if st.button("Supprimer", key=f"del_{i}"): os.remove(f); st.rerun()

# =========================================================
# 2. APPLICATION MOBILE (FIX : ANTI-VOTE & ANIMATION CSS)
# =========================================================
elif est_utilisateur:
    # STYLE MOBILE ET ANIMATION BALLONS CSS (Plus fiable que JS)
    st.markdown("""
    <style>
        .stApp { background-color: black; color: white; }
        [data-testid='stHeader'] { display: none; }
        @keyframes flyUp { 0% { transform: translateY(0) rotate(0deg); opacity: 1; } 100% { transform: translateY(-120vh) rotate(20deg); opacity: 0; } }
        .balloon { position: fixed; bottom: -50px; font-size: 30px; animation: flyUp 3s ease-in forwards; z-index: 9999; pointer-events: none; }
    </style>
    """, unsafe_allow_html=True)

    # FORCE ANTI-FRAUDE PAR LOCALSTORAGE
    components.html("""<script>
        if(localStorage.getItem('voted_2026_final_v3')) {
            if(!window.parent.location.href.includes('blocked=true')) {
                window.parent.location.href = window.parent.location.href + '&blocked=true';
            }
        }
    </script>""", height=0)

    if is_blocked:
        # Affichage des ballons CSS au moment du blocage
        balloons_html = "".join([f'<div class="balloon" style="left:{random.randint(5,95)}vw; animation-delay:{random.random()*2}s;">🎈</div>' for _ in range(20)])
        st.markdown(balloons_html, unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; margin-top:50px;'><h2>✅ VOTE ENREGISTRÉ</h2><p>Merci pour votre participation !</p></div>", unsafe_allow_html=True)
        st.stop()

    if "user_pseudo" not in st.session_state:
        pseudo = st.text_input("Ton prénom :")
        if st.button("VOTER", type="primary", use_container_width=True) and pseudo:
            st.session_state.user_pseudo = pseudo; st.rerun()
    else:
        cfg = load_json(CONFIG_FILE, st.session_state.config)
        if cfg["mode_affichage"] == "photos_live":
            st.camera_input("📸 Ta photo sur le mur")
        else:
            if not cfg["session_ouverte"]: st.info("⏳ En attente des votes...")
            else:
                # Utilisation d'une clé dynamique pour forcer Streamlit à voir le changement
                choix = st.multiselect("Choisis 3 vidéos :", cfg["candidats"], max_selections=3, key=f"v_{st.session_state.session_ui_id}")
                
                if len(choix) == 3:
                    if st.button("🚀 VALIDER MON VOTE", type="primary", use_container_width=True):
                        vts = load_json(VOTES_FILE, {})
                        for v in choix: vts[v] = vts.get(v, 0) + 1
                        save_json(VOTES_FILE, vts)
                        # On marque le vote et on redirige vers la page avec ballons
                        components.html("""<script>
                            localStorage.setItem('voted_2026_final_v3', 'true');
                            window.parent.location.href = window.parent.location.href + '&blocked=true';
                        </script>""", height=0)
                        st.rerun()

# =========================================================
# 3. MUR SOCIAL (FIX : PODIUM PETIT & REBOND QR)
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2000, key="wall_refresh")
    cfg = load_json(CONFIG_FILE, st.session_state.config)
    
    st.markdown(f"""
    <style>
        body, .stApp {{ background-color: black !important; overflow: hidden; }}
        [data-testid='stHeader'] {{ display: none !important; }}
        .social-header {{ position: fixed; top: 0; left: 0; width: 100%; height: 12vh; background: #E2001A; display: flex; align-items: center; justify-content: center; border-bottom: 5px solid white; z-index: 5000; }}
        .social-title {{ color: white; font-size: 45px; text-transform: uppercase; font-family: sans-serif; font-weight: bold; }}
        
        /* GAGNANT : RÉDUIT À 350PX ET DESCENDU */
        .winner-box {{ 
            position: fixed; top: 65%; left: 50%; 
            transform: translate(-50%, -50%); 
            width: 350px; text-align: center; z-index: 1000; 
        }}
        .winner-card {{ 
            background: rgba(15, 15, 15, 0.98); border: 8px solid #FFD700; border-radius: 40px; padding: 25px;
            box-shadow: 0 0 50px #FFD700; animation: glow 1.5s infinite alternate;
        }}
        @keyframes glow {{ from {{ box-shadow: 0 0 10px #FFD700; }} to {{ box-shadow: 0 0 50px #FFD700; }} }}
    </style>
    <div class="social-header"><h1 class="social-title">{cfg['titre_mur']}</h1></div>
    """, unsafe_allow_html=True)

    mode = cfg.get("mode_affichage")
    
    # NETTOYAGE RADICAL DES EFFETS POUR L'ACCUEIL
    if mode == "attente":
        components.html("<script>var l = window.parent.document.getElementById('effect-layer'); if(l) l.remove();</script>", height=0)
        st.markdown("<h1 style='text-align:center; color:white; margin-top:40vh; font-size:80px;'>BIENVENUE</h1>", unsafe_allow_html=True)
    
    elif mode == "votes" or mode == "photos_live":
        if cfg.get("reveal_resultats"):
            v_data = load_json(VOTES_FILE, {})
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)
            if sorted_v:
                winner, pts = sorted_v[0]
                st.balloons()
                st.markdown(f"""<div class="winner-box"><div class="winner-card">
                    <h1 style="color:#FFD700; font-size:80px; margin:0;">🏆</h1>
                    <h1 style="color:white; font-size:45px; margin:10px 0;">{winner}</h1>
                    <h2 style="color:#FFD700; font-size:25px; margin:0;">VAINQUEUR</h2>
                </div></div>""", unsafe_allow_html=True)
        else:
            host = st.context.headers.get('host', 'localhost')
            qr_buf = BytesIO(); qrcode.make(f"http://{host}/?mode=vote").save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            st.markdown(f"""<div style="position:fixed; top:55%; left:50%; transform:translate(-50%, -50%); z-index:1500; background:white; padding:25px; border-radius:30px; text-align:center; border: 8px solid #E2001A;">
                <img src="data:image/png;base64,{qr_b64}" width="230"><h2 style="color:black; margin-top:15px; font-size:22px;">SCANNEZ POUR VOTER</h2></div>""", unsafe_allow_html=True)

        # BULLES 220PX AVEC REBOND SUR QR/PODIUM
        photos = glob.glob(f"{LIVE_DIR}/*")
        if photos:
            img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-15:]])
            components.html(f"""<script>
                var doc = window.parent.document;
                var container = doc.getElementById('bubble-wall') || doc.createElement('div');
                container.id = 'bubble-wall'; container.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:1;pointer-events:none;';
                if(!doc.getElementById('bubble-wall')) doc.body.appendChild(container);
                const imgs = {img_js}; const bubbles = []; const bSize = 220;
                const qrRect = {{ x: window.innerWidth/2 - 250, y: window.innerHeight/2 - 250, w: 500, h: 550 }};
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
                        if(b.x + b.size > qrRect.x && b.x < qrRect.x + qrRect.w && b.y + b.size > qrRect.y && b.y < qrRect.y + qrRect.h) {{
                            b.vx *= -1; b.vy *= -1; b.x += b.vx*5; b.y += b.vy*5;
                        }}
                        b.el.style.transform = `translate(${{b.x}}px, ${{b.y}}px)`;
                    }});
                    requestAnimationFrame(animate);
                }} animate();
            </script>""", height=0)
