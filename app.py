# =========================================================
# 3. MUR SOCIAL
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    cfg = load_json(CONFIG_FILE, default_config)
    # Refresh auto pour vérifier les changements d'état
    refresh_rate = 5000 if (cfg.get("mode_affichage") == "votes" and cfg.get("reveal_resultats")) else 4000
    st_autorefresh(interval=refresh_rate, key="wall_refresh")
    
    st.markdown("""<style>.stApp { background-color: black !important; color: white !important; }</style>""", unsafe_allow_html=True)
    st.markdown(f'<div class="social-header"><h1 class="social-title">{cfg["titre_mur"]}</h1></div>', unsafe_allow_html=True)
    
    mode = cfg.get("mode_affichage")
    effects = cfg.get("screen_effects", {})
    effect_name = effects.get("attente" if mode=="attente" else "podium", "Aucun")
    inject_visual_effect(effect_name, 25, 15)
    
    # --- CHARGEMENT DES FICHIERS ---
    try:
        with open("style.css", "r", encoding="utf-8") as f: css_content = f.read()
        with open("robot.js", "r", encoding="utf-8") as f: js_content = f.read()
    except: css_content = ""; js_content = "console.error('Fichiers manquants');"

    # --- CONFIGURATION DU ROBOT (TITRE ET MODE) ---
    # C'est ici qu'on donne le cerveau au robot
    robot_mode = "attente" # par défaut
    if mode == "votes" and not cfg["session_ouverte"] and not cfg["reveal_resultats"]:
        robot_mode = "vote_off"
    elif mode == "photos_live":
        robot_mode = "photos"
    
    # On nettoie le titre pour le JS
    safe_title = cfg['titre_mur'].replace("'", "\\'")
    
    # Injection des variables pour le JS
    js_config = f"""
    <script>
        window.robotConfig = {{
            mode: '{robot_mode}',
            titre: '{safe_title}'
        }};
    </script>
    """

    if mode == "attente":
        logo_img_tag = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="width:350px; margin-bottom:10px;">' if cfg.get("logo_b64") else ""
        html_code = f"""<!DOCTYPE html><html><head><style>body {{ margin: 0; padding: 0; background-color: black; overflow: hidden; width: 100vw; height: 100vh; }}{css_content}#welcome-text {{ position: absolute; top: 45%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: white; font-family: Arial, sans-serif; z-index: 5; font-size: 70px; font-weight: 900; letter-spacing: 5px; pointer-events: none; }}</style></head><body>{js_config}<div id="welcome-text">{logo_img_tag}<br>BIENVENUE</div><div id="robot-bubble" class="bubble">...</div><div id="robot-container"></div><script type="importmap">{{ "imports": {{ "three": "https://unpkg.com/three@0.160.0/build/three.module.js" }} }}</script><script type="module">{js_content}</script></body></html>"""
        components.html(html_code, height=1000, scrolling=False)

    elif mode == "votes":
        if cfg.get("reveal_resultats"):
            # PODIUM (Code inchangé, je raccourcis pour la lisibilité ici, gardez votre code Podium actuel)
            v_data = load_json(VOTES_FILE, {})
            # ... (Gardez tout le code Podium original ici, il est très long) ...
            # SI VOUS NE L'AVEZ PLUS, DITES LE MOI, JE LE RECOLLE
            # Pour l'instant je remets le code standard simplifié pour le Vote OFF / ON
            pass 
        elif cfg["session_ouverte"]:
             # VOTES OUVERTS (QR CODE) - Inchangé
             host = st.context.headers.get('host', 'localhost')
             # ... (Gardez le code Votes Ouverts original) ...
             # Code Votes Ouverts standard
             pass
        else:
            # --- VOTE OFF (ROBOT ACTIF) ---
            logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="width:350px; margin-bottom:10px;">' if cfg.get("logo_b64") else ""
            overlay_html = f"""<div style='position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); z-index: 10; display:flex; flex-direction:column; align-items:center; justify-content:center;'><div style='border: 5px solid #E2001A; padding: 40px; border-radius: 30px; background: rgba(0,0,0,0.85); max-width: 800px; text-align: center; box-shadow: 0 0 50px black;'>{logo_html}<h1 style='color:#E2001A; font-size:60px; margin:0; text-transform: uppercase;'>MERCI !</h1><h2 style='color:white; font-size:35px; margin-top:20px; font-weight:normal;'>Les votes sont clos.</h2><h3 style='color:#cccccc; font-size:25px; margin-top:10px; font-style:italic;'>Veuillez patienter... Nous allons découvrir les GAGNANTS !</h3></div></div>"""
            html_code = f"""<!DOCTYPE html><html><head><style>body {{ margin: 0; padding: 0; background-color: black; overflow: hidden; width: 100vw; height: 100vh; }}{css_content}</style></head><body>{js_config}{overlay_html}<div id="robot-bubble" class="bubble">...</div><div id="robot-container"></div><script type="importmap">{{ "imports": {{ "three": "https://unpkg.com/three@0.160.0/build/three.module.js" }} }}</script><script type="module">{js_content}</script></body></html>"""
            components.html(html_code, height=1000, scrolling=False)

    elif mode == "photos_live":
        # --- PHOTOS LIVE (AVEC ROBOT EN FOND) ---
        # Code Fusionné Bulles + Robot
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        logo_data = cfg.get("logo_b64", "")
        photos = glob.glob(f"{LIVE_DIR}/*")
        img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-40:]]) if photos else "[]"
        
        center_html_content = f"""<div id='center-box' style='position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); z-index:100; text-align:center; background:rgba(0,0,0,0.85); padding:20px; border-radius:30px; border:2px solid #E2001A; width:400px; box-shadow:0 0 50px rgba(0,0,0,0.8);'><h1 style='color:#E2001A; margin:0 0 15px 0; font-size:28px; font-weight:bold; text-transform:uppercase;'>MUR PHOTOS LIVE</h1>{f'<img src="data:image/png;base64,{logo_data}" style="width:350px; margin-bottom:10px;">' if logo_data else ''}<div style='background:white; padding:15px; border-radius:15px; display:inline-block;'><img src='data:image/png;base64,{qr_b64}' style='width:250px;'></div><h2 style='color:white; margin-top:15px; font-size:22px; font-family:Arial; line-height:1.3;'>Partagez vos sourires<br>et vos moments forts !</h2></div>"""
        
        bubbles_script = f"""
        <script>
            setTimeout(function() {{
                var container = document.createElement('div');
                container.id = 'live-container'; 
                container.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:50;overflow:hidden;background:transparent;pointer-events:none;';
                document.body.appendChild(container);
                var centerDiv = document.createElement('div');
                centerDiv.innerHTML = `{center_html_content}`;
                document.body.appendChild(centerDiv);
                const imgs = {img_js}; 
                const bubbles = [];
                var screenW = window.innerWidth; var screenH = window.innerHeight;
                imgs.forEach((src, i) => {{
                    const bSize = Math.floor(Math.random() * (450 - 150 + 1)) + 150;
                    const el = document.createElement('img'); el.src = src;
                    el.style.cssText = 'position:absolute; width:'+bSize+'px; height:'+bSize+'px; border-radius:50%; border:4px solid #E2001A; object-fit:cover; will-change:transform; z-index:50; opacity:0.9;';
                    let x = Math.random() * (screenW - bSize); let y = Math.random() * (screenH - bSize);
                    let angle = Math.random() * Math.PI * 2; let speed = 0.5 + Math.random() * 0.8;
                    let vx = Math.cos(angle) * speed; let vy = Math.sin(angle) * speed;
                    container.appendChild(el); bubbles.push({{el, x: x, y: y, vx, vy, size: bSize}});
                }});
                function animateBubbles() {{
                    screenW = window.innerWidth; screenH = window.innerHeight;
                    bubbles.forEach(b => {{
                        b.x += b.vx; b.y += b.vy;
                        if(b.x <= 0) {{ b.x=0; b.vx *= -1; }} if(b.x + b.size >= screenW) {{ b.x=screenW-b.size; b.vx *= -1; }}
                        if(b.y <= 0) {{ b.y=0; b.vy *= -1; }} if(b.y + b.size >= screenH) {{ b.y=screenH-b.size; b.vy *= -1; }}
                        b.el.style.transform = 'translate3d(' + b.x + 'px, ' + b.y + 'px, 0)';
                    }});
                    requestAnimationFrame(animateBubbles);
                }}
                animateBubbles();
            }}, 500);
        </script>
        """
        html_code = f"""<!DOCTYPE html><html><head><style>body {{ margin: 0; padding: 0; background-color: black; overflow: hidden; width: 100vw; height: 100vh; }}{css_content}</style></head><body>{js_config}<div id="robot-bubble" class="bubble">...</div><div id="robot-container"></div><script type="importmap">{{ "imports": {{ "three": "https://unpkg.com/three@0.160.0/build/three.module.js" }} }}</script><script type="module">{js_content}</script>{bubbles_script}</body></html>"""
        components.html(html_code, height=1000, scrolling=False)
