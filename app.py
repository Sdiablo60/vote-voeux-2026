# --- 4. MODE LIVE (VERSION RAPIDE ⚡) ---
elif not mode_vote:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=20000, key="wall_refresh")
    except: pass

    config = get_config()
    logo_b64 = get_b64(LOGO_FILE)
    img_list = glob.glob(os.path.join(GALLERY_DIR, "*"))
    
    qr_url = f"https://{st.context.headers.get('host', 'localhost')}/?mode=vote"
    qr_buf = BytesIO()
    qrcode.make(qr_url).save(qr_buf, format="PNG")
    qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

    # Génération des photos avec vitesse augmentée
    photos_html = ""
    for i, img_path in enumerate(img_list[-25:]):
        b64 = get_b64(img_path)
        if b64:
            size = random.randint(130, 220)
            top = random.randint(5, 80)
            left = random.randint(5, 85)
            # VITESSE AUGMENTÉE ICI (5 à 12 secondes au lieu de 40)
            duration = random.uniform(5.0, 12.0)
            delay = random.uniform(0, 10)
            
            photos_html += f"""<img src="data:image/png;base64,{b64}" class="photo" style="width:{size}px; height:{size}px; top:{top}%; left:{left}%; animation-duration:{duration}s; animation-delay:-{delay}s;">"""

    html_code = f"""
    <html>
    <head>
        <style>
            body, html {{ margin: 0; padding: 0; background: #000; color: white; overflow: hidden; height: 100vh; width: 100vw; font-family: sans-serif; }}
            .wall {{ position: relative; width: 100vw; height: 100vh; background: #000; }}
            
            .title {{ position: absolute; top: 2%; width: 100%; text-align: center; font-weight: bold; font-size: {config['taille']}px; color: {config['couleur']}; text-shadow: 0 0 20px {config['couleur']}aa; z-index: 100; }}
            
            .center-block {{ 
                position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                display: flex; flex-direction: column; align-items: center; justify-content: center; 
                z-index: 1000; gap: 8px;
            }}
            .logo {{ width: 250px; height: auto; filter: drop-shadow(0 0 20px rgba(255,255,255,0.4)); }}
            .qr-zone {{ background: white; padding: 8px; border-radius: 12px; text-align: center; width: 100px; box-shadow: 0 0 30px rgba(255,255,255,0.2); }}

            .photo {{ 
                position: absolute; border-radius: 50%; border: 4px solid white; object-fit: cover; 
                box-shadow: 0 0 20px rgba(0,0,0,0.5); animation: floatAround linear infinite alternate; 
                opacity: 0.9; z-index: 10;
            }}

            /* MOUVEMENT PLUS AMPLE ET NERVEUX */
            @keyframes floatAround {{
                0% {{ transform: translate(0,0) rotate(0deg) scale(1); }}
                50% {{ transform: translate(100px, -80px) rotate(10deg) scale(1.1); }}
                100% {{ transform: translate(-80px, 120px) rotate(-10deg) scale(1); }}
            }}
        </style>
    </head>
    <body>
        <div class="wall">
            <div class="title">{config['texte']}</div>
            <div class="center-block">
                {"<img src='data:image/png;base64," + logo_b64 + "' class='logo'>" if logo_b64 else ""}
                <div class="qr-zone">
                    <img src="data:image/png;base64,{qr_b64}" width="90">
                    <div style="color:black; font-size:8px; font-weight:bold; margin-top:2px;">SCANNEZ MOI</div>
                </div>
            </div>
            {photos_html}
        </div>
    </body>
    </html>
    """
    components.html(html_code, height=1200, scrolling=False)
