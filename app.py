import streamlit as st
import os
import glob
import base64
import qrcode
import json
import random
from io import BytesIO
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Social Wall Pro", layout="wide")

GALLERY_DIR = "galerie_images"
ADMIN_DIR = "galerie_admin"
LOGO_FILE = "logo_entreprise.png"
VOTES_FILE = "votes.json"
PARTICIPANTS_FILE = "participants.json"
CONFIG_FILE = "config_mur.json"

for d in [GALLERY_DIR, ADMIN_DIR]:
    if not os.path.exists(d): os.makedirs(d)

config = {"mode_affichage": "attente", "titre_mur": "CONCOURS VIDÉO 2026", "vote_version": 1}
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f: config = json.load(f)

VOTE_VERSION = config.get("vote_version", 1)

if not os.path.exists(VOTES_FILE):
    with open(VOTES_FILE, "w") as f: json.dump({}, f)
if not os.path.exists(PARTICIPANTS_FILE):
    with open(PARTICIPANTS_FILE, "w") as f: json.dump([], f)

# --- 2. NAVIGATION ---
query_params = st.query_params
est_admin = query_params.get("admin") == "true"
est_utilisateur = query_params.get("mode") == "vote"

# --- 3. ADMIN (CONSOLE AVEC FILTRE PHOTOS) ---
if est_admin:
    st.markdown("""
        <style>
        div[data-testid="stSidebar"] button[kind="primary"] { background-color: #0000FF !important; color: white !important; border: 2px solid #0000FF; }
        div[data-testid="stSidebar"] button[kind="secondary"] { background-color: #FF0000 !important; color: white !important; border: 2px solid #FF0000; }
        </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE)
        if st.text_input("Code Admin", type="password") == "ADMIN_LIVE_MASTER":
            st.session_state["auth"] = True
            
        if st.session_state.get("auth"):
            st.subheader("🎮 Contrôle du Mur")
            nouveau_titre = st.text_input("Sous-titre :", value=config.get("titre_mur"))
            new_mode = st.radio("Mode Mur :", ["Attente (Photos Admin uniquement)", "Live (Tout afficher)", "Votes"], 
                                index=0 if config["mode_affichage"]=="attente" else (1 if config["mode_affichage"]=="live" else 2))
            
            mode_key = "attente" if "Attente" in new_mode else ("live" if "Live" in new_mode else "votes")

            if st.button("🔵 VALIDER : MISE À JOUR MUR", type="primary", use_container_width=True):
                with open(CONFIG_FILE, "w") as f: 
                    json.dump({"mode_affichage": mode_key, "titre_mur": nouveau_titre, "vote_version": VOTE_VERSION}, f)
                st.rerun()
            
            st.divider()
            if st.button("🔴 RESET : RÉINITIALISER LES VOTES", type="secondary", use_container_width=True):
                with open(CONFIG_FILE, "w") as f: 
                    json.dump({"mode_affichage": "attente", "titre_mur": nouveau_titre, "vote_version": VOTE_VERSION + 1}, f)
                with open(VOTES_FILE, "w") as f: json.dump({}, f)
                with open(PARTICIPANTS_FILE, "w") as f: json.dump([], f)
                st.rerun()

    if st.session_state.get("auth"):
        c1, c2 = st.columns([2, 1])
        c1.title("Console de Régie")
        if os.path.exists(LOGO_FILE): c2.image(LOGO_FILE, width=250)
        
        t1, t2 = st.tabs(["📸 Photos Admin (Équipes)", "📱 Photos Utilisateurs"])
        with t1:
            up = st.file_uploader("Ajouter photos officielles", accept_multiple_files=True)
            if up:
                for f in up:
                    with open(os.path.join(ADMIN_DIR, f.name), "wb") as out: out.write(f.getbuffer())
                st.rerun()
            imgs = glob.glob(os.path.join(ADMIN_DIR, "*"))
            for i in range(0, len(imgs), 8):
                cols = st.columns(8)
                for j in range(8):
                    if i+j < len(imgs):
                        cols[j].image(imgs[i+j], use_container_width=True)
                        if cols[j].button("🗑️", key=f"ad_{i+j}"): os.remove(imgs[i+j]); st.rerun()
        with t2:
            u_imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
            st.write(f"Nombre de photos utilisateurs : {len(u_imgs)}")
            if st.button("Supprimer toutes les photos utilisateurs"):
                for f in u_imgs: os.remove(f)
                st.rerun()

# --- 4. UTILISATEUR (VOTE TOP 3) ---
elif est_utilisateur:
    st.title("🗳️ Vote Transdev")
    vote_key = f"transdev_v{VOTE_VERSION}"
    components.html(f"<script>if(localStorage.getItem('{vote_key}')){{window.parent.postMessage({{type:'voted'}},'*');}}</script>", height=0)
    
    if st.session_state.get("voted"):
        st.success("✅ Vote déjà enregistré sur cet appareil.")
    else:
        pseudo = st.text_input("Pseudo / Prénom :")
        options = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]
        choix = st.multiselect("Sélectionnez votre Top 3 :", options, max_selections=3)
        if st.button("Confirmer le vote"):
            if pseudo and (0 < len(choix) <= 3):
                with open(PARTICIPANTS_FILE, "r") as f: parts = json.load(f)
                if pseudo not in parts:
                    parts.append(pseudo); 
                    with open(PARTICIPANTS_FILE, "w") as f: json.dump(parts, f)
                vts = json.load(open(VOTES_FILE))
                for c in choix: vts[c] = vts.get(c, 0) + 1
                with open(VOTES_FILE, "w") as f: json.dump(vts, f)
                components.html(f"<script>localStorage.setItem('{vote_key}', 'true'); setTimeout(()=>{{window.parent.location.reload();}},500);</script>", height=0)
                st.session_state["voted"] = True
            else: st.error("Saisissez votre pseudo et 1 à 3 choix.")

# --- 5. MUR LIVE (LOGIQUE DE FILTRE ET AFFICHAGE) ---
else:
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'] { display: none; } footer {display:none;}</style>", unsafe_allow_html=True)
    
    with open(PARTICIPANTS_FILE, "r") as f: nb = len(json.load(f))
    
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    st.markdown(f"<div style='text-align:center; padding-top:20px;'><p style='color:#E2001A; font-size:30px; font-weight:bold; margin:0;'>MUR PHOTO LIVE</p><h1 style='color:white; font-size:55px; margin-top:0;'>{config.get('titre_mur')}</h1></div>", unsafe_allow_html=True)

    if config["mode_affichage"] == "votes":
        v_data = json.load(open(VOTES_FILE))
        if any(v > 0 for v in v_data.values()):
            st.bar_chart(v_data)
            st.markdown(f"<div style='position:fixed; bottom:30px; right:30px; background:white; padding:10px; border-radius:15px; border:4px solid #E2001A; text-align:center;'><img src='data:image/png;base64,{qr_b64}' width='110'><p style='margin:10px 0 0 0; color:black; font-weight:bold; font-size:16px;'>{nb} PARTICIPANTS</p></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align:center; margin-top:50px;'><div style='display:inline-block; background:white; padding:40px; border-radius:30px; border:8px solid #E2001A;'><img src='data:image/png;base64,{qr_b64}' width='320'><p style='margin-top:20px; font-weight:bold; font-size:30px; color:black;'>{nb} PARTICIPANTS</p><p style='color:#E2001A; font-weight:bold; font-size:20px;'>SCANNEZ POUR VOTER</p></div></div>", unsafe_allow_html=True)
    else:
        # Filtrage des photos
        if config["mode_affichage"] == "attente":
            img_list = glob.glob(os.path.join(ADMIN_DIR, "*"))
        else:
            img_list = glob.glob(os.path.join(ADMIN_DIR, "*")) + glob.glob(os.path.join(GALLERY_DIR, "*"))
        
        photos_html = ""
        for p in img_list[-12:]:
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                photos_html += f'<img src="data:image/png;base64,{b64}" class="photo" style="width:280px; top:{random.randint(20,65)}%; left:{random.randint(5,80)}%; animation-duration:{random.uniform(10,15)}s;">'
        
        html_content = f"""<style>.photo {{ position:absolute; border:6px solid white; border-radius:15px; animation:move alternate infinite ease-in-out; box-shadow: 10px 10px 20px rgba(0,0,0,0.5); }} @keyframes move {{ from {{ transform:rotate(-3deg); }} to {{ transform:translate(40px,40px) rotate(3deg); }} }}</style><div style="width:100%; height:550px; position:relative;">{photos_html}</div><div style="position:fixed; bottom:40px; left:50%; transform:translateX(-50%); background:white; padding:15px; border-radius:20px; border:5px solid #E2001A; text-align:center; z-index:1000;"><img src="data:image/png;base64,{qr_b64}" width="160"><p style="margin:5px 0 0 0; font-weight:bold; font-size:20px; color:black;">{nb} PARTICIPANTS</p></div>"""
        components.html(html_content, height=800)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=15000, key="global_refresh")
    except: pass
