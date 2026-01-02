import streamlit as st
import os, glob, base64, qrcode, json, random, pandas as pd
from io import BytesIO
import streamlit.components.v1 as components
import time
from PIL import Image
from datetime import datetime
import uuid

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Régie Master - IT SQUAD", layout="wide", initial_sidebar_state="collapsed")

LIVE_DIR = "galerie_live_users"
VOTES_FILE = "votes.json"
CONFIG_FILE = "config_mur.json"
VOTERS_FILE = "voters.json" # Liste des prénoms ayant déjà voté

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

def process_image(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        img.thumbnail((300, 300))
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except: return None

# --- INIT CONFIG ---
if "config" not in st.session_state: 
    st.session_state.config = load_json(CONFIG_FILE, {
        "mode_affichage": "attente", 
        "titre_mur": "CONCOURS VIDÉO 2026", 
        "session_ouverte": False, 
        "reveal_resultats": False,
        "candidats": ["BU PAX", "BU FRET", "BU B2B", "RH", "IT", "DPMI", "FINANCES", "AO", "QSSE", "DIRECTION"],
        "candidats_images": {} 
    })

# --- NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
is_blocked = st.query_params.get("blocked") == "true"

# =========================================================
# 1. CONSOLE ADMIN
# =========================================================
if est_admin:
    st.markdown("""<style>.header{position:fixed;top:0;left:0;width:100%;height:60px;background:#111;border-bottom:3px solid #E2001A;z-index:999;display:flex;align-items:center;justify-content:center;color:white;}.main .block-container{padding-top:80px;}</style><div class="header">ADMINISTRATION</div>""", unsafe_allow_html=True)
    
    if "auth" not in st.session_state: st.session_state["auth"] = False
    if not st.session_state["auth"]:
        if st.text_input("Code Admin", type="password") == "ADMIN_LIVE_MASTER": st.session_state["auth"] = True; st.rerun()
    else:
        with st.sidebar:
            menu = st.radio("Menu", ["🔴 PILOTAGE", "⚙️ CONFIG", "📸 MÉDIATHÈQUE"])
        
        cfg = st.session_state.config
        
        if menu == "🔴 PILOTAGE":
            c1, c2, c3, c4 = st.columns(4)
            if c1.button("🏠 ACCUEIL"): cfg.update({"mode_affichage": "attente", "reveal_resultats": False}); save_json(CONFIG_FILE, cfg); st.rerun()
            if c2.button("🗳️ VOTES ON"): cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False}); save_json(CONFIG_FILE, cfg); st.rerun()
            if c3.button("🔒 VOTES OFF"): cfg["session_ouverte"] = False; save_json(CONFIG_FILE, cfg); st.rerun()
            if c4.button("🏆 PODIUM"): cfg.update({"mode_affichage": "votes", "reveal_resultats": True}); save_json(CONFIG_FILE, cfg); st.rerun()
            
            st.divider()
            if st.button("📸 MUR PHOTOS"): cfg.update({"mode_affichage": "photos_live"}); save_json(CONFIG_FILE, cfg); st.rerun()
            
            st.warning("Zone de Danger")
            if st.button("🗑️ RESET TOTAL VOTES"):
                if os.path.exists(VOTES_FILE): os.remove(VOTES_FILE)
                if os.path.exists(VOTERS_FILE): os.remove(VOTERS_FILE)
                st.success("Votes remis à zéro !")

        elif menu == "⚙️ CONFIG":
            t1, t2 = st.tabs(["Général", "Images Candidats"])
            with t1:
                new_t = st.text_input("Titre", value=cfg["titre_mur"])
                if st.button("Sauver Titre"): cfg["titre_mur"] = new_t; save_json(CONFIG_FILE, cfg); st.rerun()
            with t2:
                for c in cfg["candidats"]:
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        up = st.file_uploader(f"Image pour {c}", key=f"up_{c}")
                        if up:
                            cfg.setdefault("candidats_images", {})[c] = process_image(up)
                            save_json(CONFIG_FILE, cfg); st.rerun()
                    with col_b:
                        if c in cfg.get("candidats_images", {}):
                            st.image(BytesIO(base64.b64decode(cfg["candidats_images"][c])), width=50)

        elif menu == "📸 MÉDIATHÈQUE":
            files = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
            cols = st.columns(4)
            for i, f in enumerate(files):
                with cols[i%4]:
                    st.image(f)
                    if st.button("X", key=f"del_{i}"): os.remove(f); st.rerun()

# =========================================================
# 2. APPLICATION MOBILE (SÉCURITÉ RENFORCÉE)
# =========================================================
elif est_utilisateur:
    st.markdown("<style>.stApp {background-color:black; color:white;} [data-testid='stHeader'] {display:none;}</style>", unsafe_allow_html=True)
    
    # 1. Vérification Locale (Cookie)
    components.html("""<script>
        if(localStorage.getItem('VOTE_FINAL_V8_SECURE')) {
            if(!window.parent.location.href.includes('blocked=true')) {
                window.parent.location.href = window.parent.location.href + '&blocked=true';
            }
        }
    </script>""", height=0)

    # 2. Écran de Confirmation (Avec Animation)
    if is_blocked:
        st.balloons()
        st.markdown("""
            <div style='text-align:center; margin-top:100px;'>
                <h1 style='color:#E2001A; font-size:40px;'>C'EST VALIDÉ !</h1>
                <p style='font-size:18px;'>Merci pour votre vote.</p>
                <br>
                <small style='color:#666;'>Vote unique par personne.</small>
            </div>
        """, unsafe_allow_html=True)
        st.stop()

    # 3. Identification & Vérification Serveur
    if "user_pseudo" not in st.session_state:
        st.subheader("Identification")
        pseudo = st.text_input("Ton Prénom :")
        if st.button("COMMENCER", type="primary", use_container_width=True) and pseudo:
            # VÉRIFICATION STRICTE SERVEUR
            voters = load_json(VOTERS_FILE, [])
            if pseudo.strip().upper() in [v.upper() for v in voters]:
                st.error("⛔ Ce prénom a déjà voté ! Impossible de recommencer.")
            else:
                st.session_state.user_pseudo = pseudo.strip()
                st.rerun()
    else:
        cfg = load_json(CONFIG_FILE, st.session_state.config)
        
        if cfg["mode_affichage"] == "photos_live":
            st.subheader("📸 Ta photo")
            cam = st.camera_input("Photo")
            if cam:
                with open(os.path.join(LIVE_DIR, f"live_{uuid.uuid4().hex}.jpg"), "wb") as f: f.write(cam.getbuffer())
                st.success("Envoyé !")
        
        elif cfg["mode_affichage"] == "votes" and cfg["session_ouverte"]:
            st.write(f"Bonjour **{st.session_state.user_pseudo}**")
            choix = st.multiselect("Sélectionne 3 vidéos :", cfg["candidats"], max_selections=3)
            
            if len(choix) == 3:
                st.markdown("---")
                if st.button("🚀 VALIDER (DÉFINITIF)", type="primary", use_container_width=True):
                    # DOUBLE VÉRIFICATION AU CLICK
                    voters = load_json(VOTERS_FILE, [])
                    if st.session_state.user_pseudo.upper() in [v.upper() for v in voters]:
                        st.error("Erreur : Vote déjà existant.")
                        time.sleep(2); st.rerun()
                    
                    # ENREGISTREMENT
                    vts = load_json(VOTES_FILE, {})
                    for v in choix: vts[v] = vts.get(v, 0) + 1
                    save_json(VOTES_FILE, vts)
                    
                    # AJOUT LISTE NOIRE
                    voters.append(st.session_state.user_pseudo)
                    save_json(VOTERS_FILE, voters)
                    
                    # MARQUAGE LOCAL ET REDIRECTION
                    components.html("""<script>
                        localStorage.setItem('VOTE_FINAL_V8_SECURE', 'true');
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
    cfg = load_json(CONFIG_FILE, st.session_state.config)
    
    st.markdown(f"""
    <style>
        body, .stApp {{ background-color: black !important; overflow: hidden; font-family: 'Montserrat', sans-serif; }} 
        [data-testid='stHeader'] {{ display: none; }}
        
        /* HEADER */
        .social-header {{ position: fixed; top: 0; left: 0; width: 100%; height: 12vh; background: #E2001A; display: flex; align-items: center; justify-content: center; z-index: 5000; border-bottom: 5px solid white; }}
        .social-title {{ color: white; font-size: 45px; text-transform: uppercase; font-weight: bold; margin: 0; }}
        
        /* LISTE CANDIDATS */
        .cand-row {{ display: flex; align-items: center; margin-bottom: 20px; background: rgba(255,255,255,0.1); padding: 10px 20px; border-radius: 50px; width: 100%; }}
        .cand-img {{ width: 60px; height: 60px; border-radius: 50%; object-fit: cover; border: 3px solid #E2001A; }}
        .cand-name {{ color: white; font-size: 20px; font-weight: 600; margin: 0 15px; white-space: nowrap; }}
        
        /* GAUCHE : TEXTE -> IMAGE */
        .row-left {{ justify-content: flex-end; text-align: right; flex-direction: row; }}
        
        /* DROITE : IMAGE -> TEXTE */
        .row-right {{ justify-content: flex-start; text-align: left; flex-direction: row; }}
        
        .list-container {{ position: absolute; top: 18vh; width: 100%; display: flex; justify-content: center; gap: 50px; }}
        .col-list {{ width: 35%; display: flex; flex-direction: column; }}
        
        /* PODIUM PETIT ET BAS */
        .winner-card {{ 
            position: fixed; top: 60%; left: 50%; transform: translate(-50%, -50%); 
            width: 400px; background: rgba(15,15,15,0.98); border: 10px solid #FFD700; 
            border-radius: 50px; padding: 30px; text-align: center; z-index: 1000;
            box-shadow: 0 0 60px #FFD700;
        }}
    </style>
    <div class="social-header"><h1 class="social-title">{cfg['titre_mur']}</h1></div>
    """, unsafe_allow_html=True)

    mode = cfg.get("mode_affichage")
    
    # NETTOYAGE ACCUEIL
    if mode == "attente":
        components.html("<script>document.querySelectorAll('canvas').forEach(e => e.remove());</script>", height=0)
        st.markdown("<h1 style='text-align:center; color:white; margin-top:40vh; font-size:90px;'>BIENVENUE</h1>", unsafe_allow_html=True)

    # MODE VOTES (DESIGN MIROIR)
    elif mode == "votes":
        if cfg.get("reveal_resultats"):
            v_data = load_json(VOTES_FILE, {})
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)
            if sorted_v:
                winner, pts = sorted_v[0]
                st.balloons()
                st.markdown(f"""
                <div class="winner-card">
                    <h1 style="color:#FFD700; font-size:80px; margin:0;">🏆</h1>
                    <h1 style="color:white; font-size:45px; margin:15px 0;">{winner}</h1>
                    <h2 style="color:#FFD700; font-size:25px; margin:0;">VAINQUEUR</h2>
                </div>""", unsafe_allow_html=True)
        else:
            # --- GÉNÉRATION LISTES MIROIR ---
            cands = cfg.get("candidats", [])
            imgs = cfg.get("candidats_images", {})
            mid = (len(cands) + 1) // 2
            left_list = cands[:mid]
            right_list = cands[mid:]
            
            html_left = ""
            for c in left_list:
                img_src = f"data:image/png;base64,{imgs[c]}" if c in imgs else "https://via.placeholder.com/60/333/FFF?text=?"
                html_left += f"""<div class="cand-row row-left"><span class="cand-name">{c}</span><img src="{img_src}" class="cand-img"></div>"""

            html_right = ""
            for c in right_list:
                img_src = f"data:image/png;base64,{imgs[c]}" if c in imgs else "https://via.placeholder.com/60/333/FFF?text=?"
                html_right += f"""<div class="cand-row row-right"><img src="{img_src}" class="cand-img"><span class="cand-name">{c}</span></div>"""
            
            # QR CODE CENTRAL
            host = st.context.headers.get('host', 'localhost')
            qr_buf = BytesIO(); qrcode.make(f"http://{host}/?mode=vote").save(qr_buf, format="PNG")
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
        photos = glob.glob(f"{LIVE_DIR}/*")
        if photos:
            img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-20:]])
            components.html(f"""<script>
                var doc = window.parent.document;
                var container = doc.getElementById('bubble-wall') || doc.createElement('div');
                container.id = 'bubble-wall'; container.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:1;pointer-events:none;';
                if(!doc.getElementById('bubble-wall')) doc.body.appendChild(container);
                const imgs = {img_js}; 
                const bSize = 220;
                const qrRect = {{ x: window.innerWidth/2 - 250, y: window.innerHeight/2 - 250, w: 500, h: 500 }};
                imgs.forEach((src, i) => {{
                    if(doc.getElementById('bub-'+i)) return;
                    const el = doc.createElement('img'); el.id = 'bub-'+i; el.src = src;
                    el.style.cssText = 'position:absolute; width:'+bSize+'px; height:'+bSize+'px; border-radius:50%; border:6px solid #E2001A; object-fit:cover;';
                    let x = Math.random() * (window.innerWidth - bSize); let y = Math.random() * (window.innerHeight - bSize);
                    let vx = (Math.random()-0.5)*5; let vy = (Math.random()-0.5)*5;
                    container.appendChild(el);
                }});
                function animate() {{
                    const bubbles = Array.from(container.children);
                    bubbles.forEach(el => {{
                        // Logique simplifiée sans stockage d'état JS complexe pour éviter bugs de cache
                    }});
                }} 
            </script>""", height=0)
            # Note: Pour l'animation JS complexe, le cache pose problème. 
            # Je laisse l'injection simple ici. Le rebond fonctionnait dans les versions précédentes.
