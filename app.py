import streamlit as st
import os, glob, base64, json, time, uuid
from io import BytesIO
import streamlit.components.v1 as components
from PIL import Image
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Régie Master", layout="wide", initial_sidebar_state="collapsed")

# Chemins
LIVE_DIR = "galerie_live_users"
VOTES_FILE = "votes.json"
CONFIG_FILE = "config_mur.json"
VOTERS_FILE = "voters.json" # LISTE NOIRE DES PRÉNOMS

# Création des dossiers si absents
if not os.path.exists(LIVE_DIR): os.makedirs(LIVE_DIR)

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

def process_image_upload(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        img.thumbnail((300, 300))
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    except: return None

# --- INIT SESSION STATE ---
if "config" not in st.session_state: 
    st.session_state.config = load_json(CONFIG_FILE, {
        "mode_affichage": "attente", 
        "titre_mur": "CONCOURS VIDÉO 2026", 
        "session_ouverte": False, 
        "reveal_resultats": False,
        "candidats": ["BU PAX", "BU FRET", "BU B2B", "RH", "IT", "DPMI", "FINANCES", "AO", "QSSE", "DIRECTION"]
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
        cfg = st.session_state.config
        c1, c2, c3, c4 = st.columns(4)
        
        if c1.button("🏠 ACCUEIL"): 
            cfg.update({"mode_affichage": "attente", "reveal_resultats": False})
            save_json(CONFIG_FILE, cfg); st.rerun()
            
        if c2.button("🗳️ VOTES ON"): 
            cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False})
            save_json(CONFIG_FILE, cfg); st.rerun()
            
        if c3.button("🔒 VOTES OFF"): 
            cfg["session_ouverte"] = False
            save_json(CONFIG_FILE, cfg); st.rerun()
            
        if c4.button("🏆 PODIUM"): 
            cfg.update({"mode_affichage": "votes", "reveal_resultats": True})
            save_json(CONFIG_FILE, cfg); st.rerun()
            
        st.divider()
        if st.button("📸 MUR PHOTOS"): 
            cfg.update({"mode_affichage": "photos_live"})
            save_json(CONFIG_FILE, cfg); st.rerun()
            
        if st.button("⚠️ RESET TOTAL DES VOTES"):
            if os.path.exists(VOTES_FILE): os.remove(VOTES_FILE)
            if os.path.exists(VOTERS_FILE): os.remove(VOTERS_FILE)
            st.success("Système réinitialisé.")

# =========================================================
# 2. APPLICATION MOBILE (SÉCURITÉ SERVEUR + ANIMATION)
# =========================================================
elif est_utilisateur:
    st.markdown("<style>.stApp {background-color:black; color:white;} [data-testid='stHeader'] {display:none;}</style>", unsafe_allow_html=True)

    # A. VÉRIFICATION DU MARQUAGE TÉLÉPHONE (Premier niveau)
    components.html("""<script>
        if(localStorage.getItem('VOTE_FINAL_SECURE_KEY')) {
            if(!window.parent.location.href.includes('blocked=true')) {
                window.parent.location.href = window.parent.location.href + '&blocked=true';
            }
        }
    </script>""", height=0)

    # B. ÉCRAN DE FIN (AVEC ANIMATION)
    if is_blocked:
        st.balloons() # L'animation se lance ICI, sur la page stable
        st.markdown("""
            <div style='text-align:center; margin-top:100px;'>
                <h1 style='color:#E2001A;'>C'EST DANS LA BOÎTE !</h1>
                <p style='font-size:20px;'>Votre vote a été validé.</p>
                <br>
                <small style='color:#666;'>Vous ne pouvez plus modifier votre choix.</small>
            </div>
        """, unsafe_allow_html=True)
        st.stop()

    # C. FORMULAIRE
    if "user_pseudo" not in st.session_state:
        st.image("https://cdn-icons-png.flaticon.com/512/2983/2983808.png", width=60)
        st.subheader("Identification")
        pseudo_input = st.text_input("Ton Prénom :")
        
        if st.button("COMMENCER", type="primary", use_container_width=True) and pseudo_input:
            # --- VÉRIFICATION SERVEUR (IMPOSSIBLE À CONTOURNER) ---
            voters = load_json(VOTERS_FILE, [])
            clean_pseudo = pseudo_input.strip().upper()
            
            if clean_pseudo in [v.upper() for v in voters]:
                st.error("⛔ Ce prénom a déjà voté ! Accès refusé.")
            else:
                st.session_state.user_pseudo = pseudo_input.strip()
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
            choix = st.multiselect("Choisis 3 vidéos :", cfg["candidats"], max_selections=3)
            
            if len(choix) == 3:
                st.markdown("---")
                if st.button("🚀 VALIDER (DÉFINITIF)", type="primary", use_container_width=True):
                    # 1. Double vérification serveur au moment du clic
                    voters = load_json(VOTERS_FILE, [])
                    if st.session_state.user_pseudo.upper() in [v.upper() for v in voters]:
                        st.error("Erreur : Vote déjà existant.")
                        time.sleep(2)
                        st.rerun()
                    
                    # 2. Enregistrement Vote
                    vts = load_json(VOTES_FILE, {})
                    for v in choix: vts[v] = vts.get(v, 0) + 1
                    save_json(VOTES_FILE, vts)
                    
                    # 3. Enregistrement Prénom (Liste Noire)
                    voters.append(st.session_state.user_pseudo)
                    save_json(VOTERS_FILE, voters)
                    
                    # 4. Marquage Téléphone et Redirection
                    components.html("""<script>
                        localStorage.setItem('VOTE_FINAL_SECURE_KEY', 'true');
                        window.parent.location.href = window.parent.location.href + '&blocked=true';
                    </script>""", height=0)
                    st.rerun()
        else:
            st.info("⏳ En attente de l'ouverture...")

# =========================================================
# 3. MUR SOCIAL (PODIUM BAS DE PAGE & NETTOYAGE)
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2000, key="wall_refresh")
    cfg = load_json(CONFIG_FILE, st.session_state.config)
    
    # CSS GLOBAL
    st.markdown(f"""
    <style>
        body, .stApp {{ background-color: black !important; overflow: hidden; }} [data-testid='stHeader'] {{ display: none; }}
        
        /* HEADER HAUT */
        .social-header {{ position: fixed; top: 0; left: 0; width: 100%; height: 12vh; background: #E2001A; display: flex; align-items: center; justify-content: center; z-index: 5000; border-bottom: 5px solid white; }}
        .social-title {{ color: white; font-size: 40px; font-weight: bold; margin: 0; text-transform: uppercase; }}
        
        /* BANDEAU VAINQUEUR - COLLÉ EN BAS DE L'ÉCRAN */
        .winner-bar {{
            position: fixed;
            bottom: 0; left: 0; width: 100%; height: 30vh; /* Prend le bas de l'écran */
            background: linear-gradient(to top, black, #111);
            border-top: 4px solid #FFD700;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            z-index: 2000;
            box-shadow: 0 -10px 50px rgba(255, 215, 0, 0.2);
            animation: slideUp 1s ease-out;
        }}
        @keyframes slideUp {{ from {{ transform: translateY(100%); }} to {{ transform: translateY(0); }} }}
        
        .winner-trophy {{ font-size: 50px; margin-bottom: 5px; }}
        .winner-name {{ color: white; font-size: 60px; font-weight: 900; text-transform: uppercase; margin: 0; text-shadow: 0 0 20px #FFD700; }}
        .winner-pts {{ color: #FFD700; font-size: 25px; font-weight: bold; margin-top: 5px; }}
    </style>
    <div class="social-header"><h1 class="social-title">{cfg['titre_mur']}</h1></div>
    """, unsafe_allow_html=True)

    mode = cfg.get("mode_affichage")
    
    # --- NETTOYEUR DE CONFETTIS ACCUEIL ---
    if mode == "attente":
        # Supprime tout élément canvas (confettis)
        components.html("<script>document.querySelectorAll('canvas').forEach(e => e.remove());</script>", height=0)
        st.markdown("<h1 style='text-align:center; color:white; margin-top:40vh; font-size:80px;'>BIENVENUE</h1>", unsafe_allow_html=True)

    elif mode == "votes":
        if cfg.get("reveal_resultats"):
            v_data = load_json(VOTES_FILE, {})
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)
            if sorted_v:
                winner, pts = sorted_v[0]
                st.balloons()
                # NOUVEAU DESIGN : BANDEAU BAS
                st.markdown(f"""
                <div class="winner-bar">
                    <div class="winner-trophy">🏆</div>
                    <div class="winner-name">{winner}</div>
                    <div class="winner-pts">VAINQUEUR AVEC {pts} POINTS</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            host = st.context.headers.get('host', 'localhost')
            qr_buf = BytesIO(); qrcode.make(f"http://{host}/?mode=vote").save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            st.markdown(f"""<div style="position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); z-index:1500; background:white; padding:30px; border-radius:30px; text-align:center; border: 10px solid #E2001A;">
                <img src="data:image/png;base64,{qr_b64}" width="200"><h2 style="color:black; margin-top:20px; font-size:20px;">SCANNEZ POUR VOTER</h2></div>""", unsafe_allow_html=True)

    elif mode == "photos_live":
        photos = glob.glob(f"{LIVE_DIR}/*")
        if photos:
            img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-20:]])
            components.html(f"""<script>
                var doc = window.parent.document;
                var container = doc.getElementById('bubble-wall') || doc.createElement('div');
                container.id = 'bubble-wall'; container.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:1;pointer-events:none;';
                if(!doc.getElementById('bubble-wall')) doc.body.appendChild(container);
                const imgs = {img_js}; const bubbles = []; const bSize = 220;
                // Zone de rebond
                const qrRect = {{ x: window.innerWidth/2 - 200, y: window.innerHeight/2 - 200, w: 400, h: 400 }};
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
