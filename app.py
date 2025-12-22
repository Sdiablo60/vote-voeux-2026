import streamlit as st
import os, glob, base64, qrcode, json, random, pandas as pd
from io import BytesIO
import streamlit.components.v1 as components
import time

# --- 1. CONFIGURATION & FICHIERS ---
st.set_page_config(page_title="Régie Master - Pôle Aéroportuaire", layout="wide")

GALLERY_DIR, ADMIN_DIR = "galerie_images", "galerie_admin"
VOTES_FILE, PARTICIPANTS_FILE, CONFIG_FILE = "votes.json", "participants.json", "config_mur.json"

for d in [GALLERY_DIR, ADMIN_DIR]:
    if not os.path.exists(d): os.makedirs(d)

default_config = {
    "mode_affichage": "attente", 
    "titre_mur": "CONCOURS VIDÉO PÔLE AEROPORTUAIRE", 
    "session_ouverte": False, 
    "reveal_resultats": False,
    "timestamp_podium": 0,
    "logo_b64": None
}

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r") as f: return json.load(f)
        except: return default
    return default

config = load_json(CONFIG_FILE, default_config)
OPTS_BU = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]
BADGE_CSS = "margin-top:20px; background:#E2001A; display:inline-block; padding:10px 30px; border-radius:10px; font-size:22px; font-weight:bold; border:2px solid white; color:white;"

# --- 2. NAVIGATION ---
est_admin = st.query_params.get("admin") == "true"
est_utilisateur = st.query_params.get("mode") == "vote"

# --- 3. ADMINISTRATION ---
if est_admin:
    # Authentification
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
        # --- BARRE LATÉRALE PROFESSIONNELLE ---
        with st.sidebar:
            st.title("🎛️ RÉGIE MASTER")
            st.markdown("---")
            
            # 1. MENU DE NAVIGATION
            st.subheader("📍 Navigation")
            menu = st.radio(
                "Choisir l'interface :",
                ["🔴 PILOTAGE LIVE", "⚙️ Paramétrage", "📸 Médiathèque", "📊 Data & Exports"],
                label_visibility="collapsed"
            )
            
            st.markdown("---")

            # 2. MONITORING ÉTAT ACTUEL (Toujours visible)
            st.subheader("📺 État Actuel du Mur")
            curr_mode = config["mode_affichage"]
            if curr_mode == "attente":
                st.info("⏸️ MODE : ATTENTE")
            elif curr_mode == "votes" and config["session_ouverte"]:
                st.success("🟢 VOTES : OUVERTS")
            elif curr_mode == "votes" and not config["session_ouverte"] and not config["reveal_resultats"]:
                st.warning("🟠 VOTES : CLOS")
            elif config["reveal_resultats"]:
                st.error("🏆 MODE : PODIUM")
            
            nb_p = len(load_json(PARTICIPANTS_FILE, []))
            st.metric("👥 Participants", nb_p)

            st.markdown("---")
            if st.button("🔓 Déconnexion", use_container_width=True):
                st.session_state["auth"] = False
                st.rerun()

        # --- CONTENU PRINCIPAL ---
        
        # VUE 1 : LE COCKPIT DE PILOTAGE (LIVE)
        if menu == "🔴 PILOTAGE LIVE":
            st.title("🔴 COCKPIT LIVE")
            st.markdown("C'est ici que vous contrôlez ce qui se passe sur l'écran géant.")
            
            # Séquenceur d'actions (Gros boutons)
            st.subheader("1️⃣ Séquenceur")
            col1, col2, col3, col4 = st.columns(4)
            
            m, vo, re = config["mode_affichage"], config["session_ouverte"], config["reveal_resultats"]

            with col1:
                # Bouton Attente
                if st.button("1. ACCUEIL / ATTENTE", use_container_width=True, type="primary" if m=="attente" else "secondary"):
                    config.update({"mode_affichage": "attente", "session_ouverte": False, "reveal_resultats": False})
                    json.dump(config, open(CONFIG_FILE, "w")); st.rerun()
            
            with col2:
                # Bouton Ouvrir Votes
                if st.button("2. OUVRIR LES VOTES", use_container_width=True, type="primary" if (m=="votes" and vo) else "secondary"):
                    config.update({"mode_affichage": "votes", "session_ouverte": True, "reveal_resultats": False})
                    json.dump(config, open(CONFIG_FILE, "w")); st.rerun()
            
            with col3:
                # Bouton Fermer Votes
                if st.button("3. CLÔTURER VOTES", use_container_width=True, type="primary" if (m=="votes" and not vo and not re) else "secondary"):
                    config.update({"session_ouverte": False})
                    json.dump(config, open(CONFIG_FILE, "w")); st.rerun()
            
            with col4:
                # Bouton Podium
                if st.button("4. RÉVÉLER PODIUM 🏆", use_container_width=True, type="primary" if re else "secondary"):
                    config.update({"mode_affichage": "votes", "reveal_resultats": True, "session_ouverte": False, "timestamp_podium": time.time()})
                    json.dump(config, open(CONFIG_FILE, "w")); st.rerun()

            st.markdown("---")
            
            # Visualisation des résultats en direct
            st.subheader("2️⃣ Monitoring des Votes")
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                # Graphique large
                df = pd.DataFrame(list(v_data.items()), columns=['BU', 'Points']).sort_values('Points', ascending=False)
                st.bar_chart(df.set_index('BU'), color="#E2001A")
                
                # Tableau détaillé dessous
                with st.expander("Voir le détail chiffré"):
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("En attente du premier vote...")

        # VUE 2 : CONFIGURATION (TITRES & LOGOS)
        elif menu == "⚙️ Paramétrage":
            st.title("⚙️ Paramétrage de l'événement")
            st.warning("Attention : Ces modifications sont visibles immédiatement si le mur est connecté.")
            
            col_conf1, col_conf2 = st.columns(2)
            with col_conf1:
                st.subheader("Textes")
                new_title = st.text_input("Titre principal du mur", value=config["titre_mur"])
                if new_title != config["titre_mur"]:
                    if st.button("💾 Sauvegarder le Titre"):
                        config["titre_mur"] = new_title
                        json.dump(config, open(CONFIG_FILE, "w")); st.rerun()
            
            with col_conf2:
                st.subheader("Logo")
                uploaded_logo = st.file_uploader("Changer le Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])
                if uploaded_logo:
                    if st.button("💾 Appliquer ce Logo"):
                        config["logo_b64"] = base64.b64encode(uploaded_logo.read()).decode()
                        json.dump(config, open(CONFIG_FILE, "w")); st.rerun()
                
                if config.get("logo_b64"):
                    st.write("Logo actuel :")
                    st.image(BytesIO(base64.b64decode(config["logo_b64"])), width=100)

        # VUE 3 : MÉDIATHÈQUE (PHOTOS)
        elif menu == "📸 Médiathèque":
            st.title("📸 Gestion des Photos")
            tab_adm, tab_usr = st.tabs(["Photos Officielles (Admin)", "Photos Participants"])
            
            with tab_adm:
                st.write("Ces photos sont stockées dans `galerie_admin`.")
                files = glob.glob(f"{ADMIN_DIR}/*")
                if not files: st.info("Dossier vide.")
                cols = st.columns(5)
                for i, f in enumerate(files):
                    with cols[i % 5]:
                        st.image(f, use_container_width=True)
                        if st.button("🗑️", key=f):
                            os.remove(f); st.rerun()
            
            with tab_usr:
                st.write("Photos envoyées par le public via `galerie_images`.")
                files = glob.glob(f"{GALLERY_DIR}/*")
                if not files: st.info("Aucune photo reçue.")
                cols = st.columns(5)
                for i, f in enumerate(files):
                    with cols[i % 5]:
                        st.image(f, use_container_width=True)
                        if st.button("🗑️", key=f+"u"):
                            os.remove(f); st.rerun()

        # VUE 4 : DATA & EXPORTS
        elif menu == "📊 Data & Exports":
            st.title("📊 Données & Exports")
            
            st.subheader("Téléchargements")
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                df = pd.DataFrame(list(v_data.items()), columns=['BU', 'Points'])
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Télécharger les Résultats (CSV)", csv, "resultats_vote.csv", "text/csv")
            else:
                st.caption("Aucune donnée de vote à exporter.")

            st.markdown("---")
            st.subheader("Zone de Danger")
            with st.expander("🔴 RÉINITIALISER L'ÉVÉNEMENT"):
                st.warning("Cette action effacera TOUS les votes et la liste des participants. Irréversible.")
                if st.button("CONFIRMER LE RESET COMPLET", type="primary"):
                    if os.path.exists(VOTES_FILE): os.remove(VOTES_FILE)
                    if os.path.exists(PARTICIPANTS_FILE): os.remove(PARTICIPANTS_FILE)
                    st.success("Système remis à zéro !")
                    time.sleep(1)
                    st.rerun()

# --- 4. UTILISATEUR (VOTES) ---
elif est_utilisateur:
    st.markdown("<style>.stApp { background-color: black !important; color: white !important; }</style>", unsafe_allow_html=True)
    st.title("🗳️ Vote Transdev")
    
    # Vérification cookie voté
    v_key = f"v_{config.get('vote_version', 1)}"
    
    if not config["session_ouverte"]:
        st.warning("⌛ Les votes sont clos ou pas encore ouverts.")
    else:
        choix = st.multiselect("Sélectionnez vos 3 favoris :", OPTS_BU)
        if len(choix) == 3:
            if st.button("🚀 VALIDER MON VOTE", use_container_width=True, type="primary"):
                vts = load_json(VOTES_FILE, {})
                for v, pts in zip(choix, [5, 3, 1]): 
                    vts[v] = vts.get(v, 0) + pts
                json.dump(vts, open(VOTES_FILE, "w"))
                st.success("✅ Vote enregistré !")
                time.sleep(2)
                st.rerun()
        elif len(choix) > 3:
            st.error("Maximum 3 choix !")

# --- 5. MUR SOCIAL (ÉCRAN GÉANT) ---
else:
    # CSS Global pour forcer le noir et cacher les éléments Streamlit
    st.markdown("""
        <style>
            body, .stApp { background-color: black !important; } 
            [data-testid='stHeader'], footer { display: none !important; }
            .block-container { padding-top: 2rem !important; }
        </style>
    """, unsafe_allow_html=True)
    
    nb_p = len(load_json(PARTICIPANTS_FILE, []))
    
    # Préparation HTML En-tête (Logo + Titre)
    logo_img = ""
    if config.get("logo_b64"):
        logo_img = f'<img src="data:image/png;base64,{config["logo_b64"]}" style="max-height:100px; margin-bottom:15px;">'
    
    # Affichage En-tête (SANS indentation pour éviter le bug d'affichage)
    st.markdown(f"""
<div style="text-align:center; color:white;">
{logo_img}
<h1 style="font-size:55px; font-weight:bold; text-transform:uppercase; margin:0; line-height:1.1;">{config["titre_mur"]}</h1>
<div style="background:white; display:inline-block; padding:5px 20px; border-radius:20px; color:black; font-weight:bold; margin-top:15px; font-size:18px;">👥 {nb_p} CONNECTÉS</div>
</div>
""", unsafe_allow_html=True)

    # --- LOGIQUE D'AFFICHAGE SELON L'ÉTAT ---

    # 1. ATTENTE
    if config["mode_affichage"] == "attente":
        st.markdown(f"""
<div style="text-align:center; color:white; margin-top:50px;">
<div style="{BADGE_CSS}">⌛ En attente du lancement</div>
<h2 style="font-size:60px; margin-top:40px;">Bienvenue à tous ! 👋</h2>
<p style="color:#ccc; font-size:24px;">Préparez vos téléphones...</p>
</div>
""", unsafe_allow_html=True)

    # 2. VOTES (OUVERTS OU CLOS)
    elif config["mode_affichage"] == "votes" and not config["reveal_resultats"]:
        if config["session_ouverte"]:
            # --- VOTES OUVERTS ---
            host = st.context.headers.get('host', 'localhost')
            qr_url = f"https://{host}/?mode=vote"
            qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
            qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
            
            st.markdown(f'<div style="text-align:center;"><div style="{BADGE_CSS} animation:blink 1.5s infinite;">🚀 LES VOTES SONT OUVERTS</div></div>', unsafe_allow_html=True)
            st.markdown("<style>@keyframes blink{50%{opacity:0.5;}}</style>", unsafe_allow_html=True)
            
            st.markdown("<div style='margin-top:30px;'>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 0.8, 1])
            with c1:
                for opt in OPTS_BU[:5]: st.markdown(f'<div style="background:#222; color:white; padding:12px; margin-bottom:10px; border-left:5px solid #E2001A; font-weight:bold; font-size:20px;">🎥 {opt}</div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div style="background:white; padding:15px; border-radius:15px; text-align:center;"><img src="data:image/png;base64,{qr_b64}" width="220"><p style="color:black; font-weight:bold; margin-top:10px; font-size:20px;">SCANNEZ POUR VOTER</p></div>', unsafe_allow_html=True)
            with c3:
                for opt in OPTS_BU[5:]: st.markdown(f'<div style="background:#222; color:white; padding:12px; margin-bottom:10px; border-left:5px solid #E2001A; font-weight:bold; font-size:20px;">🎥 {opt}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        else:
            # --- VOTES CLOS (ANIMATION) ---
            # Note: Le HTML est collé au bord gauche pour éviter les erreurs d'indentation Python
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

    # 3. PODIUM
    elif config["reveal_resultats"]:
        temps_ecoule = time.time() - config.get("timestamp_podium", 0)
        compte = 10 - int(temps_ecoule)
        
        if compte > 0:
            # COMPTE A REBOURS
            st.markdown(f"""
<div style="text-align:center; margin-top:80px;">
<h2 style="color:white; opacity:0.8;">RÉSULTATS DANS...</h2>
<div style="font-size:250px; color:#E2001A; font-weight:bold; animation: pulse 1s infinite;">{compte}</div>
</div>
<style>@keyframes pulse {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.1); }} 100% {{ transform: scale(1); }} }}</style>
""", unsafe_allow_html=True)
            time.sleep(0.5); st.rerun()
        else:
            # AFFICHAGE GAGNANTS
            v_data = load_json(VOTES_FILE, {})
            if v_data:
                sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)[:3]
                st.markdown(f'<div style="text-align:center;"><div style="{BADGE_CSS}">🏆 LE PODIUM 2026</div><h2 style="color:white; font-style:italic; margin-top:10px;">✨ Félicitations aux grands gagnants ! ✨</h2></div>', unsafe_allow_html=True)
                cols = st.columns(3)
                m_txt = ["🥇 1er", "🥈 2ème", "🥉 3ème"]
                # Styles spécifiques pour le podium (Or, Argent, Bronze)
                colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
                
                for i, (name, score) in enumerate(sorted_v):
                    border_c = colors[i]
                    cols[i].markdown(f"""
<div style="background:#1a1a1a; padding:30px 10px; border-radius:20px; border:4px solid {border_c}; text-align:center; color:white; margin-top:30px; box-shadow: 0 0 20px {border_c};">
<h2 style="color:{border_c}; font-size:40px; margin:0;">{m_txt[i]}</h2>
<h1 style="font-size:35px; margin:15px 0;">{name}</h1>
<p style="font-size:24px; color:#ccc;">{score} pts</p>
</div>
""", unsafe_allow_html=True)
                
                # Confettis Victoire
                components.html('<script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script><script>var end=Date.now()+10000;(function frame(){confetti({particleCount:5,origin:{y:-0.2,x:Math.random()},spread:360,gravity:0.7,colors:["#E2001A","#ffffff","#ffd700"]});if(Date.now()<end)requestAnimationFrame(frame);})();</script>', height=0)

    # Auto-refresh du mur
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(5000, key="wall_ref")
    except: pass
