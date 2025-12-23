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
import shutil

# --- GESTION PDF & ALTAIR ---
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

def render_html(html_code):
    """Nettoie le HTML pour affichage propre sans bug d'indentation"""
    clean_code = textwrap.dedent(html_code).strip().replace("\n", " ")
    st.markdown(clean_code, unsafe_allow_html=True)

# --- INIT SESSION ---
if "config" not in st.session_state: st.session_state.config = load_json(CONFIG_FILE, default_config)
if "session_id" not in st.session_state.config: st.session_state.config["session_id"] = str(int(time.time()))
if "my_uuid" not in st.session_state: st.session_state.my_uuid = str(uuid.uuid4())
if "refresh_id" not in st.session_state: st.session_state.refresh_id = 0
if "cam_reset_id" not in st.session_state: st.session_state.cam_reset_id = 0
if "confirm_delete" not in st.session_state: st.session_state.confirm_delete = False
if "user_id" not in st.session_state: st.session_state.user_id = None
if "a_vote" not in st.session_state: st.session_state.a_vote = False
if "rules_accepted" not in st.session_state: st.session_state.rules_accepted = False
if "selected_photos" not in st.session_state: st.session_state.selected_photos = []

# --- LOGIQUE ---
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
        unique_id = uuid.uuid4().hex[:6]
        filename = f"live_{timestamp}_{unique_id}.jpg"
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

def generate_pdf_report(dataframe, title):
    if not HAS_FPDF: return None
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15); self.cell(0, 10, title, 0, 1, 'C'); self.ln(10)
        def footer(self):
            self.set_y(-15); self.set_font('Arial', 'I', 8); self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", size=10)
    cols = dataframe.columns.tolist(); col_width = 190 / len(cols)
    pdf.set_fill_color(200, 220, 255)
    for col in cols: pdf.cell(col_width, 10, str(col).encode('latin-1', 'replace').decode('latin-1'), 1, 0, 'C', 1)
    pdf.ln(); pdf.set_fill_color(255, 255, 255)
    for index, row in dataframe.iterrows():
        for col in cols: pdf.cell(col_width, 10, str(row[col]).encode('latin-1', 'replace').decode('latin-1'), 1, 0, 'C')
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"
is_blocked = st.query_params.get("blocked") == "true"

# =========================================================
# 1. CONSOLE ADMIN
# =========================================================
if est_admin:
    # --- CSS HEADER FIXE ADMIN ---
    logo_admin_css = ""
    if st.session_state.config.get("logo_b64"):
        logo_admin_css = f"""background-image: url('data:image/png;base64,{st.session_state.config["logo_b64"]}');"""
    
    st.markdown(f"""
    <style>
        .fixed-header {{
            position: fixed; top: 0; left: 0; width: 100%; height: 70px;
            background-color: #1E1E1E; z-index: 999999;
            display: flex; align-items: center; justify-content: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-bottom: 2px solid #E2001A;
        }}
        .header-title {{ color: white; font-size: 24px; font-weight: bold; text-transform: uppercase; }}
        .header-logo {{
            position: absolute; right: 20px; top: 5px; width: 60px; height: 60px;
            background-size: contain; background-repeat: no-repeat; background-position: center;
            {logo_admin_css}
        }}
        .block-container {{ margin-top: 40px; }}
        [data-testid="stSidebar"] {{ z-index: 999998; }}
    </style>
    <div class="fixed-header">
        <div class="header-title">Console Admin Gestion des Votes</div>
        <div class="header-logo"></div>
    </div>
    """, unsafe_allow_html=True)

    if "auth" not in st.session_state: st.session_state["auth"] = False
    if not st.session_state["auth"]:
        st.markdown("<br><br><h2 style='text-align:center;'>🔐 Authentification</h2>", unsafe_allow_html=True)
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
            
            with st.expander("🗑️ ZONE DE DANGER (Reset)"):
                c_r1, c_r2 = st.columns(2)
                if c_r1.button("♻️ RESET VOTES", type="primary", use_container_width=True):
                    for f in [VOTES_FILE, PARTICIPANTS_FILE, VOTERS_FILE, DETAILED_VOTES_FILE]: 
                        if os.path.exists(f): os.remove(f)
                    st.session_state.config["session_id"] = str(int(time.time()))
                    save_config()
                    st.toast("✅ Votes effacés !"); time.sleep(1); st.rerun()
                
                if c_r2.button("🗑️ VIDER PHOTOS", type="primary", use_container_width=True):
                    files = glob.glob(f"{LIVE_DIR}/*"); 
                    for f in files: os.remove(f)
                    st.toast("✅ Galerie vidée !"); time.sleep(1); st.rerun()

        elif menu == "⚙️ Paramétrage":
            st.title("⚙️ Paramétrage")
            
            st.subheader("1️⃣ Identité & Logo")
            c_g1, c_g2 = st.columns([2, 1])
            with c_g1:
                new_t = st.text_input("Titre de l'événement", value=st.session_state.config["titre_mur"])
                if st.button("Sauver Titre"): st.session_state.config["titre_mur"] = new_t; force_refresh(); st.rerun()
            with c_g2:
                up_l = st.file_uploader("Logo (PNG/JPG)", type=["png", "jpg"])
                if up_l:
                    b64 = process_image_upload(up_l)
                    if b64: st.session_state.config["logo_b64"] = b64; force_refresh(); st.success("Logo chargé !"); st.rerun()

            st.divider()
            
            # --- GESTION CANDIDATS ---
            st.subheader("2️⃣ Gestion des Candidats")
            st.info("Ajoutez ou supprimez des candidats ici.")
            
            # Gestion liste brute
            cands = st.session_state.config["candidats"]
            new_cand = st.text_input("Ajouter un candidat", placeholder="Nom du service...")
            if st.button("➕ Ajouter") and new_cand:
                if new_cand not in cands:
                    cands.append(new_cand)
                    st.session_state.config["candidats"] = cands
                    save_config(); st.rerun()
            
            st.markdown("---")
            st.subheader("3️⃣ Edition & Photos")
            st.write("Modifiez les noms et associez les photos.")
            
            # Affichage Ligne par Ligne
            for i, cand in enumerate(cands):
                # Colonnes : Photo | Nom (Grisé) | Boutons
                c_img, c_txt, c_btns = st.columns([1, 4, 3], vertical_alignment="center")
                
                # 1. Photo
                with c_img:
                    if cand in st.session_state.config["candidats_images"]:
                        st.image(BytesIO(base64.b64decode(st.session_state.config["candidats_images"][cand])), width=60)
                    else:
                        st.markdown("🚫")
                
                # 2. Nom (Grisé)
                with c_txt:
                    st.text_input("Nom", value=cand, disabled=True, key=f"dis_{i}", label_visibility="collapsed")
                
                # 3. Boutons
                with c_btns:
                    # Modifier le nom
                    with st.popover("✏️"):
                        new_name = st.text_input("Nouveau nom", value=cand, key=f"ren_{i}")
                        if st.button("Valider", key=f"v_ren_{i}"):
                            cands[i] = new_name
                            # Migrer l'image si elle existe
                            if cand in st.session_state.config["candidats_images"]:
                                st.session_state.config["candidats_images"][new_name] = st.session_state.config["candidats_images"].pop(cand)
                            st.session_state.config["candidats"] = cands
                            save_config(); st.rerun()
                    
                    # Upload Photo
                    with st.popover("🖼️"):
                        up = st.file_uploader(f"Photo {cand}", type=["png","jpg"], key=f"up_{i}")
                        if up:
                            b64 = process_image_upload(up)
                            if b64: st.session_state.config["candidats_images"][cand] = b64; save_config(); st.rerun()
                    
                    # Supprimer Photo
                    if cand in st.session_state.config["candidats_images"]:
                        if st.button("🗑️ Img", key=f"del_img_{i}"):
                            del st.session_state.config["candidats_images"][cand]
                            save_config(); st.rerun()
                    
                    # Supprimer Candidat
                    if st.button("❌", key=f"del_cand_{i}", help="Supprimer ce candidat"):
                        cands.pop(i)
                        st.session_state.config["candidats"] = cands
                        if cand in st.session_state.config["candidats_images"]:
                            del st.session_state.config["candidats_images"][cand]
                        save_config(); st.rerun()

        elif menu == "📸 Médiathèque":
            st.title("📸 Médiathèque & Export")
            files = glob.glob(f"{LIVE_DIR}/*"); files.sort(key=os.path.getmtime, reverse=True)
            
            if not files:
                st.warning("Aucune photo dans la galerie.")
            else:
                c_act1, c_act2, c_act3 = st.columns([1, 1, 2])
                with c_act1:
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w") as zf:
                        for f in files: zf.write(f, os.path.basename(f))
                    st.download_button("📥 TOUT TÉLÉCHARGER", data=zip_buffer.getvalue(), file_name="photos_all.zip", mime="application/zip", use_container_width=True)
                with c_act2:
                    if st.button("🗑️ TOUT SUPPRIMER", type="primary", use_container_width=True):
                        st.session_state.confirm_delete = True
                
                if st.session_state.confirm_delete:
                    st.error("Êtes-vous sûr ?")
                    c_yes, c_no = st.columns(2)
                    if c_yes.button("OUI, TOUT EFFACER"):
                        for f in files: os.remove(f)
                        st.session_state.confirm_delete = False; st.success("Terminé !"); time.sleep(1); st.rerun()
                    if c_no.button("NON"): st.session_state.confirm_delete = False; st.rerun()

                st.divider()
                st.write(f"**{len(files)} Photos**")
                
                view_mode = st.radio("Affichage :", ["🖼️ Pellicule (Grille)", "📝 Liste (Sélection)"], horizontal=True)
                
                if "Grille" in view_mode:
                    cols = st.columns(6)
                    for i, f in enumerate(files):
                        with cols[i%6]:
                            st.image(f, use_container_width=True)
                            if st.button("❌", key=f"del_g_{i}"): os.remove(f); st.rerun()
                else:
                    st.write("Sélectionnez les photos à exporter ou supprimer :")
                    c1, c2, c3 = st.columns([0.5, 3, 1])
                    c1.write("**Img**"); c2.write("**Fichier**"); c3.write("**Action**")
                    
                    selected_files = []
                    for i, f in enumerate(files):
                        c1, c2, c3 = st.columns([0.5, 3, 1], vertical_alignment="center")
                        with c1: st.image(f, width=50)
                        with c2: 
                            if st.checkbox(os.path.basename(f), key=f"chk_{i}"):
                                selected_files.append(f)
                        with c3:
                            if st.button("🗑️", key=f"del_l_{i}"): os.remove(f); st.rerun()
                    
                    if selected_files:
                        st.divider()
                        st.write(f"{len(selected_files)} photos sélectionnées")
                        sc1, sc2 = st.columns(2)
                        with sc1:
                            zip_sel = BytesIO()
                            with zipfile.ZipFile(zip_sel, "w") as zf:
                                for f in selected_files: zf.write(f, os.path.basename(f))
                            st.download_button("📥 TÉLÉCHARGER SÉLECTION", data=zip_sel.getvalue(), file_name="selection.zip", mime="application/zip", use_container_width=True)
                        with sc2:
                            if st.button("🗑️ SUPPRIMER SÉLECTION", type="primary", use_container_width=True):
                                for f in selected_files: os.remove(f)
                                st.rerun()

        elif menu == "📊 Data":
            st.title("📊 Données & Exports")
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                valid = {k:v for k,v in v_data.items() if k in st.session_state.config["candidats"]}
                if valid:
                    # 1. GRAPHIQUE
                    if HAS_ALTAIR:
                        df = pd.DataFrame(list(valid.items()), columns=['Candidat', 'Points']).sort_values('Points', ascending=False)
                        st.subheader("Graphique des Scores")
                        chart = alt.Chart(df).mark_bar().encode(
                            x='Points',
                            y=alt.Y('Candidat', sort='-x'),
                            color=alt.Color('Points', scale=alt.Scale(scheme='goldorange'))
                        )
                        st.altair_chart(chart, use_container_width=True)

                    # 2. TABLEAU
                    st.subheader("Tableau des Scores")
                    df = pd.DataFrame(list(valid.items()), columns=['Candidat', 'Points']).sort_values('Points', ascending=False)
                    st.dataframe(df, use_container_width=True)
                    if HAS_FPDF:
                        pdf_bytes = generate_pdf_report(df, "RESULTATS")
                        st.download_button("📄 PDF RESULTATS", data=pdf_bytes, file_name="resultats.pdf", mime="application/pdf")
            else: st.info("Aucun vote enregistré.")
            
            st.divider()
            st.subheader("Détail des Votants")
            det_votes = load_json(DETAILED_VOTES_FILE, [])
            if det_votes:
                df_det = pd.DataFrame(det_votes)
                st.dataframe(df_det, use_container_width=True)
                st.download_button("📥 CSV DETAILLÉ", data=df_det.to_csv().encode('utf-8'), file_name="votes_details.csv", mime="text/csv")
            else: st.info("Aucun détail.")

# =========================================================
# 2. APPLICATION MOBILE (UTILISATEUR)
# =========================================================
elif est_utilisateur:
    cfg = load_json(CONFIG_FILE, default_config)
    st.markdown("<style>.stApp {background-color:black; color:white;} [data-testid='stHeader'] {display:none;}</style>", unsafe_allow_html=True)
    
    # --- SECURITE : JS POUR DETECTER LE LOCALSTORAGE ---
    if not is_blocked:
        components.html("""
        <script>
            if(localStorage.getItem('has_voted_session_v1')) {
                window.parent.location.href = window.parent.location.href + "&blocked=true";
            }
        </script>
        """, height=0)

    if is_blocked:
        st.error("⛔ Vous avez déjà voté.")
        st.markdown("<h3 style='text-align:center; color:white;'>Merci de votre participation !</h3>", unsafe_allow_html=True)
        st.stop()

    # 2.1 ECRAN LOGIN
    if "user_pseudo" not in st.session_state:
        st.title("👋 Bienvenue")
        if cfg.get("logo_b64"): st.image(BytesIO(base64.b64decode(cfg["logo_b64"])), width=100)
        st.write("Pour participer, entrez votre prénom :")
        pseudo = st.text_input("Votre Pseudo", label_visibility="collapsed")
        if st.button("ENTRER", type="primary", use_container_width=True) and pseudo:
            st.session_state.user_pseudo = pseudo
            parts = load_json(PARTICIPANTS_FILE, [])
            if pseudo not in parts:
                parts.append(pseudo)
                with open(PARTICIPANTS_FILE, "w") as f: json.dump(parts, f)
            st.rerun()
            
    # 2.2 ECRAN REGLES (NOUVEAU)
    elif not st.session_state.rules_accepted and cfg.get("mode_affichage") != "photos_live":
        st.title("📜 Règles du vote")
        
        st.markdown("""
        <div style="background:#222; padding:15px; border-radius:10px; border:1px solid #E2001A;">
            <ul style="font-size:18px;">
                <li>Vous devez sélectionner <strong>3 candidats</strong>.</li>
                <li>Le vote est <strong>unique</strong> et définitif.</li>
            </ul>
            <hr>
            <h3 style="color:#E2001A">🏆 Pondération :</h3>
            <ul style="font-size:18px;">
                <li>🥇 <strong>1er choix :</strong> 5 Points</li>
                <li>🥈 <strong>2ème choix :</strong> 3 Points</li>
                <li>🥉 <strong>3ème choix :</strong> 1 Point</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("✅ J'AI COMPRIS", type="primary", use_container_width=True):
            st.session_state.rules_accepted = True
            st.rerun()
    
    # 2.3 ECRAN PRINCIPAL
    else:
        st.markdown(f"#### Bonjour {st.session_state.user_pseudo} !")
        
        # MODE PHOTO (Modifié avec onglets)
        if cfg.get("mode_affichage") == "photos_live":
            st.info("📷 Le mur photo est ouvert !")
            
            tab1, tab2 = st.tabs(["📸 Prendre Photo", "🖼️ Galerie"])
            
            photo_to_save = None
            
            with tab1:
                cam = st.camera_input("Camera", key=f"cam_{st.session_state.cam_reset_id}", label_visibility="collapsed")
                if cam: photo_to_save = cam
            
            with tab2:
                upl = st.file_uploader("Importer", type=["png", "jpg", "jpeg"], key=f"up_{st.session_state.cam_reset_id}", label_visibility="collapsed")
                if upl: photo_to_save = upl
            
            if photo_to_save:
                if save_live_photo(photo_to_save): 
                    st.success("Envoyée !")
                    st.session_state.cam_reset_id += 1 # Force le refresh des widgets
                    time.sleep(1)
                    st.rerun()
        
        # MODE VOTE
        else:
            if not cfg.get("session_ouverte"):
                st.warning("⏳ Les votes sont fermés pour le moment.")
            else:
                if st.session_state.get("a_vote"):
                    st.success("✅ Vote enregistré. Merci !")
                else:
                    st.write("Sélectionnez vos 3 favoris (Ordre : 1er, 2ème, 3ème) :")
                    choix = st.multiselect("Choix", cfg.get("candidats", []), label_visibility="collapsed")
                    if len(choix) == 3:
                        if st.button("VALIDER MES CHOIX (Définitif)", type="primary", use_container_width=True):
                            vts = load_json(VOTES_FILE, {})
                            pts = cfg.get("points_ponderation", [5, 3, 1])
                            for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                            json.dump(vts, open(VOTES_FILE, "w"))
                            
                            voters = load_json(VOTERS_FILE, [])
                            voters.append(st.session_state.user_pseudo) # On sauve le pseudo
                            with open(VOTERS_FILE, "w") as f: json.dump(voters, f)
                            
                            # Log détaillé
                            det = load_json(DETAILED_VOTES_FILE, [])
                            det.append({"user": st.session_state.user_pseudo, "choix_1": choix[0], "choix_2": choix[1], "choix_3": choix[2], "time": str(datetime.now())})
                            with open(DETAILED_VOTES_FILE, "w") as f: json.dump(det, f)

                            # Injection du marqueur de vote
                            components.html("""<script>localStorage.setItem('has_voted_session_v1', 'true');</script>""", height=0)
                            
                            st.session_state.a_vote = True
                            time.sleep(1)
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
        .social-header { text-align: center; margin-bottom: 20px; color: white; }
        .social-header img { max-height: 120px; margin-bottom: 10px; }
        .social-header h1 { font-size: 50px; text-transform: uppercase; margin: 0; }
        .footer-stats { text-align: center; margin-top: 20px; color: white; font-size: 20px; }
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

    # HEADER COMMUN
    header_html = f"""
    <div class="social-header">
        {logo_part}
        <h1>{cfg.get('titre_mur')}</h1>
    </div>
    """

    # FOOTER COMMUN (Participants)
    parts = load_json(PARTICIPANTS_FILE, [])
    tags_html = "".join([f"<span class='user-tag'>{p}</span>" for p in parts[-15:]]) # Max 15 derniers
    footer_html = f"""
    <div class="footer-stats">
        <div>👥 {len(parts)} CONNECTÉS</div>
        <div style="margin-top:10px;">{tags_html}</div>
    </div>
    """

    # --- A. ACCUEIL ---
    if mode == "attente":
        render_html(f"""
        <div style="height: 100vh; display: flex; flex-direction: column; justify-content: center;">
            {header_html}
            <h2 style="text-align:center; color:#E2001A; font-size:40px;">BIENVENUE</h2>
            <h3 style="text-align:center; color:#CCC;">Veuillez patienter...</h3>
            {footer_html}
        </div>
        """)

    # --- B. VOTES ---
    elif mode == "votes":
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        
        if cfg.get("session_ouverte"):
            cands = cfg.get("candidats", [])
            mid = (len(cands) + 1) // 2
            
            def build_list(items):
                h = ""
                for c in items:
                    img = ""
                    if c in cfg.get("candidats_images", {}):
                        img = f'<img src="data:image/png;base64,{cfg["candidats_images"][c]}" style="width:60px; height:60px; border-radius:50%; object-fit:cover; border:2px solid #E2001A;">'
                    h += f'<div class="cand-row">{img}<span class="cand-name">{c}</span></div>'
                return h

            col_g = build_list(cands[:mid])
            col_d = build_list(cands[mid:])
            
            render_html(f"""
            <div style="display:flex; flex-direction: column; height:98vh;">
                {header_html}
                <div style="display:flex; flex: 1; overflow: hidden;">
                    <div style="width:30%; overflow-y:auto; padding:10px;">{col_g}</div>
                    <div style="width:40%; text-align:center; display:flex; flex-direction:column; justify-content:center;">
                        <h1 style="color:#E2001A; font-size:50px;">A VOS VOTES !</h1>
                        <div style="background:white; padding:15px; border-radius:20px; display:inline-block; margin:20px auto;">
                            <img src="data:image/png;base64,{qr_b64}" width="220">
                        </div>
                        <h2 style="color:white;">Scannez pour voter</h2>
                    </div>
                    <div style="width:30%; overflow-y:auto; padding:10px;">{col_d}</div>
                </div>
                {footer_html}
            </div>
            """)
        
        elif cfg.get("reveal_resultats"):
            # PODIUM
            diff = 10 - int(time.time() - cfg.get("timestamp_podium", 0))
            
            if diff > 0:
                render_html(f"""
                <div style="height:100vh; display:flex; flex-direction:column; justify-content:center; align-items:center;">
                    {header_html}
                    <div style="font-size:200px; color:#E2001A; font-weight:bold;">{diff}</div>
                    <h2 style="color:white;">RÉSULTATS DANS...</h2>
                </div>
                """)
                time.sleep(1); st.rerun()
            else:
                v_data = load_json(VOTES_FILE, {})
                sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)[:3]
                
                c1, c2, c3 = st.columns([1,1.2,1])
                
                def get_card(rank_idx, data):
                    if not data: return ""
                    name, score = data
                    colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
                    ranks = ["🥇", "🥈", "🥉"]
                    cls = "winner-card" if rank_idx == 0 else ""
                    img_html = ""
                    if name in cfg.get("candidats_images", {}):
                        img_html = f'<img src="data:image/png;base64,{cfg["candidats_images"][name]}" style="width:120px; height:120px; border-radius:50%; margin-bottom:10px; border:3px solid {colors[rank_idx]};">'
                    
                    return f"""
                    <div class="{cls}" style="background:rgba(255,255,255,0.1); border:4px solid {colors[rank_idx]}; border-radius:20px; padding:30px; text-align:center; color:white; margin-top:{'0' if rank_idx==0 else '80'}px;">
                        <div style="font-size:60px;">{ranks[rank_idx]}</div>
                        {img_html}
                        <h2 style="font-size:35px; margin:10px 0;">{name}</h2>
                        <h3 style="font-size:25px; color:#ddd;">{score} pts</h3>
                    </div>
                    """
                
                st.markdown(header_html, unsafe_allow_html=True)
                with c1: render_html(get_card(1, sorted_v[1] if len(sorted_v)>1 else None))
                with c2: render_html(get_card(0, sorted_v[0] if len(sorted_v)>0 else None))
                with c3: render_html(get_card(2, sorted_v[2] if len(sorted_v)>2 else None))

        else:
            # Votes CLOS
            render_html(f"""
            <div style="height:100vh; display:flex; flex-direction:column; justify-content:center; align-items:center;">
                {header_html}
                <div style="border: 6px solid #E2001A; padding: 40px 80px; border-radius: 30px; background:rgba(0,0,0,0.8); text-align:center;">
                    <h1 style="color:#E2001A; font-size:80px; margin:0;">MERCI DE VOTRE PARTICIPATION</h1>
                    <h2 style="color:white; font-size:40px; margin-top:20px;">LES VOTES SONT CLOS</h2>
                </div>
                {footer_html}
            </div>
            """)

    # --- C. PHOTOS LIVE ---
    elif mode == "photos_live":
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        
        logo_live = ""
        if cfg.get("logo_b64"):
            logo_live = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:250px; width:auto; display:block; margin: 0 auto 20px auto;">'
        
        render_html(f"""
        <div style="position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); z-index:999; display:flex; flex-direction:column; align-items:center; gap:20px;">
            {logo_live}
            <h1 style="color:white; font-size:60px; font-weight:bold; text-transform:uppercase; margin-bottom:20px; text-shadow: 0 0 10px rgba(0,0,0,0.5);">MUR PHOTOS LIVE</h1>
            <div style="background:white; padding:20px; border-radius:25px; box-shadow: 0 0 60px rgba(0,0,0,0.8);">
                <img src="data:image/png;base64,{qr_b64}" width="160" style="display:block;">
            </div>
            <div style="background: #E2001A; color: white; padding: 15px 40px; border-radius: 50px; font-weight: bold; font-size: 26px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-transform: uppercase; white-space: nowrap; border: 2px solid white;">
                📸 SCANNEZ POUR PARTICIPER
            </div>
        </div>
        """)
        
        photos = glob.glob(f"{LIVE_DIR}/*"); photos.sort(key=os.path.getmtime, reverse=True); recent_photos = photos[:40] 
        img_array_js = []
        for photo_path in recent_photos:
            with open(photo_path, "rb") as f: b64 = base64.b64encode(f.read()).decode(); img_array_js.append(f"data:image/jpeg;base64,{b64}")
        js_img_list = json.dumps(img_array_js)
        
        # JS CORRIGÉ : REBOND SUR LE CENTRE + Z-INDEX
        components.html(f"""<html><head><style>body {{ margin: 0; overflow: hidden; background: transparent; }} .bubble {{ position: absolute; border-radius: 50%; border: 4px solid #E2001A; box-shadow: 0 0 20px rgba(226, 0, 26, 0.5); object-fit: cover; will-change: transform; }}</style></head><body><div id="container"></div><script>
            var doc = window.parent.document;
            var containerId = 'live-bubble-container';
            var existingContainer = doc.getElementById(containerId);
            
            if (existingContainer) {{
                existingContainer.innerHTML = '';
            }} else {{
                existingContainer = doc.createElement('div');
                existingContainer.id = containerId;
                existingContainer.style.position = 'fixed';
                existingContainer.style.top = '0';
                existingContainer.style.left = '0';
                existingContainer.style.width = '100vw';
                existingContainer.style.height = '100vh';
                existingContainer.style.pointerEvents = 'none';
                existingContainer.style.zIndex = '1';
                doc.body.appendChild(existingContainer);
            }}

            const images = {js_img_list};
            const speed = 1.0; 
            const bubbles = [];

            images.forEach((src) => {{ 
                const img = doc.createElement('img'); 
                img.src = src; 
                img.className = 'bubble'; 
                img.style.position = 'absolute';
                img.style.borderRadius = '50%';
                img.style.border = '4px solid #E2001A';
                img.style.objectFit = 'cover';
                
                const size = 60 + Math.random() * 60; 
                img.style.width = size + 'px'; 
                img.style.height = size + 'px'; 
                
                let startX = Math.random() * (window.innerWidth - size);
                let startY = Math.random() * (window.innerHeight - size);
                
                let vx = (Math.random() - 0.5) * speed * 3;
                let vy = (Math.random() - 0.5) * speed * 3;
                
                const bubble = {{ element: img, x: startX, y: startY, vx: vx, vy: vy, size: size }}; 
                
                existingContainer.appendChild(img); 
                bubbles.push(bubble); 
            }}); 
            
            function animate() {{ 
                const w = window.innerWidth; 
                const h = window.innerHeight; 
                const centerX = w / 2;
                const centerY = h / 2;
                const safeZoneW = 400; 
                const safeZoneH = 500; 

                bubbles.forEach(b => {{ 
                    b.x += b.vx; 
                    b.y += b.vy; 
                    
                    if (b.x <= 0 || b.x + b.size >= w) b.vx *= -1; 
                    if (b.y <= 0 || b.y + b.size >= h) b.vy *= -1; 
                    
                    if (b.x + b.size > centerX - safeZoneW/2 && b.x < centerX + safeZoneW/2 && 
                        b.y + b.size > centerY - safeZoneH/2 && b.y < centerY + safeZoneH/2) {{
                        if(Math.abs(b.x - centerX) > Math.abs(b.y - centerY)) b.vx *= -1;
                        else b.vy *= -1;
                    }}

                    b.element.style.transform = `translate(${{b.x}}px, ${{b.y}}px)`; 
                }}); 
                requestAnimationFrame(animate); 
            }} 
            animate();
        </script></body></html>""", height=1000)
