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

# --- 2. LOGIQUE DE NAVIGATION ---
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

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
if est_admin:
    # --- BARRE LATÉRALE ---
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Le mot de passe pour débloquer les actions critiques
        pwd = st.text_input("Code Secret Admin", type="password")
        st.divider()

        # CES MENUS SONT MAINTENANT TOUJOURS PRÉSENTS
        st.subheader("🖼️ Identité")
        ul_logo = st.file_uploader("Changer le logo", type=['png', 'jpg', 'jpeg'], key="side_logo")
        if ul_logo:
            with open(LOGO_FILE, "wb") as f: f.write(ul_logo.getbuffer())
            st.rerun()

        st.divider()
        st.subheader("🔄 Maintenance")
        if st.button("🔄 Actualiser la galerie", use_container_width=True):
            st.rerun()

        if pwd == "ADMIN_LIVE_MASTER":
            if st.button("🧨 VIDER TOUT (Danger)", use_container_width=True):
                for f in glob.glob(os.path.join(GALLERY_DIR, "*")):
                    try: os.remove(f)
                    except: pass
                st.rerun()

    # --- ZONE CENTRALE ---
    if pwd == "ADMIN_LIVE_MASTER":
        # Style
        st.markdown("""<style>.header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #f0f2f6; padding-bottom: 10px; }</style>""", unsafe_allow_html=True)
        
        # En-tête avec logo
        logo_html = ""
        if os.path.exists(LOGO_FILE):
            with open(LOGO_FILE, "rb") as f: b64 = base64.b64encode(f.read()).decode()
            logo_html = f'<img src="data:image/png;base64,{b64}" style="max-height: 60px;">'
        
        st.markdown(f'<div class="header"><h1>Console Régie</h1>{logo_html}</div>', unsafe_allow_html=True)
        st.link_button("🖥️ PROJETER LE MUR", f"https://{st.context.headers.get('host', 'localhost')}/", use_container_width=True)

        # Import Manuel (Celui-ci se referme bien après import)
        with st.expander("➕ Ajouter des photos manuellement"):
            up = st.file_uploader("Choisir les fichiers", accept_multiple_files=True, key="manual_up")
            if up:
                for f in up:
                    with open(os.path.join(GALLERY_DIR, f.name), "wb") as out:
                        out.write(f.getbuffer())
                st.success("Photos ajoutées !")
                time.sleep(1)
                st.rerun()

        st.divider()

        # Galerie
        all_imgs = [f for f in glob.glob(os.path.join(GALLERY_DIR, "*")) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        sorted_imgs = sorted(all_imgs, key=os.path.getmtime, reverse=True)

        # LIGNE DE CONTRÔLE UNIFIÉE
        c_titre, c_zip_all, c_zip_sel, c_vue = st.columns([1.5, 1, 1, 1])
        c_titre.subheader(f"🖼️ Modération ({len(sorted_imgs)})")
        
        if sorted_imgs:
            with c_zip_all:
                st.download_button("📥 Tout (ZIP)", data=create_zip(sorted_imgs), file_name=get_timestamped_name("galerie_complete"), use_container_width=True)
        
        mode_vue = c_vue.radio("Vue", ["Vignettes", "Liste"], horizontal=True, label_visibility="collapsed")

        selected_photos = []
        if not sorted_imgs:
            st.info("Aucune photo disponible.")
        else:
            if mode_vue == "Vignettes":
                for i in range(0, len(sorted_imgs), 8):
                    cols = st.columns(8)
                    for j in range(8):
                        if (i + j) < len(sorted_imgs):
                            img_p = sorted_imgs[i + j]
                            with cols[j]:
                                if st.checkbox("Sél.", key=f"v_{img_p}"): selected_photos.append(img_p)
                                try:
                                    st.image(img_p, use_container_width=True)
                                    if st.button("🗑️", key=f"del_{img_p}"):
                                        os.remove(img_p)
                                        st.rerun()
                                except: st.error("ERR")
            else:
                for img_p in sorted_imgs:
                    c1, c2, c3, c4 = st.columns([0.5, 1, 5, 1])
                    with c1:
                        if st.checkbox("", key=f"l_{img_p}"): selected_photos.append(img_p)
                    with c2: st.image(img_p, width=50)
                    with c3: st.text(os.path.basename(img_p))
                    with c4:
                        if st.button("Suppr.", key=f"btn_{img_p}", use_container_width=True):
                            os.remove(img_p)
                            st.rerun()

        # Le bouton de sélection apparaît sur la ligne du haut
        if selected_photos:
            with c_zip_sel:
                st.download_button(f"📥 Sél. ({len(selected_photos)})", data=create_zip(selected_photos), file_name=get_timestamped_name("selection"), use_container_width=True)
    else:
        st.warning("⚠️ Entrez le code secret pour activer la console.")

# --- 5. MODE LIVE & 6. MODE VOTE ---
elif not mode_vote:
    st.markdown("""<style>:root { background-color: #000000 !important; } html, body, [data-testid="stAppViewContainer"], .stApp { background-color: #000000 !important; overflow: hidden !important; height: 100vh !important; width: 100vw !important; margin: 0 !important; padding: 0 !important; } [data-testid="stHeader"], footer, #MainMenu, [data-testid="stDecoration"] { display: none !important; } </style>""", unsafe_allow_html=True)
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=25000, key="wall_refresh")
    except: pass
    img_list = [f for f in glob.glob(os.path.join(GALLERY_DIR, "*")) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
    logo_b64 = None
    if os.path.exists(LOGO_FILE):
        with open(LOGO_FILE, "rb") as f: logo_b64 = base64.b64encode(f.read()).decode()
    photos_html = ""
    for img_path in img_list[-15:]:
        with open(img_path, "rb") as f: b64 = base64.b64encode(f.read()).decode()
        photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:{random.randint(180, 260)}px; height:{random.randint(180, 260)}px; top:{random.randint(10, 70)}%; left:{random.randint(5, 80)}%; animation-duration:{random.uniform(8, 14)}s;">'
    html_code = f"""<!DOCTYPE html><html style="background: black;"><body style="margin: 0; padding: 0; background: black; overflow: hidden; height: 100vh; width: 100vw;"><style> .container {{ position: relative; width: 100vw; height: 100vh; background: black; overflow: hidden; }} .main-title {{ position: absolute; top: 40px; width: 100%; text-align: center; color: white; font-family: sans-serif; font-size: 55px; font-weight: bold; z-index: 1001; text-shadow: 0 0 20px rgba(255,255,255,0.7); }} .center-stack {{ position: absolute; top: 55%; left: 50%; transform: translate(-50%, -50%); z-index: 1000; display: flex; flex-direction: column; align-items: center; gap: 20px; }} .logo {{ max-width: 300px; filter: drop-shadow(0 0 15px white); }} .qr-box {{ background: white; padding: 12px; border-radius: 15px; text-align: center; }} .photo {{ position: absolute; border-radius: 50%; border: 5px solid white; object-fit: cover; animation: move alternate infinite ease-in-out; opacity: 0.95; box-shadow: 0 0 20px rgba(0,0,0,0.5); }} @keyframes move {{ from {{ transform: translate(0,0) rotate(0deg); }} to {{ transform: translate(60px, 80px) rotate(8deg); }} }} </style><div class="container"><div class="main-title">MEILLEURS VŒUX 2026</div><div class="center-stack">{f'<img src="data:image/png;base64,{logo_b64}" class="logo">' if logo_b64 else ''}<div class="qr-box"><img src="data:image/png;base64,{qr_b64}" width="130"></div></div>{photos_html}</div></body></html>"""
    components.html(html_code, height=1000)
else:
    st.title("📸 Envoyez votre photo !")
    f = st.file_uploader("Choisir", type=['jpg', 'jpeg', 'png'])
    if f:
        with open(os.path.join(GALLERY_DIR, f"img_{random.randint(1000,9999)}.jpg"), "wb") as out: out.write(f.getbuffer())
        st.success("✅ Reçu !")
