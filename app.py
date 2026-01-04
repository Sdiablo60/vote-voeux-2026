import streamlit as st
import os, glob, base64, qrcode, json, time, uuid, textwrap, zipfile, shutil
from io import BytesIO
import streamlit.components.v1 as components
from PIL import Image
from datetime import datetime
import pandas as pd
import random
import altair as alt

# TENTATIVE D'IMPORT DE FPDF
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# --- CONFIGURATION ---
st.set_page_config(page_title="Régie Master", layout="wide", initial_sidebar_state="expanded")

# Dossiers & Fichiers
LIVE_DIR = "galerie_live_users"
VOTES_FILE = "votes.json"
CONFIG_FILE = "config_mur.json"
VOTERS_FILE = "voters.json"
PARTICIPANTS_FILE = "participants.json"
DETAILED_VOTES_FILE = "detailed_votes.json"

for d in [LIVE_DIR]:
    if not os.path.exists(d): os.makedirs(d)

# --- AVATAR ---
DEFAULT_AVATAR = "iVBORw0KGgoAAAANSUhEUgAAAOEAAADhCAMAAAAJbSJIAAAAM1BMVEXk5ueutLfn6Onj5Oa+wsO2u73q6+zg4eKxvL2/w8Tk5ebl5ufm5+nm6Oni4+Tp6uvr7O24w8qOAAACvklEQVR4nO3b23KCMBBAUYiCoKD+/792RC0iF1ApOcvM2rO+lF8S50ymL6cdAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADgX0a9eT6f13E67e+P5yV/7V6Z5/V0Wubb7XKZl/x9e1Zm3u/reZ7y9+1VmV/X/Xad8vftzT/97iX/3J6V6e+365S/b6/KjP/7cf9u06f8fXtV5vF43L/bdMrft2dl5v1+u075+/aqzL/rfrtO+fv2qsz/frtO+fv2qsz4v9+uU/6+vSoz/u+365S/b6/KjP/7Trl79urMuP/frtO+fv2qsz4v9+uU/6+vSoz/u+365S/b6/KjP/7Trl79urMuP/frtO+fv2qsz4v9+uU/6+vSoz/u+365S/b6/KjP/7Trl79urMuP/frtO+fv2qsz4v9+uU/6+vSoz/u+365S/b6/KjP/7Trl79urMuP/frtO+fv2qsz4v9+uU/6+vSoz/u+365S/b6/KjP/7Trl79urMuP/frtO+fv2qsz4v9+uU/6+vSoz/u+365S/b6/KjP/7Trl79urMuP/frtO+fv2qsz4v9+uU/6+vSoz/u+365S/b6/KjP/7Trl79urMgMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP/xG2nLBH198qZpAAAAAElFTkSuQmCC"

# --- CONFIG PAR DÉFAUT ---
default_config = {
    "mode_affichage": "attente", 
    "titre_mur": "CONCOURS VIDÉO 2026", 
    "session_ouverte": False, 
    "reveal_resultats": False,
    "timestamp_podium": 0,
    "logo_b64": None,
    "candidats": ["BU PAX", "BU FRET", "BU B2B", "RH", "IT", "DPMI", "FINANCES", "AO", "QSSE", "DIRECTION"],
    "candidats_images": {}, 
    "points_ponderation": [5, 3, 1],
    "effect_intensity": 25, 
    "effect_speed": 15, 
    "screen_effects": {"attente": "Aucun", "votes_open": "Aucun", "votes_closed": "Aucun", "podium": "Aucun", "photos_live": "Aucun"},
    "session_id": str(uuid.uuid4())
}

# --- FONCTIONS ---
def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding='utf-8') as f:
                content = f.read().strip()
                return json.loads(content) if content else default
        except: return default
    return default

def save_json(file, data):
    with open(file, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def save_config():
    save_json(CONFIG_FILE, st.session_state.config)

# --- GÉNÉRATEUR PDF ---
if PDF_AVAILABLE:
    class PDFReport(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.set_text_color(226, 0, 26)
            self.cell(0, 10, 'REGIE MASTER - RAPPORT OFFICIEL', 0, 1, 'C')
            self.ln(5)
    def create_pdf_results(title, df):
        pdf = PDFReport()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14); pdf.cell(200, 10, txt=f"Resultats: {title}", ln=True)
        pdf.set_font("Arial", size=10); pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True); pdf.ln(10)
        for i, row in df.iterrows():
            pdf.cell(100, 10, str(row['Candidat']), 1); pdf.cell(40, 10, str(row['Points']), 1, 1, 'C')
        return pdf.output(dest='S').encode('latin-1')

# --- CALLBACKS RÉGIE ---
def set_state(mode, open_s, reveal):
    st.session_state.config["mode_affichage"] = mode
    st.session_state.config["session_ouverte"] = open_s
    st.session_state.config["reveal_resultats"] = reveal
    if reveal: st.session_state.config["timestamp_podium"] = time.time()
    save_config()

def reset_app_data():
    for f in [VOTES_FILE, VOTERS_FILE, PARTICIPANTS_FILE, DETAILED_VOTES_FILE]:
        if os.path.exists(f): os.remove(f)
    for f in glob.glob(f"{LIVE_DIR}/*"): os.remove(f)
    st.session_state.config["session_id"] = str(uuid.uuid4())
    save_config(); st.rerun()

def process_image(uploaded_file):
    try:
        img = Image.open(uploaded_file); img.thumbnail((800, 800))
        buf = BytesIO(); img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except: return None

# =========================================================
# 1. CONSOLE ADMIN
# =========================================================
if st.query_params.get("admin") == "true":
    st.title("🎛️ RÉGIE")
    if "auth" not in st.session_state: st.session_state["auth"] = False
    if not st.session_state["auth"]:
        if st.text_input("Code", type="password") == "ADMIN_LIVE_MASTER": st.session_state["auth"] = True; st.rerun()
    else:
        menu = st.sidebar.radio("Menu", ["PILOTAGE", "CONFIG", "MÉDIATHÈQUE", "DATA"])
        cfg = st.session_state.config
        
        if menu == "PILOTAGE":
            c1, c2, c3, c4 = st.columns(4)
            c1.button("🏠 ACCUEIL", on_click=set_state, args=("attente", False, False))
            c2.button("🗳️ VOTES ON", on_click=set_state, args=("votes", True, False))
            c3.button("🏆 PODIUM", on_click=set_state, args=("votes", False, True))
            c4.button("📸 PHOTO LIVE", on_click=set_state, args=("photos_live", False, False))
            if st.button("🗑️ RESET TOTAL"): reset_app_data()

        elif menu == "CONFIG":
            new_t = st.text_input("Titre Mur", value=cfg["titre_mur"])
            if st.button("Save Titre"): cfg["titre_mur"] = new_t; save_config()
            upl = st.file_uploader("Logo")
            if upl: cfg["logo_b64"] = process_image(upl); save_config()
            st.subheader("Candidats (15 max)")
            for i, cand in enumerate(cfg['candidats']):
                col1, col2 = st.columns([3, 1])
                new_n = col1.text_input(f"Nom {i}", value=cand, key=f"c_{i}")
                if new_n != cand: cfg['candidats'][i] = new_n; save_config(); st.rerun()
                up_c = col2.file_uploader(f"Img {i}", key=f"img_{i}")
                if up_c: cfg["candidats_images"][cand] = process_image(up_c); save_config(); st.rerun()

        elif menu == "MÉDIATHÈQUE":
            files = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
            if st.button("🗑️ TOUT SUPPRIMER"):
                for f in files: os.remove(f)
                st.rerun()
            cols = st.columns(5)
            for i, f in enumerate(files):
                with cols[i%5]:
                    st.image(f)
                    if st.checkbox("Sél.", key=f"chk_{i}"): pass
            
            zip_buf = BytesIO()
            with zipfile.ZipFile(zip_buf, "w") as zf:
                for idx, f in enumerate(files):
                    ts = os.path.getmtime(f); date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                    zf.write(f, arcname=f"Photo_Live{idx+1:02d}_{date_str}.jpg")
            st.download_button("⬇️ TÉLÉCHARGER ZIP", zip_buf.getvalue(), "photos.zip")

        elif menu == "DATA":
            votes = load_json(VOTES_FILE, {})
            df = pd.DataFrame(list(votes.items()), columns=['Candidat', 'Points']).sort_values(by='Points', ascending=False)
            st.dataframe(df)
            if PDF_AVAILABLE: st.download_button("📄 PDF", create_pdf_results(cfg['titre_mur'], df), "resultats.pdf")

# =========================================================
# 2. APPLICATION MOBILE
# =========================================================
elif st.query_params.get("mode") == "vote":
    cfg = load_json(CONFIG_FILE, default_config)
    st.markdown("<style>.stApp {background-color:black; color:white;}</style>", unsafe_allow_html=True)
    
    if cfg["mode_affichage"] == "photos_live":
        st.subheader("📸 PARTAGEZ VOS PHOTOS")
        cam = st.camera_input("Prendre une photo", key=f"cam_{time.time()}")
        up = st.file_uploader("Ou importer", type=['jpg', 'png'])
        img = cam if cam else up
        if img:
            with open(os.path.join(LIVE_DIR, f"{uuid.uuid4().hex}.jpg"), "wb") as f: f.write(img.getbuffer())
            st.success("Envoyé !"); time.sleep(1); st.rerun()
    else:
        # LOGIQUE VOTE (Sécurisée par LocalStorage)
        components.html(f"""<script>
            if(localStorage.getItem('VOTED_{cfg["session_id"]}') === 'true') {{
                window.parent.location.href = window.parent.location.href + '&blocked=true';
            }}
        </script>""", height=0)
        
        if st.query_params.get("blocked") == "true":
            st.title("✅ MERCI !")
            st.write("Votre vote est déjà enregistré.")
        else:
            pseudo = st.text_input("Prénom / Pseudo")
            if pseudo:
                st.info("Sélectionnez 3 vidéos (1er=5pt, 2e=3pt, 3e=1pt)")
                choix = st.multiselect("Vidéos", cfg["candidats"], max_selections=3)
                if len(choix) == 3 and st.button("VALIDER MON VOTE"):
                    vts = load_json(VOTES_FILE, {})
                    for i, p in enumerate([5, 3, 1]): vts[choix[i]] = vts.get(choix[i], 0) + p
                    save_json(VOTES_FILE, vts)
                    components.html(f"<script>localStorage.setItem('VOTED_{cfg['session_id']}', 'true'); window.parent.location.reload();</script>")

# =========================================================
# 3. MUR SOCIAL
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2000, key="wall_refresh")
    cfg = load_json(CONFIG_FILE, default_config)
    
    st.markdown("""
    <style>
        body, .stApp { background-color: black !important; overflow: hidden !important; }
        [data-testid='stHeader'] { display: none; }
        .social-header { position: fixed; top: 0; left: 0; width: 100%; height: 12vh; background: #E2001A; display: flex; align-items: center; justify-content: center; z-index: 5000; border-bottom: 5px solid white; }
        .social-title { color: white; font-size: 45px; font-weight: bold; text-transform: uppercase; }
        .full-screen-center { position:fixed; top:0; left:0; width:100vw; height:100vh; display:flex; flex-direction:column; justify-content:center; align-items:center; z-index: 2; }
        .cand-row { display: flex; align-items: center; margin-bottom: 10px; background: rgba(255,255,255,0.1); padding: 10px; border-radius: 50px; width: 350px; border: 1px solid #E2001A; }
        .cand-img { width: 60px; height: 60px; border-radius: 50%; object-fit: cover; margin-right: 15px; border: 2px solid white; }
        .winner-card { background: rgba(20,20,20,0.95); border: 10px solid #FFD700; border-radius: 50px; padding: 40px; text-align: center; box-shadow: 0 0 80px #FFD700; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f'<div class="social-header"><div class="social-title">{cfg["titre_mur"]}</div></div>', unsafe_allow_html=True)

    mode = cfg["mode_affichage"]
    
    if mode == "attente":
        logo = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="width:400px;">' if cfg["logo_b64"] else ""
        st.markdown(f"<div class='full-screen-center'>{logo}<h1 style='color:white; font-size:100px;'>BIENVENUE</h1></div>", unsafe_allow_html=True)

    elif mode == "votes":
        if cfg["reveal_resultats"]:
            v_data = load_json(VOTES_FILE, {})
            max_v = max(v_data.values()) if v_data else 0
            winners = [k for k, v in v_data.items() if v == max_v]
            
            cards = ""
            for w in winners:
                img = f"data:image/png;base64,{cfg['candidats_images'].get(w, '')}" if cfg['candidats_images'].get(w) else ""
                img_tag = f"<img src='{img}' style='width:200px; height:200px; border-radius:50%; border:5px solid white;'>" if img else "<div style='font-size:100px;'>🏆</div>"
                cards += f"<div class='winner-card'>{img_tag}<h1 style='color:white; font-size:60px;'>{w}</h1><h2 style='color:#FFD700;'>VAINQUEUR</h2></div>"
            st.markdown(f"<div class='full-screen-center'><div style='display:flex; gap:30px;'>{cards}</div></div>", unsafe_allow_html=True)
        else:
            # AFFICHAGE VOTE ON
            cands = cfg["candidats"]
            mid = (len(cands) + 1) // 2
            colL, colC, colR = st.columns([1, 1, 1])
            with colL:
                st.markdown("<br><br><br><br>", unsafe_allow_html=True)
                for c in cands[:mid]:
                    img = cfg["candidats_images"].get(c, "")
                    src = f"data:image/png;base64,{img}" if img else "https://via.placeholder.com/60"
                    st.markdown(f"<div class='cand-row'><img src='{src}' class='cand-img'><span style='color:white; font-size:20px;'>{c}</span></div>", unsafe_allow_html=True)
            with colC:
                st.markdown("<div style='height:15vh'></div>", unsafe_allow_html=True)
                if cfg["logo_b64"]: st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), width=350)
                qr_buf = BytesIO(); qrcode.make(f"https://{st.context.headers.get('host','localhost')}/?mode=vote").save(qr_buf, format="PNG")
                st.image(qr_buf, width=250)
                st.markdown("<h2 style='color:#E2001A; text-align:center;'>SCANNEZ POUR VOTER</h2>", unsafe_allow_html=True)
            with colR:
                st.markdown("<br><br><br><br>", unsafe_allow_html=True)
                for c in cands[mid:]:
                    img = cfg["candidats_images"].get(c, "")
                    src = f"data:image/png;base64,{img}" if img else "https://via.placeholder.com/60"
                    st.markdown(f"<div class='cand-row'><img src='{src}' class='cand-img'><span style='color:white; font-size:20px;'>{c}</span></div>", unsafe_allow_html=True)

    elif mode == "photos_live":
        photos = glob.glob(f"{LIVE_DIR}/*")
        img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-30:]])
        
        # --- MOTEUR BILLARD V4 ---
        components.html(f"""
        <div id="box" style="position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); width:400px; height:400px; background:rgba(0,0,0,0.8); border:5px solid #E2001A; border-radius:30px; display:flex; flex-direction:column; align-items:center; justify-content:center; z-index:100; color:white; text-align:center;">
            <h2 style="margin:0;">PHOTO LIVE</h2>
            <p>Envoyez vos moments !</p>
        </div>
        <script>
            var doc = window.parent.document;
            var wall = doc.getElementById('wall') || doc.createElement('div');
            wall.id = 'wall'; wall.style.cssText = 'position:fixed; top:0; left:0; width:100vw; height:100vh; z-index:1; pointer-events:none; overflow:hidden;';
            if(!doc.getElementById('wall')) doc.body.appendChild(wall);
            wall.innerHTML = ''; 

            const imgs = {img_js}; const bubbles = [];
            imgs.forEach(src => {{
                const size = Math.random() * 120 + 80;
                const el = doc.createElement('img');
                el.src = src;
                el.style.cssText = 'position:absolute; width:'+size+'px; height:'+size+'px; border-radius:50%; border:4px solid #E2001A; object-fit:cover;';
                
                // Spawn Aléatoire partout sauf tout en haut
                let x = Math.random() * (window.innerWidth - size);
                let y = 200 + Math.random() * (window.innerHeight - 200 - size);
                
                // Vitesse et Angle aléatoires
                let speed = 2 + Math.random() * 3;
                let angle = Math.random() * Math.PI * 2;
                
                bubbles.push({{ el, x, y, vx: Math.cos(angle)*speed, vy: Math.sin(angle)*speed, size }});
                wall.appendChild(el);
            }});

            function update() {{
                bubbles.forEach(b => {{
                    b.x += b.vx; b.y += b.vy;
                    // Rebond Gauche/Droite
                    if(b.x <= 0 || b.x + b.size >= window.innerWidth) b.vx *= -1;
                    // Rebond Bas
                    if(b.y + b.size >= window.innerHeight) b.vy *= -1;
                    // Rebond Plafond (Titre)
                    if(b.y <= 180) {{ b.y = 180; b.vy *= -1; }}
                    
                    b.el.style.transform = 'translate3d('+b.x+'px,'+b.y+'px,0)';
                }});
                requestAnimationFrame(update);
            }}
            update();
        </script>
        """, height=0)
