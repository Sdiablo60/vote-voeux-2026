import streamlit as st
import os, glob, base64, qrcode, json, time, uuid, textwrap, zipfile, shutil
from io import BytesIO
import streamlit.components.v1 as components
from PIL import Image
from datetime import datetime
import pandas as pd
import random
import altair as alt # Nécessaire pour le graphique fixe

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

# --- FONCTIONS UTILITAIRES ---
def clean_for_json(data):
    if isinstance(data, dict): return {k: clean_for_json(v) for k, v in data.items()}
    elif isinstance(data, list): return [clean_for_json(v) for v in data]
    elif isinstance(data, (str, int, float, bool, type(None))): return data
    else: return str(data)

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding='utf-8') as f:
                content = f.read().strip()
                if not content: return default
                return json.loads(content)
        except: return default
    return default

def save_json(file, data):
    try:
        safe_data = clean_for_json(data)
        with open(str(file), "w", encoding='utf-8') as f:
            json.dump(safe_data, f, ensure_ascii=False, indent=4)
    except Exception as e: print(f"Erreur Save: {e}")

def save_config():
    save_json(CONFIG_FILE, st.session_state.config)

# --- CALLBACKS ADMIN ---
def set_state(mode, open_s, reveal):
    st.session_state.config["mode_affichage"] = mode
    st.session_state.config["session_ouverte"] = open_s
    st.session_state.config["reveal_resultats"] = reveal
    if reveal:
        st.session_state.config["timestamp_podium"] = time.time()
    save_config()

def reset_app_data():
    for f in [VOTES_FILE, VOTERS_FILE, PARTICIPANTS_FILE, DETAILED_VOTES_FILE]:
        if os.path.exists(f): os.remove(f)
    files = glob.glob(f"{LIVE_DIR}/*")
    for f in files: os.remove(f)
    
    st.session_state.config["session_id"] = str(uuid.uuid4())
    save_config()
    st.toast("✅ RESET TOTAL EFFECTUÉ !", icon="🗑️")
    time.sleep(1)

def process_image(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        img.thumbnail((300, 300))
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except: return None

def get_file_info(filepath):
    try:
        ts = os.path.getmtime(filepath)
        return datetime.fromtimestamp(ts).strftime("%H:%M:%S")
    except:
        return "Inconnu"

def inject_visual_effect(effect_name, intensity, speed):
    if effect_name == "Aucun" or effect_name == "🎉 Confettis":
        components.html("<script>var old = window.parent.document.getElementById('effect-layer'); if(old) old.remove();</script>", height=0)
        return
    duration = max(3, 25 - (speed * 0.4)) 
    interval = int(5000 / (intensity + 1))
    js_code = f"""
    <script>
        var doc = window.parent.document;
        var layer = doc.getElementById('effect-layer');
        if(!layer) {{
            layer = doc.createElement('div');
            layer.id = 'effect-layer';
            layer.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:0;overflow:hidden;';
            doc.body.appendChild(layer);
        }}
        function createBalloon() {{
            var e = doc.createElement('div'); e.innerHTML = '🎈';
            e.style.cssText = 'position:absolute;bottom:-100px;left:'+Math.random()*100+'vw;font-size:'+(Math.random()*40+30)+'px;transition:bottom {duration}s linear;';
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
    if effect_name == "🎈 Ballons": js_code += f"if(!window.balloonInterval) window.balloonInterval = setInterval(createBalloon, {interval});"
    elif effect_name == "❄️ Neige": js_code += f"if(!window.snowInterval) window.snowInterval = setInterval(createSnow, {interval});"
    
    js_code += "</script>"
    components.html(js_code, height=0)

# --- NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
is_blocked = st.query_params.get("blocked") == "true"

# --- INIT SESSION ---
if "config" not in st.session_state:
    st.session_state.config = load_json(CONFIG_FILE, default_config)

# =========================================================
# 1. CONSOLE ADMIN
# =========================================================
if est_admin:
    st.title("🎛️ CONSOLE RÉGIE")
    st.write("---")
    
    if "auth" not in st.session_state: st.session_state["auth"] = False
    if not st.session_state["auth"]:
        if st.text_input("Code Admin", type="password") == "ADMIN_LIVE_MASTER":
            st.session_state["auth"] = True; st.rerun()
    else:
        cfg = st.session_state.config
        with st.sidebar:
            if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), use_container_width=True)
            st.header("MENU")
            menu = st.radio("Navigation", ["🔴 PILOTAGE LIVE", "⚙️ CONFIG", "📸 MÉDIATHÈQUE", "📊 DATA"])
            st.divider()
            st.markdown("""<a href="/" target="_blank" style="display:block; text-align:center; background:#E2001A; color:white; padding:10px; border-radius:5px; text-decoration:none;">📺 OUVRIR MUR SOCIAL</a>""", unsafe_allow_html=True)
            st.markdown("""<a href="/?mode=vote" target="_blank" style="display:block; text-align:center; background:#333; color:white; padding:10px; border-radius:5px; text-decoration:none;">📱 TESTER MOBILE</a>""", unsafe_allow_html=True)
            if st.button("🔓 DÉCONNEXION"): st.session_state["auth"] = False; st.rerun()

        if menu == "🔴 PILOTAGE LIVE":
            st.subheader("Séquenceur")
            etat = "Inconnu"
            if cfg["mode_affichage"] == "attente": etat = "ACCUEIL"
            elif cfg["mode_affichage"] == "votes":
                if cfg["reveal_resultats"]: etat = "PODIUM"
                elif cfg["session_ouverte"]: etat = "VOTES OUVERTS"
                else: etat = "VOTES FERMÉS"
            elif cfg["mode_affichage"] == "photos_live": etat = "PHOTOS LIVE"
            st.info(f"État actuel : **{etat}**")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.button("🏠 ACCUEIL", use_container_width=True, type="primary" if cfg["mode_affichage"]=="attente" else "secondary", on_click=set_state, args=("attente", False, False))
            c2.button("🗳️ VOTES ON", use_container_width=True, type="primary" if (cfg["mode_affichage"]=="votes" and cfg["session_ouverte"]) else "secondary", on_click=set_state, args=("votes", True, False))
            c3.button("🔒 VOTES OFF", use_container_width=True, type="primary" if (cfg["mode_affichage"]=="votes" and not cfg["session_ouverte"] and not cfg["reveal_resultats"]) else "secondary", on_click=set_state, args=("votes", False, False))
            c4.button("🏆 PODIUM", use_container_width=True, type="primary" if cfg["reveal_resultats"] else "secondary", on_click=set_state, args=("votes", False, True))

            st.markdown("---")
            st.button("📸 MUR PHOTOS LIVE", use_container_width=True, type="primary" if cfg["mode_affichage"]=="photos_live" else "secondary", on_click=set_state, args=("photos_live", False, False))

            st.divider()
            with st.expander("🚨 ZONE DE DANGER"):
                if st.button("🗑️ RESET TOTAL", type="primary"):
                    reset_app_data()
                    st.rerun()

        elif menu == "⚙️ CONFIG":
            t1, t2 = st.tabs(["Général", "Candidats"])
            with t1:
                new_t = st.text_input("Titre", value=cfg["titre_mur"])
                if st.button("Sauver Titre"): st.session_state.config["titre_mur"] = new_t; save_config(); st.rerun()
                upl = st.file_uploader("Logo", type=["png", "jpg"])
                if upl: st.session_state.config["logo_b64"] = process_image(upl); save_config(); st.rerun()
            with t2:
                for i, c in enumerate(cfg["candidats"]):
                    c1, c2 = st.columns([1, 4])
                    with c1:
                        if c in cfg.get("candidats_images", {}): st.image(BytesIO(base64.b64decode(cfg["candidats_images"][c])), width=50)
                    with c2:
                        up = st.file_uploader(f"Image pour {c}", key=f"u_{i}")
                        if up: st.session_state.config.setdefault("candidats_images", {})[c] = process_image(up); save_config(); st.rerun()

        elif menu == "📸 MÉDIATHÈQUE":
            st.subheader("Gestion des Photos Live")
            if st.button("🗑️ TOUT SUPPRIMER D'UN COUP", type="primary"):
                files = glob.glob(f"{LIVE_DIR}/*")
                for f in files: os.remove(f)
                st.success("Toutes les photos ont été supprimées.")
                time.sleep(1)
                st.rerun()
            st.divider()
            files = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
            if not files:
                st.info("Aucune photo pour le moment.")
            else:
                with st.form("media_form"):
                    col_actions = st.columns(2)
                    delete_btn = col_actions[0].form_submit_button("Supprimer la sélection")
                    download_btn = col_actions[1].form_submit_button("Télécharger la sélection (ZIP)")
                    st.write("---")
                    cols = st.columns(5)
                    selected_files = []
                    for i, f in enumerate(files):
                        date_str = get_file_info(f)
                        with cols[i % 5]:
                            st.image(f, use_container_width=True)
                            if st.checkbox(f"#{len(files)-i} ({date_str})", key=f"chk_{os.path.basename(f)}"):
                                selected_files.append(f)
                    if delete_btn and selected_files:
                        for f in selected_files: os.remove(f)
                        st.success(f"{len(selected_files)} photos supprimées.")
                        time.sleep(1); st.rerun()
                    if download_btn and selected_files:
                        zip_buffer = BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w") as zf:
                            for file_path in selected_files:
                                zf.write(file_path, os.path.basename(file_path))
                        st.download_button(label="💾 TÉLÉCHARGER LE ZIP", data=zip_buffer.getvalue(), file_name=f"photos_live_{int(time.time())}.zip", mime="application/zip")

        elif menu == "📊 DATA":
            st.subheader("📊 Résultats & Export")
            
            # --- CALCUL DES SCORES ---
            votes = load_json(VOTES_FILE, {})
            # Assurer que tous les candidats sont là
            all_cands = {c: 0 for c in cfg["candidats"]}
            all_cands.update(votes)
            df_totals = pd.DataFrame(list(all_cands.items()), columns=['Candidat', 'Points'])
            df_totals = df_totals.sort_values(by='Points', ascending=False)
            
            # --- GRAPHIQUE FIXE (Altair) ---
            # Le zoom est désactivé par défaut si on n'ajoute pas .interactive()
            chart = alt.Chart(df_totals).mark_bar(color="#E2001A").encode(
                x=alt.X('Points', title='Points'),
                y=alt.Y('Candidat', sort='-x', title='Candidat'),
                tooltip=['Candidat', 'Points']
            ).properties(height=400)
            
            st.altair_chart(chart, use_container_width=True)
            
            # --- EXPORTS ---
            col_exp1, col_exp2, col_exp3 = st.columns(3)
            
            # 1. CSV
            csv = df_totals.to_csv(index=False).encode('utf-8')
            col_exp1.download_button("📥 Export CSV", data=csv, file_name="resultats.csv", mime="text/csv")
            
            # 2. EXCEL (Tentative)
            try:
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_totals.to_excel(writer, sheet_name='Resultats', index=False)
                col_exp2.download_button("📊 Export Excel", data=buffer.getvalue(), file_name="resultats.xlsx", mime="application/vnd.ms-excel")
            except:
                col_exp2.warning("Excel non dispo")

            # 3. HTML (Pour PDF)
            html_content = f"""
            <html><head><style>body{{font-family:Arial;}} table{{width:100%;border-collapse:collapse;}} th,td{{border:1px solid #ddd;padding:8px;text-align:left;}} th{{background-color:#E2001A;color:white;}}</style></head>
            <body>
            <h1>Rapport de Votes - {cfg['titre_mur']}</h1>
            <p>Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            {df_totals.to_html(index=False)}
            </body></html>
            """
            col_exp3.download_button("📄 Rapport Imprimable (Pour PDF)", data=html_content, file_name="rapport_print.html", mime="text/html")

            # DETAIL DES VOTES
            st.divider()
            st.subheader("Détail des votes (Audit)")
            detailed_data = load_json(DETAILED_VOTES_FILE, [])
            if detailed_data:
                df_detail = pd.DataFrame(detailed_data)
                st.dataframe(df_detail, use_container_width=True)
            else:
                st.info("Aucun détail disponible.")

# =========================================================
# 2. APPLICATION MOBILE
# =========================================================
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, default_config)
    st.markdown("<style>.stApp {background-color:black; color:white;} [data-testid='stHeader'] {display:none;}</style>", unsafe_allow_html=True)
    
    curr_sess = cfg.get("session_id", "init")
    if "vote_success" not in st.session_state: st.session_state.vote_success = False
    
    if "rules_accepted" not in st.session_state: st.session_state.rules_accepted = False
    if "cam_reset_id" not in st.session_state: st.session_state.cam_reset_id = 0

    # 1. GESTION AUTOMATIQUE MODE PHOTO (Bypass Login)
    if cfg["mode_affichage"] == "photos_live":
        if "user_pseudo" not in st.session_state or st.session_state.user_pseudo != "Anonyme":
            st.session_state.user_pseudo = "Anonyme"
    # 2. GESTION RETOUR VOTE (Force Login)
    elif cfg["mode_affichage"] == "votes":
        if "user_pseudo" in st.session_state and st.session_state.user_pseudo == "Anonyme":
            del st.session_state["user_pseudo"]
            st.rerun()

    # --- SÉCURITÉ RENFORCÉE (UNIQUEMENT POUR LE VOTE) ---
    if cfg["mode_affichage"] != "photos_live":
        components.html(f"""<script>
            var sS = "{curr_sess}";
            var lS = localStorage.getItem('VOTE_SID_2026');
            if(lS !== sS) {{ 
                localStorage.removeItem('HAS_VOTED_2026'); 
                localStorage.setItem('VOTE_SID_2026', sS); 
                if(window.parent.location.href.includes('blocked=true')) {{
                    window.parent.location.href = window.parent.location.href.replace('&blocked=true','');
                }}
            }}
            if(localStorage.getItem('HAS_VOTED_2026') === 'true') {{
                if(!window.parent.location.href.includes('blocked=true')) {{
                    window.parent.location.href = window.parent.location.href.split('?')[0] + '?mode=vote&blocked=true';
                }}
            }}
        </script>""", height=0)

        # Si bloqué : ON ARRÊTE TOUT ICI
        if is_blocked or st.session_state.vote_success:
            st.balloons()
            st.markdown("""<div style='text-align:center; margin-top:50px; padding:20px;'><h1 style='color:#E2001A;'>MERCI !</h1><h2 style='color:white;'>Vote enregistré.</h2><br><div style='font-size:80px;'>✅</div><p style='color:#777; margin-top:20px;'>Un seul vote autorisé par appareil.</p></div>""", unsafe_allow_html=True)
            components.html("""<script>localStorage.setItem('HAS_VOTED_2026', 'true');</script>""", height=0)
            st.stop() # FIN DU SCRIPT POUR L'UTILISATEUR BLOQUÉ

    # --- ECRAN D'IDENTIFICATION ---
    if "user_pseudo" not in st.session_state:
        st.subheader("Identification")
        if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), width=100)
        pseudo = st.text_input("Veuillez entrer votre prénom ou Pseudo :")
        if st.button("ENTRER", type="primary", use_container_width=True) and pseudo:
            voters = load_json(VOTERS_FILE, [])
            if pseudo.strip().upper() in [v.upper() for v in voters]: st.error("Ce pseudo est déjà utilisé.")
            else:
                st.session_state.user_pseudo = pseudo.strip()
                parts = load_json(PARTICIPANTS_FILE, [])
                if pseudo.strip() not in parts: parts.append(pseudo.strip()); save_json(PARTICIPANTS_FILE, parts)
                st.rerun()
    else:
        # --- MODE PHOTO ---
        if cfg["mode_affichage"] == "photos_live":
            st.info("📸 ENVOYER UNE PHOTO")
            
            up_key = f"uploader_{st.session_state.cam_reset_id}"
            cam_key = f"camera_{st.session_state.cam_reset_id}"
            
            uploaded_file = st.file_uploader("Choisir dans la galerie", type=['png', 'jpg', 'jpeg'], key=up_key)
            cam_file = st.camera_input("Prendre une photo", key=cam_key)
            
            final_file = uploaded_file if uploaded_file else cam_file
            
            if final_file:
                fname = f"live_{uuid.uuid4().hex}_{int(time.time())}.jpg"
                with open(os.path.join(LIVE_DIR, fname), "wb") as f: 
                    f.write(final_file.getbuffer())
                
                st.success("Photo envoyée !")
                st.session_state.cam_reset_id += 1 # Reset immédiat
                time.sleep(1)
                st.rerun()
        
        # --- MODE VOTE ---
        elif cfg["mode_affichage"] == "votes" and cfg["session_ouverte"]:
            st.write(f"Bonjour **{st.session_state.user_pseudo}**")
            
            if not st.session_state.rules_accepted:
                st.info("⚠️ **RÈGLES DU VOTE**")
                st.markdown("""
                1. Sélectionnez **3 vidéos** par ordre de préférence.
                2. 🥇 1er choix = **5 points**
                3. 🥈 2ème choix = **3 points**
                4. 🥉 3ème choix = **1 point**
                
                **Attention :** Le vote est définitif et unique.
                """)
                if st.button("J'AI COMPRIS, JE VOTE !", type="primary", use_container_width=True):
                    st.session_state.rules_accepted = True
                    st.rerun()
            else:
                choix = st.multiselect("Vos 3 vidéos préférées :", cfg["candidats"], max_selections=3)
                if len(choix) == 3:
                    if st.button("VALIDER (DÉFINITIF)", type="primary", use_container_width=True):
                        # 1. Sauvegarde Totaux
                        vts = load_json(VOTES_FILE, {})
                        pts = cfg.get("points_ponderation", [5, 3, 1])
                        for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                        save_json(VOTES_FILE, vts)
                        
                        # 2. Sauvegarde Détail
                        details = load_json(DETAILED_VOTES_FILE, [])
                        details.append({
                            "Utilisateur": st.session_state.user_pseudo,
                            "Choix 1 (5pts)": choix[0],
                            "Choix 2 (3pts)": choix[1],
                            "Choix 3 (1pt)": choix[2],
                            "Date": datetime.now().strftime("%H:%M:%S")
                        })
                        save_json(DETAILED_VOTES_FILE, details)
                        
                        # 3. Marquer Votant
                        voters = load_json(VOTERS_FILE, [])
                        voters.append(st.session_state.user_pseudo); save_json(VOTERS_FILE, voters)
                        
                        # 4. Blocage
                        st.session_state.vote_success = True
                        components.html("""<script>localStorage.setItem('HAS_VOTED_2026', 'true'); window.parent.location.href += '&blocked=true';</script>""", height=0)
                        time.sleep(1); st.rerun()
        else: st.info("⏳ En attente...")

# =========================================================
# 3. MUR SOCIAL
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2000, key="wall_refresh")
    cfg = load_json(CONFIG_FILE, default_config)
    
    st.markdown("""
    <style>
        body, .stApp { background-color: black !important; font-family: 'Arial', sans-serif; overflow: hidden !important; }
        [data-testid='stHeader'] { display: none; }
        .social-header { position: fixed; top: 0; left: 0; width: 100%; height: 12vh; background: #E2001A; display: flex; align-items: center; justify-content: center; z-index: 5000; border-bottom: 5px solid white; }
        .social-title { color: white; font-size: 40px; font-weight: bold; margin: 0; text-transform: uppercase; }
        .vote-cta { text-align: center; color: #E2001A; font-size: 35px; font-weight: 900; margin-top: 15px; animation: blink 2s infinite; text-transform: uppercase; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .voters-fixed-container { display: flex; flex-wrap: wrap; justify-content: center; align-items: center; gap: 10px; margin-bottom: 10px; width: 100%; min-height: 40px; }
        .user-tag { background: rgba(255,255,255,0.15); color: #FFF; padding: 5px 15px; border-radius: 20px; font-size: 18px; font-weight: bold; border: 1px solid #E2001A; white-space: nowrap; }
        .cand-row { display: flex; align-items: center; justify-content: flex-start; margin-bottom: 10px; background: rgba(255,255,255,0.08); padding: 8px 15px; border-radius: 50px; width: 100%; max-width: 350px; height: 70px; margin: 0 auto 10px auto; }
        .cand-img { width: 55px; height: 55px; border-radius: 50%; object-fit: cover; border: 3px solid #E2001A; margin-right: 15px; }
        .cand-name { color: white; font-size: 20px; font-weight: 600; margin: 0; white-space: nowrap; }
        /* CSS POUR PODIUM AVEC EGALITE */
        .podium-container { display: flex; justify-content: center; gap: 40px; align-items: center; margin-top: 50px; width: 100%; flex-wrap: wrap;}
        .winner-card { width: 400px; background: rgba(15,15,15,0.98); border: 8px solid #FFD700; border-radius: 40px; padding: 30px; text-align: center; z-index: 1000; box-shadow: 0 0 50px #FFD700; margin-bottom: 20px; }
        .suspense-grid { display: flex; justify-content: center; gap: 30px; margin-top: 30px; }
        .suspense-item { text-align: center; background: rgba(255,255,255,0.1); padding: 20px; border-radius: 20px; width: 200px; }
        .full-screen-center { position:fixed; top:0; left:0; width:100vw; height:100vh; display:flex; flex-direction:column; justify-content:center; align-items:center; z-index: 2; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f'<div class="social-header"><h1 class="social-title">{cfg["titre_mur"]}</h1></div>', unsafe_allow_html=True)

    mode = cfg.get("mode_affichage")
    inject_visual_effect(cfg["screen_effects"].get("attente" if mode=="attente" else "podium", "Aucun"), 25, 15)

    parts = load_json(PARTICIPANTS_FILE, [])
    if parts and mode == "votes" and not cfg.get("reveal_resultats") and cfg.get("session_ouverte"):
        tags_html = "".join([f"<span class='user-tag'>{p}</span>" for p in parts[-10:]])
        st.markdown(f'<div style="position:fixed; top:13vh; width:100%; text-align:center; z-index:100;">{tags_html}</div>', unsafe_allow_html=True)

    if mode == "attente":
        logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="width:450px; margin-bottom:30px;">' if cfg.get("logo_b64") else ""
        st.markdown(f"<div class='full-screen-center'>{logo_html}<h1 style='color:white; font-size:100px; margin:0; font-weight:bold;'>BIENVENUE</h1></div>", unsafe_allow_html=True)

    elif mode == "votes":
        if cfg.get("reveal_resultats"):
            elapsed = time.time() - cfg.get("timestamp_podium", 0)
            v_data = load_json(VOTES_FILE, {})
            if not v_data: v_data = {"Personne": 0}
            max_score = max(v_data.values()) if v_data else 0
            winners = [k for k, v in v_data.items() if v == max_score]
            logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="width:300px; margin-bottom:20px;">' if cfg.get("logo_b64") else ""
            if elapsed < 10.0:
                remaining = 10 - int(elapsed)
                top3 = sorted(v_data.items(), key=lambda x: x[1], reverse=True)[:3]
                suspense_html = ""
                for name, score in top3:
                    img = ""
                    if name in cfg.get("candidats_images", {}): 
                        img = f'<img src="data:image/png;base64,{cfg["candidats_images"][name]}" style="width:100px; height:100px; border-radius:50%; object-fit:cover; margin-bottom:10px;">'
                    suspense_html += f'<div class="suspense-item">{img}<h3 style="color:white; margin:0;">{name}</h3></div>'
                st.markdown(f"<div class='full-screen-center'>{logo_html}<h1 style='color:#E2001A; font-size:80px; margin:0;'>RÉSULTATS DANS... {remaining}</h1><div class='suspense-grid'>{suspense_html}</div></div>", unsafe_allow_html=True)
                time.sleep(1); st.rerun()
            else:
                cards_html = ""
                for winner in winners:
                    img = ""
                    if winner in cfg.get("candidats_images", {}): 
                        img = f'<img src="data:image/png;base64,{cfg["candidats_images"][winner]}" style="width:150px; height:150px; border-radius:50%; border:6px solid white; object-fit:cover; margin-bottom:20px;">'
                    cards_html += f"<div class='winner-card'><div style='font-size:60px;'>🏆</div>{img}<h1 style='color:white; font-size:40px; margin:10px 0;'>{winner}</h1><h2 style='color:#FFD700; font-size:30px;'>VAINQUEUR</h2><h3 style='color:#CCC; font-size:20px;'>{max_score} points</h3></div>"
                st.markdown(f"<div class='full-screen-center'>{logo_html}<div class='podium-container'>{cards_html}</div></div>", unsafe_allow_html=True)

        elif cfg.get("session_ouverte"):
            cands = cfg.get("candidats", [])
            imgs = cfg.get("candidats_images", {})
            mid = (len(cands) + 1) // 2
            left_list, right_list = cands[:mid], cands[mid:]
            c_left, c_center, c_right = st.columns([1, 1, 1])
            with c_left:
                st.markdown("<br><br><br><br>", unsafe_allow_html=True)
                for c in left_list:
                    img_src = f"data:image/png;base64,{imgs[c]}" if c in imgs else "https://via.placeholder.com/60/333/FFF?text=?"
                    st.markdown(f"<div class='cand-row'><img src='{img_src}' class='cand-img'><span class='cand-name'>{c}</span></div>", unsafe_allow_html=True)
            with c_center:
                st.markdown("<div style='height:12vh'></div>", unsafe_allow_html=True)
                if cfg.get("logo_b64"): 
                    st.markdown(f"<div style='text-align:center; width:100%; margin-bottom:20px;'><img src='data:image/png;base64,{cfg['logo_b64']}' style='width:350px;'></div>", unsafe_allow_html=True)
                host = st.context.headers.get('host', 'localhost')
                qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
                qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
                st.markdown(f"<div style='text-align:center; width:100%;'><img src='data:image/png;base64,{qr_b64}' style='width:240px; border-radius:10px;'></div>", unsafe_allow_html=True)
                st.markdown("<div class='vote-cta'>À VOS VOTES !</div>", unsafe_allow_html=True)
            with c_right:
                st.markdown("<br><br><br><br>", unsafe_allow_html=True)
                for c in right_list:
                    img_src = f"data:image/png;base64,{imgs[c]}" if c in imgs else "https://via.placeholder.com/60/333/FFF?text=?"
                    st.markdown(f"<div class='cand-row'><img src='{img_src}' class='cand-img'><span class='cand-name'>{c}</span></div>", unsafe_allow_html=True)

        else:
            logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="width:300px; margin-bottom:30px;">' if cfg.get("logo_b64") else ""
            st.markdown(f"<div class='full-screen-center'>{logo_html}<div style='border: 5px solid #E2001A; padding: 50px; border-radius: 40px; background: rgba(0,0,0,0.9);'><h1 style='color:#E2001A; font-size:70px; margin:0;'>VOTES CLÔTURÉS</h1></div></div>", unsafe_allow_html=True)

    elif mode == "photos_live":
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        logo_data = cfg.get("logo_b64", "")
        center_html = f"<div id='center-box' style='position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); z-index:10; text-align:center; background:rgba(0,0,0,0.8); padding:20px; border-radius:30px; border:2px solid #E2001A;'>{'<img src=\"data:image/png;base64,'+logo_data+'\" style=\"width:250px; margin-bottom:15px; display:block; margin-left:auto; margin-right:auto;\">' if logo_data else ''}<div style='background:white; padding:10px; border-radius:10px; display:inline-block;'><img src='data:image/png;base64,{qr_b64}' style='width:150px;'></div><h2 style='color:white; margin-top:10px; font-size:24px;'>Partagez vos sourires et vos moments forts !</h2></div>"
        st.markdown(center_html, unsafe_allow_html=True)
        photos = glob.glob(f"{LIVE_DIR}/*")
        if not photos: photos = []
        img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-40:]]) if photos else "[]"
        components.html(f"""<script>
            var doc = window.parent.document;
            var container = doc.getElementById('bubble-wall') || doc.createElement('div');
            container.id = 'bubble-wall'; 
            container.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:1;pointer-events:none;';
            if(!doc.getElementById('bubble-wall')) doc.body.appendChild(container);
            container.innerHTML = ''; // RESET COMPLET
            const imgs = {img_js}; const bubbles = []; const bSize = 250;
            imgs.forEach((src, i) => {{
                const el = doc.createElement('img'); el.src = src;
                el.style.cssText = 'position:absolute; width:'+bSize+'px; height:'+bSize+'px; border-radius:50%; border:8px solid #E2001A; object-fit:cover;';
                let x = Math.random() * (window.innerWidth - bSize); 
                let y = Math.random() * (window.innerHeight - bSize);
                let vx = (Math.random()-0.5)*8; if(Math.abs(vx)<1) vx=2;
                let vy = (Math.random()-0.5)*8; if(Math.abs(vy)<1) vy=2;
                container.appendChild(el); bubbles.push({{el, x, y, vx, vy, size: bSize}});
            }});
            function animate() {{
                var centerBox = doc.getElementById('center-box');
                var rect = centerBox ? centerBox.getBoundingClientRect() : {{left:0, right:0, top:0, bottom:0}};
                bubbles.forEach(b => {{
                    b.x += b.vx; b.y += b.vy;
                    if(b.x <= 0 || b.x + b.size >= window.innerWidth) b.vx *= -1;
                    if(b.y <= 0 || b.y + b.size >= window.innerHeight) b.vy *= -1;
                    if(centerBox && b.x + b.size > rect.left && b.x < rect.right && b.y + b.size > rect.top && b.y < rect.bottom) {{
                           b.vx *= -1; b.vy *= -1;
                    }}
                    b.element.style.transform = `translate(${{b.x}}px, ${{b.y}}px)`;
                }});
                requestAnimationFrame(animate);
            }} animate();
        </script>""", height=0)
