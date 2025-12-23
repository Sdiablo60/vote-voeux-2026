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
st.set_page_config(page_title="Régie Master", layout="wide")

GALLERY_DIR, ADMIN_DIR, LIVE_DIR = "galerie_images", "galerie_admin", "galerie_live_users"
VOTES_FILE, PARTICIPANTS_FILE, CONFIG_FILE, VOTERS_FILE, DETAILED_VOTES_FILE = "votes.json", "participants.json", "config_mur.json", "voters.json", "detailed_votes.json"

for d in [GALLERY_DIR, ADMIN_DIR, LIVE_DIR]:
    if not os.path.exists(d): os.makedirs(d)

DEFAULT_CANDIDATS = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]

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
    "screen_effects": {"attente": "Aucun", "votes_open": "Aucun", "votes_closed": "Aucun", "podium": "🎉 Confettis", "photos_live": "Aucun"}
}

# --- UTILITAIRES ---
def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r") as f: return json.load(f)
        except: return default
    return default

# Fonction CRITIQUE corrigée : Nettoie le HTML avant affichage
def render_html(html_code):
    html_code = html_code.strip() 
    st.markdown(html_code, unsafe_allow_html=True)

# --- INIT SESSION ---
if "config" not in st.session_state:
    st.session_state.config = load_json(CONFIG_FILE, default_config)
if "session_id" not in st.session_state.config:
    st.session_state.config["session_id"] = str(int(time.time()))
if "my_uuid" not in st.session_state: st.session_state.my_uuid = str(uuid.uuid4())
if "refresh_id" not in st.session_state: st.session_state.refresh_id = 0
if "cam_reset_id" not in st.session_state: st.session_state.cam_reset_id = 0
if "confirm_delete" not in st.session_state: st.session_state.confirm_delete = False
if "user_id" not in st.session_state: st.session_state.user_id = None
if "a_vote" not in st.session_state: st.session_state.a_vote = False
if "rules_accepted" not in st.session_state: st.session_state.rules_accepted = False

# --- LOGIQUE METIER ---
def save_config():
    with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)

def force_refresh():
    st.session_state.refresh_id += 1; save_config()

def process_image_upload(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        if img.mode != "RGBA": img = img.convert("RGBA")
        img.thumbnail((300, 300))
        buffered = BytesIO()
        img.save(buffered, format="PNG") 
        return base64.b64encode(buffered.getvalue()).decode().replace('\n', '')
    except: return None

def save_live_photo(uploaded_file):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"live_{timestamp}_{random.randint(100,999)}.jpg"
        filepath = os.path.join(LIVE_DIR, filename)
        img = Image.open(uploaded_file)
        try: # Rotation EXIF
            from PIL import ExifTags
            if hasattr(img, '_getexif'):
                exif = img._getexif()
                if exif:
                    for orientation in ExifTags.TAGS.keys():
                        if ExifTags.TAGS[orientation] == 'Orientation': break
                    if exif.get(orientation) == 3: img = img.rotate(180, expand=True)
                    elif exif.get(orientation) == 6: img = img.rotate(270, expand=True)
                    elif exif.get(orientation) == 8: img = img.rotate(90, expand=True)
        except: pass
        img = img.convert("RGB")
        img.thumbnail((800, 800)) 
        img.save(filepath, "JPEG", quality=80, optimize=True)
        return True
    except: return False

def update_presence(is_active_user=False):
    presence_data = load_json(PARTICIPANTS_FILE, {})
    if isinstance(presence_data, list): presence_data = {}
    now = time.time()
    clean_data = {uid: ts for uid, ts in presence_data.items() if now - ts < 10} 
    if is_active_user: clean_data[st.session_state.my_uuid] = now
    with open(PARTICIPANTS_FILE, "w") as f: json.dump(clean_data, f)
    return len(clean_data)

def inject_visual_effect(effect_name, intensity, speed):
    if effect_name == "Aucun":
        components.html("<script>var old = window.parent.document.getElementById('effect-layer'); if(old) old.remove();</script>", height=0)
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
            setTimeout(() => {{ e.style.bottom = '110vh'; }}, 50); setTimeout(() => {{ e.remove(); }}, {duration * 1000});
        }}
        function createSnow() {{
            var e = doc.createElement('div'); e.innerHTML = '❄';
            e.style.cssText = 'position:absolute;top:-50px;left:'+Math.random()*100+'vw;color:white;font-size:'+(Math.random()*20+10)+'px;transition:top {duration}s linear;';
            layer.appendChild(e);
            setTimeout(() => {{ e.style.top = '110vh'; }}, 50); setTimeout(() => {{ e.remove(); }}, {duration * 1000});
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

# =========================================================
# 1. CONSOLE ADMIN
# =========================================================
if est_admin:
    if "auth" not in st.session_state: st.session_state["auth"] = False
    if not st.session_state["auth"]:
        st.markdown("<br><br><h1 style='text-align:center;'>🔐 ACCÈS RÉGIE</h1>", unsafe_allow_html=True)
        col_c, col_p, col_d = st.columns([1,2,1])
        with col_p:
            pwd = st.text_input("Mot de passe", type="password")
            if pwd == "ADMIN_LIVE_MASTER": st.session_state["auth"] = True; st.rerun()
    else:
        with st.sidebar:
            st.title("🎛️ RÉGIE")
            st.markdown("""<a href="/" target="_blank"><div style="background-color: #E2001A; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 20px;">📺 OUVRIR MUR SOCIAL</div></a>""", unsafe_allow_html=True)
            st.markdown("""<a href="/?mode=vote" target="_blank"><div style="background-color: #333; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 20px;">📱 APERÇU MOBILE</div></a>""", unsafe_allow_html=True)
            menu = st.radio("Menu", ["🔴 PILOTAGE LIVE", "⚙️ Paramétrage", "📸 Médiathèque", "📊 Data"], label_visibility="collapsed")
            if st.button("🔓 Déconnexion"): st.session_state["auth"] = False; st.rerun()

        if menu == "🔴 PILOTAGE LIVE":
            st.title("🔴 COCKPIT LIVE")
            st.subheader("1️⃣ Séquenceur")
            c1, c2, c3, c4 = st.columns(4)
            cfg = st.session_state.config
            m, vo, re = cfg["mode_affichage"], cfg["session_ouverte"], cfg["reveal_resultats"]

            if c1.button("1. ACCUEIL", use_container_width=True, type="primary" if m=="attente" else "secondary"):
                cfg.update({"mode_affichage": "attente", "session_ouverte": False, "reveal_resultats": False}); force_refresh(); st.rerun()
            if c2.button("2. VOTES ON", use_container_width=True, type="primary" if (m=="votes" and vo) else "secondary"):
                cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False}); force_refresh(); st.rerun()
            if c3.button("3. VOTES OFF", use_container_width=True, type="primary" if (m=="votes" and not vo and not re) else "secondary"):
                cfg.update({"session_ouverte": False}); force_refresh(); st.rerun()
            if c4.button("4. PODIUM", use_container_width=True, type="primary" if re else "secondary"):
                cfg.update({"mode_affichage": "votes", "reveal_resultats": True, "session_ouverte": False, "timestamp_podium": time.time()}); force_refresh(); st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("5. 📸 MUR PHOTOS LIVE", use_container_width=True, type="primary" if m=="photos_live" else "secondary"):
                cfg.update({"mode_affichage": "photos_live", "session_ouverte": False, "reveal_resultats": False}); save_config(); st.rerun()

            st.divider()
            st.subheader("📡 Effets")
            c_e1, c_e2 = st.columns(2)
            with c_e1:
                intensity = st.slider("Densité", 0, 50, cfg["effect_intensity"])
                speed = st.slider("Vitesse", 0, 50, cfg["effect_speed"])
                if intensity != cfg["effect_intensity"] or speed != cfg["effect_speed"]:
                    cfg["effect_intensity"] = intensity; cfg["effect_speed"] = speed; save_config(); st.rerun()
            
            EFFS = ["Aucun", "🎈 Ballons", "❄️ Neige", "🎉 Confettis", "🌌 Espace"]
            with c_e2:
                cfg["screen_effects"]["attente"] = st.selectbox("Accueil", EFFS, index=EFFS.index(cfg["screen_effects"].get("attente","Aucun")))
                cfg["screen_effects"]["votes_open"] = st.selectbox("Vote On", EFFS, index=EFFS.index(cfg["screen_effects"].get("votes_open","Aucun")))
                cfg["screen_effects"]["podium"] = st.selectbox("Podium", EFFS, index=EFFS.index(cfg["screen_effects"].get("podium","Aucun")))
                cfg["screen_effects"]["photos_live"] = st.selectbox("Photos", EFFS, index=EFFS.index(cfg["screen_effects"].get("photos_live","Aucun")))
            if st.button("💾 SAUVER EFFETS"): save_config(); st.toast("OK")

            st.divider()
            st.subheader("2️⃣ Monitoring")
            voters_list = load_json(VOTERS_FILE, [])
            st.metric("👥 Participants Validés", len(voters_list))
            
            if st.button("🗑️ RESET TOTAL (Danger)", type="primary"):
                for f in [VOTES_FILE, PARTICIPANTS_FILE, VOTERS_FILE, DETAILED_VOTES_FILE]: 
                    if os.path.exists(f): os.remove(f)
                files = glob.glob(f"{LIVE_DIR}/*"); 
                for f in files: os.remove(f)
                st.session_state.config["session_id"] = str(int(time.time()))
                save_config()
                st.success("Reset OK"); time.sleep(1); st.rerun()

        elif menu == "⚙️ Paramétrage":
            st.title("⚙️ Paramétrage")
            new_t = st.text_input("Titre", value=st.session_state.config["titre_mur"])
            if st.button("Sauver Titre"): st.session_state.config["titre_mur"] = new_t; force_refresh(); st.rerun()
            up_l = st.file_uploader("Logo", type=["png", "jpg"])
            if up_l:
                b64 = process_image_upload(up_l)
                if b64: st.session_state.config["logo_b64"] = b64; force_refresh(); st.success("Logo chargé !"); st.rerun()
            
            st.subheader("Liste des Questions")
            df_cands = pd.DataFrame(st.session_state.config["candidats"], columns=["Candidat"])
            edited_df = st.data_editor(df_cands, num_rows="dynamic", use_container_width=True)
            if st.button("💾 Enregistrer Liste"):
                new_list = [x for x in edited_df["Candidat"].astype(str).tolist() if x.strip() != ""]
                st.session_state.config["candidats"] = new_list; save_config(); st.rerun()

        elif menu == "📸 Médiathèque":
            st.title("📸 Gestion Photos")
            files = glob.glob(f"{LIVE_DIR}/*"); files.sort(key=os.path.getmtime, reverse=True)
            if files:
                cols = st.columns(6)
                for i, f in enumerate(files):
                    with cols[i%6]:
                        st.image(f, use_container_width=True)
                        if st.button("X", key=f"d{i}"): os.remove(f); st.rerun()
            else: st.info("Vide")

        elif menu == "📊 Data":
            st.title("📊 Données")
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                st.write(v_data)
            else: st.info("Aucun vote")

# =========================================================
# 2. APPLICATION MOBILE (UTILISATEUR)
# =========================================================
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, default_config)
    st.markdown("<style>.stApp {background-color:black; color:white;} [data-testid='stHeader'] {display:none;}</style>", unsafe_allow_html=True)
    
    # 2.1 ECRAN LOGIN
    if "user_pseudo" not in st.session_state:
        st.title("👋 Bienvenue")
        st.write("Pour participer, entrez votre prénom :")
        pseudo = st.text_input("Votre Pseudo", label_visibility="collapsed")
        if st.button("ENTRER", type="primary", use_container_width=True) and pseudo:
            st.session_state.user_pseudo = pseudo
            parts = load_json(PARTICIPANTS_FILE, [])
            if pseudo not in parts:
                parts.append(pseudo)
                with open(PARTICIPANTS_FILE, "w") as f: json.dump(parts, f)
            st.rerun()
    
    # 2.2 ECRAN PRINCIPAL
    else:
        st.markdown(f"#### Bonjour {st.session_state.user_pseudo} !")
        
        # MODE PHOTO
        if cfg.get("mode_affichage") == "photos_live":
            st.info("📷 Le mur photo est ouvert !")
            photo = st.camera_input("Prendre une photo", label_visibility="collapsed")
            if photo:
                if save_live_photo(photo): st.success("Envoyée !"); time.sleep(1); st.rerun()
        
        # MODE VOTE
        else:
            if not cfg.get("session_ouverte"):
                st.warning("⏳ Les votes sont fermés pour le moment.")
            else:
                if st.session_state.get("a_vote"):
                    st.success("✅ Vote enregistré. Merci !")
                else:
                    st.write("Choisissez vos 3 favoris :")
                    choix = st.multiselect("Choix", cfg.get("candidats", []), label_visibility="collapsed")
                    if len(choix) == 3:
                        if st.button("VALIDER MES CHOIX", type="primary", use_container_width=True):
                            vts = load_json(VOTES_FILE, {})
                            pts = cfg.get("points_ponderation", [5, 3, 1])
                            for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                            json.dump(vts, open(VOTES_FILE, "w"))
                            
                            voters = load_json(VOTERS_FILE, [])
                            voters.append(st.session_state.user_pseudo) # On sauve le pseudo
                            with open(VOTERS_FILE, "w") as f: json.dump(voters, f)
                            
                            st.session_state.a_vote = True
                            st.rerun()
                    elif len(choix) > 3: st.error("Maximum 3 choix !")

# =========================================================
# 3. MUR SOCIAL (CONSOLE SOCIALE)
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2000, key="wall_autorefresh")
    cfg = load_json(CONFIG_FILE, default_config)
    
    st.markdown("""
    <style>
        body, .stApp { background-color: black !important; overflow: hidden; height: 100vh; font-family: sans-serif; } 
        [data-testid='stHeader'] { display: none !important; } 
        .block-container { padding: 0 !important; max-width: 100% !important; }
        .user-tag { display: inline-block; background: rgba(255, 255, 255, 0.2); color: white; border-radius: 20px; padding: 5px 15px; margin: 5px; font-size: 18px; }
        .winner-card { border: 6px solid #FFD700 !important; background: rgba(255, 215, 0, 0.1) !important; transform: scale(1.1); z-index: 10; }
        .cand-row { display: flex; align-items: center; margin-bottom: 10px; background: rgba(255,255,255,0.1); padding: 10px; border-radius: 10px; }
        .cand-name { color: white; font-size: 20px; margin-left: 10px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    mode = cfg.get("mode_affichage")
    
    # Injection Effets
    key_eff = "attente"
    if mode == "photos_live": key_eff = "photos_live"
    elif cfg.get("reveal_resultats"): key_eff = "podium"
    elif mode == "votes": key_eff = "votes_open" if cfg.get("session_ouverte") else "votes_closed"
    inject_visual_effect(cfg["screen_effects"].get(key_eff, "Aucun"), cfg.get("effect_intensity", 25), cfg.get("effect_speed", 25))

    # LOGO COMMUN
    logo_part = ""
    if cfg.get("logo_b64"): 
        logo_part = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:150px; display:block; margin: 0 auto 20px auto;">'

    # --- A. ACCUEIL ---
    if mode == "attente":
        parts = load_json(PARTICIPANTS_FILE, [])
        tags_html = "".join([f"<span class='user-tag'>{p}</span>" for p in parts[-60:]])
        
        html = f"""
        <div style="text-align:center; padding-top:5vh;">
            {logo_part}
            <h1 style="color:white; font-size:80px; margin:0;">BIENVENUE</h1>
            <h2 style="color:#E2001A; font-size:40px; margin-top:10px;">{cfg.get('titre_mur')}</h2>
            <h3 style="color:#CCC; margin-top:30px;">Veuillez patienter, l'événement va commencer...</h3>
            <div style="margin-top:50px;">
                <div style="font-size:30px; color:white; font-weight:bold; margin-bottom:20px;">
                    👥 {len(parts)} PARTICIPANTS CONNECTÉS
                </div>
                <div style="width:90%; margin:0 auto; line-height:1.5;">{tags_html}</div>
            </div>
        </div>
        """
        render_html(html)

    # --- B. VOTES ---
    elif mode == "votes":
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        
        if cfg.get("session_ouverte"):
            cands = cfg.get("candidats", [])
            mid = (len(cands) + 1) // 2
            
            # Construction Colonnes HTML
            def build_list(items):
                h = ""
                for c in items:
                    img = ""
                    if c in cfg.get("candidats_images", {}):
                        img = f'<img src="data:image/png;base64,{cfg["candidats_images"][c]}" style="width:50px; height:50px; border-radius:5px; object-fit:cover;">'
                    h += f'<div class="cand-row">{img}<span class="cand-name">{c}</span></div>'
                return h

            col_g = build_list(cands[:mid])
            col_d = build_list(cands[mid:])
            
            html = f"""
            <div style="display:flex; height:90vh; padding:20px;">
                <div style="width:30%; overflow-y:auto;">{col_g}</div>
                <div style="width:40%; text-align:center; display:flex; flex-direction:column; justify-content:center; align-items:center;">
                    <h1 style="color:#E2001A; font-size:60px;">A VOS VOTES !</h1>
                    <div style="background:white; padding:20px; border-radius:20px; margin:30px;">
                        <img src="data:image/png;base64,{qr_b64}" width="250">
                    </div>
                    <h2 style="color:white;">Scannez pour voter</h2>
                </div>
                <div style="width:30%; overflow-y:auto;">{col_d}</div>
            </div>
            """
            render_html(html)
        
        elif cfg.get("reveal_resultats"):
            # PODIUM
            v_data = load_json(VOTES_FILE, {})
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)[:3]
            
            render_html(f"<h1 style='text-align:center; color:#FFD700; font-size:80px; margin-top:20px;'>🏆 RÉSULTATS 🏆</h1>")
            
            c1, c2, c3 = st.columns([1,1.2,1])
            
            # Helpers pour affichage safe
            def get_card(rank_idx, data):
                if not data: return ""
                name, score = data
                colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
                ranks = ["🥇", "🥈", "🥉"]
                cls = "winner-card" if rank_idx == 0 else ""
                img_html = ""
                if name in cfg.get("candidats_images", {}):
                    img_html = f'<img src="data:image/png;base64,{cfg["candidats_images"][name]}" style="width:100px; height:100px; border-radius:50%; margin-bottom:10px; border:3px solid {colors[rank_idx]};">'
                
                return f"""
                <div class="{cls}" style="background:rgba(255,255,255,0.1); border:4px solid {colors[rank_idx]}; border-radius:20px; padding:30px; text-align:center; color:white; margin-top:{'0' if rank_idx==0 else '80'}px;">
                    <div style="font-size:60px;">{ranks[rank_idx]}</div>
                    {img_html}
                    <h2 style="font-size:35px; margin:10px 0;">{name}</h2>
                    <h3 style="font-size:25px; color:#ddd;">{score} pts</h3>
                </div>
                """

            with c1: render_html(get_card(1, sorted_v[1] if len(sorted_v)>1 else None))
            with c2: render_html(get_card(0, sorted_v[0] if len(sorted_v)>0 else None))
            with c3: render_html(get_card(2, sorted_v[2] if len(sorted_v)>2 else None))

        else:
            # Votes CLOS
            render_html("""
            <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); text-align:center;">
                <div style="border: 10px solid #E2001A; padding: 60px 100px; border-radius: 40px; background:rgba(0,0,0,0.8);">
                    <h1 style="color:#E2001A; font-size:100px; margin:0;">🛑 VOTES CLOS</h1>
                    <h2 style="color:white; font-size:50px; margin-top:20px;">Calcul des résultats...</h2>
                </div>
            </div>
            """)

    # --- C. PHOTOS LIVE ---
    elif mode == "photos_live":
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        
        # Overlay fixe
        html = f"""
        <div style="position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); z-index:999; text-align:center;">
            <div style="background: rgba(0,0,0,0.85); padding: 40px; border-radius: 40px; border: 2px solid #555; box-shadow: 0 0 50px black;">
                {logo_part}
                <h1 style="color:white; font-size:60px; text-transform:uppercase; margin-bottom:20px;">MUR PHOTOS LIVE</h1>
                <div style="background:white; padding:15px; border-radius:20px; display:inline-block; margin-bottom:20px;">
                    <img src="data:image/png;base64,{qr_b64}" width="200">
                </div>
                <br>
                <div style="background:#E2001A; color:white; padding:10px 40px; border-radius:50px; font-weight:bold; font-size:28px; display:inline-block; border:3px solid white;">
                    📸 SCANNEZ POUR ENVOYER
                </div>
            </div>
        </div>
        """
        render_html(html)
        
        # Bulles
        files = glob.glob(f"{LIVE_DIR}/*"); files.sort(key=os.path.getmtime, reverse=True)
        img_list = []
        if files:
            for f in files[:30]:
                try: 
                    with open(f, "rb") as i: img_list.append(f"data:image/jpeg;base64,{base64.b64encode(i.read()).decode()}")
                except: pass
            
            components.html(f"""<script>
                var imgs = {json.dumps(img_list)};
                // Nettoyage radical
                var old = window.parent.document.querySelectorAll('.bubble-img');
                old.forEach(e => e.remove());
                
                imgs.forEach(src => {{
                    var i = document.createElement('img'); i.src = src; i.className = 'bubble-img';
                    var size = Math.random()*120 + 80;
                    i.style.cssText = 'position:absolute; border-radius:50%; border:3px solid #E2001A; object-fit:cover; z-index:1; width:'+size+'px; height:'+size+'px; left:'+(Math.random()*90)+'vw; top:'+(Math.random()*90)+'vh; transition: all 3s ease-in-out;';
                    window.parent.document.body.appendChild(i);
                    
                    // Mouvement simple CSS
                    setInterval(() => {{
                        i.style.left = (Math.random()*90) + 'vw';
                        i.style.top = (Math.random()*90) + 'vh';
                    }}, 3000 + Math.random()*2000);
                }});
            </script>""", height=0)
