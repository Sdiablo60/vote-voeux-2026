# --- 5. MUR SOCIAL (ÉCRAN PROJETÉ) ---
else:
    st.markdown("<style>body, .stApp { background-color: black !important; } [data-testid='stHeader'], footer { display: none !important; }</style>", unsafe_allow_html=True)
    host = st.context.headers.get('host', 'localhost')
    qr_url = f"https://{host}/?mode=vote"
    qr_buf = BytesIO(); qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
    
    nb_p = len(load_json(PARTICIPANTS_FILE, []))
    v_data = load_json(VOTES_FILE, {})

    # En-tête Mur
    st.markdown(f"""
        <div style="text-align:center; color:white; padding-top:40px;">
            <h1 style="font-size:50px; margin:0; text-transform:uppercase; letter-spacing:2px; font-weight:bold;">{config["titre_mur"]}</h1>
            <div style="margin-top:10px; background:white; display:inline-block; padding:3px 15px; border-radius:20px; color:black; font-weight:bold; font-size:16px;">
                👥 {nb_p} PARTICIPANTS CONNECTÉS
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 1. MODE ATTENTE
    if config["mode_affichage"] == "attente":
        st.markdown(f"""
            <div style="text-align:center; margin-top:15px; color:white;">
                <div style="background:#E2001A; display:inline-block; padding:8px 25px; border-radius:10px; font-size:20px; font-weight:bold; border:2px solid white; color:white;">
                    ⌛ En attente de l'ouverture des Votes
                </div>
                <div style="margin-top:60px;">
                    <h2 style="font-size:55px; opacity:0.9;">Bienvenue à tous ! 👋</h2>
                    <p style="font-size:30px; color:#ccc; margin-top:15px;">Installez-vous confortablement.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # 2. MODE VOTES (QR Code au centre, aligné avec les listes)
    elif config["mode_affichage"] == "votes" and not config["reveal_resultats"]:
        st.markdown(f"""
            <div style="text-align:center; margin-top:15px;">
                <div style="background:#E2001A; color:white; padding:8px 25px; border-radius:10px; font-size:24px; font-weight:bold; border:2px solid white; animation:blink 1.5s infinite;">
                    🚀 LES VOTES SONT OUVERTS
                </div>
            </div>
            <style>@keyframes blink{{50%{{opacity:0.3;}}}}</style>
        """, unsafe_allow_html=True)

        # Conteneur pour aligner verticalement les 3 colonnes
        st.markdown("<div style='margin-top:40px;'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 0.8, 1]) # QR Code légèrement plus étroit (0.8)
        
        with col1: # Liste Gauche
            for opt in OPTS_BU[:5]:
                st.markdown(f'<div style="background:#222; color:white; padding:12px 15px; border-radius:10px; margin-bottom:12px; border-left:5px solid #E2001A; font-size:18px; font-weight:bold;">🎥 {opt}</div>', unsafe_allow_html=True)
        
        with col2: # QR Code Central aligné
            st.markdown(f"""
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
                    <div style="background:white; padding:8px; border-radius:12px; display:inline-block;">
                        <img src="data:image/png;base64,{qr_b64}" width="180">
                    </div>
                    <div style="text-align:center; margin-top:15px; color:white; font-size:14px; font-weight:bold; letter-spacing:1px; text-transform:uppercase;">
                        Scannez pour voter
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col3: # Liste Droite
            for opt in OPTS_BU[5:]:
                st.markdown(f'<div style="background:#222; color:white; padding:12px 15px; border-radius:10px; margin-bottom:12px; border-left:5px solid #E2001A; font-size:18px; font-weight:bold;">🎥 {opt}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 3. MODE PODIUM
    elif config["mode_affichage"] == "votes" and config["reveal_resultats"]:
        if v_data:
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)[:3]
            cols = st.columns(3)
            m_txt = ["🥇 1er", "🥈 2ème", "🥉 3ème"]
            for i, (name, score) in enumerate(sorted_v):
                cols[i].markdown(f'<div style="background:#222;padding:30px;border-radius:20px;border:4px solid #E2001A;text-align:center;color:white;min-height:200px;"><h2 style="color:#E2001A;">{m_txt[i]}</h2><h1 style="font-size:35px;">{name}</h1><p>{score} pts</p></div>', unsafe_allow_html=True)

    # 4. MODE LIVE PHOTOS
    elif config["mode_affichage"] == "live":
        img_list = glob.glob(os.path.join(ADMIN_DIR, "*")) + glob.glob(os.path.join(GALLERY_DIR, "*"))
        if img_list:
            p_html = "".join([f'<img src="data:image/png;base64,{base64.b64encode(open(p,"rb").read()).decode()}" style="position:absolute;width:240px;border:5px solid white;border-radius:10px;top:{random.randint(10,50)}%;left:{random.randint(5,75)}%;transform:rotate({random.randint(-10,10)}deg);box-shadow:5px 5px 15px rgba(0,0,0,0.5);">' for p in img_list[-12:]])
            components.html(f'<div style="position:relative;width:100%;height:550px;overflow:hidden;">{p_html}</div>', height=600)

    try: 
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(5000, key="wall_ref")
    except: pass
