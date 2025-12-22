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

# MAPPING DES EFFETS PAR DEFAUT
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
    # NOUVEAU SYSTEME D'EFFETS
    "global_effect": "Aucun", # Effet prioritaire (écrase tout)
    "screen_effects": {       # Effets par écran (si global est "Aucun")
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

# Migration structurelle si nécessaire (pour ne pas planter si l'ancien fichier config existe)
if "screen_effects" not in st.session_state.config:
    st.session_state.config["screen_effects"] = default_config["screen_effects"]
if "global_effect" not in st.session_state.config:
    st.session_state.config["global_effect"] = "Aucun"

if "session_id" not in st.session_state.config:
    st.session_state.config["session_id"] = str(int(time.time()))

if "my_uuid" not in st.session_state:
    st.session_state.my_uuid = str(uuid.uuid4())

if "refresh_id" not in st.session_state: st.session_state.refresh_id = 0
if "cam_reset_id" not in st.session_state: st.session_state.cam_reset_id = 0
if "confirm_delete" not in st.session_state: st.session_state.confirm_delete = False

# Variables User
if "user_id" not in st.session_state: st.session_state.user_id = None
if "a_vote" not in st.session_state: st.session_state.a_vote = False
if "rules_accepted" not in st.session_state: st.session_state.rules_accepted = False

# Sécurités structure
if "candidats" not in st.session_state.config: st.session_state.config["candidats"] = DEFAULT_CANDIDATS
if "candidats_images" not in st.session_state.config: st.session_state.config["candidats_images"] = {}
if "points_ponderation" not in st.session_state.config: st.session_state.config["points_ponderation"] = [5, 3, 1]

BADGE_CSS = "margin-top:20px; background:#E2001A; display:inline-block; padding:10px 30px; border-radius:10px; font-size:22px; font-weight:bold; border:2px solid white; color:white;"

# --- 1. BIBLIOTHEQUE D'EFFETS (MUR SOCIAL - PLEIN ECRAN) ---
EFFECTS_LIB = {
    "Aucun": """<script>var old=window.parent.document.getElementById('effect-layer');if(old)old.remove();</script>""",
    "🎈 Ballons": """<script>var old=window.parent.document.getElementById('effect-layer');if(old)old.remove();var l=document.createElement('div');l.id='effect-layer';l.style.cssText='position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:99999;overflow:hidden;';window.parent.document.body.appendChild(l);function c(){if(!window.parent.document.getElementById('effect-layer'))return;const d=document.createElement('div');d.innerHTML='🎈';d.style.cssText='position:absolute;bottom:-50px;left:'+Math.random()*100+'vw;font-size:'+(Math.random()*30+30)+'px;opacity:'+(Math.random()*0.5+0.5)+';transition:bottom '+(Math.random()*5+5)+'s linear,left '+(Math.random()*5+5)+'s ease-in-out;';l.appendChild(d);requestAnimationFrame(()=>{d.style.bottom='110vh';d.style.left=(parseFloat(d.style.left)+(Math.random()*20-10))+'vw';});setTimeout(()=>{d.remove()},12000);}setInterval(c,600);</script>""",
    "❄️ Neige": """<script>var old=window.parent.document.getElementById('effect-layer');if(old)old.remove();var l=document.createElement('div');l.id='effect-layer';l.style.cssText='position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:99999;';window.parent.document.body.appendChild(l);var s=document.createElement('style');s.innerHTML='.sf{position:absolute;top:-20px;color:#FFF;animation:f linear forwards}@keyframes f{to{transform:translateY(105vh)}}';l.appendChild(s);setInterval(()=>{if(!window.parent.document.getElementById('effect-layer'))return;const f=document.createElement('div');f.className='sf';f.textContent='❄';f.style.left=Math.random()*100+'vw';f.style.animationDuration=Math.random()*3+3+'s';f.style.fontSize=Math.random()*15+10+'px';f.style.opacity=Math.random();l.appendChild(f);setTimeout(()=>f.remove(),6000)},100);</script>""",
    "🎉 Confettis": """<script>var old=window.parent.document.getElementById('effect-layer');if(old)old.remove();var s=document.createElement('script');s.src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js";s.onload=function(){(function f(){if(!window.parent.document.body.contains(s))return;window.parent.confetti({particleCount:2,angle:90,spread:90,origin:{x:Math.random(),y:-0.1},colors:['#E2001A','#ffffff'],zIndex:0});requestAnimationFrame(f)}())};var l=document.createElement('div');l.id='effect-layer';l.appendChild(s);window.parent.document.body.appendChild(l);</script>""",
    "🌌 Espace": """<script>var old=window.parent.document.getElementById('effect-layer');if(old)old.remove();var l=document.createElement('div');l.id='effect-layer';l.style.cssText='position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:-1;background:transparent;';window.parent.document.body.appendChild(l);var s=document.createElement('style');s.innerHTML='.st{position:absolute;background:white;border-radius:50%;animation:z 3s infinite linear;opacity:0}@keyframes z{0%{opacity:0;transform:scale(0.1)}50%{opacity:1}100%{opacity:0;transform:scale(5)}}';l.appendChild(s);setInterval(()=>{if(!window.parent.document.getElementById('effect-layer'))return;const d=document.createElement('div');d.className='st';d.style.left=Math.random()*100+'vw';d.style.top=Math.random()*100+'vh';d.style.width=Math.random()*3+'px';d.style.height=d.style.width;l.appendChild(d);setTimeout(()=>d.remove(),3000)},50);</script>""",
    "💸 Billets": """<script>var old=window.parent.document.getElementById('effect-layer');if(old)old.remove();var l=document.createElement('div');l.id='effect-layer';l.style.cssText='position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:99999;overflow:hidden;';window.parent.document.body.appendChild(l);setInterval(()=>{if(!window.parent.document.getElementById('effect-layer'))return;const d=document.createElement('div');d.innerHTML='💸';d.style.cssText='position:absolute;top:-50px;left:'+Math.random()*100+'vw;font-size:30px;';l.appendChild(d);d.animate([{transform:'translateY(0)'},{transform:'translateY(110vh)'}],{duration:3000,iterations:1});setTimeout(()=>d.remove(),3000)},200);</script>""",
    "🟢 Matrix": """<script>var old=window.parent.document.getElementById('effect-layer');if(old)old.remove();var c=document.createElement('canvas');c.id='effect-layer';c.style.cssText='position:fixed;top:0;left:0;width:100%;height:100%;z-index:-1;opacity:0.3;pointer-events:none;';window.parent.document.body.appendChild(c);const x=c.getContext('2d');c.width=window.innerWidth;c.height=window.innerHeight;const l='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';const fs=16;const cols=c.width/fs;const r=[];for(let i=0;i<cols;i++)r[i]=1;const d=()=>{if(!window.parent.document.getElementById('effect-layer'))return;x.fillStyle='rgba(0,0,0,0.05)';x.fillRect(0,0,c.width,c.height);x.fillStyle='#0F0';x.font=fs+'px monospace';for(let i=0;i<r.length;i++){const t=l.charAt(Math.floor(Math.random()*l.length));x.fillText(t,i*fs,r[i]*fs);if(r[i]*fs>c.height&&Math.random()>0.975)r[i]=0;r[i]++}};setInterval(d,30);</script>"""
}

# --- 2. BIBLIOTHEQUE DE PREVISUALISATION (ADMIN - BOITE NOIRE) ---
PREVIEW_LIB = {
    "Aucun": "<div style='width:100%;height:100%;background:black;display:flex;align-items:center;justify-content:center;color:#555;font-family:sans-serif;'>Aucun effet</div>",
    
    "🎈 Ballons": """
    <div style='background:black;width:100%;height:100%;overflow:hidden;position:relative;'>
    <script>
    setInterval(function(){
        var d = document.createElement('div');
        d.innerHTML = '🎈';
        d.style.cssText = 'position:absolute;bottom:-30px;left:'+Math.random()*90+'%;font-size:24px;transition:bottom 3s linear;';
        document.body.appendChild(d);
        setTimeout(function(){ d.style.bottom = '120%'; }, 50);
        setTimeout(function(){ d.remove(); }, 3000);
    }, 500);
    </script></div>""",
    
    "❄️ Neige": """
    <div style='background:black;width:100%;height:100%;overflow:hidden;position:relative;'>
    <style>.f {position:absolute;color:#FFF;animation:d 2s linear forwards} @keyframes d{to{transform:translateY(250px)}}</style>
    <script>
    setInterval(function(){
        var d = document.createElement('div');
        d.className = 'f'; d.innerHTML = '❄';
        d.style.left = Math.random()*95+'%'; d.style.top = '-20px'; d.style.fontSize = (Math.random()*15+10)+'px';
        document.body.appendChild(d);
        setTimeout(function(){ d.remove(); }, 2000);
    }, 100);
    </script></div>""",
    
    "🎉 Confettis": """
    <div style='background:black;width:100%;height:100%;overflow:hidden;'>
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
    <script>
    setInterval(function(){
        confetti({particleCount:7, spread:60, origin:{y:0.6}, colors:['#E2001A','#ffffff'], disableForReducedMotion:true, zIndex:100});
    }, 600);
    </script></div>""",
    
    "🌌 Espace": """
    <div style='background:black;width:100%;height:100%;overflow:hidden;position:relative;'>
    <style>.s{position:absolute;background:white;border-radius:50%;animation:z 2s infinite linear;opacity:0} @keyframes z{0%{opacity:0;transform:scale(0.1)}50%{opacity:1}100%{opacity:0;transform:scale(3)}}</style>
    <script>
    setInterval(function(){
        var d = document.createElement('div'); d.className='s';
        d.style.left=Math.random()*100+'%'; d.style.top=Math.random()*100+'%'; d.style.width='2px'; d.style.height='2px';
        document.body.appendChild(d);
        setTimeout(function(){ d.remove(); }, 2000);
    }, 50);
    </script></div>""",
    
    "💸 Billets": """
    <div style='background:black;width:100%;height:100%;overflow:hidden;position:relative;'>
    <script>
    setInterval(function(){
        var d = document.createElement('div'); d.innerHTML = '💸';
        d.style.cssText = 'position:absolute;top:-30px;left:'+Math.random()*90+'%;font-size:24px;';
        document.body.appendChild(d);
        d.animate([{transform:'translateY(0)'}, {transform:'translateY(250px)'}], {duration:2000, iterations:1});
        setTimeout(function(){ d.remove(); }, 1900);
    }, 400);
    </script></div>""",
    
    "🟢 Matrix": """
    <div style='background:black;width:100%;height:100%;overflow:hidden;position:relative;'>
    <canvas id="m" style="width:100%;height:100%;"></canvas>
    <script>
    var c=document.getElementById('m'); var x=c.getContext('2d');
    c.width=300; c.height=200;
    var col=c.width/10; var r=[]; for(var i=0;i<col;i++)r[i]=1;
    setInterval(function(){
        x.fillStyle='rgba(0,0,0,0.1)'; x.fillRect(0,0,c.width,c.height);
        x.fillStyle='#0F0'; x.font='10px monospace';
        for(var i=0;i<r.length;i++){
            x.fillText(Math.floor(Math.random()*2), i*10, r[i]*10);
            if(r[i]*10>c.height && Math.random()>0.9) r[i]=0; r[i]++;
        }
    }, 50);
    </script></div>"""
}

# --- FONCTIONS CRITIQUES ---

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(st.session_state.config, f)

def force_refresh():
    st.session_state.refresh_id += 1
    save_config()

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
        try:
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
        img.thumbnail((500, 500)) 
        img.save(filepath, "JPEG", quality=85)
        return True
    except Exception as e:
        return False

def update_presence(is_active_user=False):
    presence_data = load_json(PARTICIPANTS_FILE, {})
    if isinstance(presence_data, list): presence_data = {}
    now = time.time()
    clean_data = {uid: ts for uid, ts in presence_data.items() if now - ts < 10} 
    if is_active_user:
        clean_data[st.session_state.my_uuid] = now
    with open(PARTICIPANTS_FILE, "w") as f:
        json.dump(clean_data, f)
    return len(clean_data)

def generate_pdf_report(dataframe, title):
    if not HAS_FPDF: return None
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, title, 0, 1, 'C')
            self.ln(10)
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    cols = dataframe.columns.tolist()
    col_width = 190 / len(cols)
    pdf.set_fill_color(200, 220, 255)
    for col in cols:
        pdf.cell(col_width, 10, str(col).encode('latin-1', 'replace').decode('latin-1'), 1, 0, 'C', 1)
    pdf.ln()
    pdf.set_fill_color(255, 255, 255)
    for index, row in dataframe.iterrows():
        for col in cols:
            txt = str(row[col]).encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(col_width, 10, txt, 1, 0, 'C')
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

def inject_visual_effect(effect_name):
    if effect_name in EFFECTS_LIB:
        components.html(EFFECTS_LIB[effect_name], height=0)

# --- 2. NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"

# --- 3. ADMINISTRATION ---
if est_admin:
    if "auth" not in st.session_state: st.session_state["auth"] = False
    
    if not st.session_state["auth"]:
        st.markdown("<br><br><h1 style='text-align:center;'>🔐 ACCÈS RÉGIE</h1>", unsafe_allow_html=True)
        col_c, col_p, col_d = st.columns([1,2,1])
        with col_p:
            pwd = st.text_input("Mot de passe", type="password")
            if pwd == "ADMIN_LIVE_MASTER":
                st.session_state["auth"] = True
                st.rerun()
    else:
        with st.sidebar:
            st.title("🎛️ RÉGIE MASTER")
            st.markdown("""<a href="/" target="_blank" style="text-decoration:none;"><div style="background-color: #E2001A; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 20px; border: 1px solid white; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">📺 OUVRIR LE MUR SOCIAL ⧉</div></a>""", unsafe_allow_html=True)
            st.markdown("---")
            menu = st.radio("Navigation :", ["🔴 PILOTAGE LIVE", "⚙️ Paramétrage", "📸 Médiathèque (Gestion)", "📊 Data & Exports"], label_visibility="collapsed")
            st.markdown("---")
            if st.button("🔓 Déconnexion", use_container_width=True):
                st.session_state["auth"] = False
                st.rerun()

        # --- MENU: PILOTAGE LIVE ---
        if menu == "🔴 PILOTAGE LIVE":
            st.title("🔴 COCKPIT LIVE")
            
            # --- ZONE GESTION EFFETS ---
            st.markdown("### 🎨 Gestion des Effets Visuels")
            
            # 1. Selecteur d'effet prioritaire (GLOBAL)
            st.caption("🚀 EFFET PRIORITAIRE (Applique immédiatement sur tous les écrans)")
            global_eff = st.selectbox("Forcer un effet Global :", ["Aucun"] + [k for k in EFFECTS_LIB.keys() if k!="Aucun"], index=0, key="sel_global")
            
            # Mise à jour si changement
            if global_eff != st.session_state.config.get("global_effect"):
                st.session_state.config["global_effect"] = global_eff
                save_config()
                st.toast(f"Global : {global_eff}")
                st.rerun()

            st.markdown("---")
            
            # 2. Configuration par écran
            st.caption("🛠️ CONFIGURATION PAR ÉCRAN (Actif si 'Effet Global' est sur Aucun)")
            
            col_conf, col_visu = st.columns([1.5, 1])
            
            with col_conf:
                # Dictionnaire local pour stocker les choix avant sauvegarde si besoin, 
                # mais ici on update direct pour fluidité
                map_eff = st.session_state.config["screen_effects"]
                
                def update_screen_eff(key, screen_key):
                    val = st.session_state[key]
                    st.session_state.config["screen_effects"][screen_key] = val
                    save_config()

                # Liste des ecrans
                screens = [
                    ("🏠 Accueil (Attente)", "attente"),
                    ("🗳️ Votes Ouverts", "votes_open"),
                    ("🏁 Votes Clos", "votes_closed"),
                    ("🏆 Podium", "podium"),
                    ("📸 Mur Photos", "photos_live")
                ]
                
                # On garde en mémoire le dernier survolé/modifié pour la preview ? 
                # Simplification : On ajoute un selecteur "Voir Preview de..."
                
                preview_target = st.selectbox("👁️ Prévisualiser l'effet de :", [s[0] for s in screens], index=0)
                target_key = next(s[1] for s in screens if s[0] == preview_target)
                
                # Affichage des selectbox pour chaque écran
                st.write("**Réglages des ambiances :**")
                for label, s_key in screens:
                    curr_val = map_eff.get(s_key, "Aucun")
                    # On recupere l'index
                    idx = list(EFFECTS_LIB.keys()).index(curr_val) if curr_val in EFFECTS_LIB else 0
                    st.selectbox(label, list(EFFECTS_LIB.keys()), index=idx, key=f"sel_{s_key}", on_change=update_screen_eff, args=(f"sel_{s_key}", s_key))

            with col_visu:
                st.markdown(f"**Aperçu : {preview_target}**")
                
                # On détermine quel effet montrer dans la boite noire
                # Si Global est actif, on montre global. Sinon on montre celui de l'écran selectionné.
                eff_to_show = "Aucun"
                if st.session_state.config["global_effect"] != "Aucun":
                    eff_to_show = st.session_state.config["global_effect"]
                    st.warning(f"🔒 Global '{eff_to_show}' est actif !")
                else:
                    eff_to_show = st.session_state.config["screen_effects"].get(target_key, "Aucun")
                
                # RENDER PREVIEW BOX
                if eff_to_show in PREVIEW_LIB:
                    components.html(PREVIEW_LIB[eff_to_show], height=250)
                else:
                    st.write("Pas de prévisualisation")

            st.divider()

            # 2. SEQUENCEUR (Reste inchangé)
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
            c_live, c_vide = st.columns([1, 3])
            with c_live:
                if st.button("5. 📸 MUR PHOTOS LIVE", use_container_width=True, type="primary" if m=="photos_live" else "secondary"):
                    cfg.update({"mode_affichage": "photos_live", "session_ouverte": False, "reveal_resultats": False})
                    save_config()
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("🗑️ OPTIONS DE RÉINITIALISATION (Zone de danger)"):
                col_rst, col_info = st.columns([1, 2])
                with col_rst:
                    if st.button("♻️ VIDER LES VOTES", use_container_width=True, help="Remet tout à 0"):
                        for f in [VOTES_FILE, PARTICIPANTS_FILE, VOTERS_FILE, DETAILED_VOTES_FILE]:
                            if os.path.exists(f): os.remove(f)
                        st.session_state.config["session_id"] = str(int(time.time()))
                        save_config()
                        st.toast("✅ Session entièrement réinitialisée !")
                        time.sleep(1); st.rerun()
                    if st.button("🗑️ VIDER PHOTOS LIVE", use_container_width=True):
                        files = glob.glob(f"{LIVE_DIR}/*")
                        for f in files: os.remove(f)
                        st.toast("✅ Galerie Live vidée !")
                        time.sleep(1); st.rerun()
                with col_info: st.info("Efface les scores ou les photos live.")

            st.markdown("---")
            st.subheader("2️⃣ Monitoring")
            voters_list = load_json(VOTERS_FILE, [])
            st.metric("👥 Participants Validés", len(voters_list))
            
            show_summary = st.toggle("📊 Afficher le Graphique & Podiums", value=True)
            if show_summary:
                v_data = load_json(VOTES_FILE, {})
                if v_data:
                    valid = {k:v for k,v in v_data.items() if k in cfg["candidats"]}
                    if valid:
                        import altair as alt
                        df = pd.DataFrame(list(valid.items()), columns=['Candidat', 'Points'])
                        df = df.sort_values('Points', ascending=False).reset_index(drop=True)
                        df['Rang'] = df.index + 1
                        def get_color(rank): return '#FFD700' if rank == 1 else '#C0C0C0' if rank == 2 else '#CD7F32' if rank == 3 else '#E2001A'
                        df['Color'] = df['Rang'].apply(get_color)
                        base = alt.Chart(df).encode(x=alt.X('Points', axis=None), y=alt.Y('Candidat', sort='-x', axis=alt.Axis(labelFontSize=14, title=None)))
                        bars = base.mark_bar().encode(color=alt.Color('Color', scale=None))
                        text = base.mark_text(align='left', baseline='middle', dx=3).encode(text='Points')
                        st.altair_chart((bars + text).properties(height=400).configure_view(strokeWidth=0), use_container_width=True)
                    else: st.info("Aucun vote actif.")
                else: st.info("En attente de votes...")

            show_details = st.toggle("👁️ Afficher le tableau des votants", value=False)
            if show_details:
                st.markdown("##### 🕵️‍♂️ Détail des votes (Live)")
                detailed_votes = load_json(DETAILED_VOTES_FILE, [])
                if detailed_votes:
                    df_details = pd.DataFrame(detailed_votes)
                    if not df_details.empty:
                        st.dataframe(df_details, use_container_width=True, hide_index=True, column_config={"timestamp": "Heure", "user": "Pseudo", "choix_1": "🥇 1er", "choix_2": "🥈 2ème", "choix_3": "🥉 3ème"})
                else: st.info("Aucun vote détaillé.")

        elif menu == "⚙️ Paramétrage":
            st.title("⚙️ Paramétrage")
            t1, t2 = st.tabs(["Identité", "Gestion Questions"])
            with t1:
                new_t = st.text_input("Titre", value=st.session_state.config["titre_mur"], key=f"titre_{st.session_state.refresh_id}")
                if new_t != st.session_state.config["titre_mur"]:
                    if st.button("Sauver Titre"): st.session_state.config["titre_mur"] = new_t; force_refresh(); st.rerun()
                up_l = st.file_uploader("Logo", type=["png", "jpg"])
                if up_l:
                    b64 = process_image_upload(up_l)
                    if b64: st.session_state.config["logo_b64"] = b64; force_refresh(); st.success("Logo chargé !"); st.rerun()
                if st.session_state.config.get("logo_b64"): st.markdown(f'<img src="data:image/png;base64,{st.session_state.config["logo_b64"]}" width="150" style="background:gray; padding:10px;">', unsafe_allow_html=True)
            with t2:
                st.subheader("📋 Liste des Questions")
                current_list = st.session_state.config["candidats"]
                df_cands = pd.DataFrame(current_list, columns=["Nom du Candidat"])
                edited_df = st.data_editor(df_cands, num_rows="dynamic", use_container_width=True, key="editor_cands")
                if st.button("💾 ENREGISTRER LISTE", type="primary"):
                    new_list = [x for x in edited_df["Nom du Candidat"].astype(str).tolist() if x.strip() != ""]
                    st.session_state.config["candidats"] = new_list
                    save_config(); st.success("Mise à jour !"); time.sleep(1); st.rerun()
                st.markdown("---")
                st.subheader("🖼️ Photos Questions")
                if st.session_state.config["candidats"]:
                    sel = st.selectbox("Candidat :", st.session_state.config["candidats"])
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        if sel in st.session_state.config["candidats_images"]:
                            st.image(BytesIO(base64.b64decode(st.session_state.config["candidats_images"][sel])), width=100)
                            if st.button("Supprimer"): del st.session_state.config["candidats_images"][sel]; save_config(); st.rerun()
                        else: st.info("Aucune image")
                    with c2:
                        up = st.file_uploader(f"Image pour {sel}", type=["png", "jpg"])
                        if up:
                            b64 = process_image_upload(up)
                            if b64: st.session_state.config["candidats_images"][sel] = b64; save_config(); st.rerun()

        elif menu == "📸 Médiathèque (Gestion)":
            st.markdown("""<style>div[data-testid="stButton"] button[key="btn_download"] { background-color: #007bff; color: white; border-color: #007bff; } div[data-testid="stButton"] button[key="btn_download"]:hover { background-color: #0056b3; border-color: #0056b3; } div[data-testid="stButton"] button[key="btn_delete"] { background-color: #dc3545; color: white; border-color: #dc3545; } div[data-testid="stButton"] button[key="btn_delete"]:hover { background-color: #a71d2a; border-color: #a71d2a; }</style>""", unsafe_allow_html=True)
            st.title("📸 Médiathèque & Export")
            files = glob.glob(f"{LIVE_DIR}/*"); files.sort(key=os.path.getmtime, reverse=True)
            if not files: st.warning("Aucune photo.")
            else:
                c_sel_all, c_dl, c_del = st.columns([1, 1.5, 1.5], vertical_alignment="center")
                with c_sel_all: select_all = st.checkbox("✅ Tout sélectionner", value=False)
                with c_dl:
                    if select_all:
                        zip_buffer = BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w") as zf:
                            for f in files: zf.write(f, os.path.basename(f))
                        st.download_button(label=f"📥 TÉLÉCHARGER TOUT ({len(files)})", data=zip_buffer.getvalue(), file_name=f"photos_full_{int(time.time())}.zip", mime="application/zip", use_container_width=True, key="btn_download")
                    else: st.caption("Cochez 'Tout sélectionner' ou utilisez la liste.")
                with c_del:
                    if select_all:
                        if st.button(f"🗑️ SUPPRIMER TOUT ({len(files)})", use_container_width=True, key="btn_delete"): st.session_state.confirm_delete = True
                    else: st.caption("Sélectionnez tout pour suppression de masse.")
                if st.session_state.confirm_delete:
                    st.error("⚠️ ATTENTION : SUPPRESSION DÉFINITIVE !")
                    col_conf_1, col_conf_2 = st.columns(2)
                    if col_conf_1.button("✅ OUI, TOUT EFFACER"):
                        for f in files: os.remove(f)
                        st.session_state.confirm_delete = False; st.success("Galerie vidée !"); time.sleep(1); st.rerun()
                    if col_conf_2.button("❌ ANNULER"): st.session_state.confirm_delete = False; st.rerun()
                st.divider()
                view_mode = st.radio("Affichage :", ["▦ Grille", "☰ Liste Détaillée"], horizontal=True, label_visibility="collapsed")
                if "Grille" in view_mode:
                    cols = st.columns(6)
                    for i, f in enumerate(files):
                        with cols[i%6]:
                            st.image(f, use_container_width=True)
                            if st.button("🗑️", key=f"del_g_{i}"): os.remove(f); st.rerun()
                else:
                    manual_selection = []
                    st.write("Sélection manuelle :")
                    h1, h2, h3, h4 = st.columns([0.5, 0.5, 3, 1]); h1.write("**Img**"); h2.write("**Sel**"); h3.write("**Infos**"); h4.write("**Action**")
                    st.markdown("---")
                    for i, f in enumerate(files):
                        c1, c2, c3, c4 = st.columns([0.5, 0.5, 3, 1], vertical_alignment="center")
                        with c1: st.image(f, width=50)
                        with c2: 
                            if st.checkbox("", key=f"sel_man_{i}", label_visibility="collapsed"): manual_selection.append(f)
                        with c3: st.write(f"**{os.path.basename(f)}**")
                        with c4:
                            if st.button("🗑️", key=f"del_l_{i}"): os.remove(f); st.rerun()
                    if manual_selection:
                        st.markdown("---")
                        zip_man = BytesIO()
                        with zipfile.ZipFile(zip_man, "w") as zf:
                            for f in manual_selection: zf.write(f, os.path.basename(f))
                        st.download_button("📥 Télécharger la sélection", data=zip_man.getvalue(), file_name="selection.zip", mime="application/zip")

        elif menu == "📊 Data & Exports":
            st.title("📊 Data & Exports")
            st.subheader("1️⃣ Résultats Globaux (Scores)")
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                valid = {k:v for k,v in v_data.items() if k in st.session_state.config["candidats"]}
                if valid:
                    df = pd.DataFrame(list(valid.items()), columns=['Candidat', 'Points']).sort_values('Points', ascending=False)
                    st.dataframe(df, hide_index=True, use_container_width=True)
                    c1, c2 = st.columns(2)
                    with c1: st.download_button("📥 Télécharger CSV", data=df.to_csv(index=False).encode('utf-8'), file_name=f"resultats_globaux_{int(time.time())}.csv", mime="text/csv", use_container_width=True)
                    with c2:
                        if HAS_FPDF:
                            pdf_bytes = generate_pdf_report(df, "RESULTATS GLOBAUX")
                            st.download_button("📄 Télécharger PDF", data=pdf_bytes, file_name=f"resultats_globaux_{int(time.time())}.pdf", mime="application/pdf", use_container_width=True)
                        else: st.warning("Installez 'fpdf'")
                else: st.info("Aucun vote valide.")
            else: st.info("Aucun vote.")
            st.divider()
            st.subheader("2️⃣ Historique Détaillé (Votants)")
            detailed_votes = load_json(DETAILED_VOTES_FILE, [])
            if detailed_votes:
                df_det = pd.DataFrame(detailed_votes)
                st.dataframe(df_det, hide_index=True, use_container_width=True)
                c1, c2 = st.columns(2)
                with c1: st.download_button("📥 Télécharger CSV", data=df_det.to_csv(index=False).encode('utf-8'), file_name=f"historique_detaille_{int(time.time())}.csv", mime="text/csv", use_container_width=True)
                with c2:
                    if HAS_FPDF:
                        pdf_bytes = generate_pdf_report(df_det, "HISTORIQUE DETAILLE")
                        st.download_button("📄 Télécharger PDF", data=pdf_bytes, file_name=f"historique_detaille_{int(time.time())}.pdf", mime="application/pdf", use_container_width=True)
                    else: st.warning("Installez 'fpdf'")
            else: st.info("Pas d'historique.")
            st.divider()
            st.subheader("⚠️ Réinitialisation")
            st.markdown("""<div style="border: 1px solid red; padding: 15px; border-radius: 5px; background-color: #fff5f5; color: #8b0000;"><strong>ATTENTION :</strong> Efface TOUTES les données.</div><br>""", unsafe_allow_html=True)
            if st.button("🔥 RESET TOUT", type="primary"):
                 for f in [VOTES_FILE, PARTICIPANTS_FILE, VOTERS_FILE, DETAILED_VOTES_FILE]:
                     if os.path.exists(f): os.remove(f)
                 for f in glob.glob(f"{LIVE_DIR}/*"): os.remove(f)
                 st.session_state.config["session_id"] = str(int(time.time()))
                 save_config()
                 st.success("✅ Reset OK ! Session renouvelée."); time.sleep(1); st.rerun()

# --- 4. UTILISATEUR (MOBILE) ---
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, default_config)
    current_session = cfg.get("session_id", "v1")
    ls_key = f"vote_record_{current_session}"

    st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }
        .stApp { background-color: black !important; color: white !important; visibility: hidden; } 
        [data-testid="stHeader"] { display: none !important; }
        h1 { font-size: 1.5rem !important; text-align: center; margin-bottom: 0.5rem !important; }
        .stTabs [data-baseweb="tab-list"] { justify-content: center; }
        div[data-testid="stCameraInput"] button { width: 100%; }
        .stMultiSelect div[data-baseweb="select"] { border: 4px solid white !important; border-radius: 12px !important; box-shadow: 0 0 15px rgba(255, 255, 255, 0.3) !important; }
        .stMultiSelect div[data-baseweb="tag"] { background-color: #E2001A !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)
    
    is_blocked_url = st.query_params.get("blocked") == "yes"
    
    if cfg["mode_affichage"] != "photos_live": 
        components.html(f"""
        <script>
            var voted = localStorage.getItem('{ls_key}');
            if (voted === 'true') {{
                const params = new URLSearchParams(window.location.search);
                if (!params.has('blocked')) {{
                    params.set('blocked', 'yes');
                    window.location.search = params.toString();
                }} else {{
                    var overlay = document.createElement('div');
                    overlay.style.position = 'fixed'; overlay.style.top = '0'; overlay.style.left = '0';
                    overlay.style.width = '100%'; overlay.style.height = '100%';
                    overlay.style.backgroundColor = 'rgba(0,0,0,0.95)'; overlay.style.zIndex = '2147483647';
                    overlay.style.display = 'flex'; overlay.style.flexDirection = 'column';
                    overlay.style.justifyContent = 'center'; overlay.style.alignItems = 'center';
                    overlay.style.color = 'white'; overlay.style.fontFamily = 'sans-serif'; overlay.style.textAlign = 'center';
                    overlay.innerHTML = '<h1 style="font-size:4rem; margin:0;">🚫</h1><h2 style="color:#E2001A; margin-top:20px;">Vote Déjà Enregistré</h2><p style="font-size:1.2rem;">Vous avez déjà soumis votre participation.</p>';
                    window.parent.document.body.appendChild(overlay);
                    var app = window.parent.document.querySelector('.stApp');
                    if (app) app.style.filter = 'blur(10px)';
                }}
            }} else {{
                window.parent.document.querySelector('.stApp').style.visibility = 'visible';
            }}
        </script>
        """, height=0)
    else:
        components.html("""<script>window.parent.document.querySelector('.stApp').style.visibility = 'visible';</script>""", height=0)

    if not is_blocked_url:
        update_presence(is_active_user=True)

    if cfg["mode_affichage"] == "photos_live":
        st.markdown("<h1 style='color:#E2001A;'>📸 MUR PHOTO LIVE</h1>", unsafe_allow_html=True)
        if cfg.get("logo_b64"): st.markdown(f'<div style="text-align:center; margin-bottom:10px;"><img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:60px; width:auto;"></div>', unsafe_allow_html=True)
        tab_native, tab_web = st.tabs(["📱 Téléphone", "💻 Webcam"])
        with tab_native:
            photo_native = st.file_uploader("Prendre une photo", type=["png", "jpg", "jpeg"], key=f"upl_{st.session_state.cam_reset_id}", label_visibility="collapsed")
            if photo_native:
                if save_live_photo(photo_native): st.balloons(); st.toast("✅ Envoyé !", icon="🚀"); st.session_state.cam_reset_id += 1; time.sleep(1.5); st.rerun()
        with tab_web:
            photo_web = st.camera_input("Photo", key=f"cam_{st.session_state.cam_reset_id}", label_visibility="collapsed")
            if photo_web:
                if save_live_photo(photo_web): st.toast("✅ Envoyé !", icon="🚀"); st.session_state.cam_reset_id += 1; time.sleep(0.5); st.rerun()

    else:
        if st.session_state.get("a_vote", False):
            st.balloons()
            st.markdown("""<div style="text-align:center; padding-top:50px;"><div style="font-size:80px;">✅</div><h1 style="color:#E2001A;">Vote Enregistré !</h1><p>Merci d'avoir participé.</p></div>""", unsafe_allow_html=True)
        
        elif not cfg["session_ouverte"]:
            st.title("🗳️ Vote Transdev")
            if cfg.get("logo_b64"): st.markdown(f'<div style="text-align:center; margin-bottom:20px;"><img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:80px; width:auto;"></div>', unsafe_allow_html=True)
            st.warning("⌛ Votes clos ou attente.")
            
        else:
            st.title("🗳️ Vote Transdev")
            if cfg.get("logo_b64"): st.markdown(f'<div style="text-align:center; margin-bottom:20px;"><img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:80px; width:auto;"></div>', unsafe_allow_html=True)
            
            if not st.session_state.user_id:
                nom = st.text_input("Votre Pseudo / Nom :")
                if st.button("Commencer"):
                    if len(nom) > 2:
                        clean_id = nom.strip().lower()
                        voters = load_json(VOTERS_FILE, [])
                        if clean_id in voters: st.error("Ce nom a déjà voté.")
                        else: st.session_state.user_id = clean_id; st.rerun()
                    else: st.warning("Nom invalide.")
            
            elif not st.session_state.rules_accepted:
                st.markdown("""<div style="background:#222; padding:20px; border-radius:10px; border:2px solid #E2001A; margin-bottom:20px;">
                <h3 style="color:#E2001A; margin-top:0;">📜 RÈGLES DU JEU</h3>
                <ul><li>Vous ne pouvez voter qu'<strong>UNE SEULE FOIS</strong>.</li><li>Vous devez sélectionner <strong>3 CHOIX</strong>.</li></ul>
                <hr style="border-color:#555;"><h3 style="color:white; margin-top:10px;">🏆 PONDÉRATION</h3>""", unsafe_allow_html=True)
                pts = cfg.get("points_ponderation", [5, 3, 1])
                st.markdown(f"""* 🥇 **1er Choix :** {pts[0]} Points\n* 🥈 **2ème Choix :** {pts[1]} Points\n* 🥉 **3ème Choix :** {pts[2]} Points</div>""", unsafe_allow_html=True)
                if st.button("✅ J'AI COMPRIS, PASSER AU VOTE", type="primary", use_container_width=True):
                    st.session_state.rules_accepted = True; st.rerun()

            else:
                choix = st.multiselect("Sélectionnez vos 3 favoris :", cfg["candidats"])
                if len(choix) == 3 and st.button("VALIDER MON VOTE", type="primary", use_container_width=True):
                    vts = load_json(VOTES_FILE, {})
                    pts = cfg.get("points_ponderation", [5, 3, 1])
                    for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                    json.dump(vts, open(VOTES_FILE, "w"))
                    
                    voters = load_json(VOTERS_FILE, [])
                    voters.append(st.session_state.user_id)
                    with open(VOTERS_FILE, "w") as f: json.dump(voters, f)
                    
                    details = load_json(DETAILED_VOTES_FILE, [])
                    details.append({"timestamp": datetime.now().strftime("%H:%M:%S"), "user": st.session_state.user_id, "choix_1": choix[0], "choix_2": choix[1], "choix_3": choix[2]})
                    with open(DETAILED_VOTES_FILE, "w") as f: json.dump(details, f)
                    
                    st.session_state["a_vote"] = True
                    components.html(f"""<script>localStorage.setItem('{ls_key}', 'true'); location.reload();</script>""", height=0)
                    time.sleep(1)
                elif len(choix) > 3: st.error("⚠️ 3 choix maximum !")
                elif len(choix) > 0 and len(choix) < 3: st.warning(f"Encore {3-len(choix)} choix.")

# --- 5. MUR SOCIAL ---
else:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=2000, key="wall_autorefresh")
    except ImportError:
        st.error("⚠️ Module 'streamlit-autorefresh' manquant.")
        st.stop()

    st.markdown("""
    <style>
        body, .stApp { background-color: black !important; overflow: hidden; height: 100vh; } 
        [data-testid='stHeader'], footer { display: none !important; } 
        .block-container { padding-top: 1rem !important; padding-bottom: 0 !important; max-width: 98% !important; }
        .participant-badge { display: inline-block; background: rgba(255, 255, 255, 0.1); color: #ccc; border: 1px solid #444; border-radius: 15px; padding: 4px 12px; margin: 4px; font-size: 14px; font-weight: bold; white-space: nowrap; }
        .badges-container { display: flex; flex-wrap: wrap; justify-content: center; max-height: 25vh; overflow-y: auto; margin-top: 10px; padding: 10px; scrollbar-width: none; }
        .badges-container::-webkit-scrollbar { display: none; }
        @keyframes pulse-winner { 0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 215, 0, 0.7); } 70% { transform: scale(1.05); box-shadow: 0 0 20px 10px rgba(255, 215, 0, 0); } 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 215, 0, 0); } }
        .winner-card { animation: pulse-winner 2s infinite; border-color: #FFD700 !important; border-width: 6px !important; z-index: 10; }
    </style>
    """, unsafe_allow_html=True)
    
    config = load_json(CONFIG_FILE, default_config)
    voters_list = load_json(VOTERS_FILE, [])
    nb_p = len(voters_list)
    logo_html = ""
    if config.get("logo_b64"): logo_html = f'<img src="data:image/png;base64,{config["logo_b64"]}" style="max-height:80px; display:block; margin: 0 auto 10px auto;">'

    # --- DECISION LOGIQUE DE L'EFFET A AFFICHER ---
    effect_to_apply = "Aucun"
    
    # 1. Priorité: Effet Global (Force)
    if config.get("global_effect", "Aucun") != "Aucun":
        effect_to_apply = config["global_effect"]
    
    # 2. Sinon: Effet par écran
    else:
        # Determination de la clé d'écran
        screen_key = "attente" # Defaut
        if config["mode_affichage"] == "attente": screen_key = "attente"
        elif config["mode_affichage"] == "photos_live": screen_key = "photos_live"
        elif config["reveal_resultats"]: screen_key = "podium"
        elif config["mode_affichage"] == "votes":
            if config["session_ouverte"]: screen_key = "votes_open"
            else: screen_key = "votes_closed"
            
        effect_to_apply = config["screen_effects"].get(screen_key, "Aucun")

    # 3. Injection
    inject_visual_effect(effect_to_apply)

    # --- AFFICHAGE ECRANS ---
    
    if config["mode_affichage"] != "photos_live":
        st.markdown(f'<div style="text-align:center; color:white;">{logo_html}<h1 style="font-size:40px; font-weight:bold; text-transform:uppercase; margin:0; line-height:1.1;">{config["titre_mur"]}</h1></div>', unsafe_allow_html=True)

    if config["mode_affichage"] == "attente":
        st.markdown(f"""<div style="text-align:center; color:white; margin-top:80px;"><div style="{BADGE_CSS}">✨ BIENVENUE ✨</div><h2 style="font-size:50px; margin-top:40px; font-weight:lighter;">L'événement va commencer...</h2></div>""", unsafe_allow_html=True)

    elif config["mode_affichage"] == "photos_live":
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        
        logo_live = ""
        if config.get("logo_b64"):
            logo_live = f'<img src="data:image/png;base64,{config["logo_b64"]}" style="max-height:250px; width:auto; display:block; margin: 0 auto 20px auto;">'
        title_html = '<h1 style="color:white; font-size:60px; font-weight:bold; text-transform:uppercase; margin-bottom:20px; text-shadow: 0 0 10px rgba(0,0,0,0.5);">MUR PHOTOS LIVE</h1>'

        st.markdown(f"""<div style="position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); z-index:9999; display:flex; flex-direction:column; align-items:center; gap:20px;">{logo_live}{title_html}<div style="background:white; padding:20px; border-radius:25px; box-shadow: 0 0 60px rgba(0,0,0,0.8);"><img src="data:image/png;base64,{qr_b64}" width="160" style="display:block;"></div><div style="background: #E2001A; color: white; padding: 15px 40px; border-radius: 50px; font-weight: bold; font-size: 26px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-transform: uppercase; white-space: nowrap; border: 2px solid white;">📸 SCANNEZ POUR PARTICIPER</div></div>""", unsafe_allow_html=True)
        photos = glob.glob(f"{LIVE_DIR}/*"); photos.sort(key=os.path.getmtime, reverse=True); recent_photos = photos[:40] 
        img_array_js = []
        for photo_path in recent_photos:
            with open(photo_path, "rb") as f: b64 = base64.b64encode(f.read()).decode(); img_array_js.append(f"data:image/jpeg;base64,{b64}")
        js_img_list = json.dumps(img_array_js)
        components.html(f"""<html><head><style>body {{ margin: 0; overflow: hidden; background: transparent; }} .bubble {{ position: absolute; border-radius: 50%; border: 4px solid #E2001A; box-shadow: 0 0 20px rgba(226, 0, 26, 0.5); object-fit: cover; will-change: transform; }}</style></head><body><div id="container"></div><script>const images = {js_img_list}; const container = document.getElementById('container'); const bubbles = []; const speed = 2.5; const centerX_min = window.innerWidth * 0.35; const centerX_max = window.innerWidth * 0.65; const centerY_min = window.innerHeight * 0.30; const centerY_max = window.innerHeight * 0.70; images.forEach((src, index) => {{ const img = document.createElement('img'); img.src = src; img.className = 'bubble'; const size = 80 + Math.random() * 150; let startX, startY; do {{ startX = Math.random() * (window.innerWidth - 150); startY = Math.random() * (window.innerHeight - 150); }} while (startX > centerX_min && startX < centerX_max && startY > centerY_min && startY < centerY_max); const bubble = {{ element: img, x: startX, y: startY, vx: (Math.random() - 0.5) * speed * 2, vy: (Math.random() - 0.5) * speed * 2, size: size }}; img.style.width = bubble.size + 'px'; img.style.height = bubble.size + 'px'; container.appendChild(img); bubbles.push(bubble); }}); function animate() {{ const w = window.innerWidth; const h = window.innerHeight; bubbles.forEach(b => {{ b.x += b.vx; b.y += b.vy; if (b.x <= 0 || b.x + b.size >= w) b.vx *= -1; if (b.y <= 0 || b.y + b.size >= h) b.vy *= -1; if (b.x + b.size > centerX_min && b.x < centerX_max && b.y + b.size > centerY_min && b.y < centerY_max) {{ const centerX = (centerX_min + centerX_max) / 2; if (b.x < centerX) b.vx = -Math.abs(b.vx); else b.vx = Math.abs(b.vx); }} b.element.style.transform = `translate(${{b.x}}px, ${{b.y}}px)`; }}); requestAnimationFrame(animate); }} animate();</script></body></html>""", height=900)

    elif config["mode_affichage"] == "votes" and not config["reveal_resultats"]:
        st.markdown(f'<div style="text-align:center; margin-top:5px; margin-bottom:5px;"><div style="background:white; display:inline-block; padding:2px 15px; border-radius:15px; color:black; font-weight:bold; font-size:16px;">👥 {nb_p} PARTICIPANTS</div></div>', unsafe_allow_html=True)
        if voters_list:
            badges_html = "".join([f'<div class="participant-badge">{v}</div>' for v in voters_list[::-1]])
            st.markdown(f'<div class="badges-container">{badges_html}</div>', unsafe_allow_html=True)
        if config["session_ouverte"]:
            host = st.context.headers.get('host', 'localhost')
            qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            cands = config["candidats"]; mid = (len(cands) + 1) // 2
            def get_item_html(label):
                img_html = '<span style="font-size:30px; margin-right:15px;">🎥</span>'
                if label in config.get("candidats_images", {}):
                    b64 = config["candidats_images"][label]
                    img_html = f'<img src="data:image/png;base64,{b64}" style="width:50px; height:50px; object-fit:cover; border-radius:8px; margin-right:10px; border:2px solid #E2001A;">'
                return f'<div style="background:#222; color:white; padding:8px; margin-bottom:8px; border-left:4px solid #E2001A; font-weight:bold; font-size:18px; display:flex; align-items:center;">{img_html}{label}</div>'
            st.markdown("<div style='margin-top:20px;'>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 0.6, 1])
            with c1:
                for c in cands[:mid]: st.markdown(get_item_html(c), unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div style="background:white; padding:4px; border-radius:10px; text-align:center; margin: 0 auto; width: fit-content;"><img src="data:image/png;base64,{qr_b64}" width="160" style="display:block;"><p style="color:black; font-weight:bold; margin-top:5px; margin-bottom:0; font-size:14px;">SCANNEZ</p></div>', unsafe_allow_html=True)
                st.markdown(f'<div style="text-align:center; margin-top:15px;"><div style="{BADGE_CSS} animation:blink 1.5s infinite; font-size:18px; padding:8px 20px;">🚀 VOTES OUVERTS</div></div>', unsafe_allow_html=True)
            with c3:
                for c in cands[mid:]: st.markdown(get_item_html(c), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div style="text-align:center; color:white; margin-top:80px;"><div style="{BADGE_CSS} background:#333; animation: none;">🏁 LES VOTES SONT CLOS</div><div style="font-size:120px; margin-top:40px;">🙏</div><h1 style="color:#E2001A; font-size:50px; margin-top:20px;">MERCI DE VOTRE PARTICIPATION</h1></div>""", unsafe_allow_html=True)

    elif config["reveal_resultats"]:
        diff = 10 - int(time.time() - config.get("timestamp_podium", 0))
        if diff > 0:
            st.markdown(f"""<div style="text-align:center; margin-top:80px;"><div style="font-size:250px; color:#E2001A; font-weight:bold;">{diff}</div></div>""", unsafe_allow_html=True)
            time.sleep(0.5); st.rerun()
        else:
            v_data = load_json(VOTES_FILE, {})
            valid = {k:v for k,v in v_data.items() if k in config["candidats"]}
            sorted_v = sorted(valid.items(), key=lambda x: x[1], reverse=True)[:3]
            top_score = sorted_v[0][1] if sorted_v else 0
            winners = [x for x in sorted_v if x[1] == top_score]
            is_tie = len(winners) > 1
            title_text = "🏆 LES VAINQUEURS SONT..." if is_tie else "🏆 LE GAGNANT EST..."
            st.markdown(f'<div style="text-align:center;"><div style="{BADGE_CSS}">{title_text}</div></div>', unsafe_allow_html=True)
            cols = st.columns(3)
            ranks = ["🥇", "🥈", "🥉"]; colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
            for i, (name, score) in enumerate(sorted_v):
                is_winner = (score == top_score)
                css_class = "winner-card" if is_winner else ""
                rank_icon = ranks[0] if is_winner else (ranks[i] if i < 3 else "")
                border_col = colors[0] if is_winner else (colors[i] if i < 3 else "#333")
                img_p = ""
                if name in config.get("candidats_images", {}):
                     img_p = f'<img src="data:image/png;base64,{config["candidats_images"][name]}" style="width:120px; height:120px; border-radius:50%; border:4px solid {border_col}; display:block; margin:0 auto 15px auto;">'
                cols[i].markdown(f"""<div class="{css_class}" style="background:#1a1a1a; padding:30px; border:4px solid {border_col}; text-align:center; color:white; margin-top:30px; border-radius:20px;"><h2>{rank_icon}</h2>{img_p}<h1>{name}</h1><p>{score} pts</p></div>""", unsafe_allow_html=True)
            components.html('<script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script><script>confetti({particleCount:300,spread:120,origin:{y:0},gravity:1.2,drift:0});</script>', height=0)
