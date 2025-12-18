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

# --- 3. LOGIQUE DE NAVIGATION ---
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

# --- 4. FONCTIONS ---
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

# --- 5. INTERFACE ADMINISTRATION ---
if est_admin:
    # CSS POUR FIGER LE HAUT
    st.markdown("""
        <style>
        /* Conteneur principal */
        .main-header-sticky {
            position: sticky;
            top: 45px;
            background-color: white;
            z-index: 999;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f2f6;
        }
        /* Ajustement pour Streamlit Cloud */
        [data-testid="stHeader"] { background: rgba(0,0,0,0); }
        .stApp { background-color: white; }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("<h2 style='text-align: center; margin-top:-20px;'>⚙️ Régie Live</h2>", unsafe_allow_html=True)
        pwd_input = st.text_input("Accès Régie (Code)", type="password", key="main_login_input")
        
        if pwd_input == st.session_state["admin_password"]:
            st.session_state["authenticated"] = True
        else:
            st.session_state["authenticated"] = False

        st.divider()

        if st.session_state["authenticated"]:
            st.success("✅ Connecté")
            with st.expander("🔑 Changer le mot de passe"):
                new_pwd = st.text_input("Nouveau code", type="password")
                if st.button("Enregistrer"):
                    st.session_state["admin_password"] = new_pwd
                    st.rerun()
            st.divider()
            ul_logo = st.file_uploader("Logo", type=['png', 'jpg', 'jpeg'])
            if ul_logo:
                with open(LOGO_FILE, "wb") as f: f.write(ul_logo.getbuffer())
                st.rerun()
            if st.button("🧨 VIDER LE MUR", use_container_width=True):
                for f in glob.glob(os.path.join(GALLERY_DIR, "*")):
                    try: os.remove(f)
                    except: pass
                st.rerun()
        else:
            st.warning("🔒 Entrez le code à gauche")

    if st.session_state["authenticated"]:
        # --- SECTION FIGÉE (STICKY) ---
        header_container = st.container()
        with header_container:
            # On enveloppe dans un div HTML pour le CSS sticky
            st.markdown('<div class="main-header-sticky">', unsafe_allow_html=True)
            
            logo_b64 = ""
            if os.path.exists(LOGO_FILE):
                with open(LOGO_FILE, "rb") as f: logo_b64 = base64.b64encode(f.read()).decode()
            
            # Titre et Logo
            st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <h1 style="margin:0; color: black; font-size: 24px;">Console de Modération</h1>
                    {f'<img src="data:image/png;base64,{logo_b64}" style="max-height:50px;">' if logo_b64 else ''}
                </div>
            """, unsafe_allow_html=True)
            
            st.link_button("🖥️ ACCÉDER AU MUR PLEIN ÉCRAN", f"https://{st.context.headers.get('host', 'localhost')}/", use_container_width=True)

            # Ligne de contrôle des photos
            all_imgs = [f for f in glob.glob(os.path.join(GALLERY_DIR, "*")) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            sorted_imgs = sorted(all_imgs, key=os.path.getmtime, reverse=True)
            selected_photos = []

            c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
            c1.markdown(f"**Photos : {len(all_imgs)}**")
            
            if all_imgs:
                with c2:
                    st.download_button("📥 Tout (ZIP)", data=create_zip(all_imgs), file_name=get_timestamped_name("complet"), use_container_width=True)
            
            with c4:
                mode_vue = st.radio("Vue", ["Vignettes", "Liste"], horizontal=True, label_visibility="collapsed")
            
            st.markdown('</div>', unsafe_allow_html=True)

        # --- CONTENU DÉFILANT ---
        with st.expander("➕ Ajouter des photos manuellement"):
            up = st.file_uploader("Images", accept_multiple_files=True, key="manual_up")
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
                        if (i + j) < len(sorted_imgs):
                            img_p = sorted_imgs[i + j]
                            with cols[j]:
                                if st.checkbox("Sél.", key=f"v_{img_p}"): selected_photos.append(img_p)
                                st.image(img_p, use_container_width=True)
                                if st.button("🗑️", key=f"del_{img_p}"): os.remove(img_p); st.rerun()
            else:
                for img_p in sorted_imgs:
                    col_chk, col_img, col_name, col_del = st.columns([0.5, 1, 5, 1])
                    if col_chk.checkbox("", key=f"l_{img_p}"): selected_photos.append(img_p)
                    col_img.image(img_p, width=50)
                    col_name.text(os.path.basename(img_p))
                    if col_del.button("Suppr.", key=f"btn_{img_p}", use_container_width=True): os.remove(img_p); st.rerun()

        # Injection du bouton de sélection dynamique
        if selected_photos:
            with c3:
                st.download_button(f"📥 Sél. ({len(selected_photos)})", data=create_zip(selected_photos), file_name=get_timestamped_name("selection"), use_container_width=True, type="primary")

    else:
        st.markdown('<div style="text-align:center; margin-top:100px; padding:50px; border:2px dashed #ccc; border-radius:20px;"><h1>🔒 Console Verrouillée</h1><p>Saisissez le code dans la barre latérale.</p></div>', unsafe_allow_html=True)

# --- 6. MODE LIVE (MUR NOIR) ---
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

# --- 7. MODE VOTE ---
else:
    st.title("📸 Envoyez votre photo !")
    f = st.file_uploader("Image", type=['jpg', 'jpeg', 'png'])
    if f:
        with open(os.path.join(GALLERY_DIR, f"img_{random.randint(1000,9999)}.jpg"), "wb") as out: out.write(f.getbuffer())
        st.success("✅ Photo envoyée !")
