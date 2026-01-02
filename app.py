import streamlit as st
import os, glob, base64, qrcode, json, random, pandas as pd
from io import BytesIO
import streamlit.components.v1 as components
import time
from PIL import Image
from datetime import datetime
import zipfile
import uuid

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Régie Master - IT SQUAD", layout="wide", initial_sidebar_state="collapsed")

LIVE_DIR = "galerie_live_users"
VOTES_FILE, CONFIG_FILE, VOTERS_FILE = "votes.json", "config_mur.json", "voters.json"

if not os.path.exists(LIVE_DIR): os.makedirs(LIVE_DIR)

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
        "candidats": ["BU PAX", "BU FRET", "BU B2B", "RH", "IT", "DPMI", "FINANCES", "AO", "QSSE", "DIRECTION"]
    })

# --- NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
is_blocked = st.query_params.get("blocked") == "true"

# =========================================================
# 1. CONSOLE ADMIN (FIX CLIGNOTEMENT)
# =========================================================
if est_admin:
    st.markdown("""<style>
        .admin-hdr { position: fixed; top: 0; left: 0; width: 100%; height: 60px; background: #111; 
                     border-bottom: 3px solid #E2001A; z-index: 9999; display: flex; align-items: center; justify-content: center; }
        .admin-txt { color: white; font-weight: bold; font-family: sans-serif; font-size: 20px; }
        .main .block-container { padding-top: 80px; }
    </style><div class="admin-hdr"><div class="admin-txt">CONSOLE ADMIN - GESTION DES VOTES</div></div>""", unsafe_allow_html=True)

    with st.sidebar:
        menu = st.radio("NAVIGATION", ["🔴 PILOTAGE", "📸 MÉDIATHÈQUE"])

    cfg = st.session_state.config
    if menu == "🔴 PILOTAGE":
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("🏠 ACCUEIL"): cfg.update({"mode_affichage": "attente", "reveal_resultats": False}); save_json(CONFIG_FILE, cfg); st.rerun()
        if c2.button("🗳️ VOTES ON"): cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False}); save_json(CONFIG_FILE, cfg); st.rerun()
        if c3.button("🔒 VOTES OFF"): cfg["session_ouverte"] = False; save_json(CONFIG_FILE, cfg); st.rerun()
        if c4.button("🏆 PODIUM"): cfg.update({"mode_affichage": "votes", "reveal_resultats": True}); save_json(CONFIG_FILE, cfg); st.rerun()
        st.divider()
        if st.button("📸 MUR PHOTOS LIVE", type="primary", use_container_width=True):
            cfg.update({"mode_affichage": "photos_live", "session_ouverte": False}); save_json(CONFIG_FILE, cfg); st.rerun()
    
    elif menu == "📸 MÉDIATHÈQUE":
        photos = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
        cols = st.columns(4)
        for i, p in enumerate(photos):
            with cols[i%4]:
                st.image(p)
                if st.button("Supprimer", key=f"del_{i}"): os.remove(p); st.rerun()

# =========================================================
# 2. APPLICATION MOBILE (MARQUAGE & ANIMATION BALLONS)
# =========================================================
elif est_utilisateur:
    st.markdown("<style>.stApp {background-color: black; color: white;} [data-testid='stHeader'] {display:none;}</style>", unsafe_allow_html=True)
    
    # --- MARQUAGE TECHNIQUE DU TÉLÉPHONE (localStorage) ---
    components.html("""<script>
        if(localStorage.getItem('DEVICE_MARKED_VOTED_2026')) {
            if(!window.parent.location.href.includes('blocked=true')) {
                window.parent.location.href = window.parent.location.href + '&blocked=true';
            }
        }
    </script>""", height=0)

    if is_blocked:
        # L'animation se joue sur la page de succès
        st.balloons()
        st.markdown("<div style='text-align:center; margin-top:100px;'><h2>✅ VOTE ENREGISTRÉ</h2><p>Merci ! Votre participation est bien prise en compte.</p></div>", unsafe_allow_html=True)
        st.stop()

    if "pseudo" not in st.session_state:
        st.subheader("🦸 Identification")
        pseudo = st.text_input("Entre ton prénom :")
        if st.button("ACCÉDER AU VOTE", type="primary", use_container_width=True) and pseudo:
            st.session_state.pseudo = pseudo; st.rerun()
    else:
        cfg = load_json(CONFIG_FILE, st.session_state.config)
        if cfg["mode_affichage"] == "votes" and cfg["session_ouverte"]:
            st.write(f"Votant : **{st.session_state.pseudo}**")
            choix = st.multiselect("Sélectionne tes 3 vidéos favorites :", cfg["candidats"], max_selections=3)
            
            # LE BOUTON APPARAÎT IMMÉDIATEMENT DÈS QUE 3 SONT CHOISIS
            if len(choix) == 3:
                st.markdown("---")
                if st.button("🚀 VALIDER MON VOTE", type="primary", use_container_width=True):
                    # 1. Sauvegarde Serveur
                    vts = load_json(VOTES_FILE, {})
                    for v in choix: vts[v] = vts.get(v, 0) + 1
                    save_json(VOTES_FILE, vts)
                    
                    # 2. Marquage du téléphone et Redirection
                    components.html("""<script>
                        localStorage.setItem('DEVICE_MARKED_VOTED_2026', 'true');
                        window.parent.location.href = window.parent.location.href + '&blocked=true';
                    </script>""", height=0)
                    st.rerun()
        else:
            st.info("⏳ En attente du signal de la régie...")

# =========================================================
# 3. MUR SOCIAL (PODIUM CENTRÉ & ZÉRO CONFETTI)
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2000, key="wall_refresh")
    cfg = load_json(CONFIG_FILE, st.session_state.config)
    
    st.markdown(f"""
        <style>
            body, .stApp {{ background-color: black !important; overflow: hidden; }}
            [data-testid='stHeader'] {{ display: none !important; }}
            .social-header {{ position: fixed; top: 0; left: 0; width: 100%; height: 12vh; background: #E2001A; 
                             display: flex; align-items: center; justify-content: center; border-bottom: 5px solid white; z-index: 5000; }}
            .social-title {{ color: white; font-size: 50px; text-transform: uppercase; font-weight: bold; font-family: sans-serif; }}
            
            /* GAGNANT : RÉDUIT À 350PX ET POSITIONNÉ AU CENTRE BAS (60%) */
            .winner-card {{ 
                position: fixed; top: 60%; left: 50%; transform: translate(-50%, -50%); 
                width: 350px; background: rgba(15,15,15,0.98); border: 8px solid #FFD700; 
                border-radius: 50px; padding: 30px; text-align: center; z-index: 1000;
                box-shadow: 0 0 60px #FFD700;
            }}
        </style>
        <div class="social-header"><h1 class="social-title">{cfg['titre_mur']}</h1></div>
    """, unsafe_allow_html=True)

    mode = cfg.get("mode_affichage")
    
    # --- FIX : SUPPRESSION RADICALE DES EFFETS POUR L'ACCUEIL ---
    if mode == "attente":
        components.html("<script>var l = window.parent.document.getElementById('effect-layer'); if(l) l.remove();</script>", height=0)
        st.markdown("<h1 style='text-align:center; color:white; margin-top:40vh; font-size:90px;'>BIENVENUE</h1>", unsafe_allow_html=True)

    elif mode == "votes" or mode == "photos_live":
        if cfg.get("reveal_resultats"):
            v_data = load_json(VOTES_FILE, {})
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)
            if sorted_v:
                winner, pts = sorted_v[0]
                st.balloons()
                st.markdown(f"""
                    <div class="winner-card">
                        <h1 style="color:#FFD700; font-size:80px; margin:0;">🏆</h1>
                        <h1 style="color:white; font-size:45px; margin:15px 0; text-transform:uppercase;">{winner}</h1>
                        <h2 style="color:#FFD700; font-size:25px; margin:0;">VAINQUEUR</h2>
                    </div>
                """, unsafe_allow_html=True)
        else:
            host = st.context.headers.get('host', 'localhost')
            qr_buf = BytesIO(); qrcode.make(f"http://{host}/?mode=vote").save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            st.markdown(f"""<div style="position:fixed; top:55%; left:50%; transform:translate(-50%, -50%); z-index:1500; background:white; padding:30px; border-radius:30px; text-align:center; border: 10px solid #E2001A;">
                <img src="data:image/png;base64,{qr_b64}" width="250"><h2 style="color:black; margin-top:20px; font-size:25px;">SCANNEZ POUR VOTER</h2></div>""", unsafe_allow_html=True)

        # BULLES 220PX AVEC REBOND SUR QR
        photos = glob.glob(f"{LIVE_DIR}/*")
        if photos:
            img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-15:]])
            components.html(f"""<script>
                var doc = window.parent.document;
                var container = doc.getElementById('bubble-wall') || doc.createElement('div');
                container.id = 'bubble-wall'; container.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:1;pointer-events:none;';
                if(!doc.getElementById('bubble-wall')) doc.body.appendChild(container);
                const imgs = {img_js}; const bubbles = []; const bSize = 220;
                const qrRect = {{ x: window.innerWidth/2 - 250, y: window.innerHeight/2 - 250, w: 500, h: 500 }};
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
