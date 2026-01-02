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
DEFAULT_AVATAR = "iVBORw0KGgoAAAANSUhEUgAAAOEAAADhCAMAAAAJbSJIAAAAM1BMVEXk5ueutLfn6Onj5Oa+wsO2u73q6+zg4eKxvL2/w8Tk5ebl5ufm5+nm6Oni4+Tp6uvr7O24w8qOAAACvklEQVR4nO3b23KCMBBAUYiCoKD+/792RC0iF1ApOcvM2rO+lF8S50ymL6cdAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADgX0a9eT6f13E67e+P5yV/7V6Z5/V0Wubb7XKZl/x9e1Zm3u/reZ7y9+1VmV/X/Xad8vftzT/97iX/3J6V6e+365S/b6/KjP/7cf9u06f8fXtV5vF43L/bdMrft2dl5v1+u075+/aqzL/rfrtO+fv2qsz/frtO+fv2qsz4v9+uU/6+vSoz/u+365S/b6/KjP/77Trl79urMuP/frtO+fv2qsz4v9+uU/6+vSoz/u+365S/b6/KjP/77Trl79urMuP/frtO+fv2qsz4v9+uU/6+vSoz/u+365S/b6/KjP/77Trl79urMuP/frtO+fv2qsz4v9+uU/6+vSoz/u+365S/b6/KjP/77Trl79urMuP/frtO+fv2qsz4v9+uU/6+vSoz/u+365S/b6/KjP/77Trl79urMuP/frtO+fv2qsz4v9+uU/6+vSoz/u+365S/b6/KjP/77Trl79urMgMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP/xG2nLBH198qZpAAAAAElFTkSuQmCC"

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
    # Force la sauvegarde immédiate
    save_json(CONFIG_FILE, st.session_state.config)

# --- GÉNÉRATEUR PDF ---
if PDF_AVAILABLE:
    class PDFReport(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.set_text_color(226, 0, 26)
            self.cell(0, 10, 'REGIE MASTER - RAPPORT OFFICIEL', 0, 1, 'C')
            self.ln(5)
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def create_pdf_results(title, df):
        pdf = PDFReport()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt=f"Resultats: {title}", ln=True, align='L')
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 10, txt=f"Genere le : {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='L')
        pdf.ln(10)
        pdf.set_fill_color(226, 0, 26)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(100, 10, "Candidat", 1, 0, 'C', 1)
        pdf.cell(40, 10, "Points", 1, 1, 'C', 1)
        pdf.set_text_color(0, 0, 0)
        pdf.ln()
        for i, row in df.iterrows():
            cand = str(row['Candidat']).encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(100, 10, cand, 1)
            pdf.cell(40, 10, str(row['Points']), 1, 1, 'C')
            pdf.ln()
        return pdf.output(dest='S').encode('latin-1')

    def create_pdf_audit(title, df):
        pdf = PDFReport()
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt=f"Audit Detail: {title}", ln=True, align='L')
        pdf.ln(5)
        cols = df.columns.tolist()
        w = 190 / len(cols)
        pdf.set_fill_color(50, 50, 50)
        pdf.set_text_color(255)
        for col in cols:
            c_txt = str(col).encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(w, 8, c_txt, 1, 0, 'C', 1)
        pdf.ln()
        pdf.set_text_color(0)
        for i, row in df.iterrows():
            for col in cols:
                txt = str(row[col]).encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(w, 8, txt, 1)
            pdf.ln()
        return pdf.output(dest='S').encode('latin-1')

# --- ACTIONS ---
def set_state(mode, open_s, reveal):
    st.session_state.config["mode_affichage"] = mode
    st.session_state.config["session_ouverte"] = open_s
    st.session_state.config["reveal_resultats"] = reveal
    if reveal: st.session_state.config["timestamp_podium"] = time.time()
    save_config()

def reset_app_data():
    for f in [VOTES_FILE, VOTERS_FILE, PARTICIPANTS_FILE, DETAILED_VOTES_FILE]:
        if os.path.exists(f): os.remove(f)
    files = glob.glob(f"{LIVE_DIR}/*")
    for f in files: os.remove(f)
    st.session_state.config["session_id"] = str(uuid.uuid4())
    save_config()
    st.toast("✅ RESET TOTAL OK")
    time.sleep(1)

def process_image(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        img.thumbnail((800, 800))
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except: return None

def get_file_info(filepath):
    try:
        ts = os.path.getmtime(filepath)
        return datetime.fromtimestamp(ts).strftime("%H:%M:%S")
    except: return "?"

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
                if st.button("🗑️ RESET TOTAL", type="primary"): reset_app_data(); st.rerun()

        elif menu == "⚙️ CONFIG":
            t1, t2 = st.tabs(["Général", "Candidats & Images"])
            with t1:
                new_t = st.text_input("Titre", value=cfg["titre_mur"])
                if st.button("Sauver Titre"): st.session_state.config["titre_mur"] = new_t; save_config(); st.rerun()
                upl = st.file_uploader("Logo", type=["png", "jpg"])
                if upl: st.session_state.config["logo_b64"] = process_image(upl); save_config(); st.rerun()
            with t2:
                st.subheader(f"Liste des participants ({len(cfg['candidats'])}/15)")
                if len(cfg['candidats']) < 15:
                    with st.form("add_cand"):
                        col_add1, col_add2 = st.columns([4, 1])
                        new_cand = col_add1.text_input("Nouveau participant")
                        if col_add2.form_submit_button("➕ Ajouter") and new_cand:
                            if new_cand not in cfg['candidats']:
                                cfg['candidats'].append(new_cand)
                                save_config(); st.rerun()
                            else: st.error("Existe déjà !")
                else: st.warning("Maximum atteint.")
                st.divider()
                candidates_to_remove = []
                for i, cand in enumerate(cfg['candidats']):
                    c1, c2, c3 = st.columns([0.5, 3, 2])
                    with c1:
                        # AFFICHAGE IMAGE ACTUELLE
                        if cand in cfg.get("candidats_images", {}): 
                            st.image(BytesIO(base64.b64decode(cfg["candidats_images"][cand])), width=40)
                        else: st.write("🚫")
                    with c2:
                        new_name = st.text_input(f"Participant {i+1}", value=cand, key=f"edit_{i}", label_visibility="collapsed")
                        if new_name != cand and new_name:
                            cfg['candidats'][i] = new_name
                            if cand in cfg.get("candidats_images", {}): cfg["candidats_images"][new_name] = cfg["candidats_images"].pop(cand)
                            save_config(); st.rerun()
                    with c3:
                        col_up, col_del = st.columns([3, 1])
                        up_img = col_up.file_uploader(f"Img {cand}", type=["png", "jpg"], key=f"up_{i}", label_visibility="collapsed")
                        if up_img: 
                            # SAUVEGARDE IMAGE CORRIGEE
                            if "candidats_images" not in st.session_state.config: st.session_state.config["candidats_images"] = {}
                            st.session_state.config["candidats_images"][cand] = process_image(up_img)
                            save_config() # Sauvegarde explicite
                            st.success("Image OK")
                            time.sleep(0.5)
                            st.rerun()
                        if col_del.button("🗑️", key=f"del_{i}"): candidates_to_remove.append(cand)
                
                if candidates_to_remove:
                    for c in candidates_to_remove:
                        cfg['candidats'].remove(c)
                        if c in cfg.get("candidats_images", {}): del cfg["candidats_images"][c]
                    save_config(); st.rerun()

        elif menu == "📸 MÉDIATHÈQUE":
            st.subheader("Gestion des Photos Live")
            if st.button("🗑️ TOUT SUPPRIMER D'UN COUP", type="primary"):
                files = glob.glob(f"{LIVE_DIR}/*")
                for f in files: os.remove(f)
                st.success("Suppression OK"); time.sleep(1); st.rerun()
            st.divider()
            files = sorted(glob.glob(f"{LIVE_DIR}/*"), key=os.path.getmtime, reverse=True)
            if not files: st.info("Aucune photo.")
            else:
                st.write("**Sélectionnez les photos :**")
                cols = st.columns(5)
                new_selection = []
                for i, f in enumerate(files):
                    date_str = get_file_info(f)
                    with cols[i % 5]:
                        st.image(f, use_container_width=True)
                        if st.checkbox(f"Sel. {i+1}", key=f"chk_{os.path.basename(f)}"): new_selection.append(f)
                st.write("---")
                c1, c2, c3 = st.columns(3)
                if c1.button("Supprimer la sélection") and new_selection:
                    for f in new_selection: os.remove(f)
                    st.success("Supprimé !"); time.sleep(1); st.rerun()
                if new_selection:
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w") as zf:
                        for idx, file_path in enumerate(new_selection): 
                            ts = os.path.getmtime(file_path); date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                            new_name = f"Photo_Live{idx+1:02d}_{date_str}.jpg"
                            zf.write(file_path, arcname=new_name)
                    c2.download_button("⬇️ Télécharger Sélection (ZIP)", data=zip_buffer.getvalue(), file_name="selection.zip", mime="application/zip")
                zip_all = BytesIO()
                with zipfile.ZipFile(zip_all, "w") as zf:
                    for idx, file_path in enumerate(files): 
                        ts = os.path.getmtime(file_path); date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                        new_name = f"Photo_Live{idx+1:02d}_{date_str}.jpg"
                        zf.write(file_path, arcname=new_name)
                c3.download_button("⬇️ TOUT TÉLÉCHARGER (ZIP)", data=zip_all.getvalue(), file_name=f"toutes_photos.zip", mime="application/zip", type="primary")

        elif menu == "📊 DATA":
            st.subheader("📊 Résultats & Export")
            votes = load_json(VOTES_FILE, {})
            all_cands = {c: 0 for c in cfg["candidats"]}
            all_cands.update(votes)
            df_totals = pd.DataFrame(list(all_cands.items()), columns=['Candidat', 'Points']).sort_values(by='Points', ascending=False)
            chart = alt.Chart(df_totals).mark_bar(color="#E2001A").encode(x=alt.X('Points'), y=alt.Y('Candidat', sort='-x'), tooltip=['Candidat', 'Points']).properties(height=400).interactive(bind_y=False, bind_x=False)
            st.altair_chart(chart, use_container_width=True)
            col_exp1, col_exp2, col_exp3 = st.columns(3)
            col_exp1.download_button("📥 Résultats (CSV)", data=df_totals.to_csv(index=False).encode('utf-8'), file_name="resultats.csv", mime="text/csv")
            parts = load_json(PARTICIPANTS_FILE, [])
            col_exp2.download_button("👥 Votants (CSV)", data=pd.DataFrame(parts, columns=["Nom"]).to_csv(index=False).encode('utf-8'), file_name="votants.csv", mime="text/csv")
            if PDF_AVAILABLE:
                col_exp3.download_button("📄 Résultats (PDF)", data=create_pdf_results(cfg['titre_mur'], df_totals), file_name="resultats.pdf", mime="application/pdf")
            st.divider()
            st.subheader("Audit Détaillé")
            detailed_data = load_json(DETAILED_VOTES_FILE, [])
            if detailed_data:
                df_detail = pd.DataFrame(detailed_data)
                st.dataframe(df_detail, use_container_width=True)
                if PDF_AVAILABLE: st.download_button("📄 Audit (PDF)", data=create_pdf_audit(cfg['titre_mur'], df_detail), file_name="audit.pdf", mime="application/pdf")
            else: st.info("Vide")

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

    if cfg["mode_affichage"] == "photos_live":
        if "user_pseudo" not in st.session_state or st.session_state.user_pseudo != "Anonyme": st.session_state.user_pseudo = "Anonyme"
    elif cfg["mode_affichage"] == "votes":
        if "user_pseudo" in st.session_state and st.session_state.user_pseudo == "Anonyme": del st.session_state["user_pseudo"]; st.rerun()

    if cfg["mode_affichage"] != "photos_live":
        components.html(f"""<script>
            var sS = "{curr_sess}";
            var lS = localStorage.getItem('VOTE_SID_2026');
            if(lS !== sS) {{ localStorage.removeItem('HAS_VOTED_2026'); localStorage.setItem('VOTE_SID_2026', sS); if(window.parent.location.href.includes('blocked=true')) {{ window.parent.location.href = window.parent.location.href.replace('&blocked=true',''); }} }}
            if(localStorage.getItem('HAS_VOTED_2026') === 'true') {{ if(!window.parent.location.href.includes('blocked=true')) {{ window.parent.location.href = window.parent.location.href.split('?')[0] + '?mode=vote&blocked=true'; }} }}
        </script>""", height=0)
        if is_blocked or st.session_state.vote_success:
            st.balloons()
            st.markdown("""<div style='text-align:center; margin-top:50px; padding:20px;'><h1 style='color:#E2001A;'>MERCI !</h1><h2 style='color:white;'>Vote enregistré.</h2><br><div style='font-size:80px;'>✅</div></div>""", unsafe_allow_html=True)
            components.html("""<script>localStorage.setItem('HAS_VOTED_2026', 'true');</script>""", height=0)
            st.stop()

    if "user_pseudo" not in st.session_state:
        st.subheader("Identification")
        if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), width=100)
        pseudo = st.text_input("Veuillez entrer votre prénom ou Pseudo :")
        if st.button("ENTRER", type="primary", use_container_width=True) and pseudo:
            voters = load_json(VOTERS_FILE, [])
            if pseudo.strip().upper() in [v.upper() for v in voters]: st.error("Ce pseudo a déjà voté.")
            else:
                st.session_state.user_pseudo = pseudo.strip()
                parts = load_json(PARTICIPANTS_FILE, [])
                if pseudo.strip() not in parts: parts.append(pseudo.strip()); save_json(PARTICIPANTS_FILE, parts)
                st.rerun()
    else:
        if cfg["mode_affichage"] == "photos_live":
            st.info("📸 ENVOYER UNE PHOTO")
            up_key = f"uploader_{st.session_state.cam_reset_id}"
            cam_key = f"camera_{st.session_state.cam_reset_id}"
            uploaded_file = st.file_uploader("Choisir dans la galerie", type=['png', 'jpg', 'jpeg'], key=up_key)
            cam_file = st.camera_input("Prendre une photo", key=cam_key)
            final_file = uploaded_file if uploaded_file else cam_file
            if final_file:
                fname = f"live_{uuid.uuid4().hex}_{int(time.time())}.jpg"
                with open(os.path.join(LIVE_DIR, fname), "wb") as f: f.write(final_file.getbuffer())
                st.success("Photo envoyée !")
                st.session_state.cam_reset_id += 1; time.sleep(1); st.rerun()
        
        elif cfg["mode_affichage"] == "votes" and cfg["session_ouverte"]:
            st.write(f"Bonjour **{st.session_state.user_pseudo}**")
            if not st.session_state.rules_accepted:
                st.info("⚠️ **RÈGLES DU VOTE**")
                st.markdown("1. Sélectionnez **3 vidéos**.\n2. 🥇 1er = **5 pts**\n3. 🥈 2ème = **3 pts**\n4. 🥉 3ème = **1 pt**\n\n**Vote unique et définitif.**")
                if st.button("J'AI COMPRIS, JE VOTE !", type="primary", use_container_width=True): st.session_state.rules_accepted = True; st.rerun()
            else:
                choix = st.multiselect("Vos 3 vidéos préférées :", cfg["candidats"], max_selections=3)
                if len(choix) == 3:
                    if st.button("VALIDER (DÉFINITIF)", type="primary", use_container_width=True):
                        voters = load_json(VOTERS_FILE, [])
                        if st.session_state.user_pseudo.upper() in [v.upper() for v in voters]: st.error("Vote déjà enregistré !"); st.stop()
                        vts = load_json(VOTES_FILE, {})
                        pts = cfg.get("points_ponderation", [5, 3, 1])
                        for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                        save_json(VOTES_FILE, vts)
                        details = load_json(DETAILED_VOTES_FILE, [])
                        details.append({"Utilisateur": st.session_state.user_pseudo, "Choix 1 (5pts)": choix[0], "Choix 2 (3pts)": choix[1], "Choix 3 (1pt)": choix[2], "Date": datetime.now().strftime("%H:%M:%S")})
                        save_json(DETAILED_VOTES_FILE, details)
                        voters.append(st.session_state.user_pseudo); save_json(VOTERS_FILE, voters)
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

    ph = st.empty()
    
    if mode == "attente":
        logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="width:450px; margin-bottom:30px;">' if cfg.get("logo_b64") else ""
        ph.markdown(f"<div class='full-screen-center'>{logo_html}<h1 style='color:white; font-size:100px; margin:0; font-weight:bold;'>BIENVENUE</h1></div>", unsafe_allow_html=True)

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
                    img_src = f"data:image/png;base64,{cfg['candidats_images'][name]}" if name in cfg.get("candidats_images", {}) else f"data:image/png;base64,{DEFAULT_AVATAR}"
                    suspense_html += f'<div class="suspense-item"><img src="{img_src}" style="width:100px; height:100px; border-radius:50%; object-fit:cover; margin-bottom:10px;"><h3 style="color:white; margin:0;">{name}</h3></div>'
                ph.markdown(f"<div class='full-screen-center'>{logo_html}<h1 style='color:#E2001A; font-size:80px; margin:0;'>RÉSULTATS DANS... {remaining}</h1><div class='suspense-grid'>{suspense_html}</div></div>", unsafe_allow_html=True)
                time.sleep(1); st.rerun()
            else:
                cards_html = ""
                for winner in winners:
                    img_src = f"data:image/png;base64,{cfg['candidats_images'][winner]}" if winner in cfg.get("candidats_images", {}) else f"data:image/png;base64,{DEFAULT_AVATAR}"
                    cards_html += f"<div class='winner-card'><div style='font-size:60px;'>🏆</div><img src='{img_src}' style='width:150px; height:150px; border-radius:50%; border:6px solid white; object-fit:cover; margin-bottom:20px;'><h1 style='color:white; font-size:40px; margin:10px 0;'>{winner}</h1><h2 style='color:#FFD700; font-size:30px;'>VAINQUEUR</h2><h3 style='color:#CCC; font-size:20px;'>{max_score} points</h3></div>"
                ph.markdown(f"<div class='full-screen-center'>{logo_html}<div class='podium-container'>{cards_html}</div></div>", unsafe_allow_html=True)

        elif cfg.get("session_ouverte"):
            with ph.container():
                cands = cfg.get("candidats", [])
                imgs = cfg.get("candidats_images", {})
                mid = (len(cands) + 1) // 2
                left_list, right_list = cands[:mid], cands[mid:]
                c_left, c_center, c_right = st.columns([1, 1, 1])
                with c_left:
                    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
                    for c in left_list:
                        img_src = f"data:image/png;base64,{imgs[c]}" if c in imgs else f"data:image/png;base64,{DEFAULT_AVATAR}"
                        st.markdown(f"<div class='cand-row'><img src='{img_src}' class='cand-img'><span class='cand-name'>{c}</span></div>", unsafe_allow_html=True)
                with c_center:
                    st.markdown("<div style='height:12vh'></div>", unsafe_allow_html=True)
                    if cfg.get("logo_b64"): st.markdown(f"<div style='text-align:center; width:100%; margin-bottom:20px;'><img src='data:image/png;base64,{cfg['logo_b64']}' style='width:350px;'></div>", unsafe_allow_html=True)
                    host = st.context.headers.get('host', 'localhost')
                    qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
                    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
                    st.markdown(f"<div style='text-align:center; width:100%;'><img src='data:image/png;base64,{qr_b64}' style='width:240px; border-radius:10px;'></div>", unsafe_allow_html=True)
                    st.markdown("<div class='vote-cta'>À VOS VOTES !</div>", unsafe_allow_html=True)
                with c_right:
                    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
                    for c in right_list:
                        img_src = f"data:image/png;base64,{imgs[c]}" if c in imgs else f"data:image/png;base64,{DEFAULT_AVATAR}"
                        st.markdown(f"<div class='cand-row'><img src='{img_src}' class='cand-img'><span class='cand-name'>{c}</span></div>", unsafe_allow_html=True)

        else:
            logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="width:300px; margin-bottom:30px;">' if cfg.get("logo_b64") else ""
            ph.markdown(f"<div class='full-screen-center'>{logo_html}<div style='border: 5px solid #E2001A; padding: 50px; border-radius: 40px; background: rgba(0,0,0,0.9);'><h1 style='color:#E2001A; font-size:70px; margin:0;'>VOTES CLÔTURÉS</h1></div></div>", unsafe_allow_html=True)

    elif mode == "photos_live":
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        logo_data = cfg.get("logo_b64", "")
        center_html = f"<div id='center-box' style='position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); z-index:10; text-align:center; background:rgba(0,0,0,0.8); padding:20px; border-radius:30px; border:2px solid #E2001A;'>{'<img src=\"data:image/png;base64,'+logo_data+'\" style=\"width:200px; margin-bottom:15px; display:block; margin-left:auto; margin-right:auto;\">' if logo_data else ''}<div style='background:white; padding:10px; border-radius:10px; display:inline-block;'><img src='data:image/png;base64,{qr_b64}' style='width:150px;'></div><h2 style='color:white; margin-top:10px; font-size:24px;'>Partagez vos sourires et vos moments forts !</h2></div>"
        
        ph.markdown(center_html, unsafe_allow_html=True)
        
        photos = glob.glob(f"{LIVE_DIR}/*")
        if not photos: photos = []
        img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-40:]]) if photos else "[]"
        
        # --- SOLUTION ANIMATION ---
        # 1. setTimeout pour laisser le DOM charger
        # 2. Coordonnées explicites
        # 3. RequestAnimationFrame en boucle
        components.html(f"""<script>
            setTimeout(function() {{
                var doc = window.parent.document;
                var container = doc.getElementById('bubble-wall');
                if(container) container.remove();
                
                container = doc.createElement('div');
                container.id = 'bubble-wall'; 
                container.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:1;pointer-events:none;overflow:hidden;';
                doc.body.appendChild(container);
                
                const imgs = {img_js}; const bubbles = []; const bSize = 250;
                
                imgs.forEach((src, i) => {{
                    const el = doc.createElement('img'); el.src = src;
                    el.style.cssText = 'position:absolute; width:'+bSize+'px; height:'+bSize+'px; border-radius:50%; border:8px solid #E2001A; object-fit:cover;';
                    
                    // SPAWN ZONE: BAS DE L'ECRAN (Y > 500)
                    let startX = Math.random() * (window.innerWidth - bSize);
                    let startY = window.innerHeight - 300 - (Math.random() * 300);
                    
                    // IFRAME FIX: Si hauteur 0 détectée, on force
                    if(startY < 100) startY = 600;

                    let b = {{
                        el: el,
                        x: startX,
                        y: startY,
                        vx: (Math.random() - 0.5) * 6,
                        vy: - (3 + Math.random() * 4), // UPWARD SPEED
                        size: bSize
                    }};
                    container.appendChild(el); 
                    bubbles.push(b);
                }});
                
                function animate() {{
                    var centerBox = doc.getElementById('center-box');
                    // Fallback rectangle si pas de box
                    var rect = centerBox ? centerBox.getBoundingClientRect() : {{left:0, right:0, top:0, bottom:0}};
                    
                    bubbles.forEach(b => {{
                        b.x += b.vx; 
                        b.y += b.vy;
                        
                        // REBONDS SIMPLE
                        if(b.x <= 0 || b.x + b.size >= window.innerWidth) b.vx *= -1;
                        if(b.y <= 0 || b.y + b.size >= window.innerHeight) b.vy *= -1;
                        
                        // REPULSION CENTRALE
                        if(centerBox && b.x + b.size > rect.left && b.x < rect.right && b.y + b.size > rect.top && b.y < rect.bottom) {{
                            b.vx *= -1; b.vy *= -1;
                        }}
                        
                        // ANTI-COLLAGE HAUT DE PAGE
                        if(b.y < 50) b.vy = Math.abs(b.vy) + 2; 

                        b.el.style.transform = 'translate(' + b.x + 'px, ' + b.y + 'px)';
                    }});
                    requestAnimationFrame(animate);
                }}
                animate();
            }}, 500);
        </script>""", height=0)
