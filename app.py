import streamlit as st
import os, glob, base64, qrcode, json, random, pandas as pd
import altair as alt  # NOUVEAU : Import pour le graphique personnalisé
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

# --- GESTION ÉTAT SESSION ---
if "config" not in st.session_state:
    st.session_state.config = load_json(CONFIG_FILE, default_config)

if "refresh_id" not in st.session_state:
    st.session_state.refresh_id = 0

# Sécurités
if "candidats" not in st.session_state.config: st.session_state.config["candidats"] = DEFAULT_CANDIDATS
if "candidats_images" not in st.session_state.config: st.session_state.config["candidats_images"] = {}
if "points_ponderation" not in st.session_state.config: st.session_state.config["points_ponderation"] = [5, 3, 1]

BADGE_CSS = "margin-top:20px; background:#E2001A; display:inline-block; padding:10px 30px; border-radius:10px; font-size:22px; font-weight:bold; border:2px solid white; color:white;"

# --- FONCTIONS CRITIQUES ---

def force_refresh():
    st.session_state.refresh_id += 1
    save_config()

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(st.session_state.config, f)

def process_image_upload(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img.thumbnail((200, 200))
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode()
    except: return None

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
                cfg.update({"mode_affichage": "attente", "session_ouverte": False, "reveal_resultats": False}); force_refresh(); st.rerun()
            if c2.button("2. VOTES ON", use_container_width=True, type="primary" if (m=="votes" and vo) else "secondary"):
                cfg.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False}); force_refresh(); st.rerun()
            if c3.button("3. VOTES OFF", use_container_width=True, type="primary" if (m=="votes" and not vo and not re) else "secondary"):
                cfg.update({"session_ouverte": False}); force_refresh(); st.rerun()
            if c4.button("4. PODIUM", use_container_width=True, type="primary" if re else "secondary"):
                cfg.update({"mode_affichage": "votes", "reveal_resultats": True, "session_ouverte": False, "timestamp_podium": time.time()}); force_refresh(); st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("🗑️ OPTIONS DE RÉINITIALISATION (Zone de danger)"):
                col_rst, col_info = st.columns([1, 2])
                with col_rst:
                    if st.button("♻️ VIDER LES VOTES", use_container_width=True, help="Remet les scores et les participants à 0"):
                        if os.path.exists(VOTES_FILE): os.remove(VOTES_FILE)
                        if os.path.exists(PARTICIPANTS_FILE): os.remove(PARTICIPANTS_FILE)
                        st.toast("✅ Session entièrement réinitialisée !")
                        time.sleep(1); st.rerun()
                with col_info:
                    st.info("Efface les scores ET le compteur de participants.")

            st.markdown("---")
            st.subheader("2️⃣ Monitoring des Résultats")
            
            # --- VISUALISATION GRAPHIQUE AMÉLIORÉE ---
            v_data = load_json(VOTES_FILE, {})
            all_cands = st.session_state.config["candidats"]
            
            # Construction des données complètes (même ceux à 0)
            full_data = {c: v_data.get(c, 0) for c in all_cands}
            
            if full_data:
                # Création DataFrame
                df = pd.DataFrame(list(full_data.items()), columns=['Candidat', 'Points'])
                df = df.sort_values('Points', ascending=False).reset_index(drop=True)
                df['Rang'] = df.index + 1
                
                # Définition des couleurs : Or, Argent, Bronze, puis Rouge Transdev pour les autres
                def get_color(rank):
                    if rank == 1: return '#FFD700' # Or
                    if rank == 2: return '#C0C0C0' # Argent
                    if rank == 3: return '#CD7F32' # Bronze
                    return '#E2001A' # Rouge
                
                df['Color'] = df['Rang'].apply(get_color)

                # Graphique Altair personnalisé (Fixe, propre, avec labels)
                base = alt.Chart(df).encode(
                    x=alt.X('Points', axis=None), # Pas d'axe X
                    y=alt.Y('Candidat', sort='-x', axis=alt.Axis(labelFontSize=14, title=None)) # Noms plus gros
                )

                bars = base.mark_bar().encode(
                    color=alt.Color('Color', scale=None), # Utilise la colonne couleur définie plus haut
                    tooltip=['Candidat', 'Points', 'Rang']
                )

                text = base.mark_text(
                    align='left',
                    baseline='middle',
                    dx=3,  # Décalage du texte
                    fontSize=14,
                    fontWeight='bold'
                ).encode(
                    text='Points'
                )

                chart = (bars + text).properties(height=500).configure_view(strokeWidth=0)
                
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("En attente de votes...")

        elif menu == "⚙️ Paramétrage":
            st.title("⚙️ Paramétrage")
            t1, t2 = st.tabs(["Identité", "Gestion Questions"])
            
            with t1:
                new_t = st.text_input("Titre", value=st.session_state.config["titre_mur"], key=f"titre_{st.session_state.refresh_id}")
                if new_t != st.session_state.config["titre_mur"]:
                    if st.button("Sauver Titre"):
                        st.session_state.config["titre_mur"] = new_t; force_refresh(); st.rerun()
                
                up_l = st.file_uploader("Logo", type=["png", "jpg"])
                if up_l:
                    b64 = process_image_upload(up_l)
                    if b64:
                        st.session_state.config["logo_b64"] = b64; force_refresh(); st.success("Logo OK"); st.rerun()

            with t2:
                c_add1, c_add2 = st.columns([3, 1])
                new_cand = c_add1.text_input("Nouveau candidat", key=f"new_cand_{st.session_state.refresh_id}", label_visibility="collapsed", placeholder="Nom...")
                if c_add2.button("➕ Ajouter", use_container_width=True):
                    if new_cand and new_cand not in st.session_state.config["candidats"]:
                        st.session_state.config["candidats"].append(new_cand)
                        force_refresh(); st.rerun()
                
                st.markdown("---")
                
                if not st.session_state.config["candidats"]:
                    st.warning("Liste vide.")
                else:
                    cols_head = st.columns([0.5, 3, 0.5, 0.5, 0.5, 0.5])
                    cols_head[0].markdown("**Img**")
                    cols_head[1].markdown("**Nom (Éditable)**")
                    
                    rid = st.session_state.refresh_id
                    
                    for i, cand in enumerate(st.session_state.config["candidats"]):
                        cols = st.columns([0.5, 3, 0.5, 0.5, 0.5, 0.5], vertical_alignment="center")
                        
                        with cols[0]:
                            if cand in st.session_state.config["candidats_images"]:
                                st.image(BytesIO(base64.b64decode(st.session_state.config["candidats_images"][cand])), width=40)
                            else: st.write("⚪")
                        
                        with cols[1]:
                            val_edit = st.text_input("Nom", value=cand, key=f"n_{i}_{rid}", label_visibility="collapsed")
                            if val_edit != cand:
                                if cand in st.session_state.config["candidats_images"]:
                                    st.session_state.config["candidats_images"][val_edit] = st.session_state.config["candidats_images"].pop(cand)
                                st.session_state.config["candidats"][i] = val_edit
                                force_refresh(); st.rerun()
                        
                        with cols[2]:
                            if i > 0:
                                if st.button("⬆️", key=f"u_{i}_{rid}"):
                                    st.session_state.config["candidats"][i], st.session_state.config["candidats"][i-1] = st.session_state.config["candidats"][i-1], st.session_state.config["candidats"][i]
                                    force_refresh(); st.rerun()
                        
                        with cols[3]:
                            if i < len(st.session_state.config["candidats"]) - 1:
                                if st.button("⬇️", key=f"d_{i}_{rid}"):
                                    st.session_state.config["candidats"][i], st.session_state.config["candidats"][i+1] = st.session_state.config["candidats"][i+1], st.session_state.config["candidats"][i]
                                    force_refresh(); st.rerun()

                        with cols[4]:
                            with st.popover("🖼️"):
                                st.write(f"**{cand}**")
                                up_p = st.file_uploader("Fichier", type=["png", "jpg"], key=f"up_{i}_{rid}")
                                if up_p:
                                    b64 = process_image_upload(up_p)
                                    if b64:
                                        st.session_state.config["candidats_images"][cand] = b64
                                        force_refresh(); st.rerun()
                                
                                if cand in st.session_state.config["candidats_images"]:
                                    if st.button("Supprimer Photo", key=f"di_{i}_{rid}"):
                                        del st.session_state.config["candidats_images"][cand]
                                        force_refresh(); st.rerun()

                        with cols[5]:
                            if st.button("🗑️", key=f"del_{i}_{rid}"):
                                st.session_state.config["candidats"].pop(i)
                                if cand in st.session_state.config["candidats_images"]: del st.session_state.config["candidats_images"][cand]
                                force_refresh(); st.rerun()

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
                 if os.path.exists(PARTICIPANTS_FILE): os.remove(PARTICIPANTS_FILE)
                 st.success("Reset!"); st.rerun()

# --- 4. UTILISATEUR ---
elif est_utilisateur:
    st.markdown("<style>.stApp { background-color: black !important; color: white !important; }</style>", unsafe_allow_html=True)
    
    cfg = load_json(CONFIG_FILE, default_config)
    
    # LOGO SUR MOBILE
    if cfg.get("logo_b64"):
        st.markdown(f"""
        <div style="text-align:center; margin-bottom:20px;">
            <img src="data:image/png;base64,{cfg["logo_b64"]}" style="max-height:80px; width:auto;">
        </div>
        """, unsafe_allow_html=True)
    
    st.title("🗳️ Vote Transdev")
    
    # Enregistrement Participant
    if "participant_recorded" not in st.session_state:
        parts = load_json(PARTICIPANTS_FILE, [])
        parts.append(time.time())
        with open(PARTICIPANTS_FILE, "w") as f: json.dump(parts, f)
        st.session_state["participant_recorded"] = True

    if st.session_state.get("a_vote", False):
        st.balloons()
        st.markdown("""
        <div style="text-align:center; padding-top:50px;">
            <div style="font-size:80px;">👏</div>
            <h1 style="color:#E2001A;">MERCI !</h1>
            <p style="font-size:20px;">Votre vote a bien été pris en compte.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Modifier mon vote"):
             st.session_state["a_vote"] = False
             st.rerun()
    
    elif not cfg["session_ouverte"]: 
        st.warning("⌛ Les votes sont clos ou pas encore ouverts.")
    else:
        choix = st.multiselect("Sélectionnez vos 3 favoris (dans l'ordre) :", cfg["candidats"])
        pts = cfg.get("points_ponderation", [5, 3, 1])
        st.caption(f"ℹ️ Points : 1er={pts[0]}, 2ème={pts[1]}, 3ème={pts[2]}")

        if len(choix) == 3:
            if st.button("🚀 VALIDER MON VOTE", use_container_width=True, type="primary"):
                vts = load_json(VOTES_FILE, {})
                for v, p in zip(choix, pts): vts[v] = vts.get(v, 0) + p
                json.dump(vts, open(VOTES_FILE, "w"))
                
                st.session_state["a_vote"] = True
                st.rerun()
        elif len(choix) > 3: st.error("Maximum 3 choix !")

# --- 5. MUR SOCIAL ---
else:
    st.markdown("""<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'], footer { display: none !important; } .block-container { padding-top: 2rem !important; }</style>""", unsafe_allow_html=True)
    
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
                st.markdown(f'<div style="background:white; padding:4px; border-radius:10px; text-align:center; margin: 0 auto; width: fit-content;"><img src="data:image/png;base64,{qr_b64}" width="180" style="display:block;"><p style="color:black; font-weight:bold; margin-top:5px; margin-bottom:0; font-size:14px;">SCANNEZ</p></div>', unsafe_allow_html=True)
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
