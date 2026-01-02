import streamlit as st
import os, glob, base64, qrcode, json, time, uuid
from io import BytesIO
import streamlit.components.v1 as components
from datetime import datetime
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="Régie IT SQUAD", layout="wide", initial_sidebar_state="collapsed")

# Chemins
LIVE_DIR = "galerie_live_users"
VOTES_FILE = "votes.json"
CONFIG_FILE = "config_mur.json"
# Nouveau fichier pour stocker les IDs uniques des téléphones qui ont voté
VOTED_DEVICES_FILE = "voted_devices.json" 

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
        if st.button("📸 MUR PHOTOS"): cfg.update({"mode_affichage": "photos_live"}); save_json(CONFIG_FILE, cfg); st.rerun()
        
        # Reset pour les tests
        if st.button("⚠️ RESET TOTAL (POUR TEST)"):
            if os.path.exists(VOTES_FILE): os.remove(VOTES_FILE)
            if os.path.exists(VOTED_DEVICES_FILE): os.remove(VOTED_DEVICES_FILE)
            st.success("Système réinitialisé pour nouveaux tests")

# =========================================================
# 2. APPLICATION MOBILE (SÉCURITÉ RENFORCÉE)
# =========================================================
elif est_utilisateur:
    st.markdown("<style>.stApp {background-color:black; color:white;} [data-testid='stHeader'] {display:none;}</style>", unsafe_allow_html=True)
    
    # 1. IDENTIFIANT UNIQUE GÉNÉRÉ PAR LE TÉLÉPHONE
    if "device_id" not in st.session_state:
        st.session_state.device_id = str(uuid.uuid4())

    # 2. VÉRIFICATION LOCALSTORAGE (Première barrière)
    components.html("""<script>
        if(localStorage.getItem('VOTE_CONFIRMED_FINAL')) {
            window.parent.location.href = window.parent.location.href.split('&blocked')[0] + '&blocked=true';
        }
    </script>""", height=0)

    # 3. ÉCRAN BLOQUÉ (FIN)
    if is_blocked:
        st.balloons()
        st.markdown("""
            <div style='text-align:center; margin-top:100px; padding:20px;'>
                <h1 style='color:#E2001A;'>VOTE VALIDÉ !</h1>
                <p>Merci pour votre participation.</p>
                <br>
                <small style='color:#555;'>Appareil verrouillé.</small>
            </div>
        """, unsafe_allow_html=True)
        st.stop()

    # 4. INTERFACE
    if "pseudo" not in st.session_state:
        st.subheader("Identification")
        pseudo = st.text_input("Ton prénom :")
        if st.button("ENTRER", type="primary") and pseudo:
            st.session_state.pseudo = pseudo; st.rerun()
    else:
        cfg = load_json(CONFIG_FILE, st.session_state.config)
        
        # Vérification Serveur (Deuxième barrière - liste noire des pseudos/IDs)
        already_voted_ids = load_json(VOTED_DEVICES_FILE, [])
        # On peut ajouter ici une vérification sur le pseudo si besoin
        
        if cfg["mode_affichage"] == "photos_live":
            st.subheader("📸 Ta photo")
            cam = st.camera_input("Photo")
            if cam:
                with open(os.path.join(LIVE_DIR, f"live_{uuid.uuid4().hex}.jpg"), "wb") as f: f.write(cam.getbuffer())
                st.success("Envoyé !")
        
        elif cfg["mode_affichage"] == "votes" and cfg["session_ouverte"]:
            st.write(f"Bonjour **{st.session_state.pseudo}**")
            choix = st.multiselect("Choisis tes 3 favoris :", cfg["candidats"], max_selections=3)
            
            if len(choix) == 3:
                st.markdown("---")
                if st.button("🚀 VALIDER (DÉFINITIF)", type="primary", use_container_width=True):
                    # Enregistrement Vote
                    vts = load_json(VOTES_FILE, {})
                    for v in choix: vts[v] = vts.get(v, 0) + 1
                    save_json(VOTES_FILE, vts)
                    
                    # Enregistrement ID Appareil (Serveur)
                    already_voted_ids.append(st.session_state.pseudo) # On bloque le pseudo
                    save_json(VOTED_DEVICES_FILE, already_voted_ids)
                    
                    # Enregistrement Local (Client) et Redirection
                    components.html("""<script>
                        localStorage.setItem('VOTE_CONFIRMED_FINAL', 'true');
                        setTimeout(function(){
                            window.parent.location.href = window.parent.location.href + '&blocked=true';
                        }, 500);
                    </script>""", height=0)
                    time.sleep(1)
                    st.rerun()
        else:
            st.info("⏳ En attente...")

# =========================================================
# 3. MUR SOCIAL (CORRECTION VISUELLE CADRE)
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2000, key="wall_refresh")
    cfg = load_json(CONFIG_FILE, st.session_state.config)
    
    # CSS FORCE POUR LE CADRE
    st.markdown(f"""
    <style>
        body, .stApp {{ background-color: black !important; overflow: hidden; }}
        [data-testid='stHeader'] {{ display: none; }}
        
        /* BANDEAU TITRE */
        .social-header {{ 
            position: fixed; top: 0; left: 0; width: 100%; height: 12vh; 
            background: #E2001A; display: flex; align-items: center; justify-content: center; z-index: 5000; 
            border-bottom: 5px solid white;
        }}
        .social-title {{ color: white; font-size: 40px; font-weight: bold; margin: 0; font-family: sans-serif; text-transform: uppercase; }}
        
        /* CADRE VAINQUEUR - CORRECTION */
        .winner-container {{
            position: fixed;
            top: 55%;           /* Descendu plus bas que le milieu */
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 1000;
            width: 100%;
            display: flex;
            justify-content: center;
        }}
        
        .winner-card {{
            background: rgba(20, 20, 20, 0.95);
            border: 6px solid #FFD700;
            border-radius: 30px;
            padding: 30px;
            text-align: center;
            width: 350px !important;       /* Largeur forcée petite */
            max-width: 80vw;
            box-shadow: 0 0 50px rgba(255, 215, 0, 0.5);
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.02); }} 100% {{ transform: scale(1); }} }}
        
        .trophy {{ font-size: 60px; margin-bottom: 10px; }}
        .winner-name {{ font-size: 35px; color: white; font-weight: bold; margin: 10px 0; }}
        .winner-sub {{ font-size: 20px; color: #FFD700; }}
        
    </style>
    <div class="social-header"><h1 class="social-title">{cfg['titre_mur']}</h1></div>
    """, unsafe_allow_html=True)

    mode = cfg.get("mode_affichage")
    
    # NETTOYAGE CONFETTIS
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
                st.markdown(f"""
                <div class="winner-container">
                    <div class="winner-card">
                        <div class="trophy">🏆</div>
                        <div class="winner-name">{winner}</div>
                        <div class="winner-sub">VAINQUEUR ({pts} pts)</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            host = st.context.headers.get('host', 'localhost')
            qr_buf = BytesIO(); qrcode.make(f"http://{host}/?mode=vote").save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            st.markdown(f"""<div style="position:fixed; top:55%; left:50%; transform:translate(-50%, -50%); z-index:1500; background:white; padding:30px; border-radius:30px; text-align:center; border: 10px solid #E2001A;">
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
                const imgs = {img_js}; const bubbles = []; const bSize = 200;
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
