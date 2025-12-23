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
default_config = {
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
        "attente": "Aucun",
        "votes_open": "Aucun",
        "votes_closed": "Aucun",
        "podium": "🎉 Confettis",
        "photos_live": "Aucun"
    }
}

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r") as f: return json.load(f)
        except: return default
    return default

# --- GESTION ÉTAT SESSION ---
if "config" not in st.session_state:
    st.session_state.config = load_json(CONFIG_FILE, default_config)

# --- FONCTION D'INJECTION D'EFFETS (MUR SOCIAL) ---
def inject_visual_effect(effect_name, intensity, speed):
    if effect_name == "Aucun":
        components.html("""<script>var old = window.parent.document.getElementById('effect-layer'); if(old) old.remove();</script>""", height=0)
        return

    duration = max(2, 20 - (speed * 0.35))
    interval = int(4000 / (intensity + 5))
    
    js_base = """
    <script>
        var doc = window.parent.document;
        var old = doc.getElementById('effect-layer');
        if(old) old.remove();
        var layer = doc.createElement('div');
        layer.id = 'effect-layer';
        layer.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:999999;overflow:hidden;';
        doc.body.appendChild(layer);
    """

    if effect_name == "🎈 Ballons":
        js_code = js_base + f"""
        function create() {{
            var e = doc.createElement('div');
            e.innerHTML = '🎈';
            e.style.cssText = 'position:absolute;bottom:-100px;left:'+Math.random()*100+'vw;font-size:'+(Math.random()*40+20)+'px;transition:bottom {duration}s linear;';
            layer.appendChild(e);
            setTimeout(() => {{ e.style.bottom = '110vh'; }}, 50);
            setTimeout(() => {{ e.remove(); }}, {duration * 1000});
        }}
        setInterval(create, {interval});
        </script>"""

    elif effect_name == "❄️ Neige":
        js_code = js_base + f"""
        function create() {{
            var e = doc.createElement('div');
            e.innerHTML = '❄';
            e.style.cssText = 'position:absolute;top:-50px;left:'+Math.random()*100+'vw;color:white;font-size:'+(Math.random()*20+10)+'px;transition:top {duration}s linear;';
            layer.appendChild(e);
            setTimeout(() => {{ e.style.top = '110vh'; }}, 50);
            setTimeout(() => {{ e.remove(); }}, {duration * 1000});
        }}
        setInterval(create, {interval});
        </script>"""

    elif effect_name == "🎉 Confettis":
        count = max(1, int(intensity * 1.5))
        fire_rate = max(150, 2000 - (speed * 35))
        js_code = js_base + f"""
        var s = doc.createElement('script');
        s.src = "https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js";
        s.onload = function() {{
            function fire() {{
                window.parent.confetti({{ particleCount: {count}, angle: 90, spread: 100, origin: {{ x: Math.random(), y: -0.2 }}, gravity: 0.8, ticks: 400 }});
                setTimeout(fire, {fire_rate});
            }}
            fire();
        }};
        layer.appendChild(s);
        </script>"""

    elif effect_name == "🌌 Espace":
        js_code = js_base + f"""
        function create() {{
            var e = doc.createElement('div');
            var size = (Math.random() * 3 + 1) + 'px';
            e.style.cssText = 'position:absolute;background:white;border-radius:50%;width:'+size+';height:'+size+';left:'+Math.random()*100+'vw;top:'+Math.random()*100+'vh;opacity:0;transition:opacity {duration/2}s; box-shadow: 0 0 5px white;';
            layer.appendChild(e);
            setTimeout(() => {{ e.style.opacity = '1'; }}, 50);
            setTimeout(() => {{ e.style.opacity = '0'; }}, {duration * 800});
            setTimeout(() => {{ e.remove(); }}, {duration * 1000});
        }}
        setInterval(create, {interval});
        </script>"""

    elif effect_name == "💸 Billets":
        js_code = js_base + f"""
        function create() {{
            var e = doc.createElement('div');
            e.innerHTML = '💸';
            e.style.cssText = 'position:absolute;top:-50px;left:'+Math.random()*100+'vw;font-size:30px;transition:top {duration}s linear;';
            layer.appendChild(e);
            setTimeout(() => {{ e.style.top = '110vh'; }}, 50);
            setTimeout(() => {{ e.remove(); }}, {duration * 1000});
        }}
        setInterval(create, {interval});
        </script>"""

    elif effect_name == "🟢 Matrix":
        font_size = max(10, 40 - intensity)
        refresh = max(20, 150 - (speed * 2.5))
        js_code = js_base + f"""
        var canvas = doc.createElement('canvas');
        canvas.style.cssText = 'width:100%;height:100%;opacity:0.6;';
        layer.appendChild(canvas);
        var ctx = canvas.getContext('2d');
        canvas.width = window.parent.innerWidth; canvas.height = window.parent.innerHeight;
        var columns = canvas.width / {font_size}; var drops = [];
        for(var i=0; i<columns; i++) drops[i] = 1;
        function draw() {{
            ctx.fillStyle = 'rgba(0, 0, 0, 0.1)'; ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#0F0'; ctx.font = '{font_size}px monospace';
            for(var i=0; i<drops.length; i++) {{
                ctx.fillText(Math.floor(Math.random()*2), i*{font_size}, drops[i]*{font_size});
                if(drops[i]*{font_size} > canvas.height && Math.random() > 0.975) drops[i] = 0;
                drops[i]++;
            }}
        }}
        setInterval(draw, {refresh});
        </script>"""
    
    components.html(js_code, height=0)

# --- 2. GENERATEUR HTML DE TV RETRO (PREVIEW ADMIN) ---
def get_tv_html(effect_js):
    return f"""
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 0; background: transparent; font-family: sans-serif; display: flex; justify-content: center; overflow: hidden; }}
            .tv-container {{ position: relative; width: 320px; height: 240px; margin: 0 auto; }}
            .antenna {{ position: absolute; top: -50px; left: 50%; transform: translateX(-50%); width: 100px; height: 50px; z-index: 0; }}
            .ant-l {{ position: absolute; bottom: 0; left: 0; width: 3px; height: 100%; background: #666; transform: rotate(-25deg); transform-origin: bottom; }}
            .ant-r {{ position: absolute; bottom: 0; right: 0; width: 3px; height: 100%; background: #666; transform: rotate(25deg); transform-origin: bottom; }}
            .ant-base {{ position: absolute; bottom: 0; left: 35px; width: 30px; height: 15px; background: #222; border-radius: 50% 50% 0 0; }}
            .cabinet {{
                position: absolute; width: 100%; height: 100%; top: 0; left: 0;
                background: #5D4037; border: 6px solid #3E2723; border-radius: 20px;
                box-shadow: 5px 5px 15px rgba(0,0,0,0.6); z-index: 5;
                display: flex; padding: 12px; box-sizing: border-box;
            }}
            .screen-bezel {{
                flex: 1; background: #222; border: 4px solid #8D6E63; border-radius: 16px;
                box-shadow: inset 0 0 20px #000; margin-right: 12px;
                position: relative; overflow: hidden;
            }}
            .screen-content {{ width: 100%; height: 100%; background: black; position: relative; overflow: hidden; }}
            .controls {{
                width: 60px; background: #3E2723; border-radius: 8px;
                display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 15px; padding: 5px 0;
            }}
            .knob {{ width: 30px; height: 30px; background: #BCAAA4; border-radius: 50%; border: 2px solid #222; box-shadow: 1px 2px 3px rgba(0,0,0,0.5); }}
            .speaker {{ width: 30px; height: 40px; background: repeating-linear-gradient(0deg, #222, #222 3px, #4E342E 3px, #4E342E 6px); border: 1px solid #111; border-radius: 4px; }}
            .legs {{ position: absolute; bottom: -40px; left: 0; width: 100%; display: flex; justify-content: space-between; padding: 0 40px; box-sizing: border-box; z-index: 1; }}
            .leg {{ width: 15px; height: 50px; background: #222; }}
            .leg-l {{ transform: skewX(10deg); }} .leg-r {{ transform: skewX(-10deg); }}
        </style>
    </head>
    <body>
        <div class="tv-container">
            <div class="antenna"><div class="ant-l"></div><div class="ant-base"></div><div class="ant-r"></div></div>
            <div class="legs"><div class="leg leg-l"></div><div class="leg leg-r"></div></div>
            <div class="cabinet">
                <div class="screen-bezel">
                    <div class="screen-content" id="preview-screen">
                        {effect_js}
                    </div>
                </div>
                <div class="controls">
                    <div class="knob" style="transform: rotate(45deg);"></div>
                    <div class="knob" style="transform: rotate(-20deg);"></div>
                    <div class="speaker"></div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

# --- 3. GENERATEUR JS POUR PREVIEW (DANS TV ADMIN) ---
def get_preview_js(effect_name, intensity, speed):
    if effect_name == "Aucun":
        return "<div style='width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:#444;font-size:12px;'>OFF</div>"
    
    interval = int(3500 / (intensity + 5))
    duration = max(2, 15 - (speed * 0.25))

    if effect_name == "🎈 Ballons":
        return f"""<script>const sc=document.getElementById('preview-screen'); setInterval(()=>{{const e=document.createElement('div');e.innerHTML='🎈';e.style.cssText='position:absolute;bottom:-30px;left:'+Math.random()*90+'%;font-size:18px;transition:bottom {duration}s linear;';sc.appendChild(e);setTimeout(()=>{{e.style.bottom='150px'}},50);setTimeout(()=>{{e.remove()}},{duration*1000})}},{interval});</script>"""
    elif effect_name == "❄️ Neige":
        return f"""<style>.sf{{position:absolute;color:white;animation:f {duration}s linear infinite}}@keyframes f{{to{{transform:translateY(150px)}}}}</style><script>const sc=document.getElementById('preview-screen');setInterval(()=>{{const e=document.createElement('div');e.className='sf';e.innerHTML='❄';e.style.left=Math.random()*90+'%';e.style.top='-10px';e.style.fontSize=(Math.random()*10+5)+'px';sc.appendChild(e);setTimeout(()=>{{e.remove()}},{duration*1000})}},{interval});</script>"""
    elif effect_name == "🎉 Confettis":
        return f"""<canvas id="cf-cv" style="width:100%;height:100%;"></canvas><script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script><script>const cv=document.getElementById('cf-cv'); const mc=confetti.create(cv,{{resize:true}}); setInterval(()=>{{mc({{particleCount:Math.max(1, {intensity}/5),spread:60,origin:{{y:0.6}},colors:['#E2001A','#fff']}});}},800);</script>"""
    elif effect_name == "🌌 Espace":
        return f"""<style>.st-p{{position:absolute;background:white;border-radius:50%;opacity:0;box-shadow: 0 0 3px white; animation: blink-p {duration}s infinite;}} @keyframes blink-p {{ 0%, 100% {{ opacity: 0; }} 50% {{ opacity: 1; }} }}</style><script>const sc=document.getElementById('preview-screen');setInterval(()=>{{const e=document.createElement('div');e.className='st-p';e.style.left=Math.random()*100+'%';e.style.top=Math.random()*100+'%';e.style.width='2px';e.style.height='2px';sc.appendChild(e);setTimeout(()=>{{e.remove()}},{duration*1000})}},{interval});</script>"""
    elif effect_name == "💸 Billets":
        return f"""<script>const sc=document.getElementById('preview-screen'); setInterval(()=>{{const e=document.createElement('div');e.innerHTML='💸';e.style.cssText='position:absolute;top:-30px;left:'+Math.random()*90+'%;font-size:18px;';sc.appendChild(e);e.animate([{{transform:'translateY(0)'}},{{transform:'translateY(160px)'}}],{{duration:{duration*1000}}});setTimeout(()=>{{e.remove()}},{duration*1000})}},{interval});</script>"""
    elif effect_name == "🟢 Matrix":
        font_s = max(8, 25 - (intensity/4))
        ref = max(20, 150 - (speed*2))
        return f"""<canvas id="mx-cv" style="width:100%;height:100%;"></canvas><script>const v=document.getElementById('mx-cv');const x=v.getContext('2d');v.width=180;v.height=140;const cl=v.width/{font_s};const r=Array(Math.floor(cl)).fill(1);setInterval(()=>{{x.fillStyle='rgba(0,0,0,0.1)';x.fillRect(0,0,v.width,v.height);x.fillStyle='#0F0';x.font='{font_s}px mono';r.forEach((y,i)=>{{x.fillText(Math.floor(Math.random()*2),i*{font_s},y*{font_s});if(y*{font_s}>v.height&&Math.random()>0.9)r[i]=0;r[i]++}})}},{ref});</script>"""
    return ""

# --- FONCTIONS UTILITAIRES ---
def save_config():
    with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)

# --- NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"

# --- ADMINISTRATION ---
if est_admin:
    # CSS POUR FIGER LES TITRES (STICKY)
    st.markdown("""
        <style>
            /* Cible tous les titres h1 (st.title) pour les figer */
            div[data-testid="stVerticalBlock"] > div:has(h1) {
                position: sticky;
                top: 0;
                background-color: white;
                z-index: 1000;
                padding: 1rem 0;
                border-bottom: 2px solid #f0f2f6;
            }
            @media (prefers-color-scheme: dark) {
                div[data-testid="stVerticalBlock"] > div:has(h1) {
                    background-color: #0e1117;
                    border-bottom: 2px solid #262730;
                }
            }
        </style>
    """, unsafe_allow_html=True)

    if "auth" not in st.session_state: st.session_state["auth"] = False
    
    if not st.session_state["auth"]:
        st.markdown("<br><br><h1 style='text-align:center;'>🔐 ACCÈS RÉGIE</h1>", unsafe_allow_html=True)
        col_c, col_p, col_d = st.columns([1,2,1])
        with col_p:
            pwd = st.text_input("Mot de passe", type="password")
            if pwd == "ADMIN_LIVE_MASTER":
                st.session_state["auth"] = True; st.rerun()
    else:
        with st.sidebar:
            st.title("🎛️ RÉGIE MASTER")
            menu = st.radio("Navigation :", ["🔴 PILOTAGE LIVE", "⚙️ Paramétrage", "📸 Médiathèque", "📊 Data"], label_visibility="collapsed")
            if st.button("🔓 Déconnexion", use_container_width=True):
                st.session_state["auth"] = False; st.rerun()

        if menu == "🔴 PILOTAGE LIVE":
            st.title("🔴 COCKPIT LIVE")
            st.markdown("### 🧪 Laboratoire & Visuels")
            c_test_sel, c_test_tv = st.columns([1, 1.5], gap="medium", vertical_alignment="center")
            with c_test_sel:
                st.markdown("#### 1. Choix Aperçu")
                EFFECT_NAMES_LIST = ["Aucun", "🎈 Ballons", "❄️ Neige", "🎉 Confettis", "🌌 Espace", "💸 Billets", "🟢 Matrix"]
                if "preview_selected" not in st.session_state: st.session_state.preview_selected = "Aucun"
                prev_sel = st.radio("Effet", EFFECT_NAMES_LIST, key="radio_prev", label_visibility="collapsed")
                st.session_state.preview_selected = prev_sel
            with c_test_tv:
                cur_int = st.session_state.config.get("effect_intensity", 25)
                cur_spd = st.session_state.config.get("effect_speed", 25)
                js_preview = get_preview_js(st.session_state.preview_selected, cur_int, cur_spd)
                components.html(get_tv_html(js_preview), height=350)
            
            st.divider()
            st.markdown("### 📡 Diffusion Live")
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                intensity = st.slider("🔢 Densité", 0, 50, st.session_state.config.get("effect_intensity", 25))
            with c_p2:
                speed = st.slider("🚀 Vitesse", 0, 50, st.session_state.config.get("effect_speed", 25))

            if intensity != st.session_state.config.get("effect_intensity") or speed != st.session_state.config.get("effect_speed"):
                st.session_state.config["effect_intensity"] = intensity
                st.session_state.config["effect_speed"] = speed
                save_config(); st.rerun()

            c_1, c_2 = st.columns(2)
            screen_map = st.session_state.config["screen_effects"]
            def update_eff(key_w, key_c):
                st.session_state.config["screen_effects"][key_c] = st.session_state[key_w]
                save_config()

            with c_1:
                st.markdown("#### 🏠 Accueil")
                st.selectbox("Effet", EFFECT_NAMES_LIST, index=EFFECT_NAMES_LIST.index(screen_map.get("attente", "Aucun")), key="s_attente", on_change=update_eff, args=("s_attente", "attente"))
                st.markdown("#### 🗳️ Votes Ouverts")
                st.selectbox("Effet", EFFECT_NAMES_LIST, index=EFFECT_NAMES_LIST.index(screen_map.get("votes_open", "Aucun")), key="s_open", on_change=update_eff, args=("s_open", "votes_open"))
            with c_2:
                st.markdown("#### 🏆 Podium")
                st.selectbox("Effet", EFFECT_NAMES_LIST, index=EFFECT_NAMES_LIST.index(screen_map.get("podium", "Aucun")), key="s_podium", on_change=update_eff, args=("s_podium", "podium"))
                st.markdown("#### 📸 Mur Photos")
                st.selectbox("Effet", EFFECT_NAMES_LIST, index=EFFECT_NAMES_LIST.index(screen_map.get("photos_live", "Aucun")), key="s_photos", on_change=update_eff, args=("s_photos", "photos_live"))

            st.divider()
            c1, c2, c3, c4 = st.columns(4)
            cfg = st.session_state.config
            if c1.button("1. ACCUEIL", use_container_width=True): cfg.update({"mode_affichage":"attente","session_ouverte":False,"reveal_resultats":False}); save_config(); st.rerun()
            if c2.button("2. VOTES ON", use_container_width=True): cfg.update({"mode_affichage":"votes","session_ouverte":True,"reveal_resultats":False}); save_config(); st.rerun()
            if c3.button("3. VOTES OFF", use_container_width=True): cfg.update({"session_ouverte":False}); save_config(); st.rerun()
            if c4.button("4. PODIUM", use_container_width=True): cfg.update({"mode_affichage":"votes","reveal_resultats":True,"session_ouverte":False,"timestamp_podium":time.time()}); save_config(); st.rerun()

        elif menu == "⚙️ Paramétrage":
            st.title("⚙️ Paramétrage")
            new_t = st.text_input("Titre", value=st.session_state.config["titre_mur"])
            if st.button("Sauver Titre"): st.session_state.config["titre_mur"] = new_t; save_config(); st.rerun()
            up_l = st.file_uploader("Logo", type=["png", "jpg"])
            if up_l:
                b64 = base64.b64encode(up_l.read()).decode()
                st.session_state.config["logo_b64"] = b64; save_config(); st.success("OK"); st.rerun()

        elif menu == "📸 Médiathèque":
            st.title("📸 Médiathèque")
            files = glob.glob(f"{LIVE_DIR}/*")
            if files:
                cols = st.columns(6)
                for i, f in enumerate(files):
                    with cols[i%6]:
                        st.image(f, use_container_width=True)
                        if st.button("🗑️", key=f"d_{i}"): os.remove(f); st.rerun()

        elif menu == "📊 Data":
            st.title("📊 Data")
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                df = pd.DataFrame(list(v_data.items()), columns=['Candidat', 'Points']).sort_values('Points', ascending=False)
                st.dataframe(df, use_container_width=True)

# --- UTILISATEUR (MOBILE) ---
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, default_config)
    st.markdown("<style>.stApp { background-color: black !important; color: white !important; }</style>", unsafe_allow_html=True)
    if cfg["mode_affichage"] == "photos_live":
        st.title("📸 Mur Photos")
        photo = st.camera_input("Prendre une photo")
        if photo:
            img = Image.open(photo)
            img.save(f"{LIVE_DIR}/img_{int(time.time())}.jpg", "JPEG"); st.success("Envoyé !"); st.balloons()
    else:
        if not cfg["session_ouverte"]: st.warning("⌛ Attente des votes...")
        else:
            if st.session_state.get("a_vote", False): st.success("Merci !")
            else:
                st.title("🗳️ Vote Transdev")
                choix = st.multiselect("Choisissez vos 3 favoris :", cfg["candidats"])
                if len(choix) == 3 and st.button("VALIDER"):
                    vts = load_json(VOTES_FILE, {}); pts = [5, 3, 1]
                    for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                    with open(VOTES_FILE, "w") as f: json.dump(vts, f)
                    st.session_state.a_vote = True; st.rerun()

# --- MUR SOCIAL ---
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2500, key="wall_ref")
    st.markdown("""<style>body, .stApp { background-color: black !important; overflow: hidden; } [data-testid='stHeader'] { display: none !important; } .block-container { padding: 0 !important; max-width: 100% !important; }</style>""", unsafe_allow_html=True)
    
    cfg = load_json(CONFIG_FILE, default_config)
    
    screen_key = "attente"
    if cfg["mode_affichage"] == "attente": screen_key = "attente"
    elif cfg["mode_affichage"] == "photos_live": screen_key = "photos_live"
    elif cfg["reveal_resultats"]: screen_key = "podium"
    elif cfg["mode_affichage"] == "votes":
        screen_key = "votes_open" if cfg["session_ouverte"] else "votes_closed"
    
    eff = cfg["screen_effects"].get(screen_key, "Aucun")
    inject_visual_effect(eff, cfg.get("effect_intensity", 25), cfg.get("effect_speed", 25))

    if cfg["mode_affichage"] != "photos_live":
        if cfg.get("logo_b64"): st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:80px;"></div>', unsafe_allow_html=True)
        st.markdown(f'<h1 style="text-align:center; color:white; font-size:40px;">{cfg["titre_mur"]}</h1>', unsafe_allow_html=True)

    if cfg["mode_affichage"] == "attente":
        st.markdown('<div style="text-align:center; color:white; margin-top:20vh;"><h2>Événement en cours...</h2></div>', unsafe_allow_html=True)
    
    elif cfg["mode_affichage"] == "photos_live":
        st.markdown('<h1 style="text-align:center; color:white;">📸 LIVE</h1>', unsafe_allow_html=True)
        files = glob.glob(f"{LIVE_DIR}/*"); files.sort(key=os.path.getmtime, reverse=True)
        if files:
            img_list = []
            for f in files[:12]:
                with open(f, "rb") as b: img_list.append(f"data:image/jpeg;base64,{base64.b64encode(b.read()).decode()}")
            js_imgs = json.dumps(img_list)
            components.html(f"""<div id="grid" style="display:flex;flex-wrap:wrap;justify-content:center;gap:15px;padding:20px;"></div><script>var imgs={js_imgs}; var g=document.getElementById('grid'); imgs.forEach(s=>{{var i=document.createElement('img');i.src=s;i.style.height='250px';i.style.borderRadius='15px';i.style.border='4px solid #E2001A';g.appendChild(i);}});</script>""", height=800)

    elif cfg["mode_affichage"] == "votes" and not cfg["reveal_resultats"]:
        if cfg["session_ouverte"]:
            host = st.context.headers.get('host', 'localhost')
            qr = qrcode.make(f"https://{host}/?mode=vote")
            buf = BytesIO(); qr.save(buf, format="PNG")
            st.markdown(f'<div style="text-align:center; background:white; width:220px; margin:40px auto; padding:15px; border-radius:20px;"><img src="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}" width="190"><br><b style="color:black; font-size:20px;">VOTEZ ICI</b></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align:center; color:#E2001A; margin-top:100px;"><h1>🏁 VOTES CLOS</h1></div>', unsafe_allow_html=True)

    elif cfg["reveal_resultats"]:
        v_data = load_json(VOTES_FILE, {})
        sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)[:3]
        st.markdown('<h1 style="text-align:center; color:gold;">🏆 PODIUM</h1>', unsafe_allow_html=True)
        cols = st.columns(3); ranks = ["🥇", "🥈", "🥉"]
        for i, (name, score) in enumerate(sorted_v):
            cols[i].markdown(f"""<div style="text-align:center; color:white; background:#111; padding:30px; border-radius:20px; border:4px solid gold;"><h1>{ranks[i]}</h1><h2>{name}</h2><h3>{score} pts</h3></div>""", unsafe_allow_html=True)
