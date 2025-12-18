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
        .admin-header { display: flex; justify-content: space-between; align-items: center; padding: 10px 20px; border-bottom: 1px solid #eee; margin-bottom: 20px; }
        .logo-top-right { max-width: 100px; max-height: 50px; object-fit: contain; }
        [data-testid="stSidebar"] { min-width: 300px !important; }
        
        /* Force les colonnes à ne pas s'empiler sur une seule ligne (Responsive OFF) */
        [data-testid="column"] {
            min-width: 0px !important;
            flex-basis: 0 !important;
            flex-grow: 1 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, use_container_width=True)
        st.title("⚙️ Régie")
        pwd = st.text_input("Code Secret Admin", type="password")
        st.divider()

        if pwd == "ADMIN_LIVE_MASTER":
            st.success("Admin connecté")
            st.subheader("🖼️ Logo")
            ul_sidebar = st.file_uploader("Changer le logo", type=['png', 'jpg', 'jpeg'], key="logo_side")
            if ul_sidebar:
                with open(LOGO_FILE, "wb") as f: f.write(ul_sidebar.getbuffer())
                st.rerun()
            if st.button("🧨 VIDER LA GALERIE", use_container_width=True):
                for f in glob.glob(os.path.join(GALLERY_DIR, "*")): os.remove(f)
                st.rerun()
        else:
            st.warning("Identification requise.")

    if pwd == "ADMIN_LIVE_MASTER":
        # HEADER
        logo_html = ""
        if os.path.exists(LOGO_FILE):
            with open(LOGO_FILE, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            logo_html = f'<img src="data:image/png;base64,{data}" class="logo-top-right">'
        
        st.markdown(f'<div class="admin-header"><div><h2 style="margin:0;">Console Régie</h2></div><div>{logo_html}</div></div>', unsafe_allow_html=True)
        
        st.link_button("🖥️ PROJETER LE MUR", f"https://{st.context.headers.get('host', 'localhost')}/", use_container_width=True)

        with st.expander("➕ Ajouter des photos manuellement"):
            up_center = st.file_uploader("Fichiers", accept_multiple_files=True, key="ph_center")
            if up_center:
                for f in up_center:
                    with open(os.path.join(GALLERY_DIR, f.name), "wb") as file: file.write(f.getbuffer())
                st.rerun()

        st.divider()

        # --- GESTION DE LA GALERIE ---
        imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
        col_t, col_s = st.columns([2, 1])
        with col_t:
            st.subheader(f"🖼️ Modération ({len(imgs)} photos)")
        with col_s:
            mode_vue = st.radio("Affichage :", ["Vignettes", "Liste"], horizontal=True, label_visibility="collapsed")

        if not imgs:
            st.info("Aucune photo.")
        else:
            sorted_imgs = sorted(imgs, key=os.path.getmtime, reverse=True)

            # --- MODE VIGNETTES (FORCE 8 COLONNES) ---
            if mode_vue == "Vignettes":
                # On utilise une boucle pour créer des rangées de 8
                for i in range(0, len(sorted_imgs), 8):
                    cols = st.columns(8)
                    for j in range(8):
                        if i + j < len(sorted_imgs):
                            img_p = sorted_imgs[i + j]
                            with cols[j]:
                                st.image(img_p, use_container_width=True)
                                if st.button("🗑️", key=f"vign_{i+j}"):
                                    os.remove(img_p)
                                    st.rerun()

            # --- MODE LISTE (FORCE 4 COLONNES) ---
            else:
                for i in range(0, len(sorted_imgs), 4):
                    cols = st.columns(4)
                    for j in range(4):
                        if i + j < len(sorted_imgs):
                            img_p = sorted_imgs[i + j]
                            with cols[j]:
                                # Mini ligne compacte
                                c1, c2 = st.columns([1, 3])
                                with c1: st.image(img_p, width=40)
                                with c2:
                                    if st.button(f"Suppr. {len(sorted_imgs)-(i+j)}", key=f"list_{i+j}", use_container_width=True):
                                        os.remove(img_p)
                                        st.rerun()
    else:
        st.markdown('<div style="text-align:center; margin-top:100px;"><h1>🔒 Accès Réservé</h1></div>', unsafe_allow_html=True)

# --- 4. MODE LIVE (MUR NOIR) ---
elif not mode_vote:
    st.markdown("""<style>:root { background-color: #000000 !important; } html, body, [data-testid="stAppViewContainer"], .stApp { background-color: #000000 !important; overflow: hidden !important; height: 100vh !important; width: 100vw !important; margin: 0 !important; padding: 0 !important; } [data-testid="stHeader"], footer, #MainMenu, [data-testid="stDecoration"] { display: none !important; } iframe { position: fixed !important; top: 0 !important; left: 0 !important; width: 100vw !important; height: 100vh !important; border: none !important; background-color: #000000 !important; z-index: 9999; }</style>""", unsafe_allow_html=True)
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
            size, top, left = random.randint(180, 260), random.randint(10, 70), random.randint(5, 80)
            photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:{size}px; height:{size}px; top:{top}%; left:{left}%; animation-duration:{random.uniform(8, 14)}s;">'
    html_code = f"""<!DOCTYPE html><html style="background: black;"><body style="margin: 0; padding: 0; background: black; overflow: hidden; height: 100vh; width: 100vw; opacity: 0; animation: fadeIn 1.5s forwards;"><style>@keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }} .container {{ position: relative; width: 100vw; height: 100vh; background: black; overflow: hidden; }} .main-title {{ position: absolute; top: 40px; width: 100%; text-align: center; color: white; font-family: sans-serif; font-size: 55px; font-weight: bold; z-index: 1001; text-shadow: 0 0 20px rgba(255,255,255,0.7); }} .center-stack {{ position: absolute; top: 55%; left: 50%; transform: translate(-50%, -50%); z-index: 1000; display: flex; flex-direction: column; align-items: center; gap: 20px; }} .logo {{ max-width: 300px; filter: drop-shadow(0 0 15px white); }} .qr-box {{ background: white; padding: 12px; border-radius: 15px; text-align: center; }} .photo {{ position: absolute; border-radius: 50%; border: 5px solid white; object-fit: cover; animation: move alternate infinite ease-in-out; opacity: 0.95; box-shadow: 0 0 20px rgba(0,0,0,0.5); }} @keyframes move {{ from {{ transform: translate(0,0) rotate(0deg); }} to {{ transform: translate(60px, 80px) rotate(8deg); }} }} </style><div class="container"><div class="main-title">MEILLEURS VŒUX 2026</div><div class="center-stack">{f'<img src="data:image/png;base64,{logo_b64}" class="logo">' if logo_b64 else ''}<div class="qr-box"><img src="data:image/png;base64,{qr_b64}" width="130"></div></div>{photos_html}</div></body></html>"""
    components.html(html_code)

# --- 5. MODE VOTE ---
else:
    st.title("📸 Envoyez votre photo !")
    f = st.file_uploader("Choisir", type=['jpg', 'jpeg', 'png'])
    if f:
        with open(os.path.join(GALLERY_DIR, f"img_{random.randint(1000,9999)}.jpg"), "wb") as out: out.write(f.getbuffer())
        st.success("✅ Reçu !")
