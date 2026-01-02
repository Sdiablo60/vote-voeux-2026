import streamlit as st
import os, glob, base64, qrcode, json, random, pandas as pd
from io import BytesIO
import streamlit.components.v1 as components
import time
from PIL import Image
from datetime import datetime
import uuid

# --- 1. CONFIGURATION INITIALE ---
st.set_page_config(page_title="Régie Master IT", layout="wide", initial_sidebar_state="collapsed")

# Chemins et Fichiers
LIVE_DIR = "galerie_live_users"
VOTES_FILE = "votes.json"
CONFIG_FILE = "config_mur.json"
VOTERS_FILE = "voters.json"

for d in [LIVE_DIR]:
    if not os.path.exists(d): os.makedirs(d)

# Fonctions de gestion des données
def charger_donnees(fichier, defaut):
    if os.path.exists(fichier):
        try:
            with open(fichier, "r", encoding='utf-8') as f: return json.load(f)
        except: return defaut
    return defaut

def sauver_donnees(fichier, donnee):
    with open(fichier, "w", encoding='utf-8') as f:
        json.dump(donnee, f, ensure_ascii=False, indent=4)

# --- 2. ÉTAT DE LA CONFIGURATION ---
if "config" not in st.session_state:
    st.session_state.config = charger_donnees(CONFIG_FILE, {
        "mode_affichage": "attente",
        "titre_mur": "VŒUX 2026",
        "session_ouverte": False,
        "reveal_resultats": False,
        "candidats": ["BU PAX", "BU FRET", "BU B2B", "RH", "IT", "DPMI", "FINANCES", "AO", "QSSE", "DIRECTION"]
    })

# --- 3. LOGIQUE DE NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
est_bloque = st.query_params.get("blocked") == "true"

# =========================================================
# A. CONSOLE ADMIN (FIX CLIGNOTEMENT)
# =========================================================
if est_admin:
    st.markdown("""
        <style>
            .admin-hdr { position: fixed; top: 0; left: 0; width: 100%; height: 60px; background: #111; 
                         border-bottom: 3px solid #E2001A; z-index: 9999; display: flex; align-items: center; justify-content: center; }
            .admin-txt { color: white; font-weight: bold; font-family: sans-serif; font-size: 20px; }
            .main .block-container { padding-top: 80px; }
        </style>
        <div class="admin-hdr"><div class="admin-txt">CONSOLE ADMIN - GESTION DES VOTES</div></div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        menu = st.radio("MENU", ["VOTES", "PHOTOS"])

    if menu == "VOTES":
        st.subheader("Pilotage du direct")
        cfg = st.session_state.config
        col1, col2, col3, col4 = st.columns(4)
        if col1.button("🏠 ACCUEIL"): cfg.update({"mode_affichage": "attente", "reveal_resultats": False}); sauver_donnees(CONFIG_FILE, cfg); st.rerun()
        if col2.button("🗳️ VOTES ON"): cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False}); sauver_donnees(CONFIG_FILE, cfg); st.rerun()
        if col3.button("🔒 VOTES OFF"): cfg["session_ouverte"] = False; sauver_donnees(CONFIG_FILE, cfg); st.rerun()
        if col4.button("🏆 PODIUM"): cfg.update({"mode_affichage": "votes", "reveal_resultats": True}); sauver_donnees(CONFIG_FILE, cfg); st.rerun()
    
    else:
        st.subheader("Médiathèque (Triée par heure)")
        photos = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
        cols = st.columns(4)
        for i, p in enumerate(photos):
            with cols[i%4]:
                st.image(p)
                if st.button("Supprimer", key=f"del_{i}"): os.remove(p); st.rerun()

# =========================================================
# B. APPLICATION MOBILE (FIX ANIMATION & ANTI-FRAUDE)
# =========================================================
elif est_utilisateur:
    st.markdown("<style>.stApp {background-color: black; color: white;} [data-testid='stHeader'] {display:none;}</style>", unsafe_allow_html=True)
    
    # --- ANTI-FRAUDE NOUVELLE CLÉ ---
    components.html("""<script>
        if(localStorage.getItem('CLE_UNIQUE_VOTE_2026')) {
            if(!window.parent.location.href.includes('blocked=true')) {
                window.parent.location.href = window.parent.location.href + '&blocked=true';
            }
        }
    </script>""", height=0)

    if est_bloque:
        # L'ANIMATION SE LANCE ICI POUR ÊTRE SÛRE DE NE PAS ÊTRE COUPÉE
        st.balloons()
        st.markdown("<div style='text-align:center; margin-top:100px;'><h2>✅ VOTE ENREGISTRÉ</h2><p>Merci pour votre participation !</p></div>", unsafe_allow_html=True)
        st.stop()

    if "pseudo" not in st.session_state:
        pseudo = st.text_input("Ton prénom :")
        if st.button("ENTRER", type="primary", use_container_width=True) and pseudo:
            st.session_state.pseudo = pseudo; st.rerun()
    else:
        cfg = charger_donnees(CONFIG_FILE, st.session_state.config)
        if cfg["mode_affichage"] == "votes" and cfg["session_ouverte"]:
            st.write(f"Bonjour **{st.session_state.pseudo}**")
            choix = st.multiselect("Sélectionne 3 vidéos :", cfg["candidats"], max_selections=3)
            
            if len(choix) == 3:
                st.markdown("---")
                if st.button("🚀 VALIDER MON VOTE", type="primary", use_container_width=True):
                    # Sauvegarde et Blocage
                    vts = charger_donnees(VOTES_FILE, {})
                    for v in choix: vts[v] = vts.get(v, 0) + 1
                    sauver_donnees(VOTES_FILE, vts)
                    
                    components.html("""<script>
                        localStorage.setItem('CLE_UNIQUE_VOTE_2026', 'true');
                        window.parent.location.href = window.parent.location.href + '&blocked=true';
                    </script>""", height=0)
                    st.rerun()
        else:
            st.info("⏳ En attente de la régie...")

# =========================================================
# C. MUR SOCIAL (FIX PODIUM TAILLE & NETTOYAGE ACCUEIL)
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2000, key="wall_refresh")
    cfg = charger_donnees(CONFIG_FILE, st.session_state.config)
    
    st.markdown(f"""
        <style>
            body, .stApp {{ background-color: black !important; overflow: hidden; font-family: sans-serif; }}
            [data-testid='stHeader'] {{ display: none !important; }}
            .social-header {{ position: fixed; top: 0; left: 0; width: 100%; height: 12vh; background: #E2001A; 
                             display: flex; align-items: center; justify-content: center; border-bottom: 5px solid white; z-index: 5000; }}
            .social-title {{ color: white; font-size: 50px; text-transform: uppercase; font-weight: bold; }}
            
            /* CADRE VAINQUEUR PETIT ET BAS */
            .winner-card {{ 
                position: fixed; top: 450px; left: 50%; transform: translateX(-50%);
                width: 400px; background: rgba(10,10,10,0.95); border: 8px solid #FFD700; 
                border-radius: 40px; padding: 30px; text-align: center; z-index: 1000;
                box-shadow: 0 0 50px #FFD700;
            }}
        </style>
        <div class="social-header"><h1 class="social-title">{cfg['titre_mur']}</h1></div>
    """, unsafe_allow_html=True)

    if cfg["mode_affichage"] == "attente":
        # NETTOYAGE FORCÉ DES EFFETS
        components.html("<script>var l = window.parent.document.getElementById('effect-layer'); if(l) l.remove();</script>", height=0)
        st.markdown("<h1 style='text-align:center; color:white; margin-top:40vh; font-size:80px;'>BIENVENUE</h1>", unsafe_allow_html=True)

    elif cfg["mode_affichage"] == "votes":
        if cfg["reveal_resultats"]:
            v_data = charger_donnees(VOTES_FILE, {})
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)
            if sorted_v:
                winner, pts = sorted_v[0]
                st.balloons()
                st.markdown(f"""
                    <div class="winner-card">
                        <h1 style="color:#FFD700; font-size:80px; margin:0;">🏆</h1>
                        <h1 style="color:white; font-size:50px; margin:10px 0;">{winner}</h1>
                        <h2 style="color:#FFD700; font-size:25px; margin:0;">VAINQUEUR</h2>
                    </div>
                """, unsafe_allow_html=True)
        else:
            # QR CODE
            host = st.context.headers.get('host', 'localhost')
            qr_buf = BytesIO(); qrcode.make(f"http://{host}/?mode=vote").save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            st.markdown(f"""<div style="position:fixed; top:55%; left:50%; transform:translate(-50%, -50%); z-index:1500; background:white; padding:30px; border-radius:30px; text-align:center; border: 10px solid #E2001A;">
                <img src="data:image/png;base64,{qr_b64}" width="250"><h2 style="color:black; margin-top:20px; font-size:25px;">SCANNEZ POUR VOTER</h2></div>""", unsafe_allow_html=True)

        # BULLES 220PX AVEC REBOND
        photos = glob.glob(f"{LIVE_DIR}/*")
        if photos:
            img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-20:]])
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
