import streamlit as st
import os, glob, base64, qrcode, json, random, pandas as pd
from io import BytesIO
import streamlit.components.v1 as components
import time
from PIL import Image
from datetime import datetime
import zipfile
import uuid

# --- 1. CONFIGURATION & FICHIERS ---
st.set_page_config(page_title="Régie Master - Pôle Aéroportuaire", layout="wide")

GALLERY_DIR, ADMIN_DIR = "galerie_images", "galerie_admin"
LIVE_DIR = "galerie_live_users"
VOTES_FILE, PARTICIPANTS_FILE, CONFIG_FILE, VOTERS_FILE, DETAILED_VOTES_FILE = "votes.json", "participants.json", "config_mur.json", "voters.json", "detailed_votes.json"

for d in [GALLERY_DIR, ADMIN_DIR, LIVE_DIR]:
    if not os.path.exists(d): os.makedirs(d)

DEFAULT_CANDIDATS = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r") as f: return json.load(f)
        except: return default
    return default

# Initialisation de la configuration
if "config" not in st.session_state:
    st.session_state.config = load_json(CONFIG_FILE, {
        "mode_affichage": "attente", 
        "titre_mur": "CONCOURS VIDÉO PÔLE AEROPORTUAIRE", 
        "session_ouverte": False, 
        "reveal_resultats": False,
        "timestamp_podium": 0,
        "logo_b64": None,
        "candidats": DEFAULT_CANDIDATS,
        "candidats_images": {}, 
        "points_ponderation": [5, 3, 1],
        "session_id": "session_init_001",
        "effect_intensity": 25, 
        "effect_speed": 25,     
        "screen_effects": {       
            "attente": "Aucun", "votes_open": "Aucun", "votes_closed": "Aucun", "podium": "🎉 Confettis", "photos_live": "Aucun"
        }
    })

def save_config():
    with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)

# --- FONCTION D'INJECTION D'EFFETS (MUR SOCIAL) ---
def inject_visual_effect(effect_name, intensity, speed):
    if effect_name == "Aucun":
        components.html("""<script>var old = window.parent.document.getElementById('effect-layer'); if(old) old.remove();</script>""", height=0)
        return
    
    # Calculs pour harmoniser l'intensité et la vitesse
    duration = max(2, 20 - (speed * 0.35))
    interval = int(4000 / (intensity + 5))
    
    js_code = f"""
    <script>
        var doc = window.parent.document;
        var old = doc.getElementById('effect-layer');
        if(old) old.remove();
        var layer = doc.createElement('div');
        layer.id = 'effect-layer';
        layer.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:99;overflow:hidden;';
        doc.body.appendChild(layer);
        
        function createBalloon() {{
            var e = doc.createElement('div'); e.innerHTML = '🎈';
            e.style.cssText = 'position:absolute;bottom:-100px;left:'+Math.random()*100+'vw;font-size:'+(Math.random()*40+20)+'px;transition:bottom {duration}s linear;';
            layer.appendChild(e);
            setTimeout(() => {{ e.style.bottom = '110vh'; }}, 50);
            setTimeout(() => {{ e.remove(); }}, {duration * 1000});
        }}
        function createSnow() {{
            var e = doc.createElement('div'); e.innerHTML = '❄';
            e.style.cssText = 'position:absolute;top:-50px;left:'+Math.random()*100+'vw;color:white;font-size:'+(Math.random()*20+10)+'px;transition:top {duration}s linear;';
            layer.appendChild(e);
            setTimeout(() => {{ e.style.top = '110vh'; }}, 50);
            setTimeout(() => {{ e.remove(); }}, {duration * 1000});
        }}
        function createStar() {{
            var e = doc.createElement('div');
            var size = (Math.random() * 4 + 1) + 'px';
            e.style.cssText = 'position:absolute;background:white;border-radius:50%;width:'+size+';height:'+size+';left:'+Math.random()*100+'vw;top:'+Math.random()*100+'vh;opacity:0;transition:opacity {duration/2}s; box-shadow: 0 0 5px white;';
            layer.appendChild(e);
            setTimeout(() => {{ e.style.opacity = '1'; }}, 50);
            setTimeout(() => {{ e.style.opacity = '0'; }}, {duration * 800});
            setTimeout(() => {{ e.remove(); }}, {duration * 1000});
        }}
    """
    
    if effect_name == "🎈 Ballons": js_code += f"setInterval(createBalloon, {interval});"
    elif effect_name == "❄️ Neige": js_code += f"setInterval(createSnow, {interval});"
    elif effect_name == "🌌 Espace": js_code += f"setInterval(createStar, {interval});"
    elif effect_name == "🎉 Confettis":
        js_code += f"""
        var s = doc.createElement('script'); s.src = "https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js";
        s.onload = function() {{
            function fire() {{ 
                window.parent.confetti({{ particleCount: {max(1, int(intensity*1.5))}, angle: 90, spread: 100, origin: {{ x: Math.random(), y: -0.2 }}, gravity: 0.8, ticks: 400 }}); 
                setTimeout(fire, {max(200, 2000 - (speed * 35))}); 
            }}
            fire();
        }}; layer.appendChild(s);"""
    elif effect_name == "🟢 Matrix":
        f_size = max(10, 40 - intensity)
        js_code += f"""
        var canvas = doc.createElement('canvas'); canvas.style.cssText = 'width:100%;height:100%;opacity:0.6;'; layer.appendChild(canvas);
        var ctx = canvas.getContext('2d'); canvas.width = window.parent.innerWidth; canvas.height = window.parent.innerHeight;
        var columns = canvas.width / {f_size}; var drops = []; for(var i=0; i<columns; i++) drops[i] = 1;
        function draw() {{ 
            ctx.fillStyle = 'rgba(0, 0, 0, 0.1)'; ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#0F0'; ctx.font = '{f_size}px monospace'; 
            for(var i=0; i<drops.length; i++) {{ 
                ctx.fillText(Math.floor(Math.random()*2), i*{f_size}, drops[i]*{f_size}); 
                if(drops[i]*{f_size} > canvas.height && Math.random() > 0.975) drops[i] = 0; drops[i]++; 
            }} 
        }}
        setInterval(draw, {max(20, 150 - (speed * 2.5))});"""
        
    js_code += "</script>"
    components.html(js_code, height=0)

# --- NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"

# --- ADMINISTRATION ---
if est_admin:
    st.markdown("""<style>
        [data-testid="stHeader"] { visibility: hidden; }
        .block-container { padding-top: 5rem !important; }
        .fixed-header { 
            position: fixed; top: 0; left: 0; width: 100%; 
            background-color: #E2001A; color: white; text-align: center; 
            padding: 15px 0; z-index: 999999; box-shadow: 0 4px 10px rgba(0,0,0,0.3); 
            font-family: sans-serif; font-weight: bold; font-size: 22px; text-transform: uppercase; 
        }
    </style>""", unsafe_allow_html=True)
    
    if "auth" not in st.session_state: st.session_state.auth = False
    if not st.session_state.auth:
        st.markdown("<div class='fixed-header'>🔐 ACCÈS RÉSERVÉ</div>", unsafe_allow_html=True)
        pwd = st.text_input("Mot de passe", type="password")
        if pwd == "ADMIN_LIVE_MASTER": st.session_state.auth = True; st.rerun()
    else:
        with st.sidebar:
            st.title("🎛️ RÉGIE MASTER")
            menu = st.radio("Navigation", ["🔴 PILOTAGE LIVE", "⚙️ Paramètres", "📸 Médiathèque"])
        st.markdown(f"<div class='fixed-header'>{menu}</div>", unsafe_allow_html=True)

        if menu == "🔴 PILOTAGE LIVE":
            # 1. SEQUENCEUR (EN PREMIER)
            st.subheader("🎬 Séquenceur de Diffusion")
            bt1, bt2, bt3, bt4, bt5 = st.columns(5)
            cfg = st.session_state.config
            if bt1.button("🏠 ACCUEIL", use_container_width=True): cfg.update({"mode_affichage":"attente","reveal_resultats":False,"session_ouverte":False}); save_config(); st.rerun()
            if bt2.button("🗳️ VOTES ON", use_container_width=True): cfg.update({"mode_affichage":"votes","session_ouverte":True,"reveal_resultats":False}); save_config(); st.rerun()
            if bt3.button("🛑 VOTES OFF", use_container_width=True): cfg.update({"session_ouverte":False}); save_config(); st.rerun()
            if bt4.button("🏆 PODIUM", use_container_width=True): cfg.update({"mode_affichage":"votes","reveal_resultats":True,"session_ouverte":False,"timestamp_podium":time.time()}); save_config(); st.rerun()
            if bt5.button("📸 PHOTO LIVE", use_container_width=True): cfg.update({"mode_affichage":"photos_live","reveal_resultats":False}); save_config(); st.rerun()
            
            st.divider()
            
            # 2. REGLAGES
            st.subheader("📡 Gestion des Effets")
            c_e1, c_e2 = st.columns(2)
            with c_e1:
                intensity = st.slider("🔢 Densité (Nombre)", 0, 50, cfg["effect_intensity"])
                speed = st.slider("🚀 Vitesse (Animation)", 0, 50, cfg["effect_speed"])
                if intensity != cfg["effect_intensity"] or speed != cfg["effect_speed"]:
                    cfg["effect_intensity"] = intensity; cfg["effect_speed"] = speed; save_config(); st.rerun()
            
            EFFECT_LIST = ["Aucun", "🎈 Ballons", "❄️ Neige", "🎉 Confettis", "🌌 Espace", "💸 Billets", "🟢 Matrix"]
            col1, col2 = st.columns(2)
            with col1:
                s1 = st.selectbox("Accueil", EFFECT_LIST, index=EFFECT_LIST.index(cfg["screen_effects"].get("attente","Aucun")), key="s1")
                s2 = st.selectbox("Votes", EFFECT_LIST, index=EFFECT_LIST.index(cfg["screen_effects"].get("votes_open","Aucun")), key="s2")
            with col2:
                s3 = st.selectbox("Podium", EFFECT_LIST, index=EFFECT_LIST.index(cfg["screen_effects"].get("podium","Aucun")), key="s3")
                s4 = st.selectbox("Photos", EFFECT_LIST, index=EFFECT_LIST.index(cfg["screen_effects"].get("photos_live","Aucun")), key="s4")
            
            if st.button("💾 APPLIQUER CONFIGURATION"):
                cfg["screen_effects"].update({"attente":s1, "votes_open":s2, "podium":s3, "photos_live":s4})
                save_config(); st.toast("Config mise à jour !")

        elif menu == "⚙️ Paramètres":
            st.title("Configuration")
            new_title = st.text_input("Titre du Mur", value=cfg["titre_mur"])
            if st.button("Sauver Titre"): cfg["titre_mur"] = new_title; save_config(); st.rerun()

        elif menu == "📸 Médiathèque":
            st.title("Photos Live")
            files = glob.glob(f"{LIVE_DIR}/*")
            if files:
                cols = st.columns(6)
                for i, f in enumerate(files):
                    with cols[i%6]:
                        st.image(f, use_container_width=True)
                        if st.button("🗑️", key=f"del_{i}"): os.remove(f); st.rerun()

# --- UTILISATEUR MOBILE ---
elif est_utilisateur:
    cfg_user = load_json(CONFIG_FILE, {})
    st.markdown("<style>.stApp { background-color: black; color: white; }</style>", unsafe_allow_html=True)
    if cfg_user.get("mode_affichage") == "photos_live":
        st.title("📸 Envoyer Photo")
        photo = st.camera_input("Photo")
        if photo:
            img = Image.open(photo)
            img.save(f"{LIVE_DIR}/img_{int(time.time())}.jpg", "JPEG"); st.success("Envoyé !")
    else:
        st.title("🗳️ Vote")
        st.info("Interface de vote active")

# --- MUR SOCIAL ---
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=3000, key="wall")
    cfg_wall = load_json(CONFIG_FILE, {})
    st.markdown("<style>body, .stApp { background-color: black; overflow: hidden; } [data-testid='stHeader'] { display: none; }</style>", unsafe_allow_html=True)
    
    screen_key = "attente"
    if cfg_wall.get("mode_affichage") == "photos_live": screen_key = "photos_live"
    elif cfg_wall.get("reveal_resultats"): screen_key = "podium"
    elif cfg_wall.get("mode_affichage") == "votes": screen_key = "votes_open" if cfg_wall.get("session_ouverte") else "votes_closed"
    
    inject_visual_effect(cfg_wall.get("screen_effects", {}).get(screen_key, "Aucun"), cfg_wall.get("effect_intensity", 25), cfg_wall.get("effect_speed", 25))

    if cfg_wall.get("mode_affichage") == "photos_live":
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        logo_html = f'<img src="data:image/png;base64,{cfg_wall["logo_b64"]}" style="max-height:120px; margin-bottom:20px;">' if cfg_wall.get("logo_b64") else ""
        
        st.markdown(f"""
            <div style="position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); z-index:1000; text-align:center; width:100%; pointer-events:none;">
                <div style="display:inline-block; pointer-events:auto; background: rgba(0,0,0,0.7); padding: 40px; border-radius: 40px; border: 1px solid rgba(255,255,255,0.1);">
                    {logo_html}
                    <h1 style="color:white; font-size:60px; text-transform:uppercase; margin-bottom:30px; text-shadow: 2px 2px 10px rgba(0,0,0,0.8);">Mur Photos Live</h1>
                    <div style="background:white; padding:20px; border-radius:30px; box-shadow: 0 0 50px rgba(0,0,0,0.5); display:inline-block; margin-bottom:30px;">
                        <img src="data:image/png;base64,{qr_b64}" width="220">
                    </div>
                    <br>
                    <div style="background:#E2001A; color:white; padding:15px 40px; border-radius:50px; font-weight:bold; font-size:28px; display:inline-block; border:4px solid white; box-shadow: 0 10px 20px rgba(0,0,0,0.4);">
                        📸 SCANNEZ POUR ENVOYER VOTRE PHOTO
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        files = glob.glob(f"{LIVE_DIR}/*"); files.sort(key=os.path.getmtime, reverse=True)
        if files:
            img_list = [f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in files[:20]]
            components.html(f"""<script>
                window.parent.document.querySelectorAll('.bubble').forEach(b => b.remove());
                var imgs = {json.dumps(img_list)};
                imgs.forEach(src => {{
                    var i = document.createElement('img'); i.src = src; i.style.cssText = 'position:absolute; border-radius:50%; border:4px solid #E2001A; width:'+(Math.random()*150 + 100)+'px; height:auto; aspect-ratio:1/1; object-fit:cover; z-index:1; left:'+(Math.random()*90)+'vw; top:'+(Math.random()*90)+'vh;';
                    window.parent.document.body.appendChild(i);
                    var vx = (Math.random() > 0.5 ? 1 : -1) * 0.15; var vy = (Math.random() > 0.5 ? 1 : -1) * 0.15;
                    function anim() {{
                        if(!i.parentElement) return;
                        var l = parseFloat(i.style.left); var t = parseFloat(i.style.top);
                        if(l <= 1 || l >= 94) vx *= -1; if(t <= 1 || t >= 94) vy *= -1;
                        i.style.left = (l + vx) + 'vw'; i.style.top = (t + vy) + 'vh';
                        requestAnimationFrame(anim);
                    }} anim();
                }});
            </script>""", height=0)
    else:
        logo_html = f'<img src="data:image/png;base64,{cfg_wall["logo_b64"]}" style="max-height:150px; display:block; margin:auto;">' if cfg_wall.get("logo_b64") else ""
        st.markdown(f"<div style='margin-top:150px; text-align:center;'>{logo_html}<h1 style='color:white; font-size:65px; margin-top:40px;'>{cfg_wall.get('titre_mur')}</h1></div>", unsafe_allow_html=True)
