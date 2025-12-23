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
VOTES_FILE = "votes.json"
CONFIG_FILE = "config_mur.json"
PARTICIPANTS_FILE = "participants.json" # Nouveau fichier pour les pseudos

# Création des dossiers
for d in [GALLERY_DIR, ADMIN_DIR, LIVE_DIR]:
    if not os.path.exists(d): os.makedirs(d)

# Liste des 10 vidéos/candidats
DEFAULT_CANDIDATS = [
    "1. BU PAX", "2. BU FRET", "3. BU B2B", "4. SERVICE RH", 
    "5. SERVICE IT", "6. DPMI (Atelier)", "7. SERVICE FINANCIER", 
    "8. SERVICE AO", "9. SERVICE QSSE", "10. DIRECTION POLE"
]

# --- FONCTIONS UTILITAIRES ---
def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r") as f: return json.load(f)
        except: return default
    return default

def save_json(file, data):
    with open(file, "w") as f: json.dump(data, f)

# Initialisation Config
if "config" not in st.session_state:
    st.session_state.config = load_json(CONFIG_FILE, {
        "mode_affichage": "attente", 
        "titre_mur": "CONCOURS VIDÉO PÔLE AEROPORTUAIRE", 
        "session_ouverte": False, 
        "reveal_resultats": False,
        "timestamp_podium": 0,
        "logo_b64": None,
        "candidats": DEFAULT_CANDIDATS,
        "effect_intensity": 25, 
        "effect_speed": 25,     
        "screen_effects": {       
            "attente": "Aucun", "votes_open": "Aucun", "votes_closed": "Aucun", "podium": "🎉 Confettis", "photos_live": "Aucun"
        }
    })

def save_config():
    save_json(CONFIG_FILE, st.session_state.config)

# --- COMPRESSION PHOTO ---
def save_optimized_photo(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img.thumbnail((800, 800))
        filename = f"img_{int(time.time())}_{uuid.uuid4().hex[:4]}.jpg"
        filepath = os.path.join(LIVE_DIR, filename)
        img.save(filepath, "JPEG", quality=70, optimize=True)
        return True
    except: return False

# --- EFFETS VISUELS ---
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
        layer.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:0;overflow:hidden;';
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
    
    js_code += "</script>"
    components.html(js_code, height=0)

# --- NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"

# ==========================================
# 1. CONSOLE ADMIN
# ==========================================
if est_admin:
    st.markdown("""<style>[data-testid="stHeader"] {visibility: hidden;} .block-container {padding-top: 5rem !important;} .fixed-header {position: fixed; top: 0; left: 0; width: 100%; background-color: #E2001A; color: white; text-align: center; padding: 15px 0; z-index: 999999; box-shadow: 0 4px 10px rgba(0,0,0,0.3); font-family: sans-serif; font-weight: bold; font-size: 22px; text-transform: uppercase;}</style>""", unsafe_allow_html=True)
    
    if "auth" not in st.session_state: st.session_state.auth = False
    if not st.session_state.auth:
        st.markdown("<div class='fixed-header'>🔐 ACCÈS RÉSERVÉ</div>", unsafe_allow_html=True)
        pwd = st.text_input("Mot de passe", type="password")
        if pwd == "ADMIN_LIVE_MASTER": st.session_state.auth = True; st.rerun()
    else:
        cfg = st.session_state.config
        with st.sidebar:
            st.title("🎛️ RÉGIE")
            menu = st.radio("Menu", ["🔴 PILOTAGE", "⚙️ Paramètres", "📸 Photos"])
            st.markdown("---")
            st.markdown('<a href="./" target="_blank"><button style="width:100%; background-color:#E2001A; color:white; border:none; padding:10px; border-radius:5px; cursor:pointer; margin-bottom:10px;">📺 OUVRIR MUR SOCIAL</button></a>', unsafe_allow_html=True)
            st.markdown('<a href="./?mode=vote" target="_blank"><button style="width:100%; background-color:#333; color:white; border:none; padding:10px; border-radius:5px; cursor:pointer;">📱 APERÇU MOBILE</button></a>', unsafe_allow_html=True)

        st.markdown(f"<div class='fixed-header'>{menu}</div>", unsafe_allow_html=True)

        if menu == "🔴 PILOTAGE":
            st.subheader("🎬 Séquenceur")
            b1, b2, b3, b4, b5 = st.columns(5)
            if b1.button("🏠 ACCUEIL"): cfg.update({"mode_affichage":"attente","reveal_resultats":False,"session_ouverte":False}); save_config(); st.rerun()
            if b2.button("🗳️ VOTE ON"): cfg.update({"mode_affichage":"votes","session_ouverte":True,"reveal_resultats":False}); save_config(); st.rerun()
            if b3.button("🛑 VOTE OFF"): cfg.update({"session_ouverte":False}); save_config(); st.rerun()
            if b4.button("🏆 PODIUM"): cfg.update({"mode_affichage":"votes","reveal_resultats":True,"session_ouverte":False}); save_config(); st.rerun()
            if b5.button("📸 PHOTOS"): cfg.update({"mode_affichage":"photos_live","reveal_resultats":False}); save_config(); st.rerun()
            
            st.divider()
            st.subheader("📡 Effets")
            c1, c2 = st.columns(2)
            with c1: 
                cfg["effect_intensity"] = st.slider("Densité", 0, 50, cfg["effect_intensity"])
                cfg["effect_speed"] = st.slider("Vitesse", 0, 50, cfg["effect_speed"])
            
            EFFS = ["Aucun", "🎈 Ballons", "❄️ Neige", "🎉 Confettis", "🌌 Espace"]
            with c2:
                cfg["screen_effects"]["attente"] = st.selectbox("Effet Accueil", EFFS, index=EFFS.index(cfg["screen_effects"].get("attente","Aucun")))
                cfg["screen_effects"]["votes_open"] = st.selectbox("Effet Vote", EFFS, index=EFFS.index(cfg["screen_effects"].get("votes_open","Aucun")))
                cfg["screen_effects"]["podium"] = st.selectbox("Effet Podium", EFFS, index=EFFS.index(cfg["screen_effects"].get("podium","Aucun")))
                cfg["screen_effects"]["photos_live"] = st.selectbox("Effet Photos", EFFS, index=EFFS.index(cfg["screen_effects"].get("photos_live","Aucun")))
            
            if st.button("💾 SAUVER EFFETS"): save_config(); st.toast("OK")

        elif menu == "⚙️ Paramètres":
            cfg["titre_mur"] = st.text_input("Titre", cfg["titre_mur"])
            if st.button("Sauver Titre"): save_config()
            up = st.file_uploader("Logo", type=["png","jpg"])
            if up: cfg["logo_b64"] = base64.b64encode(up.read()).decode(); save_config(); st.success("Logo OK")
            
            if st.button("🗑️ RESET PARTICIPANTS"):
                if os.path.exists(PARTICIPANTS_FILE): os.remove(PARTICIPANTS_FILE)
                if os.path.exists(VOTES_FILE): os.remove(VOTES_FILE)
                st.success("Remise à zéro effectuée !")

        elif menu == "📸 Photos":
            files = glob.glob(f"{LIVE_DIR}/*")
            if files:
                cols = st.columns(6)
                for i, f in enumerate(files):
                    with cols[i%6]:
                        st.image(f, use_container_width=True)
                        if st.button("Suppr", key=f"d{i}"): os.remove(f); st.rerun()

# ==========================================
# 2. APPLICATION MOBILE (UTILISATEUR)
# ==========================================
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, {})
    st.markdown("<style>.stApp {background-color:black; color:white;}</style>", unsafe_allow_html=True)
    
    # Étape 1 : Demande de Pseudo
    if "user_pseudo" not in st.session_state:
        st.title("👋 Bienvenue !")
        pseudo = st.text_input("Entrez votre Prénom / Pseudo :")
        if st.button("Entrer") and pseudo:
            st.session_state.user_pseudo = pseudo
            # Enregistrement du participant
            parts = load_json(PARTICIPANTS_FILE, [])
            if pseudo not in parts:
                parts.append(pseudo)
                save_json(PARTICIPANTS_FILE, parts)
            st.rerun()
    
    # Étape 2 : Interface principale
    else:
        st.markdown(f"### Bonjour {st.session_state.user_pseudo} !")
        
        if cfg.get("mode_affichage") == "photos_live":
            st.info("Le mur photo est ouvert !")
            photo = st.camera_input("Prendre une photo")
            if photo:
                if save_optimized_photo(photo): st.success("Envoyée !")
        
        else:
            if not cfg.get("session_ouverte"):
                st.warning("⏳ Les votes ne sont pas encore ouverts.")
            else:
                if st.session_state.get("a_vote"):
                    st.success("✅ Vote enregistré. Merci !")
                else:
                    st.write("Choisissez vos 3 vidéos préférées :")
                    choix = st.multiselect("", cfg.get("candidats", []))
                    if len(choix) == 3:
                        if st.button("VALIDER MES CHOIX"):
                            vts = load_json(VOTES_FILE, {})
                            for c in choix: vts[c] = vts.get(c, 0) + 1
                            save_json(VOTES_FILE, vts)
                            st.session_state.a_vote = True
                            st.rerun()
                    elif len(choix) > 3: st.error("Maximum 3 choix !")

# ==========================================
# 3. MUR SOCIAL (CONSOLE SOCIALE)
# ==========================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=3000, key="wall")
    cfg = load_json(CONFIG_FILE, {})
    
    # CSS GLOBAL
    st.markdown("""
    <style>
        body, .stApp { background-color: black; overflow: hidden; font-family: 'Arial', sans-serif; }
        [data-testid='stHeader'] { display: none; }
        .block-container { padding: 0 !important; max-width: 100% !important; }
        
        /* Style des Tags Utilisateurs */
        .user-tag {
            display: inline-block;
            background: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: white;
            padding: 8px 15px;
            margin: 5px;
            border-radius: 20px;
            font-size: 18px;
            backdrop-filter: blur(5px);
        }
        
        /* Zoom Effect pour le vainqueur */
        @keyframes zoomPulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); box-shadow: 0 0 30px gold; }
            100% { transform: scale(1); }
        }
        .winner-zoom {
            animation: zoomPulse 3s infinite ease-in-out;
            border: 6px solid #FFD700 !important;
            background: rgba(255, 215, 0, 0.1) !important;
            z-index: 10;
        }
        
        /* Listes des candidats */
        .cand-item { color: white; font-size: 24px; padding: 10px; border-bottom: 1px solid #333; }
        
        /* Bulles Photos */
        .bubble { position: absolute; border-radius: 50%; border: 3px solid #E2001A; object-fit: cover; z-index: 1; pointer-events: none; }
    </style>
    """, unsafe_allow_html=True)

    # Logique d'affichage
    mode = cfg.get("mode_affichage")
    session_open = cfg.get("session_ouverte")
    reveal = cfg.get("reveal_resultats")
    
    # Définition de la clé d'effet
    if mode == "photos_live": key_eff = "photos_live"
    elif reveal: key_eff = "podium"
    elif mode == "votes": key_eff = "votes_open" if session_open else "votes_closed"
    else: key_eff = "attente"
    
    inject_visual_effect(cfg["screen_effects"].get(key_eff, "Aucun"), cfg.get("effect_intensity", 25), cfg.get("effect_speed", 25))

    # --- CONTENU PAR MODE ---

    # A. ACCUEIL (ATTENTE)
    if mode == "attente":
        logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:180px; margin-bottom:20px;">' if cfg.get("logo_b64") else ""
        parts = load_json(PARTICIPANTS_FILE, [])
        tags_html = "".join([f"<span class='user-tag'>{p}</span>" for p in parts[-70:]]) # Max 70 derniers
        
        st.markdown(f"""
            <div style="text-align:center; padding-top:10vh;">
                {logo_html}
                <h1 style="color:white; font-size:70px; margin-bottom:10px;">BIENVENUE</h1>
                <h2 style="color:#E2001A; font-size:40px;">{cfg.get('titre_mur')}</h2>
                <h3 style="color:#AAA; margin-top:30px;">Veuillez patienter, l'événement va commencer...</h3>
                
                <div style="margin-top:50px;">
                    <div style="font-size:30px; color:white; font-weight:bold; margin-bottom:20px;">
                        👥 {len(parts)} PARTICIPANTS CONNECTÉS
                    </div>
                    <div style="width:80%; margin:0 auto; line-height:1.5;">
                        {tags_html}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # B. VOTES (ON / OFF)
    elif mode == "votes":
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        
        if session_open:
            # Votes OUVERTS : 3 colonnes (Liste G, QR, Liste D)
            cands = cfg.get("candidats", [])
            mid = len(cands)//2
            col_g_html = "".join([f"<div class='cand-item'>{c}</div>" for c in cands[:mid]])
            col_d_html = "".join([f"<div class='cand-item'>{c}</div>" for c in cands[mid:]])
            
            st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; padding:0 50px; height:90vh;">
                    <div style="width:30%; text-align:left;">{col_g_html}</div>
                    <div style="width:30%; text-align:center;">
                        <h1 style="color:#E2001A; font-size:50px;">A VOS VOTES !</h1>
                        <div style="background:white; padding:15px; border-radius:20px; display:inline-block; margin:20px 0;">
                            <img src="data:image/png;base64,{qr_b64}" width="220">
                        </div>
                        <h3 style="color:white;">Scannez pour voter pour vos 3 favoris</h3>
                    </div>
                    <div style="width:30%; text-align:right;">{col_d_html}</div>
                </div>
            """, unsafe_allow_html=True)
        
        elif reveal:
            # PODIUM
            v_data = load_json(VOTES_FILE, {})
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)[:3]
            
            st.markdown("<h1 style='text-align:center; color:#FFD700; font-size:70px; margin-top:30px;'>🏆 RÉSULTATS 🏆</h1>", unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns([1,1.2,1]) # Colonne du milieu plus large pour le 1er
            
            # Affichage 2ème
            if len(sorted_v) > 1:
                with c1:
                    st.markdown(f"""
                    <div style="margin-top:100px; background:rgba(192,192,192,0.1); border:4px solid #C0C0C0; border-radius:20px; padding:20px; text-align:center; color:white;">
                        <div style="font-size:50px;">🥈</div>
                        <h2 style="font-size:30px;">{sorted_v[1][0]}</h2>
                        <h3>{sorted_v[1][1]} Pts</h3>
                    </div>""", unsafe_allow_html=True)
            
            # Affichage 1er (ZOOM)
            if len(sorted_v) > 0:
                with c2:
                    st.markdown(f"""
                    <div class="winner-zoom" style="background:rgba(255,215,0,0.1); border:4px solid #FFD700; border-radius:30px; padding:40px; text-align:center; color:white;">
                        <div style="font-size:80px;">🥇</div>
                        <h1 style="font-size:50px; color:#FFD700;">{sorted_v[0][0]}</h1>
                        <h2>{sorted_v[0][1]} Pts</h2>
                    </div>""", unsafe_allow_html=True)
            
            # Affichage 3ème
            if len(sorted_v) > 2:
                with c3:
                    st.markdown(f"""
                    <div style="margin-top:120px; background:rgba(205,127,50,0.1); border:4px solid #CD7F32; border-radius:20px; padding:20px; text-align:center; color:white;">
                        <div style="font-size:50px;">🥉</div>
                        <h2 style="font-size:30px;">{sorted_v[2][0]}</h2>
                        <h3>{sorted_v[2][1]} Pts</h3>
                    </div>""", unsafe_allow_html=True)

        else:
            # Votes CLOS (Attente résultats)
            st.markdown(f"""
                <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); text-align:center;">
                    <div style="border: 8px solid #E2001A; padding: 40px 80px; border-radius: 30px; background:rgba(0,0,0,0.8);">
                        <h1 style="color:#E2001A; font-size:80px; margin:0;">🛑 VOTES CLOS</h1>
                        <h2 style="color:white; font-size:40px; margin-top:20px;">Calcul des résultats en cours...</h2>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # C. MUR PHOTO LIVE
    elif mode == "photos_live":
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:120px; margin-bottom:20px;">' if cfg.get("logo_b64") else ""
        
        # Bloc Central Fixe
        st.markdown(f"""
            <div style="position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); z-index:1000; text-align:center; width:100%; pointer-events:none;">
                <div style="display:inline-block; pointer-events:auto; background: rgba(0,0,0,0.8); padding: 40px; border-radius: 40px; border: 2px solid #444;">
                    {logo_html}
                    <div style="background:white; padding:15px; border-radius:20px; display:inline-block; margin-bottom:20px;">
                        <img src="data:image/png;base64,{qr_b64}" width="200">
                    </div>
                    <br>
                    <div style="background:#E2001A; color:white; padding:10px 30px; border-radius:50px; font-weight:bold; font-size:24px; display:inline-block;">
                        📸 ENVOYEZ VOS PHOTOS
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Animation des bulles
        files = glob.glob(f"{LIVE_DIR}/*"); files.sort(key=os.path.getmtime, reverse=True)
        if files:
            img_list = [f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in files[:25]]
            components.html(f"""<script>
                window.parent.document.querySelectorAll('.bubble').forEach(b => b.remove());
                var imgs = {json.dumps(img_list)};
                imgs.forEach(src => {{
                    var i = document.createElement('img'); i.src = src; i.className = 'bubble';
                    var size = Math.random()*150 + 80;
                    i.style.cssText = 'position:absolute; border-radius:50%; border:3px solid #E2001A; width:'+size+'px; height:'+size+'px; object-fit:cover; z-index:1; left:'+(Math.random()*90)+'vw; top:'+(Math.random()*90)+'vh;';
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
