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

# --- FONCTION D'INJECTION D'EFFETS (MUR SOCIAL) ---
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
        layer.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:999999;overflow:hidden;';
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
            var e = doc.createElement('div'); var size = (Math.random() * 3 + 1) + 'px';
            e.style.cssText = 'position:absolute;background:white;border-radius:50%;width:'+size+';height:'+size+';left:'+Math.random()*100+'vw;top:'+Math.random()*100+'vh;opacity:0;transition:opacity 1s, transform {duration}s;';
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
            function fire() {{ window.parent.confetti({{ particleCount: {max(1, int(intensity*1.5))}, angle: 90, spread: 100, origin: {{ x: Math.random(), y: -0.2 }}, gravity: 0.8, ticks: 400 }}); setTimeout(fire, {max(200, 2000 - (speed * 35))}); }}
            fire();
        }}; layer.appendChild(s);"""
    elif effect_name == "🟢 Matrix":
        font_size = max(10, 40 - intensity)
        js_code += f"""
        var canvas = doc.createElement('canvas'); canvas.style.cssText = 'width:100%;height:100%;opacity:0.6;'; layer.appendChild(canvas);
        var ctx = canvas.getContext('2d'); canvas.width = window.parent.innerWidth; canvas.height = window.parent.innerHeight;
        var columns = canvas.width / {font_size}; var drops = []; for(var i=0; i<columns; i++) drops[i] = 1;
        function draw() {{ ctx.fillStyle = 'rgba(0, 0, 0, 0.1)'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.fillStyle = '#0F0'; ctx.font = '{font_size}px monospace'; for(var i=0; i<drops.length; i++) {{ ctx.fillText(Math.floor(Math.random()*2), i*{font_size}, drops[i]*{font_size}); if(drops[i]*{font_size} > canvas.height && Math.random() > 0.975) drops[i] = 0; drops[i]++; }} }}
        setInterval(draw, {max(20, 150 - (speed * 2.5))});"""
    js_code += "</script>"
    components.html(js_code, height=0)

# --- 2. GENERATEUR TV PREVIEW ---
def get_tv_html(effect_js):
    return f"""<html><head><style>body {{ margin: 0; display: flex; justify-content: center; background: transparent; overflow: hidden; }} .tv {{ position: relative; width: 300px; height: 230px; background: #5D4037; border: 5px solid #3E2723; border-radius: 20px; display: flex; padding: 10px; box-sizing: border-box; }} .screen {{ flex: 1; background: black; border: 3px solid #222; border-radius: 10px; overflow: hidden; position: relative; }} .controls {{ width: 50px; display: flex; flex-direction: column; align-items: center; justify-content: space-around; }} .knob {{ width: 25px; height: 25px; background: #AAA; border-radius: 50%; border: 2px solid #333; }}</style></head><body><div class="tv"><div class="screen">{effect_js}</div><div class="controls"><div class="knob"></div><div class="knob"></div></div></div></body></html>"""

def get_preview_js(effect_name, intensity, speed):
    if effect_name == "Aucun": return "<div style='color:white;text-align:center;margin-top:80px;'>OFF</div>"
    interval = int(3500 / (intensity + 5))
    duration = max(2, 10 - (speed * 0.15))
    if effect_name == "🎈 Ballons": return f"<script>setInterval(()=>{{var e=document.createElement('div');e.innerHTML='🎈';e.style.cssText='position:absolute;bottom:-30px;left:'+Math.random()*90+'%;font-size:20px;transition:bottom {duration}s linear;';document.body.appendChild(e);setTimeout(()=>{{e.style.bottom='250px'}},50);}},{interval});</script>"
    return "<div style='color:white;text-align:center;margin-top:80px;'>Aperçu Actif</div>"

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
                EFFECT_LIST = ["Aucun", "🎈 Ballons", "❄️ Neige", "🎉 Confettis", "🌌 Espace", "💸 Billets", "🟢 Matrix"]
                prev = st.radio("Tester l'effet", EFFECT_LIST)
                intensity = st.slider("🔢 Densité", 0, 50, cfg["effect_intensity"])
                speed = st.slider("🚀 Vitesse", 0, 50, cfg["effect_speed"])
                if intensity != cfg["effect_intensity"] or speed != cfg["effect_speed"]:
                    cfg["effect_intensity"] = intensity; cfg["effect_speed"] = speed; save_config(); st.rerun()
            with c2: components.html(get_tv_html(get_preview_js(prev, intensity, speed)), height=300)

            st.divider()
            st.subheader("⚙️ Config par écran")
            col1, col2 = st.columns(2)
            with col1:
                st.selectbox("Effet Accueil", EFFECT_LIST, index=EFFECT_LIST.index(cfg["screen_effects"].get("attente","Aucun")), key="s1")
                st.selectbox("Effet Votes", EFFECT_LIST, index=EFFECT_LIST.index(cfg["screen_effects"].get("votes_open","Aucun")), key="s2")
            with col2:
                st.selectbox("Effet Podium", EFFECT_LIST, index=EFFECT_LIST.index(cfg["screen_effects"].get("podium","Aucun")), key="s3")
                st.selectbox("Effet Photos", EFFECT_LIST, index=EFFECT_LIST.index(cfg["screen_effects"].get("photos_live","Aucun")), key="s4")
            if st.button("💾 SAUVEGARDER"):
                cfg["screen_effects"].update({"attente":st.session_state.s1, "votes_open":st.session_state.s2, "podium":st.session_state.s3, "photos_live":st.session_state.s4})
                save_config(); st.toast("Config OK")

elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, {})
    st.markdown("<style>.stApp { background-color: black; color: white; }</style>", unsafe_allow_html=True)
    if cfg.get("mode_affichage") == "photos_live":
        st.title("📸 Envoyer une photo")
        photo = st.camera_input("Smile !")
        if photo:
            img = Image.open(photo)
            img.save(f"{LIVE_DIR}/img_{int(time.time())}.jpg", "JPEG"); st.success("Envoyé !")
    else:
        st.title("🗳️ Vote")
        if cfg.get("session_ouverte"):
            choix = st.multiselect("Choisissez 3 services :", cfg.get("candidats", []))
            if len(choix) == 3 and st.button("Voter"):
                vts = load_json(VOTES_FILE, {})
                for c in choix: vts[c] = vts.get(c, 0) + 1
                with open(VOTES_FILE, "w") as f: json.dump(vts, f)
                st.success("Merci !")
        else: st.info("⌛ Attente...")

else:
    # --- MUR SOCIAL ---
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2500, key="wall")
    cfg = load_json(CONFIG_FILE, {})
    st.markdown("<style>body, .stApp { background-color: black; overflow: hidden; } [data-testid='stHeader'] { display: none; } .bubble { position: absolute; border-radius: 50%; border: 4px solid #E2001A; object-fit: cover; }</style>", unsafe_allow_html=True)
    
    screen_key = "attente"
    if cfg.get("mode_affichage") == "photos_live": screen_key = "photos_live"
    elif cfg.get("reveal_resultats"): screen_key = "podium"
    elif cfg.get("mode_affichage") == "votes": screen_key = "votes_open" if cfg.get("session_ouverte") else "votes_closed"
    
    inject_visual_effect(cfg.get("screen_effects", {}).get(screen_key, "Aucun"), cfg.get("effect_intensity", 25), cfg.get("effect_speed", 25))

    if cfg.get("mode_affichage") == "photos_live":
        # HEADER PHOTO
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:100px;">' if cfg.get("logo_b64") else ""
        
        st.markdown(f"""<div style="position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); z-index:1000; text-align:center; color:white; width:100%;">
            {logo_html}<h1 style="font-size:60px; margin:20px 0;">MUR PHOTOS LIVE</h1>
            <div style="background:white; display:inline-block; padding:15px; border-radius:20px; margin-bottom:20px;"><img src="data:image/png;base64,{qr_b64}" width="180"></div>
            <div style="background:#E2001A; padding:10px 30px; border-radius:50px; font-weight:bold; font-size:24px; display:inline-block; border:3px solid white;">📸 SCANNES POUR ENVOYER TA PHOTO</div>
        </div>""", unsafe_allow_html=True)
        
        # BULLES PHOTOS
        files = glob.glob(f"{LIVE_DIR}/*"); files.sort(key=os.path.getmtime, reverse=True)
        if files:
            img_list = [f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in files[:25]]
            components.html(f"""<script>
                var imgs = {json.dumps(img_list)};
                imgs.forEach(src => {{
                    var i = document.createElement('img'); i.src = src; i.className = 'bubble';
                    var size = Math.random()*150 + 100;
                    i.style.width = size+'px'; i.style.height = size+'px';
                    i.style.left = Math.random()*80 + 10 + 'vw'; i.style.top = Math.random()*80 + 10 + 'vh';
                    window.parent.document.body.appendChild(i);
                    var vx = (Math.random()-0.5)*2; var vy = (Math.random()-0.5)*2;
                    function anim() {{
                        var l = parseFloat(i.style.left); var t = parseFloat(i.style.top);
                        if(l<0 || l>90) vx*=-1; if(t<0 || t>90) vy*=-1;
                        i.style.left = (l+vx)+'vw'; i.style.top = (t+vy)+'vh';
                        requestAnimationFrame(anim);
                    }} anim();
                }});
            </script>""", height=0)
    else:
        # AFFICHAGE TITRE NORMAL
        logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:150px; display:block; margin:auto;">' if cfg.get("logo_b64") else ""
        st.markdown(f"<div style='margin-top:100px;'>{logo_html}<h1 style='text-align:center; color:white; font-size:65px; margin-top:40px;'>{cfg.get('titre_mur')}</h1></div>", unsafe_allow_html=True)
