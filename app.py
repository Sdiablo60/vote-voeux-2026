import streamlit as st
import os, glob, base64, qrcode, json, random, pandas as pd
from io import BytesIO
import streamlit.components.v1 as components
import time
from PIL import Image
from datetime import datetime
import uuid

# --- 1. CONFIGURATION & FICHIERS ---
st.set_page_config(page_title="IT SQUAD - Régie Master", layout="wide", initial_sidebar_state="collapsed")

# Gestion des dossiers
LIVE_DIR = "galerie_live_users"
VOTES_FILE, CONFIG_FILE, VOTERS_FILE = "votes.json", "config_mur.json", "voters.json"

for d in [LIVE_DIR]:
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

# --- 2. CSS GLOBAL (ANTI-CLIGNOTEMENT & STABILITÉ) ---
st.markdown("""
<style>
    /* Fix Admin Title */
    .admin-header { position: fixed; top: 0; left: 0; width: 100%; height: 60px; background: #1E1E1E; 
                    z-index: 10000; display: flex; align-items: center; justify-content: center; border-bottom: 3px solid #E2001A; }
    .admin-header h2 { color: white; margin: 0; font-size: 20px; text-transform: uppercase; font-family: sans-serif; }
    
    /* Social Wall Style */
    body, .stApp { background-color: black !important; color: white; }
    .social-hdr { position: fixed; top: 0; left: 0; width: 100%; height: 12vh; background: #E2001A; 
                  display: flex; align-items: center; justify-content: center; border-bottom: 5px solid white; z-index: 5000; }
    .social-hdr h1 { color: white; font-size: 45px; margin: 0; font-weight: bold; text-transform: uppercase; }

    /* Winner Card - Fix Taille et Position */
    .podium-box { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -35%); 
                  width: 400px; text-align: center; z-index: 6000; }
    .podium-card { background: rgba(10,10,10,0.98); border: 8px solid #FFD700; border-radius: 40px; 
                   padding: 30px; box-shadow: 0 0 50px #FFD700; animation: glow 1.5s infinite alternate; }
    @keyframes glow { from { box-shadow: 0 0 10px #FFD700; } to { box-shadow: 0 0 60px #FFD700; } }
</style>
""", unsafe_allow_html=True)

# --- 3. INITIALISATION ---
if "config" not in st.session_state:
    st.session_state.config = load_json(CONFIG_FILE, {
        "mode_affichage": "attente", "titre_mur": "CONCOURS 2026", "session_ouverte": False, "reveal_resultats": False,
        "candidats": ["BU PAX", "BU FRET", "BU B2B", "RH", "IT", "DPMI", "FINANCES", "AO", "QSSE", "DIRECTION"]
    })

# Navigation
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
est_bloque = st.query_params.get("blocked") == "true"

# =========================================================
# A. CONSOLE ADMIN
# =========================================================
if est_admin:
    st.markdown('<div class="admin-header"><h2>Pilotage Régie - IT SQUAD</h2></div>', unsafe_allow_html=True)
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    cfg = st.session_state.config
    if c1.button("🏠 ACCUEIL"): cfg.update({"mode_affichage": "attente", "reveal_resultats": False}); save_json(CONFIG_FILE, cfg); st.rerun()
    if c2.button("🗳️ VOTES ON"): cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False}); save_json(CONFIG_FILE, cfg); st.rerun()
    if c3.button("🔒 VOTES OFF"): cfg["session_ouverte"] = False; save_json(CONFIG_FILE, cfg); st.rerun()
    if c4.button("🏆 PODIUM"): cfg.update({"mode_affichage": "votes", "reveal_resultats": True}); save_json(CONFIG_FILE, cfg); st.rerun()
    
    st.divider()
    st.subheader("📸 Médiathèque (Dernières photos reçues)")
    photos = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
    cols = st.columns(4)
    for i, p in enumerate(photos):
        with cols[i%4]:
            st.image(p)
            if st.button("Supprimer", key=f"del_{i}"): os.remove(p); st.rerun()

# =========================================================
# B. APPLICATION MOBILE (ANTI-VOTE & BALLONS)
# =========================================================
elif est_utilisateur:
    # Anti-fraude : Nouveau Verrou
    components.html("""<script>
        if(localStorage.getItem('VERROU_VOTE_V4')) {
            if(!window.parent.location.href.includes('blocked=true')) {
                window.parent.location.href = window.parent.location.href + '&blocked=true';
            }
        }
    </script>""", height=0)

    if est_bloque:
        st.markdown("<div style='text-align:center; margin-top:100px;'><h2>✅ VOTE ENREGISTRÉ</h2><p>Merci pour votre participation !</p></div>", unsafe_allow_html=True)
        st.stop()

    if "pseudo" not in st.session_state:
        pseudo = st.text_input("Ton prénom :")
        if st.button("ENTRER", type="primary", use_container_width=True) and pseudo:
            st.session_state.pseudo = pseudo; st.rerun()
    else:
        cfg = load_json(CONFIG_FILE, st.session_state.config)
        st.write(f"Votant : **{st.session_state.pseudo}**")
        
        if cfg["mode_affichage"] == "votes" and cfg["session_ouverte"]:
            choix = st.multiselect("Choisis 3 vidéos :", cfg["candidats"], max_selections=3)
            if len(choix) == 3:
                st.markdown("---")
                if st.button("🚀 VALIDER MON VOTE", type="primary", use_container_width=True):
                    # 1. Enregistrement
                    vts = load_json(VOTES_FILE, {})
                    for v in choix: vts[v] = vts.get(v, 0) + 1
                    save_json(VOTES_FILE, vts)
                    # 2. Animation avant redirection
                    st.balloons()
                    components.html("""<script>
                        localStorage.setItem('VERROU_VOTE_V4', 'true');
                        setTimeout(() => { window.parent.location.href += '&blocked=true'; }, 2500);
                    </script>""", height=0)
                    st.info("Transmission en cours... 🎈")
                    time.sleep(2.5)
        else:
            st.info("⏳ En attente du signal de la régie...")

# =========================================================
# C. MUR SOCIAL (FIX PODIUM & NETTOYAGE ACCUEIL)
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2000, key="wall_refresh")
    cfg = load_json(CONFIG_FILE, st.session_state.config)
    
    st.markdown(f'<div class="social-hdr"><h1>{cfg["titre_mur"]}</h1></div>', unsafe_allow_html=True)

    if cfg["mode_affichage"] == "attente":
        # NETTOYAGE PHYSIQUE DES CALQUES JS
        components.html("<script>var l = window.parent.document.getElementById('effect-layer'); if(l) l.remove();</script>", height=0)
        st.markdown("<h1 style='text-align:center; color:white; margin-top:40vh; font-size:100px;'>BIENVENUE</h1>", unsafe_allow_html=True)

    elif cfg["mode_affichage"] == "votes" or cfg["mode_affichage"] == "photos_live":
        if cfg["reveal_resultats"]:
            v_data = load_json(VOTES_FILE, {})
            res = sorted(v_data.items(), key=lambda x: x[1], reverse=True)
            if res:
                winner, pts = res[0]
                st.balloons()
                st.markdown(f"""
                <div class="podium-box">
                    <div class="podium-card">
                        <h1 style="color:#FFD700; font-size:80px; margin:0;">🏆</h1>
                        <h1 style="color:white; font-size:45px; margin:15px 0;">{winner}</h1>
                        <h2 style="color:#FFD700; font-size:25px; margin:0;">VAINQUEUR</h2>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            # QR CODE
            host = st.context.headers.get('host', 'localhost')
            qr_buf = BytesIO(); qrcode.make(f"http://{host}/?mode=vote").save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            st.markdown(f"""<div style="position:fixed; top:55%; left:50%; transform:translate(-50%, -50%); z-index:1500; background:white; padding:30px; border-radius:30px; text-align:center; border: 10px solid #E2001A;">
                <img src="data:image/png;base64,{qr_b64}" width="250"><h2 style="color:black; margin-top:20px; font-size:25px;">SCANNEZ POUR VOTER</h2></div>""", unsafe_allow_html=True)

        # ANIMATION BULLES 220PX
        photos = glob.glob(f"{LIVE_DIR}/*")
        if photos:
            img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-20:]])
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
