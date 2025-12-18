import streamlit as st
import pandas as pd
import os
import glob
import random
import base64
import qrcode
from io import BytesIO
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Social Wall", layout="wide", initial_sidebar_state="collapsed")

GALLERY_DIR = "galerie_images"
LOGO_FILE = "logo_entreprise.png"
if not os.path.exists(GALLERY_DIR): os.makedirs(GALLERY_DIR)

# --- 2. LOGIQUE DE NAVIGATION ---
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

# --- 3. INTERFACE ADMIN ---
if est_admin:
    # ON FORCE UN STYLE CLAIR RADICAL POUR L'ADMIN
    st.markdown("""
        <style>
        /* Réinitialisation complète des couleurs pour l'admin */
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            background-color: white !important;
            color: black !important;
        }
        * { color: black !important; }
        .stTextInput input { color: black !important; background-color: #f0f2f6 !important; }
        [data-testid="stHeader"], footer { display: block !important; }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("⚙️ Console d'Administration")
    
    # Sécurité par code
    input_pwd = st.text_input("Code de sécurité", type="password")
    
    if input_pwd == "ADMIN_LIVE_MASTER":
        st.success("Connecté")
        
        col1, col2 = st.columns(2)
        with col1:
            st.header("Logo")
            ul = st.file_uploader("Upload Logo", type=['png', 'jpg', 'jpeg'])
            if ul:
                with open(LOGO_FILE, "wb") as f: f.write(ul.getbuffer())
                st.rerun()
                
        with col2:
            st.header("Photos")
            up = st.file_uploader("Ajouter des photos", accept_multiple_files=True)
            if up:
                for f in up:
                    with open(os.path.join(GALLERY_DIR, f.name), "wb") as file: file.write(f.getbuffer())
                st.rerun()

        st.divider()
        imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
        if st.button("🗑️ VIDER LA GALERIE"):
            for f in imgs: os.remove(f)
            st.rerun()
            
        if imgs:
            st.subheader(f"Galerie ({len(imgs)} photos)")
            cols = st.columns(5)
            for i, img in enumerate(imgs):
                with cols[i % 5]:
                    st.image(img, use_container_width=True)
                    if st.button("Supprimer", key=f"del_{i}"):
                        os.remove(img)
                        st.rerun()
    else:
        st.stop()

# --- 4. MODE LIVE (MUR NOIR) ---
elif not mode_vote:
    # STYLE NOIR UNIQUEMENT POUR LE MUR
    st.markdown("""
        <style>
        :root { background-color: black !important; }
        html, body, [data-testid="stAppViewContainer"], .stApp {
            background-color: black !important;
            overflow: hidden !important;
        }
        [data-testid="stHeader"], footer, #MainMenu { display: none !important; }
        iframe {
            position: fixed !important;
            top: 0; left: 0; width: 100vw !important; height: 100vh !important;
            border: none !important; z-index: 999;
        }
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
            top, left = random.randint(15, 70), random.randint(5, 85)
            duration = random.uniform(7, 13)
            photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:{size}px; height:{size}px; top:{top}%; left:{left}%; animation-duration:{duration}s;">'

    html_code = f"""
    <!DOCTYPE html>
    <html style="background: black;">
    <body style="margin: 0; background: black; overflow: hidden; height: 100vh; width: 100vw; opacity: 0; animation: fadeIn 1.5s forwards;">
        <style>
            @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
            .container {{ position: relative; width: 100vw; height: 100vh; background: black; overflow: hidden; }}
            .main-title {{
                position: absolute; top: 40px; width: 100%; text-align: center;
                color: white; font-family: sans-serif; font-size: 50px; font-weight: bold;
                z-index: 1001; text-shadow: 0 0 20px rgba(255,255,255,0.6);
            }}
            .center-stack {{ 
                position: absolute; top: 55%; left: 50%; transform: translate(-50%, -50%); 
                z-index: 1000; display: flex; flex-direction: column; align-items: center; gap: 20px; 
            }}
            .logo {{ max-width: 260px; filter: drop-shadow(0 0 15px white); }}
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
    st.title("📸 Envoyez votre photo")
    f = st.file_uploader("Image", type=['jpg', 'jpeg', 'png'])
    if f:
        with open(os.path.join(GALLERY_DIR, f"img_{random.randint(1,9999)}.jpg"), "wb") as out:
            out.write(f.getbuffer())
        st.success("Reçu !")
