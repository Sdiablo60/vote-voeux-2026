import streamlit as st
import os, glob, base64, json, time, uuid
from io import BytesIO
import streamlit.components.v1 as components
from PIL import Image
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Régie IT SQUAD", layout="wide", initial_sidebar_state="collapsed")

LIVE_DIR = "galerie_live_users"
VOTES_FILE = "votes.json"
CONFIG_FILE = "config_mur.json"
VOTERS_FILE = "voters.json" # Fichier liste des prénoms ayant voté

for d in [LIVE_DIR]:
    if not os.path.exists(d): os.makedirs(d)

# --- FONCTIONS ---
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

# --- INIT ---
if "config" not in st.session_state: 
    st.session_state.config = load_json(CONFIG_FILE, {
        "mode_affichage": "attente", 
        "titre_mur": "CONCOURS VIDÉO 2026", 
        "session_ouverte": False, 
        "reveal_resultats": False,
        "candidats": ["BU PAX", "BU FRET", "BU B2B", "RH", "IT", "DPMI", "FINANCES", "AO", "QSSE", "DIRECTION"]
    })

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
        if st.text_input("Code", type="password") == "ADMIN_LIVE_MASTER": st.session_state["auth"] = True; st.rerun()
    else:
        cfg = st.session_state.config
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("🏠 ACCUEIL"): cfg.update({"mode_affichage": "attente", "reveal_resultats": False}); save_json(CONFIG_FILE, cfg); st.rerun()
        if c2.button("🗳️ VOTES ON"): cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False}); save_json(CONFIG_FILE, cfg); st.rerun()
        if c3.button("🔒 VOTES OFF"): cfg["session_ouverte"] = False; save_json(CONFIG_FILE, cfg); st.rerun()
        if c4.button("🏆 PODIUM"): cfg.update({"mode_affichage": "votes", "reveal_resultats": True}); save_json(CONFIG_FILE, cfg); st.rerun()
        st.divider()
        
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            if st.button("📸 MUR PHOTOS"): cfg.update({"mode_affichage": "photos_live"}); save_json(CONFIG_FILE, cfg); st.rerun()
        with c_p2:
            if st.button("🗑️ RESET VOTANTS (Débloquer les noms)"):
                if os.path.exists(VOTERS_FILE): os.remove(VOTERS_FILE)
                if os.path.exists(VOTES_FILE): os.remove(VOTES_FILE)
                st.success("Base de données votants effacée !")

# =========================================================
# 2. APPLICATION MOBILE (SÉCURITÉ RENFORCÉE SERVEUR)
# =========================================================
elif est_utilisateur:
    st.markdown("<style>.stApp {background-color:black; color:white;} [data-testid='stHeader'] {display:none;}</style>", unsafe_allow_html=True)
    
    # 1. Vérification Locale (Cookie)
    components.html("""<script>
        if(localStorage.getItem('VOTE_SECURE_V7')) {
            if(!window.parent.location.href.includes('blocked=true')) {
                window.parent.location.href = window.parent.location.href + '&blocked=true';
            }
        }
    </script>""", height=0)

    # 2. Page de Fin (Bloquée)
    if is_blocked:
        # Animation CSS Pure (Plus fiable)
        st.markdown("""
        <style>
            @keyframes float { 0% { transform: translateY(100vh); opacity: 1; } 100% { transform: translateY(-100vh); opacity: 0; } }
            .balloon { position: fixed; bottom: -100px; font-size: 3rem; animation: float 4s ease-in infinite; z-index: 9999; }
        </style>
        <div class="balloon" style="left: 10%; animation-duration: 3s;">🎈</div>
        <div class="balloon" style="left: 30%; animation-duration: 4s;">🎈</div>
        <div class="balloon" style="left: 70%; animation-duration: 3.5s;">🎈</div>
        <div style='text-align:center; margin-top:100px;'>
            <h1 style='color:#E2001A;'>VOTE ENREGISTRÉ</h1>
            <p>Merci pour votre participation.</p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # 3. Interface de Vote
    if "pseudo" not in st.session_state:
        st.subheader("Identification")
        pseudo_input = st.text_input("Ton prénom :")
        if st.button("ENTRER", type="primary") and pseudo_input:
            # --- VÉRIFICATION SERVEUR STRICTE ---
            # On charge la liste des gens qui ont DÉJÀ voté
            voters_list = load_json(VOTERS_FILE, [])
            # On normalise (majuscules) pour comparer
            if pseudo_input.strip().upper() in [v.upper() for v in voters_list]:
                st.error("⛔ Ce prénom a déjà voté ! Impossible de recommencer.")
            else:
                st.session_state.pseudo = pseudo_input.strip()
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
            st.write(f"Votant : **{st.session_state.pseudo}**")
            choix = st.multiselect("Choisis 3 favoris :", cfg["candidats"], max_selections=3)
            
            if len(choix) == 3:
                st.markdown("---")
                if st.button("🚀 VALIDER DÉFINITIVEMENT", type="primary", use_container_width=True):
                    # --- DOUBLE SÉCURITÉ AU MOMENT DU CLICK ---
                    voters_list = load_json(VOTERS_FILE, [])
                    if st.session_state.pseudo.upper() in [v.upper() for v in voters_list]:
                        st.error("Erreur : Vote déjà comptabilisé pour ce nom.")
                        time.sleep(2)
                        st.rerun()
                    else:
                        # 1. Enregistrement du Vote
                        vts = load_json(VOTES_FILE, {})
                        for v in choix: vts[v] = vts.get(v, 0) + 1
                        save_json(VOTES_FILE, vts)
                        
                        # 2. Enregistrement du Nom (Blocage Serveur)
                        voters_list.append(st.session_state.pseudo)
                        save_json(VOTERS_FILE, voters_list)
                        
                        # 3. Blocage Navigateur
                        components.html("""<script>
                            localStorage.setItem('VOTE_SECURE_V7', 'true');
                            window.parent.location.href = window.parent.location.href + '&blocked=true';
                        </script>""", height=0)
        else:
            st.info("⏳ En attente...")

# =========================================================
# 3. MUR SOCIAL (NOUVEAU DESIGN "BANDEAU BAS")
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2000, key="wall_refresh")
    cfg = load_json(CONFIG_FILE, st.session_state.config)
    
    # CSS GLOBAL
    st.markdown(f"""
    <style>
        body, .stApp {{ background-color: black !important; overflow: hidden; }} [data-testid='stHeader'] {{ display: none; }}
        
        /* HEADER TITRE (HAUT) */
        .social-header {{ position: fixed; top: 0; left: 0; width: 100%; height: 12vh; background: #E2001A; display: flex; align-items: center; justify-content: center; z-index: 5000; border-bottom: 5px solid white; }}
        .social-title {{ color: white; font-size: 40px; font-weight: bold; margin: 0; font-family: sans-serif; text-transform: uppercase; }}
        
        /* BANDEAU VAINQUEUR (BAS DE L'ÉCRAN - style Cinéma) */
        .winner-banner {{
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 35vh; /* Prend le tiers bas de l'écran */
            background: linear-gradient(to top, #000 10%, #E2001A 90%);
            border-top: 5px solid white;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            z-index: 2000;
            animation: slideUp 1s ease-out;
        }}
        @keyframes slideUp {{ from {{ transform: translateY(100%); }} to {{ transform: translateY(0); }} }}
        
        .winner-trophy {{ font-size: 60px; margin-bottom: 10px; }}
        .winner-text {{ color: white; font-size: 50px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px; text-shadow: 0 0 20px black; }}
        .winner-sub {{ color: #FFD700; font-size: 25px; margin-top: 5px; font-weight: bold; }}
    </style>
    <div class="social-header"><h1 class="social-title">{cfg['titre_mur']}</h1></div>
    """, unsafe_allow_html=True)

    mode = cfg.get("mode_affichage")
    
    # NETTOYAGE CONFETTIS ACCUEIL
    if mode == "attente":
        components.html("<script>document.querySelectorAll('canvas').forEach(e => e.remove());</script>", height=0)
        st.markdown("<h1 style='text-align:center; color:white; margin-top:40vh; font-size:80px;'>BIENVENUE</h1>", unsafe_allow_html=True)

    elif mode == "votes":
        if cfg.get("reveal_resultats"):
            v_data = load_json(VOTES_FILE, {})
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)
            if sorted_v:
                winner, pts = sorted_v[0]
                st.balloons()
                # NOUVEAU DESIGN : BANDEAU EN BAS
                st.markdown(f"""
                <div class="winner-banner">
                    <div class="winner-trophy">🏆</div>
                    <div class="winner-text">{winner}</div>
                    <div class="winner-sub">GRAND VAINQUEUR ({pts} PTS)</div>
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
                const imgs = {img_js}; 
                const bSize = 200;
                // Zone de rebond centrale (Titre en haut, rien en bas)
                const qrRect = {{ x: window.innerWidth/2 - 200, y: window.innerHeight/2 - 200, w: 400, h: 400 }};
                
                imgs.forEach((src, i) => {{
                    if(doc.getElementById('bub-'+i)) return;
                    const el = doc.createElement('img'); el.id = 'bub-'+i; el.src = src;
                    el.style.cssText = 'position:absolute; width:'+bSize+'px; height:'+bSize+'px; border-radius:50%; border:6px solid #E2001A; object-fit:cover;';
                    let x = Math.random() * (window.innerWidth - bSize); let y = Math.random() * (window.innerHeight - bSize);
                    let vx = (Math.random()-0.5)*5; let vy = (Math.random()-0.5)*5;
                    container.appendChild(el);
                }});
            </script>""", height=0)
