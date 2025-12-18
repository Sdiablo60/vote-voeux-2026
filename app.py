import streamlit as st
import os
import glob
import base64
import qrcode
import time
import zipfile
import datetime
import random
from io import BytesIO
import streamlit.components.v1 as components

# --- 1. CONFIGURATION INITIALE ---
st.set_page_config(page_title="Social Wall Pro", layout="wide")

GALLERY_DIR = "galerie_images"
LOGO_FILE = "logo_entreprise.png"
if not os.path.exists(GALLERY_DIR): os.makedirs(GALLERY_DIR)

# --- 2. GESTION DE LA SESSION ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "admin_password" not in st.session_state:
    st.session_state["admin_password"] = "ADMIN_LIVE_MASTER"
if "all_selected" not in st.session_state:
    st.session_state["all_selected"] = False

# --- 3. FONCTIONS ---
def create_zip(file_list):
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for f in file_list:
            if os.path.exists(f):
                z.write(f, os.path.basename(f))
    return buf.getvalue()

def get_timestamped_name(prefix):
    now = datetime.datetime.now()
    return f"{now.strftime('%Y-%m-%d_%Hh%M')}_{prefix}.zip"

# --- 4. INTERFACE ADMINISTRATION ---
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

if est_admin:
    # --- CSS PERSONNALISÉ (TYPOGRAPHIE ET COULEURS) ---
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
        
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Roboto', sans-serif;
        }
        
        .main-header-sticky {
            position: sticky;
            top: 0px;
            background-color: white;
            z-index: 1000;
            padding: 20px 0;
            border-bottom: 3px solid #E2001A; /* Rouge Transdev par défaut */
        }
        
        h1, h2, h3 {
            color: #4D4D4D; /* Gris foncé typique */
        }
        
        [data-testid="column"] { min-width: 0px !important; }
        
        .stButton button {
            border-radius: 4px;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, use_container_width=True)
        st.markdown("<h3 style='text-align: center;'>Régie Social Wall</h3>", unsafe_allow_html=True)
        pwd_input = st.text_input("Code Accès", type="password", key="main_login_input")
        
        if pwd_input == st.session_state["admin_password"]:
            st.session_state["authenticated"] = True
        else:
            st.session_state["authenticated"] = False

        st.divider()

        if st.session_state["authenticated"]:
            with st.expander("🔑 Sécurité"):
                new_pwd = st.text_input("Nouveau code", type="password")
                if st.button("Modifier"):
                    st.session_state["admin_password"] = new_pwd
                    st.rerun()
            
            st.subheader("🖼️ Identité")
            ul_logo = st.file_uploader("Logo", type=['png', 'jpg', 'jpeg'])
            if ul_logo:
                with open(LOGO_FILE, "wb") as f: f.write(ul_logo.getbuffer())
                st.rerun()
            
            if st.button("🧨 VIDER LE MUR", use_container_width=True, type="primary"):
                for f in glob.glob(os.path.join(GALLERY_DIR, "*")):
                    try: os.remove(f)
                    except: pass
                st.rerun()

    if st.session_state["authenticated"]:
        # --- EN-TÊTE FIGÉ AVEC LOGO AGRANDI ---
        st.markdown('<div class="main-header-sticky">', unsafe_allow_html=True)
        
        # Structure de l'en-tête : Logo à gauche (plus grand), Titre à droite
        c_logo_main, c_title_main = st.columns([1, 2])
        
        if os.path.exists(LOGO_FILE):
            # Logo agrandi au centre
            c_logo_main.image(LOGO_FILE, width=250) # Taille augmentée
        
        with c_title_main:
            st.markdown("<h1 style='margin-bottom:0;'>Console de Modération</h1>", unsafe_allow_html=True)
            st.caption("Gestion de la galerie en temps réel")

        st.link_button("🖥️ ACCÉDER AU MUR PLEIN ÉCRAN", f"https://{st.context.headers.get('host', 'localhost')}/", use_container_width=True)

        all_imgs = [f for f in glob.glob(os.path.join(GALLERY_DIR, "*")) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        sorted_imgs = sorted(all_imgs, key=os.path.getmtime, reverse=True)
        selected_photos = []

        # Barre de contrôle
        ctrl1, ctrl2, ctrl3, ctrl4, ctrl5 = st.columns([1.2, 0.8, 1, 1, 1])
        ctrl1.write(f"📊 **{len(all_imgs)} fichiers**")
        
        if ctrl2.button("✅/⬜ Tout" , use_container_width=True):
            st.session_state["all_selected"] = not st.session_state["all_selected"]
            st.rerun()

        if all_imgs:
            with ctrl3:
                st.download_button("📥 ZIP Complet", data=create_zip(all_imgs), file_name=get_timestamped_name("complet"), use_container_width=True)
        
        with ctrl5:
            mode_vue = st.radio("Format", ["Vignettes", "Liste"], horizontal=True, label_visibility="collapsed")
        
        st.markdown('</div>', unsafe_allow_html=True)

        # --- CONTENU ---
        with st.expander("➕ Importer des fichiers"):
            up = st.file_uploader("Upload", accept_multiple_files=True, key="manual_up")
            if up:
                for f in up:
                    with open(os.path.join(GALLERY_DIR, f.name), "wb") as out: out.write(f.getbuffer())
                st.rerun()

        if not all_imgs:
            st.info("La galerie est vide.")
        else:
            if mode_vue == "Vignettes":
                for i in range(0, len(sorted_imgs), 8):
                    cols = st.columns(8)
                    for j in range(8):
                        idx = i + j
                        if idx < len(sorted_imgs):
                            img_p = sorted_imgs[idx]
                            with cols[j]:
                                is_checked = st.checkbox("Sél.", value=st.session_state["all_selected"], key=f"v_{img_p}_{idx}")
                                if is_checked: selected_photos.append(img_p)
                                st.image(img_p, use_container_width=True)
                                if st.button("🗑️", key=f"del_{img_p}_{idx}"): os.remove(img_p); st.rerun()
            else:
                for i in range(0, len(sorted_imgs), 4):
                    cols = st.columns(4)
                    for j in range(4):
                        idx = i + j
                        if idx < len(sorted_imgs):
                            img_p = sorted_imgs[idx]
                            with cols[j]:
                                with st.container(border=True):
                                    c_check, c_preview, c_margin = st.columns([1, 6, 1])
                                    with c_check:
                                        is_checked = st.checkbox("", value=st.session_state["all_selected"], key=f"l_chk_{img_p}_{idx}", label_visibility="collapsed")
                                        if is_checked: selected_photos.append(img_p)
                                    with c_preview:
                                        st.image(img_p, use_container_width=True)
                                    st.caption(f"ID: {os.path.basename(img_p)[:20]}")
                                    if st.button("Supprimer", key=f"btn_l_{img_p}_{idx}", use_container_width=True):
                                        os.remove(img_p); st.rerun()

        if selected_photos:
            with ctrl4:
                st.download_button(f"📥 ZIP Sél. ({len(selected_photos)})", data=create_zip(selected_photos), file_name=get_timestamped_name("selection"), use_container_width=True, type="primary")

    else:
        st.markdown('<div style="text-align:center; margin-top:100px;"><h2>🔒 Console Verrouillée</h2><p>Veuillez entrer le mot de passe dans le menu latéral.</p></div>', unsafe_allow_html=True)

# --- 5. MODE LIVE (MUR NOIR) ---
elif not mode_vote:
    st.markdown("""<style>:root { background-color: black; } [data-testid="stAppViewContainer"], .stApp { background-color: black !important; } [data-testid="stHeader"], footer { display: none !important; } </style>""", unsafe_allow_html=True)
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=25000, key="wall_refresh")
    except: pass
    img_list = [f for f in glob.glob(os.path.join(GALLERY_DIR, "*")) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
    logo_b64_live = ""
    if os.path.exists(LOGO_FILE):
        with open(LOGO_FILE, "rb") as f: logo_b64_live = base64.b64encode(f.read()).decode()
    photos_html = ""
    for img_path in img_list[-15:]:
        with open(img_path, "rb") as f: b64 = base64.b64encode(f.read()).decode()
        photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:{random.randint(200, 300)}px; height:{random.randint(200, 300)}px; top:{random.randint(10, 70)}%; left:{random.randint(5, 80)}%; animation-duration:{random.uniform(8, 14)}s;">'
    html_code = f"""<!DOCTYPE html><html><body style="margin:0; background:black; overflow:hidden; height:100vh; width:100vw;"><style> .container {{ position:relative; width:100vw; height:100vh; background:black; overflow:hidden; }} .main-title {{ position:absolute; top:40px; width:100%; text-align:center; color:white; font-family:sans-serif; font-size:55px; font-weight:bold; z-index:1001; text-shadow:0 0 20px rgba(255,255,255,0.7); }} .center-stack {{ position:absolute; top:55%; left:50%; transform:translate(-50%, -50%); z-index:1000; display:flex; flex-direction:column; align-items:center; gap:20px; }} .logo {{ max-width:350px; filter:drop-shadow(0 0 15px white); }} .qr-box {{ background:white; padding:12px; border-radius:15px; text-align:center; }} .photo {{ position:absolute; border-radius:50%; border:5px solid white; object-fit:cover; animation:move alternate infinite ease-in-out; opacity:0.95; box-shadow:0 0 20px rgba(0,0,0,0.5); }} @keyframes move {{ from {{ transform:translate(0,0) rotate(0deg); }} to {{ transform:translate(60px, 80px) rotate(8deg); }} }} </style><div class="container"><div class="main-title">MEILLEURS VŒUX 2026</div><div class="center-stack">{f'<img src="data:image/png;base64,{logo_b64_live}" class="logo">' if logo_b64_live else ''}<div class="qr-box"><img src="data:image/png;base64,{qr_b64}" width="160"></div></div>{photos_html}</div></body></html>"""
    components.html(html_code, height=1000)

# --- 6. MODE VOTE ---
else:
    st.title("📸 Envoyez votre photo !")
    f = st.file_uploader("Image", type=['jpg', 'jpeg', 'png'])
    if f:
        with open(os.path.join(GALLERY_DIR, f"img_{random.randint(1000,9999)}.jpg"), "wb") as out: out.write(f.getbuffer())
        st.success("✅ Photo envoyée !")
