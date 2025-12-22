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

# --- CHARGEMENT CONFIG ---
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
            e.style.cssText = 'position:absolute;bottom:-100px;left:'+Math.random()*100+'vw;font-size:'+(Math.random()*40+20)+'px;opacity:'+(Math.random()*0.5+0.5)+';transition:bottom {duration}s linear,left {duration}s ease-in-out;';
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
    """
    if effect_name == "🎈 Ballons": js_code += f"setInterval(createBalloon, {interval});"
    elif effect_name == "❄️ Neige": js_code += f"setInterval(createSnow, {interval});"
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

# --- NAVIGATION & AUTH ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"

if est_admin:
    st.markdown("""<style>[data-testid="stHeader"] { visibility: hidden; height: 0; } .block-container { padding-top: 5rem !important; } .fixed-header { position: fixed; top: 0; left: 0; width: 100%; background-color: #E2001A; color: white; text-align: center; padding: 15px 0; z-index: 999999; box-shadow: 0 4px 10px rgba(0,0,0,0.3); font-family: sans-serif; font-weight: bold; font-size: 24px; letter-spacing: 2px; text-transform: uppercase; }</style>""", unsafe_allow_html=True)
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
            # --- SECTEUR 1: SEQUENCER (DÉPLACÉ EN HAUT) ---
            st.subheader("🎬 Séquenceur de Diffusion")
            bt1, bt2, bt3, bt4, bt5 = st.columns(5)
            cfg = st.session_state.config
            if bt1.button("🏠 1. ACCUEIL", use_container_width=True): cfg.update({"mode_affichage":"attente","reveal_resultats":False,"session_ouverte":False}); save_config(); st.rerun()
            if bt2.button("🗳️ 2. VOTES ON", use_container_width=True): cfg.update({"mode_affichage":"votes","session_ouverte":True,"reveal_resultats":False}); save_config(); st.rerun()
            if bt3.button("🛑 3. VOTES OFF", use_container_width=True): cfg.update({"session_ouverte":False}); save_config(); st.rerun()
            if bt4.button("🏆 4. PODIUM", use_container_width=True): cfg.update({"mode_affichage":"votes","reveal_resultats":True,"session_ouverte":False,"timestamp_podium":time.time()}); save_config(); st.rerun()
            if bt5.button("📸 5. PHOTO LIVE", use_container_width=True): cfg.update({"mode_affichage":"photos_live"}); save_config(); st.rerun()
            
            st.divider()

            # --- SECTEUR 2: LABORATOIRE ---
            st.markdown("### 🧪 Laboratoire & Visuels")
            c1, c2 = st.columns([1, 1.5], gap="medium", vertical_alignment="center")
            with c1:
                EFFECT_LIST = ["Aucun", "🎈 Ballons", "❄️ Neige", "🎉 Confettis", "🌌 Espace", "💸 Billets", "🟢 Matrix"]
                if "preview_selected" not in st.session_state: st.session_state.preview_selected = "Aucun"
                prev = st.radio("Tester l'effet", EFFECT_LIST, index=EFFECT_LIST.index(st.session_state.preview_selected))
                st.session_state.preview_selected = prev
            with c2:
                intensity = st.session_state.config.get("effect_intensity", 25)
                speed = st.session_state.config.get("effect_speed", 25)
                js_preview = get_preview_js(prev, intensity, speed)
                components.html(get_tv_html(js_preview), height=320)
            
            st.divider()

            # --- SECTEUR 3: REGLAGES ---
            st.markdown("### 📡 Contrôles Globaux des Effets")
            cp1, cp2 = st.columns(2)
            with cp1: intensity = st.slider("🔢 Densité (Quantité)", 0, 50, intensity)
            with cp2: speed = st.slider("🚀 Vitesse (Animation)", 0, 50, speed)
            if intensity != st.session_state.config["effect_intensity"] or speed != st.session_state.config["effect_speed"]:
                st.session_state.config["effect_intensity"] = intensity
                st.session_state.config["effect_speed"] = speed; save_config(); st.rerun()

            col1, col2 = st.columns(2)
            screen_map = st.session_state.config["screen_effects"]
            with col1:
                st.selectbox("🏠 Effet : Accueil", EFFECT_LIST, index=EFFECT_LIST.index(screen_map.get("attente", "Aucun")), key="sel_attente")
                st.selectbox("🗳️ Effet : Votes Ouverts", EFFECT_LIST, index=EFFECT_LIST.index(screen_map.get("votes_open", "Aucun")), key="sel_open")
            with col2:
                st.selectbox("🏆 Effet : Podium", EFFECT_LIST, index=EFFECT_LIST.index(screen_map.get("podium", "Aucun")), key="sel_podium")
                st.selectbox("📸 Effet : Mur Photos", EFFECT_LIST, index=EFFECT_LIST.index(screen_map.get("photos_live", "Aucun")), key="sel_photos")
            
            if st.button("💾 SAUVEGARDER CONFIG EFFETS"):
                st.session_state.config["screen_effects"].update({"attente": st.session_state.sel_attente, "votes_open": st.session_state.sel_open, "podium": st.session_state.sel_podium, "photos_live": st.session_state.sel_photos})
                save_config(); st.toast("Configuration du mur mise à jour !")

        elif menu == "⚙️ Paramètres":
            st.title("Paramètres Généraux")
            new_title = st.text_input("Titre du Mur Social", value=st.session_state.config["titre_mur"])
            if st.button("Enregistrer"): st.session_state.config["titre_mur"] = new_title; save_config(); st.success("Titre sauvegardé")
            st.divider()
            st.subheader("Candidats / Services")
            df_cands = pd.DataFrame(st.session_state.config["candidats"], columns=["Nom du Candidat"])
            edited = st.data_editor(df_cands, num_rows="dynamic", use_container_width=True)
            if st.button("💾 Sauver Liste Candidats"): st.session_state.config["candidats"] = edited["Nom du Candidat"].tolist(); save_config(); st.rerun()

        elif menu == "📸 Médiathèque":
            st.title("Gestion des Photos")
            files = glob.glob(f"{LIVE_DIR}/*")
            if files:
                cols = st.columns(5)
                for i, f in enumerate(files):
                    with cols[i%5]:
                        st.image(f, use_container_width=True)
                        if st.button("🗑️ Supprimer", key=f"del_{i}"): os.remove(f); st.rerun()
            else: st.info("Aucune photo reçue.")

# --- UTILISATEUR (MOBILE) ---
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, {})
    st.markdown("<style>.stApp { background-color: black; color: white; }</style>", unsafe_allow_html=True)
    if cfg.get("mode_affichage") == "photos_live":
        st.title("📸 Envoyez votre photo !")
        photo = st.camera_input("Smile !")
        if photo:
            img = Image.open(photo)
            img.save(f"{LIVE_DIR}/img_{int(time.time())}.jpg", "JPEG"); st.success("Photo envoyée au Mur !")
    else:
        if not cfg.get("session_ouverte"): st.info("⌛ En attente du lancement des votes...")
        else:
            if st.session_state.get("a_vote", False): st.success("Merci ! Votre vote a été enregistré.")
            else:
                st.title("🗳️ Vote Transdev")
                choix = st.multiselect("Choisissez vos 3 favoris :", cfg.get("candidats", []))
                if len(choix) == 3 and st.button("VALIDER MON VOTE"):
                    vts = load_json(VOTES_FILE, {}); pts = [5, 3, 1]
                    for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                    with open(VOTES_FILE, "w") as f: json.dump(vts, f)
                    st.session_state.a_vote = True; st.rerun()

# --- MUR SOCIAL ---
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2500, key="wall")
    cfg = load_json(CONFIG_FILE, {})
    st.markdown("<style>body, .stApp { background-color: black; overflow: hidden; } [data-testid='stHeader'] { display: none; }</style>", unsafe_allow_html=True)
    
    # Choix de l'effet à injecter
    screen_key = "attente"
    if cfg.get("mode_affichage") == "photos_live": screen_key = "photos_live"
    elif cfg.get("reveal_resultats"): screen_key = "podium"
    elif cfg.get("mode_affichage") == "votes": screen_key = "votes_open" if cfg.get("session_ouverte") else "votes_closed"
    
    inject_visual_effect(cfg.get("screen_effects", {}).get(screen_key, "Aucun"), cfg.get("effect_intensity", 25), cfg.get("effect_speed", 25))
    
    if cfg.get("mode_affichage") == "photos_live":
        st.markdown("<h1 style='text-align:center; color:white; font-size:60px;'>📸 MUR PHOTO</h1>", unsafe_allow_html=True)
        files = glob.glob(f"{LIVE_DIR}/*"); files.sort(key=os.path.getmtime, reverse=True)
        if files:
            img_list = [f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in files[:12]]
            components.html(f"""<div style="display:flex;flex-wrap:wrap;justify-content:center;gap:15px;padding:20px;"></div><script>var imgs={json.dumps(img_list)}; imgs.forEach(s=>{{var i=document.createElement('img');i.src=s;i.style.height='250px';i.style.borderRadius='15px';i.style.border='4px solid #E2001A';document.body.firstChild.appendChild(i);}});</script>""", height=800)
    else:
        st.markdown(f"<h1 style='text-align:center; color:white; font-size:60px; margin-top:100px;'>{cfg.get('titre_mur', '')}</h1>", unsafe_allow_html=True)
