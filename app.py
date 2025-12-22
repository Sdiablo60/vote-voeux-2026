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

# --- FONCTION D'INJECTION D'EFFETS ---
def inject_visual_effect(effect_name, intensity, speed):
    if effect_name == "Aucun":
        components.html("""<script>var old = window.parent.document.getElementById('effect-layer'); if(old) old.remove();</script>""", height=0)
        return
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
    """
    if effect_name == "🎈 Ballons": js_code += f"setInterval(createBalloon, {interval});"
    elif effect_name == "🎉 Confettis":
        js_code += f"""
        var s = doc.createElement('script'); s.src = "https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js";
        s.onload = function() {{
            function fire() {{ window.parent.confetti({{ particleCount: {max(1, int(intensity*1.5))}, angle: 90, spread: 100, origin: {{ x: Math.random(), y: -0.2 }}, gravity: 0.8, ticks: 400 }}); setTimeout(fire, {max(200, 2000 - (speed * 35))}); }}
            fire();
        }}; layer.appendChild(s);"""
    js_code += "</script>"
    components.html(js_code, height=0)

# --- 2. GENERATEUR TV PREVIEW ---
def get_tv_html(effect_js):
    return f"""<html><head><style>body {{ margin: 0; display: flex; justify-content: center; background: transparent; overflow: hidden; }} .tv {{ position: relative; width: 300px; height: 180px; background: #5D4037; border: 5px solid #3E2723; border-radius: 20px; display: flex; padding: 10px; box-sizing: border-box; }} .screen {{ flex: 1; background: black; border: 3px solid #222; border-radius: 10px; overflow: hidden; position: relative; }}</style></head><body><div class="tv"><div class="screen">{effect_js}</div></div></body></html>"""

# --- NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"

if est_admin:
    st.markdown("""<style>[data-testid="stHeader"] { visibility: hidden; } .block-container { padding-top: 5rem !important; } .fixed-header { position: fixed; top: 0; left: 0; width: 100%; background-color: #E2001A; color: white; text-align: center; padding: 15px 0; z-index: 999999; box-shadow: 0 4px 10px rgba(0,0,0,0.3); font-family: sans-serif; font-weight: bold; font-size: 22px; text-transform: uppercase; }</style>""", unsafe_allow_html=True)
    if "auth" not in st.session_state: st.session_state.auth = False
    if not st.session_state.auth:
        st.markdown("<div class='fixed-header'>🔐 ACCÈS RÉSERVÉ</div>", unsafe_allow_html=True)
        pwd = st.text_input("Mot de passe", type="password")
        if pwd == "ADMIN_LIVE_MASTER": st.session_state.auth = True; st.rerun()
    else:
        with st.sidebar:
            st.title("🎛️ RÉGIE")
            menu = st.radio("Menu", ["🔴 PILOTAGE LIVE", "⚙️ Paramètres", "📸 Médiathèque"])
        st.markdown(f"<div class='fixed-header'>{menu}</div>", unsafe_allow_html=True)

        if menu == "🔴 PILOTAGE LIVE":
            st.subheader("🎬 Séquenceur")
            bt1, bt2, bt3, bt4, bt5 = st.columns(5)
            cfg = st.session_state.config
            if bt1.button("🏠 ACCUEIL", use_container_width=True): cfg.update({"mode_affichage":"attente","reveal_resultats":False,"session_ouverte":False}); save_config(); st.rerun()
            if bt2.button("🗳️ VOTES ON", use_container_width=True): cfg.update({"mode_affichage":"votes","session_ouverte":True,"reveal_resultats":False}); save_config(); st.rerun()
            if bt3.button("🛑 VOTES OFF", use_container_width=True): cfg.update({"session_ouverte":False}); save_config(); st.rerun()
            if bt4.button("🏆 PODIUM", use_container_width=True): cfg.update({"mode_affichage":"votes","reveal_resultats":True,"session_ouverte":False,"timestamp_podium":time.time()}); save_config(); st.rerun()
            if bt5.button("📸 PHOTO LIVE", use_container_width=True): cfg.update({"mode_affichage":"photos_live","reveal_resultats":False}); save_config(); st.rerun()
            
            st.divider()
            c1, c2 = st.columns([1, 1.5])
            with c1:
                intensity = st.slider("🔢 Densité", 0, 50, cfg["effect_intensity"])
                speed = st.slider("🚀 Vitesse", 0, 50, cfg["effect_speed"])
                if intensity != cfg["effect_intensity"] or speed != cfg["effect_speed"]:
                    cfg["effect_intensity"] = intensity; cfg["effect_speed"] = speed; save_config(); st.rerun()
            with c2: components.html(get_tv_html("<div style='color:white;text-align:center;margin-top:60px;'>Régie Active</div>"), height=220)

elif est_utilisateur:
    st.markdown("<style>.stApp { background-color: black; color: white; }</style>", unsafe_allow_html=True)
    st.title("🗳️ Vote / 📸 Photo")
    photo = st.camera_input("Partagez un moment !")
    if photo:
        img = Image.open(photo)
        img.save(f"{LIVE_DIR}/img_{int(time.time())}_{random.randint(0,1000)}.jpg", "JPEG")
        st.success("Photo envoyée !")

else:
    # --- MUR SOCIAL ---
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=3000, key="wall")
    cfg = load_json(CONFIG_FILE, {})
    st.markdown("<style>body, .stApp { background-color: black; overflow: hidden; } [data-testid='stHeader'] { display: none; } .bubble { position: absolute; border-radius: 50%; border: 4px solid #E2001A; object-fit: cover; z-index: 1; pointer-events: none; }</style>", unsafe_allow_html=True)
    
    screen_key = "attente"
    if cfg.get("mode_affichage") == "photos_live": screen_key = "photos_live"
    elif cfg.get("reveal_resultats"): screen_key = "podium"
    
    inject_visual_effect(cfg.get("screen_effects", {}).get(screen_key, "Aucun"), cfg.get("effect_intensity", 25), cfg.get("effect_speed", 25))

    if cfg.get("mode_affichage") == "photos_live":
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:120px; margin-bottom:20px;">' if cfg.get("logo_b64") else ""
        
        st.markdown(f"""
            <div style="position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); z-index:1000; text-align:center; width:100%; pointer-events:none;">
                <div style="display:inline-block; pointer-events:auto; background: rgba(0,0,0,0.4); padding: 40px; border-radius: 40px; backdrop-filter: blur(5px);">
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
                    var i = document.createElement('img'); i.src = src; i.className = 'bubble';
                    var size = Math.random()*150 + 100;
                    i.style.width = size+'px'; i.style.height = size+'px';
                    i.style.left = Math.random()*90 + 'vw'; i.style.top = Math.random()*90 + 'vh';
                    window.parent.document.body.appendChild(i);
                    
                    // VITESSE RALENTIE : 0.1 à 0.3 pour un effet flottant doux
                    var vx = (Math.random() > 0.5 ? 1 : -1) * (Math.random() * 0.2 + 0.1);
                    var vy = (Math.random() > 0.5 ? 1 : -1) * (Math.random() * 0.2 + 0.1);
                    
                    function anim() {{
                        if(!i.parentElement) return;
                        var l = parseFloat(i.style.left);
                        var t = parseFloat(i.style.top);
                        
                        if(l <= 1 || l >= 94) vx *= -1;
                        if(t <= 1 || t >= 94) vy *= -1;
                        
                        i.style.left = (l + vx) + 'vw';
                        i.style.top = (t + vy) + 'vh';
                        requestAnimationFrame(anim);
                    }}
                    anim();
                }});
            </script>""", height=0)
    else:
        logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:150px; display:block; margin:auto;">' if cfg.get("logo_b64") else ""
        st.markdown(f"<div style='margin-top:150px; text-align:center;'>{logo_html}<h1 style='color:white; font-size:65px; margin-top:40px;'>{cfg.get('titre_mur')}</h1></div>", unsafe_allow_html=True)
