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

# Liste par défaut
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

config = load_json(CONFIG_FILE, default_config)

# Sécurités
if "candidats" not in config: config["candidats"] = DEFAULT_CANDIDATS
if "candidats_images" not in config: config["candidats_images"] = {}
if "points_ponderation" not in config: config["points_ponderation"] = [5, 3, 1]

BADGE_CSS = "margin-top:20px; background:#E2001A; display:inline-block; padding:10px 30px; border-radius:10px; font-size:22px; font-weight:bold; border:2px solid white; color:white;"

# Fonction optimisée pour le traitement d'image
def process_image_upload(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img.thumbnail((200, 200)) # Optimisation taille
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode()
    except Exception as e:
        st.error(f"Erreur image: {e}")
        return None

# Fonction pour sauvegarder proprement
def save_config():
    json.dump(config, open(CONFIG_FILE, "w"))

# Fonction pour nettoyer le cache des inputs (Fix du bug de doublon)
def clear_input_cache():
    for key in list(st.session_state.keys()):
        if key.startswith("n_"): # On efface la mémoire des champs textes
            del st.session_state[key]

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
        # --- BARRE LATÉRALE ---
        with st.sidebar:
            st.title("🎛️ RÉGIE MASTER")
            st.markdown("---")
            st.subheader("📍 Navigation")
            menu = st.radio(
                "Interface :",
                ["🔴 PILOTAGE LIVE", "⚙️ Paramétrage", "📸 Médiathèque", "📊 Data & Exports"],
                label_visibility="collapsed"
            )
            st.markdown("---")
            
            curr_mode = config["mode_affichage"]
            if curr_mode == "attente": st.info("⏸️ MODE : ATTENTE")
            elif curr_mode == "votes" and config["session_ouverte"]: st.success("🟢 VOTES : OUVERTS")
            elif curr_mode == "votes" and not config["session_ouverte"] and not config["reveal_resultats"]: st.warning("🟠 VOTES : CLOS")
            elif config["reveal_resultats"]: st.error("🏆 MODE : PODIUM")
            
            nb_p = len(load_json(PARTICIPANTS_FILE, []))
            st.metric("👥 Participants", nb_p)
            st.markdown("---")
            if st.button("🔓 Déconnexion", use_container_width=True):
                st.session_state["auth"] = False
                st.rerun()

        # --- CONTENU PRINCIPAL ---
        
        # 1. PILOTAGE LIVE
        if menu == "🔴 PILOTAGE LIVE":
            st.title("🔴 COCKPIT LIVE")
            
            st.subheader("1️⃣ Séquenceur")
            col1, col2, col3, col4 = st.columns(4)
            m, vo, re = config["mode_affichage"], config["session_ouverte"], config["reveal_resultats"]

            with col1:
                if st.button("1. ACCUEIL / ATTENTE", use_container_width=True, type="primary" if m=="attente" else "secondary"):
                    config.update({"mode_affichage": "attente", "session_ouverte": False, "reveal_resultats": False}); save_config(); st.rerun()
            with col2:
                if st.button("2. OUVRIR LES VOTES", use_container_width=True, type="primary" if (m=="votes" and vo) else "secondary"):
                    config.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False}); save_config(); st.rerun()
            with col3:
                if st.button("3. CLÔTURER VOTES", use_container_width=True, type="primary" if (m=="votes" and not vo and not re) else "secondary"):
                    config.update({"session_ouverte": False}); save_config(); st.rerun()
            with col4:
                if st.button("4. RÉVÉLER PODIUM 🏆", use_container_width=True, type="primary" if re else "secondary"):
                    config.update({"mode_affichage": "votes", "reveal_resultats": True, "session_ouverte": False, "timestamp_podium": time.time()}); save_config(); st.rerun()

            st.markdown("---")
            st.subheader("2️⃣ Monitoring des Votes")
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                active_votes = {k: v for k, v in v_data.items() if k in config["candidats"]}
                if active_votes:
                    df = pd.DataFrame(list(active_votes.items()), columns=['Candidat', 'Points']).sort_values('Points', ascending=False)
                    st.bar_chart(df.set_index('Candidat'), color="#E2001A")
                else: st.info("Aucun vote pour les candidats actifs.")
            else: st.info("En attente du premier vote...")

        # 2. PARAMÉTRAGE (CORRECTIF BUG DOUBLON & SUPPRESSION)
        elif menu == "⚙️ Paramétrage":
            st.title("⚙️ Paramétrage de l'événement")
            
            tab_gen, tab_quest = st.tabs(["🎨 Identité Visuelle", "📝 Gestion Candidats & Photos"])

            with tab_gen:
                st.subheader("Textes & Logos")
                new_title = st.text_input("Titre principal du mur", value=config["titre_mur"])
                if new_title != config["titre_mur"]:
                    if st.button("💾 Sauvegarder le Titre"):
                        config["titre_mur"] = new_title; save_config(); st.rerun()
                
                uploaded_logo = st.file_uploader("Changer le Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])
                if uploaded_logo:
                    if st.button("💾 Appliquer ce Logo"):
                        config["logo_b64"] = base64.b64encode(uploaded_logo.read()).decode(); save_config(); st.rerun()

            with tab_quest:
                st.subheader("⚖️ Pondération")
                c_p1, c_p2, c_p3 = st.columns(3)
                p1 = c_p1.number_input("Points 1er", min_value=1, value=config["points_ponderation"][0])
                p2 = c_p2.number_input("Points 2ème", min_value=1, value=config["points_ponderation"][1])
                p3 = c_p3.number_input("Points 3ème", min_value=1, value=config["points_ponderation"][2])
                if st.button("💾 Mettre à jour la pondération"):
                    config["points_ponderation"] = [p1, p2, p3]; save_config(); st.success("OK"); time.sleep(0.5); st.rerun()

                st.markdown("---")
                
                st.subheader("📋 Liste des Questions")
                
                # Ajout
                with st.container():
                    col_add_input, col_add_btn = st.columns([3, 1])
                    new_cand = col_add_input.text_input("Ajouter un candidat", placeholder="Nom du candidat", label_visibility="collapsed")
                    if col_add_btn.button("➕ AJOUTER", use_container_width=True):
                        if new_cand and new_cand not in config["candidats"]:
                            config["candidats"].append(new_cand)
                            save_config()
                            clear_input_cache() # Important pour éviter décalage
                            st.rerun()

                st.markdown("<br>", unsafe_allow_html=True)

                if not config["candidats"]:
                    st.warning("La liste est vide.")
                else:
                    cols_head = st.columns([0.5, 3, 0.5, 0.5, 0.5, 0.5])
                    cols_head[0].markdown("**Img**")
                    cols_head[1].markdown("**Nom (Éditable)**")
                    
                    for i, cand in enumerate(config["candidats"]):
                        cols = st.columns([0.5, 3, 0.5, 0.5, 0.5, 0.5], vertical_alignment="center")
                        
                        # 1. Aperçu Image
                        with cols[0]:
                            if cand in config["candidats_images"]:
                                st.image(BytesIO(base64.b64decode(config["candidats_images"][cand])), width=40)
                            else:
                                st.write("⚪")

                        # 2. Nom (Modifiable)
                        with cols[1]:
                            # Utilisation d'une clé unique pour chaque rendu
                            new_name = st.text_input("Nom", value=cand, key=f"n_{i}", label_visibility="collapsed")
                            if new_name != cand:
                                if st.button("💾", key=f"s_{i}", help="Sauver le nom"):
                                    # Migration image
                                    if cand in config["candidats_images"]:
                                        config["candidats_images"][new_name] = config["candidats_images"].pop(cand)
                                    config["candidats"][i] = new_name
                                    save_config()
                                    clear_input_cache() # FORCE LE CLEAN
                                    st.rerun()

                        # 3. Monter
                        with cols[2]:
                            if st.button("⬆️", key=f"up_{i}"):
                                if i > 0:
                                    config["candidats"][i], config["candidats"][i-1] = config["candidats"][i-1], config["candidats"][i]
                                    save_config()
                                    clear_input_cache() # FORCE LE CLEAN pour éviter doublons
                                    st.rerun()

                        # 4. Descendre
                        with cols[3]:
                            if st.button("⬇️", key=f"dw_{i}"):
                                if i < len(config["candidats"]) - 1:
                                    config["candidats"][i], config["candidats"][i+1] = config["candidats"][i+1], config["candidats"][i]
                                    save_config()
                                    clear_input_cache() # FORCE LE CLEAN pour éviter doublons
                                    st.rerun()

                        # 5. Gestion Photo (Popover)
                        with cols[4]:
                            with st.popover("🖼️", use_container_width=True):
                                st.write(f"Image pour : **{cand}**")
                                upl = st.file_uploader("Fichier", type=["png", "jpg"], key=f"upl_{i}")
                                if upl:
                                    b64 = process_image_upload(upl)
                                    if b64:
                                        config["candidats_images"][cand] = b64
                                        save_config(); st.rerun()
                                
                                if cand in config["candidats_images"]:
                                    if st.button("Supprimer Photo", key=f"rm_img_{i}"):
                                        del config["candidats_images"][cand]
                                        save_config()
                                        st.rerun() # Refresh immédiat

                        # 6. Supprimer Ligne
                        with cols[5]:
                            if st.button("🗑️", key=f"rm_row_{i}"):
                                config["candidats"].pop(i)
                                if cand in config["candidats_images"]: del config["candidats_images"][cand]
                                save_config()
                                clear_input_cache() # FORCE LE CLEAN
                                st.rerun()

        # 3. MÉDIATHÈQUE
        elif menu == "📸 Médiathèque":
            st.title("📸 Gestion des Photos")
            t_adm, t_usr = st.tabs(["Admin", "Utilisateurs"])
            with t_adm:
                for f in glob.glob(f"{ADMIN_DIR}/*"):
                    st.image(f, width=100); 
                    if st.button("🗑️", key=f): os.remove(f); st.rerun()
            with t_usr:
                for f in glob.glob(f"{GALLERY_DIR}/*"):
                    st.image(f, width=100); 
                    if st.button("🗑️", key=f+"u"): os.remove(f); st.rerun()

        # 4. DATA
        elif menu == "📊 Data & Exports":
            st.title("📊 Données & Exports")
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                df = pd.DataFrame(list(v_data.items()), columns=['Candidat', 'Points'])
                st.download_button("📥 CSV Résultats", df.to_csv(index=False).encode('utf-8'), "resultats.csv")
            
            with st.expander("🔴 ZONE DE DANGER"):
                if st.button("RESET COMPLET (Votes + Participants)", type="primary"):
                    if os.path.exists(VOTES_FILE): os.remove(VOTES_FILE)
                    if os.path.exists(PARTICIPANTS_FILE): os.remove(PARTICIPANTS_FILE)
                    st.success("Reset effectué !"); time.sleep(1); st.rerun()

# --- 4. UTILISATEUR ---
elif est_utilisateur:
    st.markdown("<style>.stApp { background-color: black !important; color: white !important; }</style>", unsafe_allow_html=True)
    st.title("🗳️ Vote Transdev")
    if not config["session_ouverte"]:
        st.warning("⌛ Les votes sont clos ou pas encore ouverts.")
    else:
        choix = st.multiselect("Sélectionnez vos 3 favoris (dans l'ordre) :", config["candidats"])
        pts = config.get("points_ponderation", [5, 3, 1])
        st.caption(f"ℹ️ Points : 1er={pts[0]}, 2ème={pts[1]}, 3ème={pts[2]}")

        if len(choix) == 3:
            if st.button("🚀 VALIDER MON VOTE", use_container_width=True, type="primary"):
                vts = load_json(VOTES_FILE, {})
                for v, p in zip(choix, pts): 
                    vts[v] = vts.get(v, 0) + p
                json.dump(vts, open(VOTES_FILE, "w"))
                st.success("✅ Vote enregistré !"); time.sleep(2); st.rerun()
        elif len(choix) > 3: st.error("Maximum 3 choix !")

# --- 5. MUR SOCIAL ---
else:
    st.markdown("""<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'], footer { display: none !important; } .block-container { padding-top: 2rem !important; }</style>""", unsafe_allow_html=True)
    nb_p = len(load_json(PARTICIPANTS_FILE, []))
    logo_img = ""
    if config.get("logo_b64"): logo_img = f'<img src="data:image/png;base64,{config["logo_b64"]}" style="max-height:100px; margin-bottom:15px;">'
    
    st.markdown(f"""
<div style="text-align:center; color:white;">
{logo_img}
<h1 style="font-size:55px; font-weight:bold; text-transform:uppercase; margin:0; line-height:1.1;">{config["titre_mur"]}</h1>
<div style="background:white; display:inline-block; padding:5px 20px; border-radius:20px; color:black; font-weight:bold; margin-top:15px; font-size:18px;">👥 {nb_p} CONNECTÉS</div>
</div>
""", unsafe_allow_html=True)

    if config["mode_affichage"] == "attente":
        st.markdown(f"""<div style="text-align:center; color:white; margin-top:50px;"><div style="{BADGE_CSS}">⌛ En attente du lancement</div><h2 style="font-size:60px; margin-top:40px;">Bienvenue à tous ! 👋</h2></div>""", unsafe_allow_html=True)

    elif config["mode_affichage"] == "votes" and not config["reveal_resultats"]:
        if config["session_ouverte"]:
            host = st.context.headers.get('host', 'localhost')
            qr_url = f"https://{host}/?mode=vote"
            qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            
            st.markdown(f'<div style="text-align:center;"><div style="{BADGE_CSS} animation:blink 1.5s infinite;">🚀 LES VOTES SONT OUVERTS</div></div>', unsafe_allow_html=True)
            st.markdown("<style>@keyframes blink{50%{opacity:0.5;}}</style>", unsafe_allow_html=True)
            
            # --- LISTE DYNAMIQUE AVEC PHOTOS ---
            candidats = config["candidats"]
            mid = (len(candidats) + 1) // 2
            left, right = candidats[:mid], candidats[mid:]

            def get_item_html(label):
                img_html = '<span style="font-size:30px; margin-right:15px;">🎥</span>'
                if label in config.get("candidats_images", {}):
                    b64 = config["candidats_images"][label]
                    img_html = f'<img src="data:image/png;base64,{b64}" style="width:60px; height:60px; object-fit:cover; border-radius:10px; margin-right:15px; border:2px solid #E2001A;"> '
                return f'<div style="background:#222; color:white; padding:10px; margin-bottom:12px; border-left:6px solid #E2001A; font-weight:bold; font-size:22px; display:flex; align-items:center; border-radius:0 10px 10px 0;">{img_html}<span style="flex-grow:1;">{label}</span></div>'

            st.markdown("<div style='margin-top:40px;'>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 0.7, 1])
            with c1:
                for opt in left: st.markdown(get_item_html(opt), unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div style="background:white; padding:15px; border-radius:15px; text-align:center;"><img src="data:image/png;base64,{qr_b64}" width="220"><p style="color:black; font-weight:bold; margin-top:10px; font-size:20px;">SCANNEZ POUR VOTER</p></div>', unsafe_allow_html=True)
            with c3:
                for opt in right: st.markdown(get_item_html(opt), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        else:
            components.html(f"""
<div style="text-align:center; font-family:sans-serif; color:white; background:black; height:100vh; overflow:hidden;">
<div style="{BADGE_CSS} background:#333;">🏁 LES VOTES SONT CLOS</div>
<div style="font-size:120px; animation: clap 0.5s infinite alternate; margin-top:40px;">👏</div>
<h1 style="color:#E2001A; font-size:60px; margin-top:20px;">MERCI À TOUS !</h1>
</div>
<script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
<script>
var end = Date.now() + 7000;
(function frame() {{
confetti({{ particleCount: 4, origin: {{ y: -0.2, x: Math.random() }}, spread: 360, gravity: 0.8, colors: ['#E2001A', '#ffffff'] }});
if (Date.now() < end) requestAnimationFrame(frame);
}}());
</script>
<style> body {{margin:0;}} @keyframes clap {{ from {{ transform: scale(1); }} to {{ transform: scale(1.2); }} }} </style>
""", height=600)

    elif config["reveal_resultats"]:
        temps_ecoule = time.time() - config.get("timestamp_podium", 0)
        compte = 10 - int(temps_ecoule)
        if compte > 0:
            st.markdown(f"""<div style="text-align:center; margin-top:80px;"><h2 style="color:white; opacity:0.8;">RÉSULTATS DANS...</h2><div style="font-size:250px; color:#E2001A; font-weight:bold; animation: pulse 1s infinite;">{compte}</div></div><style>@keyframes pulse {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.1); }} 100% {{ transform: scale(1); }} }}</style>""", unsafe_allow_html=True)
            time.sleep(0.5); st.rerun()
        else:
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                valid = {k: v for k, v in v_data.items() if k in config["candidats"]}
                sorted_v = sorted(valid.items(), key=lambda x: x[1], reverse=True)[:3]
                
                st.markdown(f'<div style="text-align:center;"><div style="{BADGE_CSS}">🏆 LE PODIUM 2026</div><h2 style="color:white; font-style:italic; margin-top:10px;">✨ Félicitations aux grands gagnants ! ✨</h2></div>', unsafe_allow_html=True)
                cols = st.columns(3)
                m_txt, colors = ["🥇 1er", "🥈 2ème", "🥉 3ème"], ["#FFD700", "#C0C0C0", "#CD7F32"]
                for i, (name, score) in enumerate(sorted_v):
                    border_c = colors[i]
                    img_podium = ""
                    if name in config.get("candidats_images", {}):
                         img_podium = f'<img src="data:image/png;base64,{config["candidats_images"][name]}" style="width:120px; height:120px; object-fit:cover; border-radius:50%; border:4px solid {border_c}; margin-bottom:15px; display:block; margin-left:auto; margin-right:auto;">'
                    
                    cols[i].markdown(f"""<div style="background:#1a1a1a; padding:30px 10px; border-radius:20px; border:4px solid {border_c}; text-align:center; color:white; margin-top:30px; box-shadow: 0 0 30px {border_c};"><h2 style="color:{border_c}; font-size:40px; margin:0;">{m_txt[i]}</h2>{img_podium}<h1 style="font-size:30px; margin:15px 0;">{name}</h1><p style="font-size:24px; color:#ccc;">{score} pts</p></div>""", unsafe_allow_html=True)
                components.html('<script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script><script>var end=Date.now()+10000;(function frame(){confetti({particleCount:5,origin:{y:-0.2,x:Math.random()},spread:360,gravity:0.7,colors:["#E2001A","#ffffff","#ffd700"]});if(Date.now()<end)requestAnimationFrame(frame);})();</script>', height=0)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(5000, key="wall_ref")
    except: pass
