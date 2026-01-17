import streamlit as st
import os
import glob
import base64
import qrcode
import json
import time
import uuid
import textwrap
import zipfile
import shutil
from io import BytesIO
import streamlit.components.v1 as components
from PIL import Image
from datetime import datetime
import pandas as pd
import random
import altair as alt
import copy
import re
import tempfile

# =========================================================
# 1. IMPORTS & CONFIGURATION INITIALE
# =========================================================

try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

Image.MAX_IMAGE_PIXELS = None 

st.set_page_config(
    page_title="Régie Master",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- RECUPERATION PARAMETRES URL ---
qp = st.query_params
mode_url = qp.get("mode", "wall") 
admin_url = qp.get("admin", "false")
is_blocked = qp.get("blocked") == "true"
is_test_admin = qp.get("test_admin") == "true"

est_admin = (admin_url == "true")
est_utilisateur = (mode_url == "vote")

# DOSSIERS & FICHIERS
LIVE_DIR = "galerie_live_users"
ARCHIVE_DIR = "_archives_sessions"
VOTES_FILE = "votes.json"
CONFIG_FILE = "config_mur.json"
VOTERS_FILE = "voters.json"
PARTICIPANTS_FILE = "participants.json"
DETAILED_VOTES_FILE = "detailed_votes.json"
USERS_FILE = "users.json"

for d in [LIVE_DIR, ARCHIVE_DIR]:
    os.makedirs(d, exist_ok=True)

# =========================================================
# 2. CSS GLOBAL - RÉTABLISSEMENT PLEIN ÉCRAN TOTAL
# =========================================================
st.markdown("""
<style>
    /* SUPPRESSION DÉFINITIVE DES BANDES NOIRES ET DES MARGES STREAMLIT */
    [data-testid="stAppViewContainer"] {
        background-color: black !important;
        padding: 0 !important;
    }
    header[data-testid="stHeader"] { display: none !important; }
    
    /* FORCE LE CONTENU À COLLER AUX BORDS PHYSIQUES DE L'ÉCRAN */
    .main .block-container {
        max-width: 100vw !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        margin: 0 !important;
    }

    /* RÉGLAGE DES IFRAMES POUR LE PLEIN ÉCRAN TOTAL SANS BORDURES */
    iframe {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw !important;
        height: 100vh !important;
        border: none !important;
        display: block;
        z-index: 1;
    }

    /* STYLE DU HEADER ROUGE (8% de la hauteur) */
    .social-header { 
        position: fixed; 
        top: 0; left: 0; width: 100%; height: 8vh; 
        background: #E2001A !important; 
        display: flex; align-items: center; justify-content: center; 
        z-index: 999999 !important; 
        border-bottom: 3px solid white;
    }
    .social-title { 
        color: white !important; font-size: 30px !important; 
        font-weight: bold; margin: 0; text-transform: uppercase; 
    }

    /* DESIGN POUR L'ADMIN (Fond blanc si hors mur) */
    .stApp:has(button[kind="secondary"]) {
        background-color: #FFFFFF !important;
        color: black;
    }
    .stApp:has(button[kind="secondary"]) .main .block-container {
        padding: 2rem !important;
        max-width: 1200px !important;
        margin: auto !important;
    }

    ::-webkit-scrollbar { display: none; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 3. DONNEES & CONFIGURATIONS PAR DEFAUT
# =========================================================
blank_config = {
    "mode_affichage": "attente", 
    "titre_mur": "TITRE À DÉFINIR", 
    "session_ouverte": False, 
    "reveal_resultats": False,
    "timestamp_podium": 0,
    "logo_b64": None, 
    "candidats": [], 
    "candidats_images": {}, 
    "points_ponderation": [5, 3, 1],
    "effect_intensity": 25, 
    "effect_speed": 15, 
    "screen_effects": {"attente": "Aucun", "votes_open": "Aucun", "votes_closed": "Aucun", "podium": "Aucun", "photos_live": "Aucun"},
    "session_id": ""
}

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

default_users = {
    "admin": {"pwd": "ADMIN_LIVE_MASTER", "role": "Super Admin", "perms": ["all"]}
}

# =========================================================
# 4. FONCTIONS UTILITAIRES (LOGIQUE COMPLÈTE)
# =========================================================
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

def reset_app_data(init_mode="blank", preserve_config=False):
    for f in [VOTES_FILE, VOTERS_FILE, PARTICIPANTS_FILE, DETAILED_VOTES_FILE]:
        if os.path.exists(f): os.remove(f)
    files = glob.glob(f"{LIVE_DIR}/*")
    for f in files: os.remove(f)
    if not preserve_config:
        if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
        if init_mode == "blank": st.session_state.config = copy.deepcopy(blank_config)
        elif init_mode == "demo": st.session_state.config = copy.deepcopy(default_config)
    st.session_state.config["session_id"] = str(uuid.uuid4())
    save_config()

def archive_current_session():
    current_cfg = load_json(CONFIG_FILE, default_config)
    titre = current_cfg.get("titre_mur", "Session")
    safe_titre = re.sub(r'[\\/*?:"<>|]', "", titre).replace(" ", "_")
    folder_name = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{safe_titre}"
    archive_path = os.path.join(ARCHIVE_DIR, folder_name)
    os.makedirs(archive_path, exist_ok=True)
    for f in [VOTES_FILE, CONFIG_FILE, VOTERS_FILE, PARTICIPANTS_FILE, DETAILED_VOTES_FILE]:
        if os.path.exists(f): shutil.copy2(f, archive_path)
    live_archive = os.path.join(archive_path, "galerie_live_users")
    if os.path.exists(LIVE_DIR): shutil.copytree(LIVE_DIR, live_archive)
    return folder_name

def restore_session_from_archive(folder_name):
    source_path = os.path.join(ARCHIVE_DIR, folder_name)
    reset_app_data(init_mode="none")
    for f in [VOTES_FILE, CONFIG_FILE, VOTERS_FILE, PARTICIPANTS_FILE, DETAILED_VOTES_FILE]:
        src_f = os.path.join(source_path, f)
        if os.path.exists(src_f): shutil.copy2(src_f, ".")
    src_live = os.path.join(source_path, "galerie_live_users")
    if os.path.exists(src_live):
        if os.path.exists(LIVE_DIR): shutil.rmtree(LIVE_DIR)
        shutil.copytree(src_live, LIVE_DIR)

def get_advanced_stats():
    details = load_json(DETAILED_VOTES_FILE, [])
    vote_counts = {}; rank_dist = {}; unique_voters = set()
    for record in details:
        unique_voters.add(record.get('Utilisateur'))
        for idx, k in enumerate(["Choix 1 (5pts)", "Choix 2 (3pts)", "Choix 3 (1pt)"]):
            cand = record.get(k)
            if cand:
                vote_counts[cand] = vote_counts.get(cand, 0) + 1
                if cand not in rank_dist: rank_dist[cand] = {1:0, 2:0, 3:0}
                rank_dist[cand][idx+1] += 1
    return vote_counts, len(unique_voters), rank_dist

if PDF_AVAILABLE:
    class PDFReport(FPDF):
        def header(self):
            if "logo_b64" in st.session_state.config and st.session_state.config["logo_b64"]:
                try:
                    logo_data = base64.b64decode(st.session_state.config["logo_b64"])
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                        tmp.write(logo_data)
                        self.image(tmp.name, 10, 8, 33)
                        os.unlink(tmp.name)
                except: pass
            self.set_font('Arial', 'B', 15)
            self.cell(80)
            self.cell(30, 10, 'RÉSULTATS SESSION', 0, 0, 'C')
            self.ln(20)
            # =========================================================
# 5. LOGIQUE DE NAVIGATION ET ACCÈS ADMIN
# =========================================================

def process_participant_image(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        if img.mode != "RGB": img = img.convert("RGB")
        img.thumbnail((300, 300), Image.Resampling.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=75)
        return base64.b64encode(buf.getvalue()).decode()
    except: return None

def set_state(mode, open_s, reveal):
    st.session_state.config["mode_affichage"] = mode
    st.session_state.config["session_ouverte"] = open_s
    st.session_state.config["reveal_resultats"] = reveal
    if reveal: st.session_state.config["timestamp_podium"] = time.time()
    save_config()

# --- INITIALISATION SESSION STATE ---
if "config" not in st.session_state:
    st.session_state.config = load_json(CONFIG_FILE, default_config)

# =========================================================
# 6. CONSOLE ADMINISTRATION
# =========================================================
if est_admin:
    if "auth" not in st.session_state: st.session_state["auth"] = False
    users_db = load_json(USERS_FILE, default_users)
    
    if not st.session_state["auth"]:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown('<div class="login-container"><div class="login-title">🔒 ADMIN ACCESS</div>', unsafe_allow_html=True)
            u_in = st.text_input("Identifiant")
            p_in = st.text_input("Mot de passe", type="password")
            if st.button("ENTRER", use_container_width=True, type="primary"):
                if u_in in users_db and users_db[u_in]["pwd"] == p_in:
                    st.session_state["auth"] = True
                    st.session_state["current_user"] = u_in
                    st.session_state["user_perms"] = users_db[u_in].get("perms", ["all"])
                    st.rerun()
                else: st.error("Identifiants incorrects")
            st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # --- RÉCUPÉRATION DES PERMISSIONS ---
        perms = st.session_state.get("user_perms", ["all"])
        is_super = "all" in perms

        # --- GESTIONNAIRE DE SESSIONS (DASHBOARD) ---
        if "session_active" not in st.session_state or not st.session_state["session_active"]:
            st.markdown("<br>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                st.markdown(f'<div class="session-card"><div class="session-title">🗂️ GESTIONNAIRE DE SESSIONS</div>', unsafe_allow_html=True)
                st.write(f"Connecté : **{st.session_state['current_user']}**")
                
                if st.button(f"📂 OUVRIR : {st.session_state.config.get('titre_mur')}", type="primary", use_container_width=True):
                    st.session_state["session_active"] = True
                    st.rerun()
                
                if is_super or "config" in perms:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("✨ CRÉER UNE NOUVELLE SESSION VIERGE", type="secondary", use_container_width=True):
                        archive_current_session()
                        reset_app_data("blank")
                        st.session_state["session_active"] = True
                        st.rerun()
                
                st.divider()
                st.subheader("📦 Archives")
                archives = sorted([d for d in os.listdir(ARCHIVE_DIR) if os.path.isdir(os.path.join(ARCHIVE_DIR, d))], reverse=True)
                for arc in archives:
                    ca, cb = st.columns([4, 1])
                    ca.text(f"📁 {arc}")
                    if cb.button("♻️", key=f"restore_{arc}", help="Restaurer cette session"):
                        archive_current_session()
                        restore_session_from_archive(arc)
                        st.session_state.config = load_json(CONFIG_FILE, default_config)
                        st.session_state["session_active"] = True
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        else:
            # --- INTERFACE DE PILOTAGE ACTIVE ---
            cfg = st.session_state.config
            with st.sidebar:
                st.header("🎮 RÉGIE MASTER")
                if st.button("⬅️ CHANGER DE SESSION", use_container_width=True):
                    st.session_state["session_active"] = False
                    st.rerun()
                st.divider()
                if "admin_menu" not in st.session_state: st.session_state.admin_menu = "🔴 PILOTAGE LIVE"
                
                m1 = st.button("🔴 PILOTAGE LIVE", use_container_width=True, type="primary" if st.session_state.admin_menu == "🔴 PILOTAGE LIVE" else "secondary")
                if m1: st.session_state.admin_menu = "🔴 PILOTAGE LIVE"; st.rerun()
                
                m2 = st.button("⚙️ CONFIGURATION", use_container_width=True, type="primary" if st.session_state.admin_menu == "⚙️ CONFIGURATION" else "secondary")
                if m2: st.session_state.admin_menu = "⚙️ CONFIGURATION"; st.rerun()
                
                m3 = st.button("📸 MÉDIATHÈQUE", use_container_width=True, type="primary" if st.session_state.admin_menu == "📸 MÉDIATHÈQUE" else "secondary")
                if m3: st.session_state.admin_menu = "📸 MÉDIATHÈQUE"; st.rerun()
                
                m4 = st.button("📊 RÉSULTATS & DATA", use_container_width=True, type="primary" if st.session_state.admin_menu == "📊 RÉSULTATS & DATA" else "secondary")
                if m4: st.session_state.admin_menu = "📊 RÉSULTATS & DATA"; st.rerun()

                st.divider()
                host_url = st.context.headers.get("host", "localhost")
                st.markdown(f'<a href="http://{host_url}/?mode=wall" target="_blank" class="custom-link-btn btn-red">📺 OUVRIR LE MUR</a>', unsafe_allow_html=True)
                if st.button("🔓 DÉCONNEXION"):
                    st.session_state["auth"] = False
                    st.rerun()

            # --- ROUTES ADMIN ---
            menu = st.session_state.admin_menu

            if menu == "🔴 PILOTAGE LIVE":
                st.title("🔴 PILOTAGE LIVE")
                col1, col2, col3, col4 = st.columns(4)
                col1.button("🏠 ACCUEIL", on_click=set_state, args=("attente", False, False), use_container_width=True)
                col2.button("🗳️ VOTE ON", on_click=set_state, args=("votes", True, False), use_container_width=True)
                col3.button("🔒 VOTE OFF", on_click=set_state, args=("votes", False, False), use_container_width=True)
                col4.button("🏆 PODIUM", on_click=set_state, args=("votes", False, True), use_container_width=True)
                st.divider()
                st.button("📸 MUR PHOTOS LIVE", on_click=set_state, args=("photos_live", False, False), use_container_width=True)

            elif menu == "⚙️ CONFIGURATION":
                st.title("⚙️ CONFIGURATION")
                cfg["titre_mur"] = st.text_input("Titre de la soirée", value=cfg.get("titre_mur", ""))
                upl = st.file_uploader("Logo Social Wall (PNG)", type=["png", "jpg"])
                if upl: 
                    cfg["logo_b64"] = process_logo(upl)
                    save_config(); st.rerun()
                
                st.subheader("Candidats / Participants")
                new_c = st.text_input("Ajouter un candidat")
                if st.button("➕ Ajouter"):
                    if new_c and new_c not in cfg["candidats"]:
                        cfg["candidats"].append(new_c)
                        save_config(); st.rerun()
                
                for i, cand in enumerate(cfg["candidats"]):
                    c_col1, c_col2, c_col3 = st.columns([3, 2, 1])
                    c_col1.write(f"**{cand}**")
                    img_upl = c_col2.file_uploader(f"Photo {i}", type=["jpg", "png"], key=f"upl_{i}", label_visibility="collapsed")
                    if img_upl:
                        cfg["candidats_images"][cand] = process_participant_image(img_upl)
                        save_config(); st.rerun()
                    if c_col3.button("🗑️", key=f"del_{i}"):
                        cfg["candidats"].remove(cand)
                        save_config(); st.rerun()

            elif menu == "📸 MÉDIATHÈQUE":
                st.title("📸 MÉDIATHÈQUE")
                files = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
                if files:
                    zip_buf = BytesIO()
                    with zipfile.ZipFile(zip_buf, "w") as zf:
                        for f in files: zf.write(f, os.path.basename(f))
                    st.download_button("📥 TÉLÉCHARGER TOUTES LES PHOTOS (ZIP)", data=zip_buf.getvalue(), file_name="photos_live.zip", use_container_width=True)
                    
                    cols = st.columns(4)
                    for idx, f in enumerate(files):
                        with cols[idx % 4]:
                            st.image(f, use_container_width=True)
                            if st.button("Supprimer", key=f"kill_{idx}"):
                                os.remove(f); st.rerun()
                else: st.info("Aucune photo reçue.")

            elif menu == "📊 RÉSULTATS & DATA":
                st.title("📊 RÉSULTATS")
                votes = load_json(VOTES_FILE, {})
                if votes:
                    df = pd.DataFrame(list(votes.items()), columns=["Candidat", "Points"]).sort_values("Points", ascending=False)
                    st.altair_chart(alt.Chart(df).mark_bar(color="#E2001A").encode(x='Points', y=alt.Y('Candidat', sort='-x')), use_container_width=True)
                    st.table(df)
                    if PDF_AVAILABLE:
                        v_counts, v_unique, rank_dist = get_advanced_stats()
                        if st.button("📄 GÉNÉRER RAPPORT PDF"):
                            pdf_data = create_pdf_results(cfg["titre_mur"], df, v_unique, df["Points"].sum())
                            st.download_button("📥 Télécharger PDF", data=pdf_data, file_name="resultats.pdf")
                else: st.warning("En attente de votes.")
                    # =========================================================
# 7. INTERFACE UTILISATEUR MOBILE (VOTE & PHOTOS)
# =========================================================
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, default_config)
    # Style forçage mobile (fond noir, texte blanc)
    st.markdown("""
        <style>
            .stApp { background-color: black !important; color: white !important; }
            .stHeader { display: none !important; }
            h1, h2, h3, p { color: white !important; }
            .stButton>button { border-radius: 20px !important; }
        </style>
    """, unsafe_allow_html=True)
    
    if "user_pseudo" not in st.session_state:
        st.markdown(f"<h2 style='text-align:center;'>{cfg['titre_mur']}</h2>", unsafe_allow_html=True)
        st.subheader("Identification")
        pseudo = st.text_input("Entrez votre Prénom ou Pseudo :", placeholder="Ex: Jean / Team BU...")
        
        if st.button("ACCÉDER À L'ÉVÉNEMENT", type="primary", use_container_width=True):
            if pseudo and len(pseudo.strip()) > 1:
                st.session_state.user_pseudo = pseudo.strip()
                # Enregistrement dans la liste globale des participants
                parts = load_json(PARTICIPANTS_FILE, [])
                if st.session_state.user_pseudo not in parts:
                    parts.append(st.session_state.user_pseudo)
                    save_json(PARTICIPANTS_FILE, parts)
                st.rerun()
            else:
                st.error("Veuillez entrer un pseudo valide.")
    else:
        st.markdown(f"Connecté : **{st.session_state.user_pseudo}**")
        
        # --- CAS 1 : MUR PHOTOS LIVE ACTIF ---
        if cfg["mode_affichage"] == "photos_live":
            st.title("📸 MUR PHOTOS")
            st.write("Prenez une photo pour l'afficher sur le grand écran !")
            img_file = st.camera_input("Sourire obligatoire !")
            
            if img_file:
                fname = f"live_{uuid.uuid4().hex[:8]}_{int(time.time())}.jpg"
                img_path = os.path.join(LIVE_DIR, fname)
                with open(img_path, "wb") as f:
                    f.write(img_file.getbuffer())
                st.success("✅ Photo envoyée ! Elle va apparaître sur le mur.")
                time.sleep(2)
                st.rerun()

        # --- CAS 2 : VOTES OUVERTS ---
        elif cfg["mode_affichage"] == "votes" and cfg["session_ouverte"]:
            st.title("🗳️ VOTES")
            st.write("Sélectionnez vos **3 vidéos favorites** par ordre de préférence :")
            
            # Utilisation de multiselect avec limite de 3
            choix = st.multiselect(
                "Votre Top 3 :", 
                options=cfg["candidats"], 
                max_selections=3,
                placeholder="Choisissez 3 candidats"
            )
            
            if len(choix) == 3:
                st.info("💡 1er = 5pts | 2ème = 3pts | 3ème = 1pt")
                if st.button("VALIDER MON VOTE DÉFINITIF", type="primary", use_container_width=True):
                    # 1. Mise à jour des scores globaux (votes.json)
                    scores = load_json(VOTES_FILE, {})
                    points = [5, 3, 1]
                    for cand, p in zip(choix, points):
                        scores[cand] = scores.get(cand, 0) + p
                    save_json(VOTES_FILE, scores)
                    
                    # 2. Enregistrement du log détaillé (detailed_votes.json) pour le Marquee
                    details = load_json(DETAILED_VOTES_FILE, [])
                    details.append({
                        "Utilisateur": st.session_state.user_pseudo,
                        "Choix 1 (5pts)": choix[0],
                        "Choix 2 (3pts)": choix[1],
                        "Choix 3 (1pt)": choix[2],
                        "Horodatage": datetime.now().strftime("%H:%M:%S")
                    })
                    save_json(DETAILED_VOTES_FILE, details)
                    
                    st.balloons()
                    st.success("Vote enregistré ! Merci pour votre participation.")
                    st.session_state.vote_done = True
                    time.sleep(3)
                    st.rerun()
            elif len(choix) > 0:
                st.warning(f"Encore {3 - len(choix)} choix à faire...")

        # --- CAS 3 : ATTENTE OU VOTES CLOS ---
        else:
            st.markdown("<div style='text-align:center; margin-top:20vh;'>", unsafe_allow_html=True)
            st.title("⏳")
            st.subheader("Veuillez patienter...")
            st.write("L'animateur va bientôt lancer la prochaine séquence.")
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Petit bouton de rafraîchissement manuel au cas où
            if st.button("Actualiser", use_container_width=True):
                st.rerun()
                # =========================================================
# 8. MUR SOCIAL (INTERFACE TV - LOGIQUE COMPLÈTE)
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    cfg = load_json(CONFIG_FILE, default_config)
    
    # Rafraîchissement automatique pour capter les changements d'état en régie
    refresh_rate = 5000 if (cfg.get("mode_affichage") == "votes" and cfg.get("reveal_resultats")) else 4000
    st_autorefresh(interval=refresh_rate, key="wall_refresh")
    
    # Header Social Rouge Fixe
    st.markdown(f'<div class="social-header"><h1 class="social-title">{cfg["titre_mur"]}</h1></div>', unsafe_allow_html=True)
    
    mode = cfg.get("mode_affichage")
    logo_data = cfg.get("logo_b64", "")
    safe_title = cfg['titre_mur'].replace("'", "\\'")
    
    # --- CHARGEMENT DES ASSETS (JS/CSS) ---
    try:
        with open("style.css", "r", encoding="utf-8") as f: css_content = f.read()
        with open("robot.js", "r", encoding="utf-8") as f: js_content = f.read()
    except:
        css_content = ""
        js_content = "console.error('Fichiers assets manquants (robot.js/style.css)');"

    # --- CONFIGURATION DU MODE ROBOT ---
    robot_mode = "attente" 
    if mode == "votes" and not cfg["session_ouverte"] and not cfg["reveal_resultats"]:
        robot_mode = "vote_off"
    elif mode == "photos_live":
        robot_mode = "photos"
    
    js_config = f"""
    <script>
        window.robotConfig = {{
            mode: '{robot_mode}',
            titre: '{safe_title}',
            logo: '{logo_data}'
        }};
    </script>
    """
    
    import_map = """<script type="importmap">{ "imports": { "three": "https://unpkg.com/three@0.160.0/build/three.module.js", "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/" } }</script>"""

    # --- RENDU 1 : MODE ATTENTE ---
    if mode == "attente":
        logo_tag = f'<img src="data:image/png;base64,{logo_data}" style="width:350px; margin-bottom:15px;">' if logo_data else ""
        html_code = f"""
        <!DOCTYPE html><html><head><style>
            body {{ margin: 0; padding: 0; background-color: black; overflow: hidden; width: 100vw; height: 100vh; }}
            {css_content}
            #welcome-text {{ 
                position: absolute; top: 45%; left: 50%; transform: translate(-50%, -50%); 
                text-align: center; color: white; font-family: Arial, sans-serif; 
                z-index: 5; font-size: 70px; font-weight: 900; letter-spacing: 5px; 
                pointer-events: none; transition: all 1s ease-in-out;
            }}
        </style></head>
        <body>
            {js_config}
            <div id="welcome-text">{logo_tag}<br>BIENVENUE</div>
            <div id="robot-bubble" class="bubble" style="z-index: 20;">...</div>
            <div id="robot-container" style="z-index: 10; pointer-events: none;"></div>
            {import_map}
            <script type="module">{js_content}</script>
        </body></html>"""
        components.html(html_code, height=1200, scrolling=False)

    # --- RENDU 2 : MODE VOTES (OUVERT OU PODIUM) ---
    elif mode == "votes":
        if cfg.get("reveal_resultats"):
            # --- LOGIQUE DU PODIUM SPECTACLE ---
            v_data = load_json(VOTES_FILE, {})
            c_imgs = cfg.get("candidats_images", {})
            if not v_data: v_data = {"Personne": 0}
            sorted_unique = sorted(list(set(v_data.values())), reverse=True)
            s1 = sorted_unique[0] if len(sorted_unique) > 0 else 0
            s2 = sorted_unique[1] if len(sorted_unique) > 1 else 0
            s3 = sorted_unique[2] if len(sorted_unique) > 2 else 0
            
            def get_pod_html(score, emoji):
                cands = [c for c, s in v_data.items() if s == score]
                h = ""
                for c in cands:
                    img = f"<div class='p-empty'>{emoji}</div>"
                    if c in c_imgs: img = f"<img src='data:image/png;base64,{c_imgs[c]}' class='p-img'>"
                    h += f"<div class='p-card'>{img}<div class='p-name'>{c}</div></div>"
                return h

            components.html(f"""
            <div id="intro-layer" class="intro-overlay"><div id="intro-txt" class="intro-text"></div><div id="intro-num" class="intro-count"></div></div>
            <audio id="applause" preload="auto"><source src="https://www.soundjay.com/human/sounds/applause-01.mp3"></audio>
            <div class="podium-container">
                <div class="col-pod"><div class="win-box" id="win-2">{get_pod_html(s2, "🥈")}</div><div class="ped pedestal-2"><div>{s2} PTS</div><div class="rank-num">2</div></div></div>
                <div class="col-pod"><div class="win-box" id="win-1">{get_pod_html(s1, "🥇")}</div><div class="ped pedestal-1"><div>{s1} PTS</div><div class="rank-num">1</div></div></div>
                <div class="col-pod"><div class="win-box" id="win-3">{get_pod_html(s3, "🥉")}</div><div class="ped pedestal-3"><div>{s3} PTS</div><div class="rank-num">3</div></div></div>
            </div>
            <script>
                const wait=(ms)=>new Promise(res=>setTimeout(res,ms));
                async function runShow(){{
                    const l=document.getElementById('intro-layer'),t=document.getElementById('intro-txt'),n=document.getElementById('intro-num');
                    const show=(id)=>document.getElementById(id).classList.add('visible');
                    l.style.display='flex'; t.innerText="3ème POSITION..."; for(let i=3;i>0;i--){{n.innerText=i; await wait(1000);}}
                    l.style.display='none'; show('win-3'); await wait(2000);
                    l.style.display='flex'; t.innerText="2ème POSITION..."; for(let i=3;i>0;i--){{n.innerText=i; await wait(1000);}}
                    l.style.display='none'; show('win-2'); await wait(2000);
                    l.style.display='flex'; t.innerText="LE VAINQUEUR EST..."; for(let i=5;i>0;i--){{n.innerText=i; await wait(1000);}}
                    l.style.display='none'; show('win-1'); document.getElementById('applause').play();
                }}
                window.onload = runShow;
            </script>
            <style>
                body{{background:black; margin:0; font-family:Arial; overflow:hidden;}}
                .podium-container{{display:flex; justify-content:center; align-items:flex-end; height:100vh; padding-bottom:20px;}}
                .ped{{width:300px; background:linear-gradient(#444,#000); border-radius:15px 15px 0 0; text-align:center; padding-top:20px; color:white; margin:0 10px;}}
                .pedestal-1{{height:400px; border-top:5px solid gold;}} .pedestal-2{{height:260px; border-top:5px solid silver;}} .pedestal-3{{height:170px; border-top:5px solid #cd7f32;}}
                .win-box{{opacity:0; transition: 1s; transform: translateY(40px); display:flex; justify-content:center;}} .win-box.visible{{opacity:1; transform:translateY(0);}}
                .p-card{{text-align:center; margin:0 10px;}} .p-img{{width:140px; height:140px; border-radius:50%; border:4px solid white; object-fit:cover;}}
                .p-name{{font-weight:bold; margin-top:10px; font-size:20px; text-transform:uppercase; color:white;}}
                .rank-num{{font-size:100px; opacity:0.1; font-weight:900;}}
                .intro-overlay{{position:fixed; top:0; left:0; width:100vw; height:100vh; background:black; z-index:9999; display:none; flex-direction:column; justify-content:center; align-items:center;}}
                .intro-text{{color:white; font-size:45px; font-weight:bold;}} .intro-count{{color:#E2001A; font-size:120px; font-weight:900;}}
            </style>
            """, height=1200)

        elif cfg["session_ouverte"]:
            # --- VOTE OUVERT (QR + MARQUEE + CANDIDATS) ---
            host = st.context.headers.get('host', 'localhost')
            qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            
            recent = load_json(DETAILED_VOTES_FILE, [])
            voters = " &nbsp;&nbsp;•&nbsp;&nbsp; ".join([v['Utilisateur'] for v in recent[-20:]][::-1]) or "Prêt pour vos votes..."
            
            cands = cfg.get("candidats", []); mid = (len(cands) + 1) // 2
            def gen_c(lst, al):
                return "".join([f'<div style="background:rgba(255,255,255,0.15); padding:15px; margin:12px 0; border-radius:50px; color:white; font-weight:bold; width:280px; margin-{al}:auto; font-family:Arial; font-size:18px;">👤 {c}</div>' for c in lst])

            components.html(f"""
            <style>
                body {{ background: black; margin: 0; font-family: Arial; overflow: hidden; }}
                .marquee {{ position:fixed; top:8vh; width:100%; background:#E2001A; color:white; height:50px; display:flex; align-items:center; z-index:100; border-bottom:2px solid white; }}
                .marquee-content {{ white-space:nowrap; animation: scroll 30s linear infinite; font-weight:bold; font-size:22px; }}
                @keyframes scroll {{ 0% {{ transform: translateX(100vw); }} 100% {{ transform: translateX(-100%); }} }}
                .main-box {{ display:flex; justify-content:space-between; align-items:center; height:100vh; padding: 0 4%; }}
                .qr-card {{ background:white; padding:30px; border-radius:40px; border:12px solid #E2001A; text-align:center; box-shadow: 0 0 60px rgba(226,0,26,0.6); }}
            </style>
            <div class="marquee"><div class="marquee-content">DERNIERS VOTANTS : {voters}</div></div>
            <div class="main-box">
                <div>{gen_c(cands[:mid], 'left')}</div>
                <div class="qr-zone">
                    <h1 style="color:#E2001A; font-size:60px; font-weight:900; margin-bottom:20px; text-align:center;">VOTES OUVERTS</h1>
                    <div class="qr-card"><img src="data:image/png;base64,{qr_b64}" width="350"></div>
                    <h2 style="color:white; margin-top:25px; font-size:30px; text-align:center;">Scannez pour voter !</h2>
                </div>
                <div>{gen_c(cands[mid:], 'right')}</div>
            </div>""", height=1200)
        else:
            # Votes Clos avec Robot
            logo_h = f'<img src="data:image/png;base64,{logo_data}" style="width:380px; margin-bottom:20px;">' if logo_data else ""
            overlay = f"""<div style='position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); z-index: 5; text-align:center; pointer-events:none;'><div style='background:rgba(0,0,0,0.85); padding:60px; border-radius:45px; border:8px solid #E2001A; box-shadow:0 0 70px black;'>{logo_h}<h1 style='color:#E2001A; font-size:75px; margin:0; font-family:Arial; font-weight:900;'>MERCI !</h1><h2 style='color:white; font-size:40px; font-family:Arial;'>Les votes sont désormais clos.</h2></div></div>"""
            html_code = f"""<!DOCTYPE html><html><head><style>body {{ margin: 0; background-color: black; overflow: hidden; width: 100vw; height: 100vh; }}</style></head><body>{js_config}{overlay}<div id="robot-container"></div>{import_map}<script type="module">{js_content}</script></body></html>"""
            components.html(html_code, height=1200, scrolling=False)

    # --- RENDU 3 : MODE PHOTOS LIVE (BULLES + QR) ---
    elif mode == "photos_live":
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        photos = glob.glob(f"{LIVE_DIR}/*")
        img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-30:]])
        
        center_box = f"""<div style='position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); z-index:15; text-align:center; background:rgba(0,0,0,0.85); padding:35px; border-radius:40px; border:6px solid #E2001A; width:420px; box-shadow:0 0 60px black; font-family:Arial;'><h1 style='color:#E2001A; font-size:32px; margin:0 0 20px 0; font-weight:900;'>MUR PHOTOS LIVE</h1><div style='background:white; padding:20px; border-radius:25px; display:inline-block;'><img src='data:image/png;base64,{qr_b64}' width='260'></div><h2 style='color:white; font-size:24px; margin-top:20px;'>Partagez vos sourires !</h2></div>"""
        
        html_code = f"""
        <!DOCTYPE html><html><head><style>body {{ margin: 0; background-color: black; overflow: hidden; width: 100vw; height: 100vh; }} .live-bubble {{ position: absolute; border: 6px solid white; border-radius:20px; width: 320px; box-shadow: 0 20px 45px rgba(0,0,0,0.7); transition: transform 0.1s linear; object-fit: cover; }}</style></head>
        <body>
            {js_config}{center_box}<div id="photo-wall"></div><div id="robot-container"></div>
            <script type="module">{js_content}</script>
            <script>
                const imgs = {img_js}; const wall = document.getElementById('photo-wall');
                imgs.forEach(src => {{
                    const i = document.createElement('img'); i.src = src; i.className = 'live-bubble';
                    i.style.left = Math.random() * 70 + '%'; i.style.top = Math.random() * 60 + 10 + '%';
                    i.style.transform = 'rotate(' + (Math.random() * 40 - 20) + 'deg)';
                    wall.appendChild(i);
                }});
            </script>
        </body></html>"""
        components.html(html_code, height=1200, scrolling=False)
