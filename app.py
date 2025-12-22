import streamlit as st
import os, glob, base64, qrcode, json, random, pandas as pd
from io import BytesIO
import streamlit.components.v1 as components
import time
from PIL import Image

# --- 1. CONFIGURATION & FICHIERS ---
st.set_page_config(page_title="Régie Master - Pôle Aéroportuaire", layout="wide")

GALLERY_DIR, ADMIN_DIR = "galerie_images", "galerie_admin"
VOTES_FILE, PARTICIPANTS_FILE, CONFIG_FILE = "votes.json", "participants.json", "config_mur.json"

for d in [GALLERY_DIR, ADMIN_DIR]:
    if not os.path.exists(d): os.makedirs(d)

DEFAULT_CANDIDATS = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]

default_config = {
    "mode_affichage": "attente", 
    "titre_mur": "CONCOURS VIDÉO PÔLE AEROPORTUAIRE", 
    "session_ouverte": False, 
    "reveal_resultats": False,
    "timestamp_podium": 0,
    "logo_b64": None,
    "candidats": DEFAULT_CANDIDATS,
    "candidats_images": {}, 
    "points_ponderation": [5, 3, 1]
}

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r") as f: return json.load(f)
        except: return default
    return default

# Chargement initial
if "config" not in st.session_state:
    st.session_state.config = load_json(CONFIG_FILE, default_config)

# Sécurités
if "candidats" not in st.session_state.config: st.session_state.config["candidats"] = DEFAULT_CANDIDATS
if "candidats_images" not in st.session_state.config: st.session_state.config["candidats_images"] = {}
if "points_ponderation" not in st.session_state.config: st.session_state.config["points_ponderation"] = [5, 3, 1]

BADGE_CSS = "margin-top:20px; background:#E2001A; display:inline-block; padding:10px 30px; border-radius:10px; font-size:22px; font-weight:bold; border:2px solid white; color:white;"

# --- FONCTIONS UTILITAIRES (CALLBACKS) ---

def save_config():
    """Sauvegarde l'état actuel dans le fichier JSON"""
    with open(CONFIG_FILE, "w") as f:
        json.dump(st.session_state.config, f)

def force_clear_cache():
    """Force l'oubli des valeurs des champs textes pour éviter les doublons visuels"""
    keys_to_clear = [k for k in st.session_state.keys() if k.startswith("input_name_")]
    for k in keys_to_clear:
        del st.session_state[k]

def action_monter(idx):
    """Callback pour monter un élément"""
    c_list = st.session_state.config["candidats"]
    if idx > 0:
        # Echange dans la liste
        c_list[idx], c_list[idx-1] = c_list[idx-1], c_list[idx]
        save_config()
        force_clear_cache() # IMPORTANT : On vide le cache visuel

def action_descendre(idx):
    """Callback pour descendre un élément"""
    c_list = st.session_state.config["candidats"]
    if idx < len(c_list) - 1:
        c_list[idx], c_list[idx+1] = c_list[idx+1], c_list[idx]
        save_config()
        force_clear_cache() # IMPORTANT

def action_supprimer(idx):
    """Callback pour supprimer un élément"""
    nom = st.session_state.config["candidats"][idx]
    if nom in st.session_state.config["candidats_images"]:
        del st.session_state.config["candidats_images"][nom]
    st.session_state.config["candidats"].pop(idx)
    save_config()
    force_clear_cache() # IMPORTANT

def action_renommer(idx, old_name):
    """Callback quand le texte change"""
    key = f"input_name_{idx}"
    # Vérification que la clé existe (sécurité)
    if key in st.session_state:
        new_name = st.session_state[key]
        if new_name != old_name:
            if old_name in st.session_state.config["candidats_images"]:
                st.session_state.config["candidats_images"][new_name] = st.session_state.config["candidats_images"].pop(old_name)
            
            st.session_state.config["candidats"][idx] = new_name
            save_config()
            st.toast(f"✅ Renommé en : {new_name}")

def action_ajouter():
    """Callback ajout"""
    new_val = st.session_state.new_cand_input
    if new_val and new_val not in st.session_state.config["candidats"]:
        st.session_state.config["candidats"].append(new_val)
        save_config()
        st.session_state.new_cand_input = ""
        force_clear_cache()

def process_image_upload(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img.thumbnail((200, 200))
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode()
    except Exception as e: return None

# --- 2. NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"

# --- 3. ADMINISTRATION ---
if est_admin:
    if "auth" not in st.session_state: st.session_state["auth"] = False
    
    if not st.session_state["auth"]:
        st.markdown("<br><br><h1 style='text-align:center;'>🔐 ACCÈS RÉGIE</h1>", unsafe_allow_html=True)
        col_c, col_p, col_d = st.columns([1,2,1])
        with col_p:
            pwd = st.text_input("Mot de passe", type="password")
            if pwd == "ADMIN_LIVE_MASTER":
                st.session_state["auth"] = True
                st.rerun()
    else:
        with st.sidebar:
            st.title("🎛️ RÉGIE MASTER")
            st.markdown("---")
            menu = st.radio("Navigation :", ["🔴 PILOTAGE LIVE", "⚙️ Paramétrage", "📸 Médiathèque", "📊 Data & Exports"], label_visibility="collapsed")
            st.markdown("---")
            if st.button("🔓 Déconnexion", use_container_width=True):
                st.session_state["auth"] = False
                st.rerun()

        # --- CONTENU ---
        if menu == "🔴 PILOTAGE LIVE":
            st.title("🔴 COCKPIT LIVE")
            st.subheader("1️⃣ Séquenceur")
            c1, c2, c3, c4 = st.columns(4)
            cfg = st.session_state.config
            m, vo, re = cfg["mode_affichage"], cfg["session_ouverte"], cfg["reveal_resultats"]

            if c1.button("1. ACCUEIL", use_container_width=True, type="primary" if m=="attente" else "secondary"):
                cfg.update({"mode_affichage": "attente", "session_ouverte": False, "reveal_resultats": False}); save_config(); st.rerun()
            if c2.button("2. VOTES ON", use_container_width=True, type="primary" if (m=="votes" and vo) else "secondary"):
                cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False}); save_config(); st.rerun()
            if c3.button("3. VOTES OFF", use_container_width=True, type="primary" if (m=="votes" and not vo and not re) else "secondary"):
                cfg.update({"session_ouverte": False}); save_config(); st.rerun()
            if c4.button("4. PODIUM", use_container_width=True, type="primary" if re else "secondary"):
                cfg.update({"mode_affichage": "votes", "reveal_resultats": True, "session_ouverte": False, "timestamp_podium": time.time()}); save_config(); st.rerun()

            st.markdown("---")
            st.subheader("2️⃣ Monitoring")
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                valid = {k:v for k,v in v_data.items() if k in cfg["candidats"]}
                if valid:
                    df = pd.DataFrame(list(valid.items()), columns=['Candidat', 'Points']).sort_values('Points', ascending=False)
                    st.bar_chart(df.set_index('Candidat'), color="#E2001A")
                else: st.info("Aucun vote actif.")
            else: st.info("En attente de votes...")

        elif menu == "⚙️ Paramétrage":
            st.title("⚙️ Paramétrage")
            t1, t2 = st.tabs(["Identité", "Gestion Questions"])
            
            with t1:
                new_t = st.text_input("Titre", value=st.session_state.config["titre_mur"])
                if st.button("Sauver Titre"):
                    st.session_state.config["titre_mur"] = new_t; save_config(); st.success("OK")
                
                up_l = st.file_uploader("Logo", type=["png", "jpg"])
                if up_l:
                    b64 = process_image_upload(up_l)
                    if b64:
                        st.session_state.config["logo_b64"] = b64; save_config(); st.success("Logo OK"); st.rerun()

            with t2:
                # Ajout
                c_add1, c_add2 = st.columns([3, 1])
                c_add1.text_input("Nouveau candidat", key="new_cand_input", label_visibility="collapsed", placeholder="Nom...")
                c_add2.button("➕ Ajouter", on_click=action_ajouter, use_container_width=True)
                
                st.markdown("---")
                
                if not st.session_state.config["candidats"]:
                    st.warning("Liste vide.")
                else:
                    # En-tête
                    cols = st.columns([0.5, 3, 0.5, 0.5, 0.5, 0.5])
                    cols[0].markdown("**Img**")
                    cols[1].markdown("**Nom (Éditable)**")
                    
                    # BOUCLE SUR LA LISTE
                    for i, cand in enumerate(st.session_state.config["candidats"]):
                        cols = st.columns([0.5, 3, 0.5, 0.5, 0.5, 0.5], vertical_alignment="center")
                        
                        # 1. Image
                        with cols[0]:
                            if cand in st.session_state.config["candidats_images"]:
                                st.image(BytesIO(base64.b64decode(st.session_state.config["candidats_images"][cand])), width=40)
                            else: st.write("⚪")
                        
                        # 2. Input Nom (CALLBACK)
                        with cols[1]:
                            st.text_input(
                                "Nom", 
                                value=cand, 
                                key=f"input_name_{i}", 
                                label_visibility="collapsed",
                                on_change=action_renommer,
                                args=(i, cand)
                            )
                        
                        # 3. Monter (CALLBACK + CLEAR CACHE)
                        with cols[2]:
                            if i > 0:
                                st.button("⬆️", key=f"u{i}", on_click=action_monter, args=(i,))
                        
                        # 4. Descendre (CALLBACK + CLEAR CACHE)
                        with cols[3]:
                            if i < len(st.session_state.config["candidats"]) - 1:
                                st.button("⬇️", key=f"d{i}", on_click=action_descendre, args=(i,))

                        # 5. Photo Popover
                        with cols[4]:
                            with st.popover("🖼️"):
                                st.write(cand)
                                up_p = st.file_uploader("Img", type=["png", "jpg"], key=f"up_{i}")
                                if up_p:
                                    b64 = process_image_upload(up_p)
                                    if b64:
                                        st.session_state.config["candidats_images"][cand] = b64
                                        save_config()
                                        st.rerun()
                                if st.button("Suppr Photo", key=f"di_{i}"):
                                    if cand in st.session_state.config["candidats_images"]:
                                        del st.session_state.config["candidats_images"][cand]
                                        save_config()
                                        st.rerun()

                        # 6. Supprimer Ligne (CALLBACK + CLEAR CACHE)
                        with cols[5]:
                            st.button("🗑️", key=f"del{i}", on_click=action_supprimer, args=(i,))

        elif menu == "📸 Médiathèque":
            st.write("Gestion fichiers...")
            t1, t2 = st.tabs(["Admin", "User"])
            with t1:
                for f in glob.glob(f"{ADMIN_DIR}/*"):
                     st.image(f, width=100); 
                     if st.button("X", key=f): os.remove(f); st.rerun()
            with t2:
                for f in glob.glob(f"{GALLERY_DIR}/*"):
                     st.image(f, width=100); 
                     if st.button("X", key=f+"u"): os.remove(f); st.rerun()

        elif menu == "📊 Data & Exports":
            if st.button("RESET TOUT"):
                 if os.path.exists(VOTES_FILE): os.remove(VOTES_FILE)
                 st.success("Reset!"); st.rerun()

# --- 4. UTILISATEUR ---
elif est_utilisateur:
    st.markdown("<style>.stApp { background-color: black !important; color: white !important; }</style>", unsafe_allow_html=True)
    st.title("🗳️ Vote")
    cfg = load_json(CONFIG_FILE, default_config)
    if not cfg["session_ouverte"]: st.warning("Clos.")
    else:
        choix = st.multiselect("Top 3 :", cfg["candidats"])
        if len(choix) == 3 and st.button("VALIDER"):
            vts = load_json(VOTES_FILE, {})
            pts = cfg.get("points_ponderation", [5, 3, 1])
            for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
            json.dump(vts, open(VOTES_FILE, "w")); st.success("OK"); time.sleep(1); st.rerun()

# --- 5. MUR SOCIAL ---
else:
    st.markdown("""<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'], footer { display: none !important; } .block-container { padding-top: 2rem !important; }</style>""", unsafe_allow_html=True)
    
    # Rechargement config à chaque refresh
    config = load_json(CONFIG_FILE, default_config)
    nb_p = len(load_json(PARTICIPANTS_FILE, []))
    
    logo_html = ""
    if config.get("logo_b64"): logo_html = f'<img src="data:image/png;base64,{config["logo_b64"]}" style="max-height:100px; margin-bottom:15px;">'

    st.markdown(f"""
    <div style="text-align:center; color:white;">
    {logo_html}
    <h1 style="font-size:55px; font-weight:bold; text-transform:uppercase; margin:0; line-height:1.1;">{config["titre_mur"]}</h1>
    <div style="background:white; display:inline-block; padding:5px 20px; border-radius:20px; color:black; font-weight:bold; margin-top:15px; font-size:18px;">👥 {nb_p} CONNECTÉS</div>
    </div>
    """, unsafe_allow_html=True)

    if config["mode_affichage"] == "attente":
        st.markdown(f"""<div style="text-align:center; color:white; margin-top:50px;"><div style="{BADGE_CSS}">⌛ En attente</div><h2 style="font-size:60px; margin-top:40px;">Bienvenue ! 👋</h2></div>""", unsafe_allow_html=True)

    elif config["mode_affichage"] == "votes" and not config["reveal_resultats"]:
        if config["session_ouverte"]:
            host = st.context.headers.get('host', 'localhost')
            qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            
            st.markdown(f'<div style="text-align:center;"><div style="{BADGE_CSS} animation:blink 1.5s infinite;">🚀 VOTES OUVERTS</div></div><style>@keyframes blink{{50%{{opacity:0.5;}}}}</style>', unsafe_allow_html=True)
            
            # Affichage dynamique
            cands = config["candidats"]
            mid = (len(cands) + 1) // 2
            
            def get_html(lbl):
                img = '<span style="font-size:30px; margin-right:15px;">🎥</span>'
                if lbl in config.get("candidats_images", {}):
                    b64 = config["candidats_images"][lbl]
                    img = f'<img src="data:image/png;base64,{b64}" style="width:60px; height:60px; object-fit:cover; border-radius:10px; margin-right:15px; border:2px solid #E2001A;">'
                return f'<div style="background:#222; color:white; padding:10px; margin-bottom:12px; border-left:6px solid #E2001A; font-weight:bold; font-size:22px; display:flex; align-items:center;">{img}{lbl}</div>'

            st.markdown("<div style='margin-top:40px;'>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 0.7, 1])
            with c1:
                for c in cands[:mid]: st.markdown(get_html(c), unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div style="background:white; padding:15px; border-radius:15px; text-align:center;"><img src="data:image/png;base64,{qr_b64}" width="220"><p style="color:black; font-weight:bold;">SCANNEZ</p></div>', unsafe_allow_html=True)
            with c3:
                for c in cands[mid:]: st.markdown(get_html(c), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        else:
            components.html(f"""<div style="text-align:center;color:white;background:black;height:100vh;"><div style="{BADGE_CSS} background:#333;">🏁 CLOS</div><div style="font-size:100px;margin-top:40px;">👏</div><h1 style="color:#E2001A;">MERCI !</h1></div>""", height=600)

    elif config["reveal_resultats"]:
        diff = 10 - int(time.time() - config.get("timestamp_podium", 0))
        if diff > 0:
            st.markdown(f"""<div style="text-align:center; margin-top:80px;"><div style="font-size:250px; color:#E2001A; font-weight:bold;">{diff}</div></div>""", unsafe_allow_html=True)
            time.sleep(0.5); st.rerun()
        else:
            v_data = load_json(VOTES_FILE, {})
            valid = {k:v for k,v in v_data.items() if k in config["candidats"]}
            sorted_v = sorted(valid.items(), key=lambda x: x[1], reverse=True)[:3]
            st.markdown(f'<div style="text-align:center;"><div style="{BADGE_CSS}">🏆 PODIUM</div></div>', unsafe_allow_html=True)
            cols = st.columns(3)
            ranks = ["🥇", "🥈", "🥉"]
            colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
            for i, (name, score) in enumerate(sorted_v):
                img_p = ""
                if name in config.get("candidats_images", {}):
                     img_p = f'<img src="data:image/png;base64,{config["candidats_images"][name]}" style="width:120px; height:120px; border-radius:50%; border:4px solid {colors[i]}; display:block; margin:0 auto 15px auto;">'
                cols[i].markdown(f"""<div style="background:#1a1a1a; padding:30px; border:4px solid {colors[i]}; text-align:center; color:white; margin-top:30px; border-radius:20px;"><h2>{ranks[i]}</h2>{img_p}<h1>{name}</h1><p>{score} pts</p></div>""", unsafe_allow_html=True)
            components.html('<script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script><script>confetti({particleCount:100,spread:70,origin:{y:0.6}});</script>', height=0)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(5000, key="wall_ref")
    except: pass
