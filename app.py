import streamlit as st
import pandas as pd
import os
import glob
import random
import base64
import qrcode
import time
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

# --- 3. INTERFACE ADMINISTRATION ---
if est_admin:
    st.markdown("""
        <style>
        html, body, .stApp { background-color: white !important; color: black !important; }
        * { color: black !important; }
        .admin-welcome { text-align: center; margin-top: 60px; font-family: sans-serif; }
        [data-testid="stSidebar"] { min-width: 350px !important; }
        [data-testid="stSidebar"] [data-testid="stImage"] { display: flex; justify-content: center; margin: 0 !important; padding: 0 !important; }
        [data-testid="stSidebar"] [data-testid="stImage"] img { width: 100% !important; height: auto !important; }
        [data-testid="stHeader"] { display: block !important; }
        </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        # --- LOGO ACTUEL ---
        if os.path.exists(LOGO_FILE):
            try:
                st.image(LOGO_FILE, use_container_width=True)
                if st.button("🗑️ Supprimer le logo actuel"):
                    os.remove(LOGO_FILE)
                    st.rerun()
            except:
                st.error("Logo corrompu. Veuillez le supprimer.")
                if st.button("Forcer la suppression"):
                    os.remove(LOGO_FILE)
                    st.rerun()
        
        st.title("⚙️ Régie Social Wall")
        pwd = st.text_input("Code Secret Admin", type="password")
        st.divider()

        if pwd == "ADMIN_LIVE_MASTER":
            st.success("✅ Accès autorisé")
            
            url_mur = f"https://{st.context.headers.get('host', 'localhost')}/"
            st.link_button("🖥️ OUVRIR LE MUR (PLEIN ÉCRAN)", url_mur)
            st.divider()
            
            # --- GESTION DU LOGO (CORRIGÉE) ---
            st.subheader("🖼️ Gestion du Logo")
            ul = st.file_uploader("Charger un logo", type=['png', 'jpg', 'jpeg'], key="logo_up")
            if ul is not None:
                try:
                    with open(LOGO_FILE, "wb") as f:
                        f.write(ul.getbuffer())
                    st.toast("Logo enregistré !")
                    time.sleep(0.5) # Pause de sécurité
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur d'écriture : {e}")

            st.divider()
            
            # Gestion des Photos
            st.subheader("📸 Ajouter des photos")
            up = st.file_uploader("Images", accept_multiple_files=True, key="ph_up")
            if up:
                for f in up:
                    try:
                        with open(os.path.join(GALLERY_DIR, f.name), "wb") as file:
                            file.write(f.getbuffer())
                    except: pass
                st.rerun()
            
            st.divider()
            imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
            if st.button("🗑️ VIDER LA GALERIE"):
                for f in imgs: os.remove(f)
                st.rerun()

            if imgs:
                st.subheader(f"Galerie ({len(imgs)})")
                for i, img_path in enumerate(imgs):
                    st.image(img_path, use_container_width=True)
                    if st.button(f"Supprimer {i}", key=f"del_{i}"):
                        os.remove(img_path)
                        st.rerun()
        else:
            st.warning("Entrez le code pour voir les outils.")

    st.markdown('<div class="admin-welcome">', unsafe_allow_html=True)
    st.title("Bienvenue dans votre console d'administration")
    if pwd == "ADMIN_LIVE_MASTER":
        st.success("Système opérationnel")
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=200)
    else: st.error("🔒 Accès restreint")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 4. MODE LIVE (MUR NOIR) ---
elif not mode_vote:
    st.markdown("""
        <style>
        :root { background-color: #000000 !important; }
        html, body, [data-testid="stAppViewContainer"], .stApp { background-color: #000000 !important; overflow: hidden !important; height: 100vh !important; width: 100vw !important; margin: 0 !important; padding: 0 !important; }
        [data-testid="stHeader"], footer, #MainMenu, [data-testid="stDecoration"] { display: none !important; }
        iframe { position: fixed !important; top: 0 !important; left: 0 !important; width: 100vw !important; height: 100vh !important; border: none !important; background-color: #000000 !important; z-index: 9999; }
        </style>
    """, unsafe_allow_html=True)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=25000, key="wall_refresh")
    except: pass

    def get_b64(path):
        if os.path.exists(path) and os.path.getsize(path) > 0:
            try:
                with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
            except: return None
        return None

    logo_b64 = get_b64(LOGO_FILE)
    img_list = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO()
    qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    photos_html = ""
    for img_path in img_list[-15:]:
        b64 = get_b64(img_path)
        if b64:
            size = random.randint(160, 240)
            top, left = random.randint(10, 70), random.randint(5, 85)
            duration = random.uniform(7, 13)
            photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:{size}px; height:{size}px; top:{top}%; left:{left}%; animation-duration:{duration}s;">'

    html_code = f"""
    <!DOCTYPE html>
    <html style="background: black;">
    <body style="margin: 0; padding: 0; background: black; overflow: hidden; height: 100vh; width: 100vw; opacity: 0; animation: fadeIn 1.5s forwards;">
        <style>
            @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
            .container {{ position: relative; width: 100vw; height: 100vh; background: black; overflow: hidden; }}
            .main-title {{ position: absolute; top: 30px; width: 100%; text-align: center; color: white; font-family: sans-serif; font-size: 55px; font-weight: bold; z-index: 1001; text-shadow: 0 0 20px rgba(255,255,255,0.7); }}
            .center-stack {{ position: absolute; top: 55%; left: 50%; transform: translate(-50%, -50%); z-index: 1000; display: flex; flex-direction: column; align-items: center; gap: 20px; }}
            .logo {{ max-width: 280px; filter: drop-shadow(0 0 15px white); }}
            .qr-box {{ background: white; padding: 12px; border-radius: 15px; text-align: center; }}
            .photo {{ position: absolute; border-radius: 50%; border: 4px solid white; object-fit: cover; animation: move alternate infinite ease-in-out; opacity: 0.9; }}
            @keyframes move {{ from {{ transform: translate(0,0) rotate(0deg); }} to {{ transform: translate(70px, 90px) rotate(10deg); }} }}
        </style>
        <div class="container">
            <div class="main-title">MEILLEURS VŒUX 2026</div>
            <div class="center-stack">
                {f'<img src="data:image/png;base64,{logo_b64}" class="logo">' if logo_b64 else ''}
                <div class="qr-box">
                    <img src="data:image/png;base64,{qr_b64}" width="120">
                </div>
            </div>
            {photos_html}
        </div>
    </body>
    </html>
    """
    components.html(html_code)

# --- 5. MODE VOTE ---
else:
    st.markdown("<style>html, body, .stApp { background-color: #111 !important; color: white !important; }</style>", unsafe_allow_html=True)
    st.title("📸 Partagez votre photo !")
    f = st.file_uploader("Prendre une photo", type=['jpg', 'jpeg', 'png'])
    if f:
        with open(os.path.join(GALLERY_DIR, f"img_{random.randint(1000,9999)}.jpg"), "wb") as out:
            out.write(f.getbuffer())
        st.success("✅ C'est en ligne !")
