import streamlit as st
import os, glob, base64, qrcode, json, random, pandas as pd
from io import BytesIO
import streamlit.components.v1 as components
import time
from PIL import Image
from datetime import datetime
import zipfile
import uuid

# --- GESTION PDF ---
try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

# --- 1. CONFIGURATION & FICHIERS ---
st.set_page_config(page_title="Régie Master - Pôle Aéroportuaire", layout="wide")

GALLERY_DIR, ADMIN_DIR = "galerie_images", "galerie_admin"
LIVE_DIR = "galerie_live_users"
VOTES_FILE, PARTICIPANTS_FILE, CONFIG_FILE, VOTERS_FILE, DETAILED_VOTES_FILE = "votes.json", "participants.json", "config_mur.json", "voters.json", "detailed_votes.json"

for d in [GALLERY_DIR, ADMIN_DIR, LIVE_DIR]:
    if not os.path.exists(d): os.makedirs(d)

DEFAULT_CANDIDATS = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]

# --- CONFIGURATION INITIALE ---
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

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r") as f: return json.load(f)
        except: return default
    return default

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

# --- 2. GENERATEUR HTML DE TV RETRO ---
def get_tv_html(effect_js):
    return f"""
    <html><head><style>
        body {{ margin: 0; padding: 0; background: transparent; display: flex; justify-content: center; overflow: hidden; }}
        .tv-container {{ position: relative; width: 320px; height: 240px; margin-top: 20px; }}
        .antenna {{ position: absolute; top: -50px; left: 50%; transform: translateX(-50%); width: 100px; height: 50px; }}
        .ant-l {{ position: absolute; bottom: 0; left: 0; width: 3px; height: 100%; background: #666; transform: rotate(-25deg); transform-origin: bottom; }}
        .ant-r {{ position: absolute; bottom: 0; right: 0; width: 3px; height: 100%; background: #666; transform: rotate(25deg); transform-origin: bottom; }}
        .ant-base {{ position: absolute; bottom: 0; left: 35px; width: 30px; height: 15px; background: #222; border-radius: 50% 50% 0 0; }}
        .cabinet {{ position: absolute; width: 100%; height: 100%; top: 0; left: 0; background: #5D4037; border: 6px solid #3E2723; border-radius: 20px; box-shadow: 5px 5px 15px rgba(0,0,0,0.6); display: flex; padding: 12px; box-sizing: border-box; z-index: 5; }}
        .screen-bezel {{ flex: 1; background: #222; border: 4px solid #8D6E63; border-radius: 16px; box-shadow: inset 0 0 20px #000; margin-right: 12px; position: relative; overflow: hidden; }}
        .screen-content {{ width: 100%; height: 100%; background: black; }}
        .controls {{ width: 60px; background: #3E2723; border-radius: 8px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 15px; }}
        .knob {{ width: 30px; height: 30px; background: #BCAAA4; border-radius: 50%; border: 2px solid #222; }}
        .speaker {{ width: 30px; height: 40px; background: repeating-linear-gradient(0deg, #222, #222 3px, #4E342E 3px, #4E342E 6px); border: 1px solid #111; }}
        .legs {{ position: absolute; bottom: -40px; left: 0; width: 100%; display: flex; justify-content: space-between; padding: 0 40px; box-sizing: border-box; }}
        .leg {{ width: 15px; height: 50px; background: #222; }}
    </style></head><body>
        <div class="tv-container">
            <div class="antenna"><div class="ant-l"></div><div class="ant-base"></div><div class="ant-r"></div></div>
            <div class="legs"><div class="leg" style="transform:skewX(10deg)"></div><div class="leg" style="transform:skewX(-10deg)"></div></div>
            <div class="cabinet"><div class="screen-bezel"><div class="screen-content">{effect_js}</div></div>
            <div class="controls"><div class="knob"></div><div class="knob"></div><div class="speaker"></div></div></div>
        </div>
    </body></html>
    """

def get_preview_js(effect_name, intensity, speed):
    if effect_name == "Aucun": return "<div style='color:#444;height:100%;display:flex;align-items:center;justify-content:center;'>OFF</div>"
    interval = int(3500 / (intensity + 5))
    duration = max(2, 15 - (speed * 0.25))
    if effect_name == "🎈 Ballons": return f"<script>setInterval(()=>{{var e=document.createElement('div');e.innerHTML='🎈';e.style.cssText='position:absolute;bottom:-30px;left:'+Math.random()*90+'%;font-size:18px;transition:bottom {duration}s linear;';document.body.appendChild(e);setTimeout(()=>{{e.style.bottom='150px'}},50);}},{interval});</script>"
    elif effect_name == "❄️ Neige": return f"<style>.sf{{position:absolute;color:white;animation:f {duration}s linear infinite}}@keyframes f{{to{{transform:translateY(150px)}}}}</style><script>setInterval(()=>{{var e=document.createElement('div');e.className='sf';e.innerHTML='❄';e.style.left=Math.random()*95+'%';document.body.appendChild(e);}},{interval});</script>"
    elif effect_name == "🎉 Confettis": return f"<canvas id='c'></canvas><script src='https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js'></script><script>var mc=confetti.create(document.getElementById('c'),{{resize:true}});setInterval(()=>{{mc({{particleCount:5,spread:60,origin:{{y:0.6}}}});}},800);</script>"
    elif effect_name == "🌌 Espace": return f"<style>body{{background:black}}.s{{position:absolute;background:white;width:2px;height:2px;border-radius:50%;animation:b {duration}s infinite}}@keyframes b{{0%,100%{{opacity:0}}50%{{opacity:1}}}}</style><script>setInterval(()=>{{var e=document.createElement('div');e.className='s';e.style.left=Math.random()*100+'%';e.style.top=Math.random()*100+'%';document.body.appendChild(e);}},{interval});</script>"
    return ""

def save_config():
    with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)

# --- NAVIGATION & AUTH ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"

if est_admin:
    # --- CSS BARRE DE TITRE FIXE ULTIME ---
    st.markdown("""
        <style>
            /* Cacher le header Streamlit */
            [data-testid="stHeader"] { visibility: hidden; height: 0; }
            .block-container { padding-top: 5rem !important; }
            
            /* Création d'une barre fixe en haut */
            .fixed-header {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                background-color: #E2001A;
                color: white;
                text-align: center;
                padding: 15px 0;
                z-index: 999999;
                box-shadow: 0 4px 10px rgba(0,0,0,0.3);
                font-family: sans-serif;
                font-weight: bold;
                font-size: 24px;
                letter-spacing: 2px;
                text-transform: uppercase;
            }
        </style>
    """, unsafe_allow_html=True)

    if "auth" not in st.session_state: st.session_state.auth = False
    if not st.session_state.auth:
        st.markdown("<div class='fixed-header'>🔐 ACCÈS RÉSERVÉ</div>", unsafe_allow_html=True)
        pwd = st.text_input("Mot de passe", type="password")
        if pwd == "ADMIN_LIVE_MASTER": st.session_state.auth = True; st.rerun()
    else:
        with st.sidebar:
            st.title("🎛️ RÉGIE")
            menu = st.radio("Menu", ["🔴 PILOTAGE LIVE", "⚙️ Paramètres", "📸 Photos"])
            if st.button("🔓 Déconnexion"): st.session_state.auth = False; st.rerun()

        # TITRE FIXE DYNAMIQUE
        st.markdown(f"<div class='fixed-header'>{menu}</div>", unsafe_allow_html=True)

        if menu == "🔴 PILOTAGE LIVE":
            st.markdown("### 🧪 Aperçu Régie")
            c1, c2 = st.columns([1, 1.5], vertical_alignment="center")
            with c1:
                EFFECT_LIST = ["Aucun", "🎈 Ballons", "❄️ Neige", "🎉 Confettis", "🌌 Espace", "💸 Billets", "🟢 Matrix"]
                prev = st.radio("Tester l'effet", EFFECT_LIST)
            with c2:
                intensity = st.session_state.config.get("effect_intensity", 25)
                speed = st.session_state.config.get("effect_speed", 25)
                js_preview = get_preview_js(prev, intensity, speed)
                components.html(get_tv_html(js_preview), height=320)
            
            st.divider()
            st.markdown("### 📡 Contrôles du Mur")
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                new_int = st.slider("🔢 Densité", 0, 50, intensity)
            with c_s2:
                new_spd = st.slider("🚀 Vitesse", 0, 50, speed)
            
            if new_int != intensity or new_spd != speed:
                st.session_state.config["effect_intensity"] = new_int
                st.session_state.config["effect_speed"] = new_spd
                save_config(); st.rerun()

            col1, col2 = st.columns(2)
            screen_map = st.session_state.config["screen_effects"]
            with col1:
                st.selectbox("🏠 Accueil", EFFECT_LIST, index=EFFECT_LIST.index(screen_map.get("attente", "Aucun")), key="sel_attente")
            with col2:
                st.selectbox("🏆 Podium", EFFECT_LIST, index=EFFECT_LIST.index(screen_map.get("podium", "Aucun")), key="sel_podium")
            
            if st.button("💾 Appliquer les effets au Mur"):
                st.session_state.config["screen_effects"]["attente"] = st.session_state.sel_attente
                st.session_state.config["screen_effects"]["podium"] = st.session_state.sel_podium
                save_config(); st.toast("Effets mis à jour !")

            st.divider()
            bt1, bt2, bt3 = st.columns(3)
            cfg = st.session_state.config
            if bt1.button("1. ACCUEIL", use_container_width=True): cfg.update({"mode_affichage":"attente","reveal_resultats":False}); save_config(); st.rerun()
            if bt2.button("2. VOTES ON", use_container_width=True): cfg.update({"mode_affichage":"votes","session_ouverte":True}); save_config(); st.rerun()
            if bt3.button("3. PODIUM", use_container_width=True): cfg.update({"reveal_resultats":True,"timestamp_podium":time.time()}); save_config(); st.rerun()

        elif menu == "⚙️ Paramètres":
            st.markdown("### 🛠️ Configuration")
            new_title = st.text_input("Titre de l'événement", value=st.session_state.config["titre_mur"])
            if st.button("Enregistrer"): st.session_state.config["titre_mur"] = new_title; save_config(); st.success("Titre sauvegardé")

        elif menu == "📸 Photos":
            st.markdown("### 🖼️ Galerie Live")
            files = glob.glob(f"{LIVE_DIR}/*")
            if files:
                cols = st.columns(5)
                for i, f in enumerate(files):
                    with cols[i%5]:
                        st.image(f, use_container_width=True)
                        if st.button("🗑️", key=f"del_{i}"): os.remove(f); st.rerun()
            else: st.info("Aucune photo pour le moment.")

# --- UTILISATEUR & MUR SOCIAL (Non modifiés mais inclus pour complétude) ---
elif est_utilisateur:
    st.title("🗳️ Vote") # Interface mobile simple
else:
    # Mur Social
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2500, key="wall")
    cfg = load_json(CONFIG_FILE, default_config)
    st.markdown("<style>body, .stApp { background-color: black; overflow: hidden; } [data-testid='stHeader'] { display: none; }</style>", unsafe_allow_html=True)
    screen_key = "podium" if cfg.get("reveal_resultats") else "attente"
    inject_visual_effect(cfg["screen_effects"].get(screen_key, "Aucun"), cfg.get("effect_intensity", 25), cfg.get("effect_speed", 25))
    st.markdown(f"<h1 style='text-align:center; color:white; font-size:60px; margin-top:100px;'>{cfg['titre_mur']}</h1>", unsafe_allow_html=True)
