import streamlit as st
import pandas as pd
import os
from PIL import Image
from io import BytesIO
import qrcode
import glob
import random
import time
import base64

# --- 1. CONFIGURATION ---
DEFAULT_PASSWORD = "ADMIN_VOEUX_2026"
PASS_FILE = "pass_config.txt"
VOTES_DIR = "sessions_votes"
GALLERY_DIR = "galerie_images"
LOGO_FILE = "logo_entreprise.png"
PRESENCE_FILE = "presence_live.csv" # Pourrait être utilisé pour les noms des participants
MSG_FILE = "live_message.csv"

for d in [VOTES_DIR, GALLERY_DIR]:
    if not os.path.exists(d): os.makedirs(d)

st.set_page_config(page_title="Social Wall Starlight", layout="wide")

# --- 2. FONCTIONS DE GESTION ---
def get_msg():
    if os.path.exists(MSG_FILE): return pd.read_csv(MSG_FILE).iloc[0].to_dict()
    return {"texte": "Bienvenue !", "couleur": "#FF4B4B", "taille": 50, "font": "sans-serif"}

def save_msg(t, c, s, f):
    pd.DataFrame([{"texte": t, "couleur": c, "taille": s, "font": f}]).to_csv(MSG_FILE, index=False)

def img_to_base64(img_path):
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# --- 3. LOGIQUE ADMIN ---
params = st.query_params
est_admin = params.get("admin") == "true"
mode_vote = params.get("mode") == "vote"

if est_admin:
    st.title("🛠️ Régie Social Wall")
    pwd = st.sidebar.text_input("Code Admin", type="password")
    if pwd == (open(PASS_FILE).read().strip() if os.path.exists(PASS_FILE) else DEFAULT_PASSWORD):
        t1, t2 = st.tabs(["✨ Message & Logo", "🖼️ Photos"])
        with t1:
            m = get_msg()
            nt = st.text_area("Texte du message", m["texte"])
            nc = st.color_picker("Couleur", m["couleur"])
            ns = st.slider("Taille (px)", 20, 100, int(m["taille"]))
            nf = st.selectbox("Police", ["sans-serif", "serif", "cursive", "monospace"], index=["sans-serif", "serif", "cursive", "monospace"].index(m["font"]))
            if st.button("Enregistrer Message"): save_msg(nt, nc, ns, nf); st.rerun()
            st.divider()
            if os.path.exists(LOGO_FILE):
                st.image(LOGO_FILE, use_container_width=True)
                if st.button("Supprimer Logo Central", use_container_width=True):
                    os.remove(LOGO_FILE); st.rerun()
            else:
                ul = st.file_uploader("Importer Logo Central", type=['png','jpg'], label_visibility="collapsed")
                if ul: Image.open(ul).save(LOGO_FILE); st.rerun()
        with t2:
            uf = st.file_uploader("Ajouter Photos au flux", type=['png','jpg','jpeg'], accept_multiple_files=True)
            if uf:
                for f in uf: Image.open(f).save(os.path.join(GALLERY_DIR, f.name))
                st.rerun()
            st.divider()
            imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
            if imgs:
                for i, p in enumerate(imgs):
                    col1, col2 = st.columns([0.8, 0.2])
                    col1.image(p, width=100)
                    if col2.button(f"Supprimer {i}", key=i): os.remove(p); st.rerun()
    else:
        st.error("Accès refusé.")

# --- 4. MODE LIVE (ORBITAL STELLAIRE) ---
elif not mode_vote:
    msg = get_msg()
    imgs = glob.glob(os.path.join(GALLERY_DIR, "*"))
    logo_b64 = img_to_base64(LOGO_FILE) if os.path.exists(LOGO_FILE) else ""

    # Génération des étoiles en CSS
    stars = ""
    for _ in range(100): # Nombre d'étoiles
        x = random.randint(0, 100)
        y = random.randint(0, 100)
        size = random.randint(1, 3)
        duration = random.randint(5, 15)
        delay = random.randint(0, 10)
        stars += f"<div style='position:absolute; left:{x}vw; top:{y}vh; width:{size}px; height:{size}px; background:white; border-radius:50%; animation: twinkle {duration}s infinite alternate {delay}s;'></div>"

    st.markdown(f"""
        <style>
        [data-testid="stSidebar"] {{display: none;}}
        .main {{background-color: #050505; overflow: hidden; height: 100vh; position: relative;}}
        
        @keyframes twinkle {{
            0% {{ opacity: 0.5; }}
            50% {{ opacity: 1; }}
            100% {{ opacity: 0.5; }}
        }}
        .stars-background {{
            position: absolute; width: 100%; height: 100%;
            pointer-events: none; z-index: 0;
        }}

        .welcome-msg {{
            position: absolute; top: 50px; width: 100%; text-align: center;
            color: {msg['couleur']}; font-size: {msg['taille']}px; font-family: {msg['font']};
            z-index: 10; text-shadow: 0 0 15px {msg['couleur']};
        }}

        .center-logo {{
            position: absolute; top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            width: 200px; height: 200px; z-index: 5;
            border-radius: 50%; object-fit: contain; background: black;
            box-shadow: 0 0 40px {msg['couleur']}, 0 0 80px rgba(255,255,255,0.2);
            padding: 10px; /* Espace autour du logo */
        }}

        @keyframes orbit {{
            from {{ transform: rotate(0deg) translateX(300px) rotate(0deg); }}
            to {{ transform: rotate(360deg) translateX(300px) rotate(-360deg); }}
        }}

        .photo-orbit {{
            position: absolute; top: 50%; left: 50%;
            transform: translate(-50%, -50%); /* Centrage initial */
            width: 120px; height: 120px;
            border-radius: 50%; border: 3px solid white;
            object-fit: cover;
            box-shadow: 0 0 15px rgba(255,255,255,0.7), 0 0 5px rgba(255,255,255,0.5) inset; /* Effet de traînée */
            animation: orbit var(--duration)s linear infinite;
        }}

        .qr-box {{
            position: fixed; bottom: 20px; right: 20px;
            background: white; padding: 10px; border-radius: 10px; text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.5);
            z-index: 100;
        }}
        </style>
        
        <div class="stars-background">{stars}</div>
        <div class="welcome-msg">{msg['texte']}</div>
        <img src="data:image/png;base64,{logo_b64}" class="center-logo">
    """, unsafe_allow_html=True)

    # Génération des photos en orbite
    if imgs:
        shuffled_imgs = imgs[:]
        random.shuffle(shuffled_imgs) # Mélanger pour un affichage plus dynamique
        
        # Limiter le nombre de photos affichées pour la performance
        num_photos_to_display = min(len(shuffled_imgs), 12) 
        
        for i in range(num_photos_to_display):
            path = shuffled_imgs[i]
            b64 = img_to_base64(path)
            duration = 20 + (i * 3) # Vitesses différentes
            
            # Position de départ sur le cercle (pour éviter qu'elles partent toutes du même point)
            initial_rotation = (i / num_photos_to_display) * 360 
            
            st.markdown(f"""
                <img src="data:image/png;base64,{b64}" class="photo-orbit" 
                style="--duration:{duration}; animation-delay: -{initial_rotation / 360 * duration}s;">
            """, unsafe_allow_html=True)

    # QR CODE COIN DROIT
    qr_url = f"https://{st.context.headers.get('Host', '')}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_img = base64.b64encode(qr_buf.getvalue()).decode()
    st.markdown(f"""
        <div class="qr-box">
            <img src="data:image/png;base64,{qr_img}" width="100"><br>
            <b style="color:black; font-size:10px;">PARTICIPER</b>
        </div>
    """, unsafe_allow_html=True)

    time.sleep(10); st.rerun()

# --- 5. MODE VOTE (MOBILE) ---
else:
    st.title("🗳️ Vote & Présence")
    st.write("Entrez votre pseudo pour apparaître sur le Social Wall.")
    pseudo = st.text_input("Pseudo / Trigramme").strip()
    if pseudo:
        if st.button("🚀 Valider ma présence"):
            df = pd.read_csv(PRESENCE_FILE) if os.path.exists(PRESENCE_FILE) else pd.DataFrame(columns=["Pseudo"])
            if pseudo not in df['Pseudo'].values:
                pd.DataFrame([[pseudo]], columns=["Pseudo"]).to_csv(PRESENCE_FILE, mode='a', header=not os.path.exists(PRESENCE_FILE), index=False)
            st.success("Vous êtes sur le mur !")
            st.balloons()
```http://googleusercontent.com/image_generation_content/5

### Explications des ajouts :

1.  **Arrière-plan Stellaire (`.stars-background`)** :
    * Un conteneur `div` est créé pour accueillir toutes les étoiles.
    * Un script Python génère aléatoirement 100 `div` positionnés absolument (pour simuler des étoiles), avec des tailles, durées et délais d'animation aléatoires.
    * L'animation `@keyframes twinkle` fait varier l'opacité des étoiles, créant un effet de scintillement doux et continu.

2.  **Effet de Traînée (`box-shadow` sur `.photo-orbit`)** :
    * J'ai ajouté un `box-shadow` multiple aux photos en orbite.
    * `0 0 15px rgba(255,255,255,0.7)` crée une lueur blanche diffuse autour de la photo.
    * `0 0 5px rgba(255,255,255,0.5) inset` ajoute un léger halo interne.
    * Cela donne l'impression que la photo est un petit corps lumineux en mouvement dans l'espace.

3.  **Améliorations Générales** :
    * Le `center-logo` a un `padding: 10px;` et un `background: black;` pour mieux le faire ressortir si le logo n'est pas déjà rond ou transparent.
    * Le texte du message d'accueil a maintenant un `text-shadow` pour une meilleure visibilité sur le fond étoilé.
    * J'ai ajusté la logique d'animation pour que les photos démarrent à des positions différentes sur l'orbite, rendant l'effet plus fluide dès le début.



Est-ce que cette fois, l'effet visuel est celui que vous aviez en tête ?
