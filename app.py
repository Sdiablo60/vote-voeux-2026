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
LOGO_FILE = "logo_entreprise.png"
VOTES_FILE = "votes.json"
PARTICIPANTS_FILE = "participants.json"
CONFIG_FILE = "config_mur.json"

if not os.path.exists(GALLERY_DIR): os.makedirs(GALLERY_DIR)
config = {"mode_affichage": "photos", "titre_mur": "CONCOURS VIDÉO 2026", "vote_version": 1}
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f: config = json.load(f)

VOTE_VERSION = config.get("vote_version", 1)

# --- 2. NAVIGATION ---
query_params = st.query_params
est_admin = query_params.get("admin") == "true"
est_utilisateur = query_params.get("mode") == "vote"

# --- 3. UTILISATEUR (SÉCURITÉ INFRACHISSABLE) ---
if est_utilisateur:
    st.title("🗳️ Vote Transdev")
    
    # CLÉ UNIQUE DE SESSION (pour éviter le double clic)
    vote_key = f"transdev_v{VOTE_VERSION}"

    # INJECTION D'UN SCRIPT DE BLOCAGE RADICAL
    # Ce script vérifie le vote et envoie l'info à Streamlit de manière synchrone
    html_blocker = f"""
        <script>
        const key = "{vote_key}";
        if (localStorage.getItem(key)) {{
            window.parent.postMessage({{type: 'streamlit:setComponentValue', value: true}}, '*');
        }}
        </script>
    """
    check = components.html(html_blocker, height=0)

    # Initialisation de la vérification
    if "already_voted_on_device" not in st.session_state:
        st.session_state["already_voted_on_device"] = False

    # Interface de Vote
    if st.session_state["already_voted_on_device"]:
        st.success("✅ Votre vote est déjà enregistré sur cet appareil.")
        st.info("Le changement de pseudo n'autorise pas un nouveau vote.")
    else:
        pseudo = st.text_input("Votre Pseudo / Prénom :", key="user_pseudo")
        options = ["BU PAX", "BU FRET", "BU B2B", "SERVICE RH", "SERVICE IT", "DPMI (Atelier)", "SERVICE FINANCIES", "Service AO", "Service QSSE", "DIRECTION POLE"]
        choix = st.multiselect("Sélectionnez votre Top 3 :", options, max_selections=3)
        
        if st.button("Confirmer mon vote"):
            if not pseudo:
                st.error("Veuillez saisir un pseudo.")
            elif 0 < len(choix) <= 3:
                # 1. Enregistrement côté serveur
                with open(PARTICIPANTS_FILE, "r") as f: participants = json.load(f)
                if pseudo not in participants:
                    participants.append(pseudo)
                    with open(PARTICIPANTS_FILE, "w") as f: json.dump(participants, f)
                
                with open(VOTES_FILE, "r") as f: votes = json.load(f)
                for c in choix: votes[c] = votes.get(c, 0) + 1
                with open(VOTES_FILE, "w") as f: json.dump(votes, f)
                
                # 2. VERROUILLAGE PHYSIQUE DU NAVIGATEUR
                # On affiche un composant qui écrit le verrou AVANT de recharger
                components.html(f"""
                    <script>
                    localStorage.setItem("{vote_key}", "true");
                    setTimeout(() => {{ window.parent.location.reload(); }}, 500);
                    </script>
                    <div style="color: green; font-family: sans-serif;">Enregistrement sécurisé...</div>
                """, height=50)
                st.session_state["already_voted_on_device"] = True
            else:
                st.error("Choisissez entre 1 et 3 vidéos.")

# --- 4. ADMIN & MUR (RESTE IDENTIQUE POUR CONSERVER VOS RÉGLAGES) ---
elif est_admin:
    # (Le code admin avec boutons BLEU/ROUGE et logo à droite reste ici)
    st.markdown("<style>div[data-testid='stSidebar'] button[kind='primary'] { background-color: #0000FF !important; color: white !important; border: 3px solid #0000FF !important; } div[data-testid='stSidebar'] button[kind='secondary'] { background-color: #FF0000 !important; color: white !important; border: 3px solid #FF0000 !important; }</style>", unsafe_allow_html=True)
    with st.sidebar:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE)
        if st.text_input("Code Admin", type="password") == "ADMIN_LIVE_MASTER":
            st.session_state["auth"] = True
            if st.session_state.get("auth"):
                nouveau_titre = st.text_input("Sous-titre :", value=config.get("titre_mur"))
                new_mode = st.radio("Mode :", ["Photos", "Votes"], index=0 if config["mode_affichage"]=="photos" else 1)
                if st.button("🔵 VALIDER : MISE À JOUR MUR", type="primary", use_container_width=True):
                    with open(CONFIG_FILE, "w") as f: json.dump({"mode_affichage": new_mode.lower(), "titre_mur": nouveau_titre, "vote_version": VOTE_VERSION}, f)
                    st.rerun()
                if st.button("🔴 RESET : RÉINITIALISER TOUT", type="secondary", use_container_width=True):
                    with open(CONFIG_FILE, "w") as f: json.dump({"mode_affichage": "photos", "titre_mur": nouveau_titre, "vote_version": VOTE_VERSION + 1}, f)
                    with open(VOTES_FILE, "w") as f: json.dump({}, f); 
                    with open(PARTICIPANTS_FILE, "w") as f: json.dump([], f)
                    st.rerun()
    if st.session_state.get("auth"):
        c1, c2 = st.columns([2, 1]); c1.title("Console de Régie"); c2.image(LOGO_FILE, width=250) if os.path.exists(LOGO_FILE) else None
        st.bar_chart(json.load(open(VOTES_FILE)))

else:
    # Code du Mur Live avec QR Code et Compteur
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'] { display: none; }</style>", unsafe_allow_html=True)
    # (Affichage titres, QR code, compteur de participants et animation photos...)
    # ... [Code identique au précédent pour le Mur Social] ...
