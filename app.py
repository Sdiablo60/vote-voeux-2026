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
        
        /* En-tête admin épuré */
        .admin-header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            padding: 20px; 
            border-bottom: 2px solid #f0f2f6; 
            margin-bottom: 30px; 
        }
        
        /* Logo flottant à droite */
        .logo-top-right {
            max-width: 150px;
            max-height: 80px;
            object-fit: contain;
        }

        [data-testid="stSidebar"] { min-width: 350px !important; }
        [data-testid="stHeader"] { display: block !important; }
        </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        # Logo en haut de sidebar (toujours présent)
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, use_container_width=True)
        
        st.title("⚙️ Configuration")
        pwd = st.text_input("Code Secret Admin", type="password")
        st.divider()

        if pwd == "ADMIN_LIVE_MASTER":
            st.success("Accès autorisé")
            
            # --- SECTION UPLOADS ---
            st.subheader("📤 Imports")
            ul = st.file_uploader("Nouveau Logo", type=['png', 'jpg', 'jpeg'], key="logo_up")
            if ul:
                with open(LOGO_FILE, "wb") as f: f.write(ul.getbuffer())
                st.rerun()
                
            up = st.file_uploader("Nouvelles Photos", accept_multiple_files=True, key="ph_up")
            if up:
                for f in up:
                    with open(os.path.join(GALLERY_DIR, f.name), "wb") as file: file.write(f.getbuffer())
                st.rerun()
            
            st.divider()
            if st.button("🧨 VIDER TOUTE LA GALERIE", use_container_width=True):
                imgs_to_del = glob.glob(os.path.join(GALLERY_DIR, "*"))
                for f in imgs_to_del: os.remove(f)
                st.rerun()
        else:
            st.warning("Identifiez-vous à gauche.")

    # --- ÉCRAN CENTRAL ---
    if pwd == "ADMIN_LIVE_MASTER":
        # HEADER AVEC TITRE À GAUCHE ET LOGO À DROITE
        logo_html = ""
        if os.path.exists(LOGO_FILE):
            # Encodage b64 pour l'injecter dans le HTML personnalisé
            with open(LOGO_FILE, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            logo_html = f'<img src="data:image/png;base64,{data}" class="logo-top-right">'
        
        st.markdown(f"""
            <div class="admin-header">
                <div style="text-align: left;">
                    <h1 style="margin:0;">Console d'Administration</h1>
                    <p style="margin:0; opacity: 0.7;">Gestion de la galerie en temps réel</p>
                </div>
                <div>
                    {logo_html}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # BOUTON D'ACCÈS AU MUR (Centralisé et visible)
        url_mur = f"https://{st.context.headers.get('host', 'localhost')}/"
        st.link_button("🖥️ OUVRIR LE MUR EN PLEIN ÉCRAN", url_mur, type="primary", use_container_width=True)

        st.divider()

        # GALERIE DE MODÉRATION
        imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
        st.header(f"🖼️ Modération des Photos ({len(imgs)})")
        
        if not imgs:
            st.info("La galerie est vide. Ajoutez des photos via le menu de gauche.")
        else:
            # Affichage en grille de 4 colonnes
            cols = st.columns(4)
            for i, img_path in enumerate(reversed(imgs)):
                with cols[i % 4]:
                    st.image(img_path, use_container_width=True)
                    if st.button(f"Supprimer #{len(imgs)-i}", key=f"del_{i}"):
                        os.remove(img_path)
                        st.rerun()
    else:
        st.markdown('<div style="text-align:center; margin-top:100px;"><h1>🔒 Accès Réservé</h1><p>Veuillez entrer le mot de passe dans la barre latérale.</p></div>', unsafe_allow_html=True)

# --- 4. MODE LIVE (MUR NOIR) ---
elif not mode_vote:
    # (Le code du mur reste identique pour garantir la stabilité)
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
            size = random.randint(180, 260)
            top, left = random.randint(10, 70), random.randint(5, 80)
            duration = random.uniform(8, 14)
            photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:{size}px; height:{size}px; top:{top}%; left:{left}%; animation-duration:{duration}s;">'
    html_code = f"""
    <!DOCTYPE html>
    <html style="background: black;">
    <body style="margin: 0; padding: 0; background: black; overflow: hidden; height: 100vh; width: 100vw; opacity: 0; animation: fadeIn 1.5s forwards;">
        <style>
            @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
            .container {{ position: relative; width: 100vw; height: 100vh; background: black; overflow: hidden; }}
            .main-title {{ position: absolute; top: 40px; width: 100%; text-align: center; color: white; font-family: sans-serif; font-size: 55px; font-weight: bold; z-index: 1001; text-shadow: 0 0 20px rgba(255,255,255,0.7); }}
            .center-stack {{ position: absolute; top: 55%; left: 50%; transform: translate(-50%, -50%); z-index: 1000; display: flex; flex-direction: column; align-items: center; gap: 20px; }}
            .logo {{ max-width: 300px; filter: drop-shadow(0 0 15px white); }}
            .qr-box {{ background: white; padding: 12px; border-radius: 15px; text-align: center; }}
            .photo {{ position: absolute; border-radius: 50%; border: 5px solid white; object-fit: cover; animation: move alternate infinite ease-in-out; opacity: 0.95; box-shadow: 0 0 20px rgba(0,0,0,0.5); }}
            @keyframes move {{ from {{ transform: translate(0,0) rotate(0deg); }} to {{ transform: translate(60px, 80px) rotate(8deg); }} }}
        </style>
        <div class="container">
            <div class="main-title">MEILLEURS VŒUX 2026</div>
            <div class="center-stack">
                {f'<img src="data:image/png;base64,{logo_b64}" class="logo">' if logo_b64 else ''}
                <div class="qr-box">
                    <img src="data:image/png;base64,{qr_b64}" width="130">
                    <p style="color:black; font-size:12px; font-weight:bold; margin-top:5px; font-family:sans-serif;">SCANNEZ POUR PARTICIPER</p>
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
    f = st.file_uploader("Choisir une image", type=['jpg', 'jpeg', 'png'])
    if f:
        with open(os.path.join(GALLERY_DIR, f"img_{random.randint(1000,9999)}.jpg"), "wb") as out:
            out.write(f.getbuffer())
        st.success("✅ C'est envoyé !")
