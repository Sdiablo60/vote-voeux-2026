import streamlit as st
import os
import glob
import base64
import qrcode
import time
import zipfile
import datetime
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

# --- 3. FONCTIONS UTILES ---
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
    st.markdown("""
        <style>
        html, body, .stApp { background-color: white !important; color: black !important; }
        * { color: black !important; }
        .admin-header { display: flex; justify-content: space-between; align-items: center; padding: 10px 20px; border-bottom: 1px solid #eee; margin-bottom: 20px; }
        .logo-top-right { max-width: 100px; max-height: 50px; object-fit: contain; }
        [data-testid="stSidebar"] { min-width: 300px !important; }
        [data-testid="column"] { min-width: 0px !important; flex-basis: 0 !important; flex-grow: 1 !important; }
        div[data-testid="stHorizontalBlock"] { align-items: center; }
        </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, use_container_width=True)
        st.title("⚙️ Régie")
        pwd = st.text_input("Code Secret Admin", type="password")
        if pwd == "ADMIN_LIVE_MASTER":
            if st.button("🧨 VIDER TOUTE LA GALERIE", use_container_width=True):
                for f in glob.glob(os.path.join(GALLERY_DIR, "*")): os.remove(f)
                st.rerun()

    if pwd == "ADMIN_LIVE_MASTER":
        # LOGO HAUT DROITE
        logo_html = ""
        if os.path.exists(LOGO_FILE):
            with open(LOGO_FILE, "rb") as f: data = base64.b64encode(f.read()).decode()
            logo_html = f'<img src="data:image/png;base64,{data}" class="logo-top-right">'
        
        st.markdown(f'<div class="admin-header"><div><h2 style="margin:0;">Console Régie</h2></div><div>{logo_html}</div></div>', unsafe_allow_html=True)
        st.link_button("🖥️ PROJETER LE MUR", f"https://{st.context.headers.get('host', 'localhost')}/", use_container_width=True)

        # --- IMPORT MANUEL : CORRECTION DÉFINITIVE ---
        with st.expander("➕ Ajouter des photos manuellement", expanded=False):
            up = st.file_uploader("Importer", accept_multiple_files=True, key="upload_manual")
            if up:
                for f in up:
                    with open(os.path.join(GALLERY_DIR, f.name), "wb") as file:
                        file.write(f.getbuffer())
                # On vide le cache session pour forcer la relecture
                st.success("Photos enregistrées !")
                time.sleep(0.5)
                st.rerun()

        st.divider()

        # RELECTURE FORCÉE DU DOSSIER
        all_files = [f for f in glob.glob(os.path.join(GALLERY_DIR, "*")) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        sorted_imgs = sorted(all_files, key=os.path.getmtime, reverse=True)
        
        # LIGNE DE CONTRÔLE
        c_titre, c_zip_all, c_zip_sel, c_vue = st.columns([1.5, 1, 1, 1])
        with c_titre: st.subheader(f"🖼️ Modération ({len(all_files)})")
        with c_zip_all:
            if all_files:
                st.download_button(label="📥 Tout (ZIP)", data=create_zip(all_files), file_name=get_timestamped_name("galerie_complete"), mime="application/zip", use_container_width=True)
        with c_vue: mode_vue = st.radio("Vue", ["Vignettes", "Liste"], horizontal=True, label_visibility="collapsed")

        # AFFICHAGE GALERIE
        selected_photos = []
        if not all_files:
            st.info("Dossier vide. Importez des photos pour les voir apparaître.")
        else:
            if mode_vue == "Vignettes":
                for i in range(0, len(sorted_imgs), 8):
                    cols = st.columns(8)
                    for j in range(8):
                        idx = i + j
                        if idx < len(sorted_imgs):
                            img_p = sorted_imgs[idx]
                            with cols[j]:
                                if st.checkbox("Sél.", key=f"check_{img_p}_{idx}"): 
                                    selected_photos.append(img_p)
                                st.image(img_p, use_container_width=True)
                                if st.button("🗑️", key=f"btn_{img_p}_{idx}"):
                                    os.remove(img_p)
                                    st.rerun()
            else:
                for i in range(0, len(sorted_imgs), 4):
                    cols = st.columns(4)
                    for j in range(4):
                        idx = i + j
                        if idx < len(sorted_imgs):
                            img_p = sorted_imgs[idx]
                            with cols[j]:
                                c1, c2, c3 = st.columns([1, 1, 3])
                                with c1:
                                    if st.checkbox("", key=f"chk_lst_{img_p}_{idx}"): selected_photos.append(img_p)
                                with c2: st.image(img_p, width=35)
                                with c3:
                                    if st.button("Suppr.", key=f"del_lst_{img_p}_{idx}", use_container_width=True):
                                        os.remove(img_p)
                                        st.rerun()

        if selected_photos:
            with c_zip_sel:
                st.download_button(label=f"📥 Sélection ({len(selected_photos)})", data=create_zip(selected_photos), file_name=get_timestamped_name("selection"), mime="application/zip", use_container_width=True, type="primary")
    else:
        st.markdown('<div style="text-align:center; margin-top:100px;"><h1>🔒 Accès Réservé</h1></div>', unsafe_allow_html=True)

# --- 5. MODE LIVE & 6. MODE VOTE (Inchangés) ---
elif not mode_vote:
    st.markdown("""<style>:root { background-color: #000000 !important; } html, body, [data-testid="stAppViewContainer"], .stApp { background-color: #000000 !important; overflow: hidden !important; height: 100vh !important; width: 100vw !important; margin: 0 !important; padding: 0 !important; } [data-testid="stHeader"], footer, #MainMenu, [data-testid="stDecoration"] { display: none !important; } iframe { position: fixed !important; top: 0 !important; left: 0 !important; width: 100vw !important; height: 100vh !important; border: none !important; background-color: #000000 !important; z-index: 9999; }</style>""", unsafe_allow_html=True)
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
    html_code = f"""<!DOCTYPE html><html style="background: black;"><body style="margin: 0; padding: 0; background: black; overflow: hidden; height: 100vh; width: 100vw; opacity: 0; animation: fadeIn 1.5s forwards;"><style>@keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }} .container {{ position: relative; width: 100vw; height: 100vh; background: black; overflow: hidden; }} .main-title {{ position: absolute; top: 40px; width: 100%; text-align: center; color: white; font-family: sans-serif; font-size: 55px; font-weight: bold; z-index: 1001; text-shadow: 0 0 20px rgba(255,255,255,0.7); }} .center-stack {{ position: absolute; top: 55%; left: 50%; transform: translate(-50%, -50%); z-index: 1000; display: flex; flex-direction: column; align-items: center; gap: 20px; }} .logo {{ max-width: 300px; filter: drop-shadow(0 0 15px white); }} .qr-box {{ background: white; padding: 12px; border-radius: 15px; text-align: center; }} .photo {{ position: absolute; border-radius: 50%; border: 5px solid white; object-fit: cover; animation: move alternate infinite ease-in-out; opacity: 0.95; box-shadow: 0 0 20px rgba(0,0,0,0.5); }} @keyframes move {{ from {{ transform: translate(0,0) rotate(0deg); }} to {{ transform: translate(60px, 80px) rotate(8deg); }} }} </style><div class="container"><div class="main-title">MEILLEURS VŒUX 2026</div><div class="center-stack">{f'<img src="data:image/png;base64,{logo_b64}" class="logo">' if logo_b64 else ''}<div class="qr-box"><img src="data:image/png;base64,{qr_b64}" width="130"></div></div>{photos_html}</div></body></html>"""
    components.html(html_code)
else:
    st.title("📸 Envoyez votre photo !")
    f = st.file_uploader("Choisir", type=['jpg', 'jpeg', 'png'])
    if f:
        with open(os.path.join(GALLERY_DIR, f"img_{random.randint(1000,9999)}.jpg"), "wb") as out: out.write(f.getbuffer())
        st.success("✅ Reçu !")
