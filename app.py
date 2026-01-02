import streamlit as st
import os, glob, base64, qrcode, json, random, pandas as pd
from io import BytesIO
import streamlit.components.v1 as components
import time
from PIL import Image
from datetime import datetime
import zipfile
import uuid
import textwrap

# --- GESTION PDF & ALTAIR (Conservation de vos imports) ---
try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

try:
    import altair as alt
    HAS_ALTAIR = True
except ImportError:
    HAS_ALTAIR = False

# --- 1. CONFIGURATION & FICHIERS ---
st.set_page_config(page_title="Régie Master - IT SQUAD", layout="wide", initial_sidebar_state="collapsed")

GALLERY_DIR, ADMIN_DIR, LIVE_DIR = "galerie_images", "galerie_admin", "galerie_live_users"
VOTES_FILE, PARTICIPANTS_FILE, CONFIG_FILE, VOTERS_FILE, DETAILED_VOTES_FILE = "votes.json", "participants.json", "config_mur.json", "voters.json", "detailed_votes.json"

for d in [GALLERY_DIR, ADMIN_DIR, LIVE_DIR]:
    if not os.path.exists(d): os.makedirs(d)

DEFAULT_CANDIDATS = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]

# --- UTILITAIRES DE PERSISTANCE ---
def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding='utf-8') as f: return json.load(f)
        except: return default
    return default

def save_json(file, data):
    with open(file, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def render_html(html_code):
    clean_code = textwrap.dedent(html_code).strip().replace("\n", " ")
    st.markdown(clean_code, unsafe_allow_html=True)

# --- INIT CONFIG ---
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
        "effect_intensity": 25, 
        "effect_speed": 25,     
        "screen_effects": {"attente": "Aucun", "votes_open": "Aucun", "podium": "🎉 Confettis", "photos_live": "Aucun"}
    })

def save_config():
    save_json(CONFIG_FILE, st.session_state.config)

def process_image_upload(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        img.thumbnail((300, 300))
        buffered = BytesIO()
        img.save(buffered, format="PNG") 
        return base64.b64encode(buffered.getvalue()).decode()
    except: return None

def save_live_photo(uploaded_file):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(LIVE_DIR, f"live_{timestamp}_{uuid.uuid4().hex[:4]}.jpg")
        img = Image.open(uploaded_file).convert("RGB")
        img.thumbnail((800, 800)) 
        img.save(filepath, "JPEG", quality=80)
        return True
    except: return False

# --- NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
is_blocked = st.query_params.get("blocked") == "true"

# =========================================================
# 1. CONSOLE ADMIN (FIX : ANTI-CLIGNOTEMENT)
# =========================================================
if est_admin:
    logo_b64 = st.session_state.config.get("logo_b64")
    logo_admin_css = f"url('data:image/png;base64,{logo_b64}')" if logo_b64 else "none"
    
    st.markdown(f"""
    <style>
        .fixed-header {{
            position: fixed; top: 0; left: 0; width: 100%; height: 70px;
            background-color: #1E1E1E; z-index: 10000;
            display: flex; align-items: center; justify-content: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-bottom: 2px solid #E2001A;
        }}
        .header-title {{ color: white; font-size: 24px; font-weight: bold; text-transform: uppercase; }}
        .header-logo {{ position: absolute; right: 20px; top: 5px; height: 60px; width: 120px; background-size: contain; background-repeat: no-repeat; background-position: right center; background-image: {logo_admin_css}; }}
        .main .block-container {{ padding-top: 80px; }}
    </style>
    <div class="fixed-header">
        <div class="header-title">Console Admin Gestion des Votes</div>
        <div class="header-logo"></div>
    </div>
    """, unsafe_allow_html=True)

    if "auth" not in st.session_state: st.session_state["auth"] = False
    if not st.session_state["auth"]:
        pwd = st.text_input("Code Secret IT SQUAD", type="password")
        if pwd == "ADMIN_LIVE_MASTER": st.session_state["auth"] = True; st.rerun()
    else:
        with st.sidebar:
            st.title("🎛️ RÉGIE")
            menu = st.radio("Menu", ["🔴 PILOTAGE LIVE", "⚙️ Paramétrage", "📸 Médiathèque", "📊 Data"])
            if st.button("🔓 Déconnexion"): st.session_state["auth"] = False; st.rerun()

        if menu == "🔴 PILOTAGE LIVE":
            st.title("🔴 COCKPIT LIVE")
            cfg = st.session_state.config
            c1, c2, c3, c4 = st.columns(4)
            m, vo, re = cfg["mode_affichage"], cfg["session_ouverte"], cfg["reveal_resultats"]

            if c1.button("1. ACCUEIL", type="primary" if m=="attente" else "secondary", use_container_width=True):
                cfg.update({"mode_affichage": "attente", "session_ouverte": False, "reveal_resultats": False}); save_config(); st.rerun()
            if c2.button("2. VOTES ON", type="primary" if (m=="votes" and vo) else "secondary", use_container_width=True):
                cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False}); save_config(); st.rerun()
            if c3.button("3. VOTES OFF", type="primary" if (m=="votes" and not vo and not re) else "secondary", use_container_width=True):
                cfg["session_ouverte"] = False; save_config(); st.rerun()
            if c4.button("4. PODIUM", type="primary" if re else "secondary", use_container_width=True):
                cfg.update({"mode_affichage": "votes", "reveal_resultats": True, "timestamp_podium": time.time()}); save_config(); st.rerun()

            st.divider()
            if st.button("5. 📸 MUR PHOTOS LIVE", type="primary" if m=="photos_live" else "secondary", use_container_width=True):
                cfg.update({"mode_affichage": "photos_live", "session_ouverte": False}); save_config(); st.rerun()
            
            st.subheader("📡 Monitoring")
            voters_list = load_json(VOTERS_FILE, [])
            st.metric("👥 Participants Validés", len(voters_list))

        elif menu == "⚙️ Paramétrage":
            st.title("⚙️ Configuration")
            t1, t2 = st.tabs(["Général", "Candidats & Images"])
            with t1:
                new_t = st.text_input("Titre Événement", value=st.session_state.config["titre_mur"])
                if st.button("Sauver Titre"): st.session_state.config["titre_mur"] = new_t; save_config(); st.rerun()
                up_l = st.file_uploader("Logo PNG", type=["png", "jpg"])
                if up_l:
                    b64 = process_image_upload(up_l)
                    if b64: st.session_state.config["logo_b64"] = b64; save_config(); st.rerun()
            with t2:
                df_cands = pd.DataFrame(st.session_state.config["candidats"], columns=["Candidat"])
                edited_df = st.data_editor(df_cands, num_rows="dynamic", use_container_width=True)
                if st.button("💾 Enregistrer Liste"):
                    st.session_state.config["candidats"] = [x for x in edited_df["Candidat"].tolist() if x]
                    save_config(); st.rerun()

        elif menu == "📸 Médiathèque":
            st.title("📸 Médiathèque & Export")
            files = glob.glob(f"{LIVE_DIR}/*")
            if files:
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for f in files: zf.write(f, os.path.basename(f))
                st.download_button("📥 TÉLÉCHARGER TOUT", data=zip_buffer.getvalue(), file_name="photos.zip")
                if st.button("🗑️ TOUT SUPPRIMER", type="primary"):
                    for f in files: os.remove(f)
                    st.rerun()
                cols = st.columns(6)
                for i, f in enumerate(files):
                    with cols[i%6]:
                        st.image(f, use_container_width=True)
                        if st.button("❌", key=f"del_{i}"): os.remove(f); st.rerun()
            else: st.info("Galerie vide.")

        elif menu == "📊 Data":
            st.title("📊 Résultats")
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                df = pd.DataFrame(list(v_data.items()), columns=['Candidat', 'Points']).sort_values('Points', ascending=False)
                st.dataframe(df, use_container_width=True)
                if HAS_ALTAIR:
                    chart = alt.Chart(df).mark_bar().encode(x='Points', y=alt.Y('Candidat', sort='-x'), color='Points')
                    st.altair_chart(chart, use_container_width=True)

# =========================================================
# 2. APPLICATION MOBILE (FIX : VALIDATION & BALLONS)
# =========================================================
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, st.session_state.config)
    st.markdown("<style>.stApp {background-color:black; color:white;} [data-testid='stHeader'] {display:none;}</style>", unsafe_allow_html=True)
    
    if not is_blocked:
        components.html("<script>if(localStorage.getItem('voted_2026')) { window.parent.location.href += '&blocked=true'; }</script>", height=0)

    if is_blocked:
        st.error("⛔ Participation déjà enregistrée. Merci !")
        st.balloons()
        st.stop()

    if "user_pseudo" not in st.session_state:
        st.title("👋 Bienvenue")
        pseudo = st.text_input("Ton Prénom")
        if st.button("ENTRER", type="primary", use_container_width=True) and pseudo:
            st.session_state.user_pseudo = pseudo; st.rerun()
    else:
        if cfg["mode_affichage"] == "photos_live":
            st.subheader("📸 Partage ta photo sur le mur !")
            cam = st.camera_input("Sourire !", key="cam_mobile")
            if cam and save_live_photo(cam): st.success("Photo envoyée !"); time.sleep(1); st.rerun()
        else:
            if not cfg["session_ouverte"]: st.warning("⏳ Les votes ne sont pas encore ouverts.")
            else:
                st.write(f"Agent: **{st.session_state.user_pseudo}**")
                # Correction Focus : Le multiselect prévient Streamlit à chaque changement
                choix = st.multiselect("Choisis tes 3 vidéos favorites :", cfg["candidats"], max_selections=3, key="v_multi")
                
                if len(choix) == 3:
                    st.markdown("---")
                    if st.button("🚀 VALIDER MON VOTE", type="primary", use_container_width=True):
                        # Animation Ballons JS
                        components.html("""<script>
                            for(let i=0; i<25; i++) {
                                let b = window.parent.document.createElement('div');
                                b.innerHTML = '🎈'; b.style.cssText = 'position:fixed; bottom:-50px; left:'+(Math.random()*100)+'vw; font-size:30px; z-index:10001; transition: transform '+(2+Math.random()*2)+'s linear;';
                                window.parent.document.body.appendChild(b);
                                setTimeout(() => b.style.transform = 'translateY(-120vh)', 50);
                            }
                            setTimeout(() => { localStorage.setItem('voted_2026', 'true'); window.parent.location.reload(); }, 2000);
                        </script>""", height=0)
                        
                        vts = load_json(VOTES_FILE, {})
                        for v in choix: vts[v] = vts.get(v, 0) + 1
                        save_json(VOTES_FILE, vts)
                        
                        voters = load_json(VOTERS_FILE, [])
                        voters.append(st.session_state.user_pseudo); save_json(VOTERS_FILE, voters)
                        
                        st.info("Transmission sécurisée...")
                elif len(choix) > 0:
                    st.info(f"Sélectionnez encore {3 - len(choix)} vidéo(s)")

# =========================================================
# 3. MUR SOCIAL (FIX : BULLES 220PX & REBOND & GLOW)
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2000, key="wall_refresh")
    cfg = load_json(CONFIG_FILE, st.session_state.config)
    
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700&display=swap');
        body, .stApp {{ background-color: black !important; overflow: hidden; height: 100vh; font-family: 'Montserrat', sans-serif; }} 
        [data-testid='stHeader'] {{ display: none !important; }} 
        .block-container {{ padding: 0 !important; max-width: 100% !important; }}
        
        .social-header {{ 
            position: fixed; top: 0; left: 0; width: 100%; height: 12vh;
            background: #E2001A; display: flex; align-items: center; justify-content: center;
            border-bottom: 5px solid white; z-index: 1000;
        }}
        .social-title {{ color: white; font-size: 50px; text-transform: uppercase; margin: 0; }}

        .winner-box {{ margin-top: 25vh; text-align: center; display: flex; flex-direction: column; align-items: center; z-index: 500; position: relative; }}
        .winner-card {{ 
            background: rgba(10, 10, 10, 0.9); border: 8px solid #FFD700; border-radius: 40px; padding: 40px 60px;
            animation: glow-gold 2s infinite alternate;
        }}
        @keyframes glow-gold {{
            from {{ box-shadow: 0 0 20px #B8860B; }}
            to {{ box-shadow: 0 0 80px #FFD700, 0 0 30px #FFF; }}
        }}
    </style>
    <div class="social-header"><h1 class="social-title">{cfg['titre_mur']}</h1></div>
    """, unsafe_allow_html=True)

    mode = cfg.get("mode_affichage")
    
    if mode == "attente":
        st.markdown("<h1 style='text-align:center; color:white; margin-top:40vh; font-size:100px;'>BIENVENUE</h1>", unsafe_allow_html=True)

    elif mode == "votes" or mode == "photos_live":
        if cfg.get("reveal_resultats"):
            v_data = load_json(VOTES_FILE, {})
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)
            if sorted_v:
                winner, pts = sorted_v[0]
                st.balloons()
                st.markdown(f"""<div class="winner-box"><div class="winner-card"><h1 style="color:#FFD700; font-size:100px; margin:0;">🏆</h1><h1 style="color:white; font-size:80px; margin:20px 0;">{winner}</h1><h2 style="color:#FFD700; font-size:40px; margin:0;">VAINQUEUR - {pts} POINTS</h2></div></div>""", unsafe_allow_html=True)
        else:
            host = st.context.headers.get('host', 'localhost')
            qr_buf = BytesIO(); qrcode.make(f"http://{host}/?mode=vote").save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            st.markdown(f"""
            <div style="position:fixed; top:55%; left:50%; transform:translate(-50%, -50%); z-index:100; background:white; padding:30px; border-radius:30px; text-align:center; border: 10px solid #E2001A;">
                <img src="data:image/png;base64,{qr_b64}" width="280">
                <h2 style="color:black; margin-top:20px; font-size:30px;">SCANNEZ POUR PARTICIPER</h2>
            </div>""", unsafe_allow_html=True)

        # ANIMATION BULLES 220PX AVEC REBOND SUR QR
        photos = glob.glob(f"{LIVE_DIR}/*")
        if photos:
            img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-25:]])
            components.html(f"""
            <script>
                var doc = window.parent.document;
                var container = doc.getElementById('bubble-wall') || doc.createElement('div');
                container.id = 'bubble-wall'; container.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:1;pointer-events:none;';
                if(!doc.getElementById('bubble-wall')) doc.body.appendChild(container);
                
                const imgs = {img_js}; const bubbles = []; const bSize = 220;
                const qrRect = {{ x: window.innerWidth/2 - 200, y: window.innerHeight/2 - 200, w: 400, h: 450 }};

                imgs.forEach((src, i) => {{
                    if(doc.getElementById('bub-'+i)) return;
                    const el = doc.createElement('img'); el.id = 'bub-'+i; el.src = src;
                    el.style.cssText = 'position:absolute; width:'+bSize+'px; height:'+bSize+'px; border-radius:50%; border:6px solid #E2001A; object-fit:cover; box-shadow: 0 10px 30px rgba(0,0,0,0.5);';
                    let x = Math.random() * (window.innerWidth - bSize); let y = Math.random() * (window.innerHeight - bSize);
                    let vx = (Math.random()-0.5)*4; let vy = (Math.random()-0.5)*4;
                    container.appendChild(el); bubbles.push({{el, x, y, vx, vy, size: bSize}});
                }});

                function animate() {{
                    bubbles.forEach(b => {{
                        b.x += b.vx; b.y += b.vy;
                        if(b.x <= 0 || b.x + b.size >= window.innerWidth) b.vx *= -1;
                        if(b.y <= 0 || b.y + b.size >= window.innerHeight) b.vy *= -1;
                        // Rebond QR Code
                        if(b.x + b.size > qrRect.x && b.x < qrRect.x + qrRect.w && b.y + b.size > qrRect.y && b.y < qrRect.y + qrRect.h) {{
                            b.vx *= -1; b.vy *= -1; b.x += b.vx*5; b.y += b.vy*5;
                        }}
                        b.el.style.transform = `translate(${{b.x}}px, ${{b.y}}px)`;
                    }});
                    requestAnimationFrame(animate);
                }} animate();
            </script>""", height=0)
