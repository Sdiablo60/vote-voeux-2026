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

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Régie Master - IT SQUAD", layout="wide", initial_sidebar_state="collapsed")

GALLERY_DIR, LIVE_DIR = "galerie_images", "galerie_live_users"
VOTES_FILE, CONFIG_FILE, VOTERS_FILE, DETAILED_VOTES_FILE = "votes.json", "config_mur.json", "voters.json", "detailed_votes.json"

for d in [GALLERY_DIR, LIVE_DIR]:
    if not os.path.exists(d): os.makedirs(d)

DEFAULT_CANDIDATS = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding='utf-8') as f: return json.load(f)
        except: return default
    return default

def save_json(file, data):
    with open(file, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

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
        "screen_effects": {"attente": "Aucun", "votes_open": "Aucun", "podium": "🎉 Confettis"}
    })

# --- NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
is_blocked = st.query_params.get("blocked") == "true"

# =========================================================
# 1. CONSOLE ADMIN (FIX : ANTI-CLIGNOTEMENT)
# =========================================================
if est_admin:
    logo_b64 = st.session_state.config.get("logo_b64")
    logo_style = f"background-image: url('data:image/png;base64,{logo_b64}');" if logo_b64 else ""
    st.markdown(f"""<style>
        .fixed-header {{ position: fixed; top: 0; left: 0; width: 100%; height: 70px; background: #1E1E1E; z-index: 10000; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #E2001A; }}
        .header-title {{ color: white; font-size: 22px; font-weight: bold; text-transform: uppercase; }}
        .header-logo {{ position: absolute; right: 20px; top: 5px; height: 60px; width: 120px; background-size: contain; background-repeat: no-repeat; {logo_style} }}
        .main .block-container {{ padding-top: 100px; }}
    </style><div class="fixed-header"><div class="header-title">Console Admin Gestion des Votes</div><div class="header-logo"></div></div>""", unsafe_allow_html=True)

    if "auth" not in st.session_state: st.session_state["auth"] = False
    if not st.session_state["auth"]:
        pwd = st.text_input("Code Secret", type="password")
        if pwd == "ADMIN_LIVE_MASTER": st.session_state["auth"] = True; st.rerun()
    else:
        with st.sidebar:
            st.title("🎛️ RÉGIE")
            menu = st.radio("Menu", ["🔴 PILOTAGE LIVE", "⚙️ Paramétrage", "📸 MÉDIATHÈQUE", "📊 DATA"])
            if st.button("🔓 Déconnexion"): st.session_state["auth"] = False; st.rerun()

        if menu == "🔴 PILOTAGE LIVE":
            cfg = st.session_state.config
            c1, c2, c3, c4 = st.columns(4)
            if c1.button("🏠 ACCUEIL"):
                cfg.update({"mode_affichage": "attente", "session_ouverte": False, "reveal_resultats": False}); save_json(CONFIG_FILE, cfg); st.rerun()
            if c2.button("🗳️ VOTES ON"):
                cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False}); save_json(CONFIG_FILE, cfg); st.rerun()
            if c3.button("🔒 VOTES OFF"):
                cfg["session_ouverte"] = False; save_json(CONFIG_FILE, cfg); st.rerun()
            if c4.button("🏆 PODIUM"):
                cfg.update({"mode_affichage": "votes", "reveal_resultats": True, "timestamp_podium": time.time()}); save_json(CONFIG_FILE, cfg); st.rerun()
            st.divider()
            if st.button("📸 MUR PHOTOS LIVE", type="primary", use_container_width=True):
                cfg.update({"mode_affichage": "photos_live", "session_ouverte": False}); save_json(CONFIG_FILE, cfg); st.rerun()

        elif menu == "📸 MÉDIATHÈQUE":
            st.title("📸 Photos Live (Triées par Date)")
            files = glob.glob(f"{LIVE_DIR}/*")
            files.sort(key=os.path.getmtime, reverse=True)
            cols = st.columns(4)
            for i, f in enumerate(files):
                with cols[i%4]:
                    st.image(f, caption=f"Reçue à {datetime.fromtimestamp(os.path.getmtime(f)).strftime('%H:%M:%S')}")
                    if st.button("Supprimer", key=f"del_{i}"): os.remove(f); st.rerun()

        elif menu == "📊 DATA":
            st.title("📊 Données & Export Excel")
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                df = pd.DataFrame(list(v_data.items()), columns=['Candidat', 'Points']).sort_values('Points', ascending=False)
                st.dataframe(df, use_container_width=True)
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Resultats')
                st.download_button("📥 EXPORTER EXCEL", data=output.getvalue(), file_name="resultats_votes.xlsx")

# =========================================================
# 2. APPLICATION MOBILE (FIX : ANTI-FRAUDE & ANIMATION)
# =========================================================
elif est_utilisateur:
    st.markdown("<style>.stApp {background-color:black; color:white;} [data-testid='stHeader'] {display:none;}</style>", unsafe_allow_html=True)
    
    # 1. ANTI-FRAUDE STRICT (Injection locale)
    components.html("""<script>
        if(localStorage.getItem('vote_completed_2026')) {
            if(!window.parent.location.href.includes('blocked=true')) {
                window.parent.location.href = window.parent.location.href + '&blocked=true';
            }
        }
    </script>""", height=0)

    if is_blocked:
        st.markdown("<div style='text-align:center; margin-top:50px;'><h2>✅ VOTE ENREGISTRÉ</h2><p>Merci pour votre participation !</p></div>", unsafe_allow_html=True)
        st.stop()

    if "user_pseudo" not in st.session_state:
        pseudo = st.text_input("Ton prénom :")
        if st.button("VALIDER L'IDENTITÉ", type="primary", use_container_width=True) and pseudo:
            st.session_state.user_pseudo = pseudo; st.rerun()
    else:
        cfg = load_json(CONFIG_FILE, st.session_state.config)
        if cfg["mode_affichage"] == "photos_live":
            st.camera_input("📸 Ta photo sur le mur")
        else:
            if not cfg["session_ouverte"]: st.info("⏳ En attente des votes...")
            else:
                choix = st.multiselect("Choisis tes 3 favoris :", cfg["candidats"], max_selections=3)
                if len(choix) == 3:
                    st.markdown("---")
                    # BOUTON TOUJOURS VISIBLE SI 3 CHOIX
                    if st.button("🚀 VALIDER MON VOTE", type="primary", use_container_width=True):
                        # 2. ANIMATION ET BLOCAGE JS
                        components.html("""<script>
                            // Animation Ballons
                            for(let i=0; i<35; i++) {
                                let b = window.parent.document.createElement('div');
                                b.innerHTML = '🎈'; b.style.position='fixed'; b.style.bottom='-50px';
                                b.style.left = Math.random()*100+'vw'; b.style.fontSize = (25+Math.random()*25)+'px';
                                b.style.zIndex='99999'; b.style.transition = 'transform '+(2+Math.random()*2)+'s ease-in';
                                window.parent.document.body.appendChild(b);
                                setTimeout(() => b.style.transform = 'translateY(-130vh)', 50);
                            }
                            // Sauvegarde Double Vote
                            localStorage.setItem('vote_completed_2026', 'true');
                            // Redirection
                            setTimeout(() => { window.parent.location.href += '&blocked=true'; }, 2800);
                        </script>""", height=0)
                        
                        vts = load_json(VOTES_FILE, {})
                        for v in choix: vts[v] = vts.get(v, 0) + 1
                        save_json(VOTES_FILE, vts)
                        st.info("Transmission en cours... 🎈")
                        time.sleep(3)

# =========================================================
# 3. MUR SOCIAL (FIX : CADRE VAINQUEUR & SANS CONFETTI ACCUEIL)
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2000, key="wall_refresh")
    cfg = load_json(CONFIG_FILE, st.session_state.config)
    
    st.markdown(f"""<style>
        body, .stApp {{ background-color: black !important; overflow: hidden; height: 100vh; font-family: 'Montserrat', sans-serif; }} 
        [data-testid='stHeader'] {{ display: none !important; }} 
        .social-header {{ position: fixed; top: 0; left: 0; width: 100%; height: 12vh; background: #E2001A; display: flex; align-items: center; justify-content: center; border-bottom: 5px solid white; z-index: 2000; }}
        .social-title {{ color: white; font-size: 50px; text-transform: uppercase; margin: 0; }}
        
        /* GAGNANT : TAILLE FIXE 400PX ET POSITION BASSE */
        .winner-box {{ 
            position: absolute; 
            top: 62%; /* Descendu pour ne pas toucher le titre */
            left: 50%; 
            transform: translate(-50%, -50%); 
            width: 400px; /* Taille réduite demandée */
            text-align: center; 
            z-index: 1000; 
        }}
        .winner-card {{ 
            background: rgba(15, 15, 15, 0.95); border: 10px solid #FFD700; border-radius: 50px; padding: 30px;
            box-shadow: 0 0 50px #FFD700; animation: glow-gold 1.5s infinite alternate;
        }}
        @keyframes glow-gold {{ from {{ box-shadow: 0 0 20px #FFD700; }} to {{ box-shadow: 0 0 70px #FFD700, 0 0 20px #FFF; }} }}
    </style><div class="social-header"><h1 class="social-title">{cfg['titre_mur']}</h1></div>""", unsafe_allow_html=True)

    mode = cfg.get("mode_affichage")
    
    # --- FIX : SUPPRESSION DES CONFETTIS SUR L'ACCUEIL ---
    if mode == "attente":
        components.html("<script>var l = window.parent.document.getElementById('effect-layer'); if(l) l.remove();</script>", height=0)
        st.markdown("<h1 style='text-align:center; color:white; margin-top:45vh; font-size:80px;'>BIENVENUE</h1>", unsafe_allow_html=True)
    
    elif mode == "votes" or mode == "photos_live":
        if cfg.get("reveal_resultats"):
            v_data = load_json(VOTES_FILE, {})
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)
            if sorted_v:
                winner, pts = sorted_v[0]
                st.balloons()
                st.markdown(f"""<div class="winner-box"><div class="winner-card"><h1 style="color:#FFD700; font-size:80px; margin:0;">🏆</h1><h1 style="color:white; font-size:55px; margin:10px 0;">{winner}</h1><h2 style="color:#FFD700; font-size:25px; margin:0;">VAINQUEUR - {pts} POINTS</h2></div></div>""", unsafe_allow_html=True)
        else:
            host = st.context.headers.get('host', 'localhost')
            qr_buf = BytesIO(); qrcode.make(f"http://{host}/?mode=vote").save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            st.markdown(f"""<div style="position:fixed; top:55%; left:50%; transform:translate(-50%, -50%); z-index:1500; background:white; padding:30px; border-radius:30px; text-align:center; border: 10px solid #E2001A;">
                <img src="data:image/png;base64,{qr_b64}" width="250"><h2 style="color:black; margin-top:20px; font-size:25px;">SCANNEZ POUR VOTER</h2></div>""", unsafe_allow_html=True)

        # BULLES 220PX AVEC REBOND
        photos = glob.glob(f"{LIVE_DIR}/*")
        if photos:
            img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-20:]])
            components.html(f"""<script>
                var doc = window.parent.document;
                var container = doc.getElementById('bubble-wall') || doc.createElement('div');
                container.id = 'bubble-wall'; container.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:1;pointer-events:none;';
                if(!doc.getElementById('bubble-wall')) doc.body.appendChild(container);
                const imgs = {img_js}; const bubbles = []; const bSize = 220;
                const qrRect = {{ x: window.innerWidth/2 - 225, y: window.innerHeight/2 - 225, w: 450, h: 450 }};
                imgs.forEach((src, i) => {{
                    if(doc.getElementById('bub-'+i)) return;
                    const el = doc.createElement('img'); el.id = 'bub-'+i; el.src = src;
                    el.style.cssText = 'position:absolute; width:'+bSize+'px; height:'+bSize+'px; border-radius:50%; border:6px solid #E2001A; object-fit:cover;';
                    let x = Math.random() * (window.innerWidth - bSize); let y = Math.random() * (window.innerHeight - bSize);
                    let vx = (Math.random()-0.5)*5; let vy = (Math.random()-0.5)*5;
                    container.appendChild(el); bubbles.push({{el, x, y, vx, vy, size: bSize}});
                }});
                function animate() {{
                    bubbles.forEach(b => {{
                        b.x += b.vx; b.y += b.vy;
                        if(b.x <= 0 || b.x + b.size >= window.innerWidth) b.vx *= -1;
                        if(b.y <= 12 * window.innerHeight / 100 || b.y + b.size >= window.innerHeight) b.vy *= -1;
                        if(b.x + b.size > qrRect.x && b.x < qrRect.x + qrRect.w && b.y + b.size > qrRect.y && b.y < qrRect.y + qrRect.h) {{
                            b.vx *= -1; b.vy *= -1; b.x += b.vx*5; b.y += b.vy*5;
                        }}
                        b.el.style.transform = `translate(${{b.x}}px, ${{b.y}}px)`;
                    }});
                    requestAnimationFrame(animate);
                }} animate();
            </script>""", height=0)
