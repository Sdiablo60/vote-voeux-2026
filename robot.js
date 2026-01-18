# =========================================================
# 3. MUR SOCIAL (VERSION FINALE v16 - SOL CSS)
# =========================================================
else:
    from streamlit_autorefresh import st_autorefresh
    cfg = load_json(CONFIG_FILE, default_config)
    
    refresh_rate = 5000 if (cfg.get("mode_affichage") == "votes" and cfg.get("reveal_resultats")) else 4000
    st_autorefresh(interval=refresh_rate, key="wall_refresh")
    
    st.markdown("""
    <style>
        .stApp, .main, .block-container, [data-testid="stAppViewContainer"] {
            background-color: black !important;
            padding: 0 !important; margin: 0 !important;
            width: 100vw !important; max-width: 100vw !important;
            overflow: hidden !important;
        }
        .social-header { 
            position: fixed !important; top: 0 !important; left: 0 !important; 
            width: 100vw !important; height: 8vh !important;
            background-color: #E2001A !important; 
            display: flex !important; align-items: center !important; justify-content: center !important; 
            z-index: 999999 !important; 
            border-bottom: 3px solid white; 
            box-shadow: 0 5px 10px rgba(0,0,0,0.3);
        }
        .social-title { 
            color: white !important; font-family: Arial, sans-serif !important;
            font-size: 3.5vh !important; font-weight: 900 !important; 
            margin: 0 !important; text-transform: uppercase; letter-spacing: 2px;
        }
        iframe {
            position: fixed !important; top: 0 !important; left: 0 !important;
            width: 100vw !important; height: 100vh !important;
            border: none !important; z-index: 0 !important; display: block !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f'<div class="social-header"><h1 class="social-title">{cfg["titre_mur"]}</h1></div>', unsafe_allow_html=True)
    
    mode = cfg.get("mode_affichage")
    effects = cfg.get("screen_effects", {})
    effect_name = effects.get("attente" if mode=="attente" else "podium", "Aucun")
    inject_visual_effect(effect_name, 25, 15)
    
    try:
        with open("style.css", "r", encoding="utf-8") as f: css_content = f.read()
        with open("robot.js", "r", encoding="utf-8") as f: js_content = f.read()
    except: css_content = ""; js_content = "console.error('Fichiers manquants');"

    robot_mode = "attente" 
    if mode == "votes" and not cfg["session_ouverte"] and not cfg["reveal_resultats"]:
        robot_mode = "vote_off"
    elif mode == "photos_live":
        robot_mode = "photos"
    
    safe_title = cfg['titre_mur'].replace("'", "\\'")
    logo_data = cfg.get("logo_b64", "")
    
    js_config = f"""<script>window.robotConfig = {{ mode: '{robot_mode}', titre: '{safe_title}', logo: '{logo_data}' }};</script>"""
    import_map = """<script type="importmap">{ "imports": { "three": "https://unpkg.com/three@0.160.0/build/three.module.js", "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/" } }</script>"""
    
    # === CSS INTERNE (SOL EN CSS GRILLE) ===
    internal_css_base = f"""
    <style>
        body {{ margin: 0; padding: 0; background-color: black; overflow: hidden; width: 100vw; height: 100vh; }}
        #safe-zone {{ position: absolute; top: 8vh; left: 0; width: 100vw; height: 92vh; box-sizing: border-box; z-index: 100; pointer-events: none; }}
        {css_content}
        .neon-title {{
            font-family: Arial, sans-serif; font-size: 70px; font-weight: 900; letter-spacing: 5px; margin: 0; padding: 0; color: #fff;
            text-shadow: 0 0 5px #fff, 0 0 10px #fff, 0 0 20px #E2001A, 0 0 35px #E2001A, 0 0 50px #E2001A;
            animation: neon-flicker 1.5s infinite alternate;
        }}
        @keyframes neon-flicker {{
            0%, 19%, 21%, 23%, 25%, 54%, 56%, 100% {{ text-shadow: 0 0 5px #fff, 0 0 10px #fff, 0 0 20px #E2001A, 0 0 35px #E2001A, 0 0 50px #E2001A; }}
            20%, 24%, 55% {{ text-shadow: none; opacity: 0.5; }}
        }}
        /* LE SOL EN CSS (Z-INDEX 0) */
        .floor-grid {{
            position: fixed; bottom: 0; left: 0; width: 100vw; height: 40vh; z-index: 0; pointer-events: none;
            background: linear-gradient(to top, rgba(30,30,30,1), transparent),
                        repeating-linear-gradient(90deg, transparent 0, transparent 49px, #333 50px),
                        repeating-linear-gradient(0deg, transparent 0, transparent 49px, #333 50px);
            perspective: 500px; transform: perspective(500px) rotateX(45deg) scale(2) translateY(100px); opacity: 0.6;
        }}
    </style>
    """

    if mode == "attente":
        internal_css = internal_css_base + """
        <style>
            #welcome-container { position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%); text-align: center; width: 80%; z-index: 10; pointer-events: none; }
            #welcome-logo { width: 380px; margin-bottom: 60px; }
            #sub-text { margin-top: 50px; color: #eeeeee; font-family: 'Arial', sans-serif; font-size: 40px; font-weight: normal; opacity: 0; transition: opacity 1s ease-in-out; text-shadow: 0 0 10px black; }
        </style>
        """
        logo_img_tag = f'<img id="welcome-logo" src="data:image/png;base64,{logo_data}">' if logo_data else ""
        html_code = f"""<!DOCTYPE html><html><head>{internal_css}</head><body>{js_config}
            <div class="floor-grid"></div> <div id="safe-zone"></div>
            <div id="welcome-container">
                {logo_img_tag}
                <div id="welcome-title" class="neon-title">BIENVENUE</div>
                <div id="sub-text"></div>
            </div>
            <div id="robot-bubble" class="bubble" style="z-index: 20;">...</div>
            <div id="robot-container" style="z-index: 5; pointer-events: none;"></div>
            {import_map}<script type="module">{js_content}</script></body></html>"""
        components.html(html_code, height=1000, scrolling=False) 

    elif mode == "votes":
        if cfg.get("reveal_resultats"):
            # ... (CODE PODIUM INCHANGÉ) ...
            v_data = load_json(VOTES_FILE, {})
            c_imgs = cfg.get("candidats_images", {})
            if not v_data: v_data = {"Personne": 0}
            sorted_unique_scores = sorted(list(set(v_data.values())), reverse=True)
            s1 = sorted_unique_scores[0] if len(sorted_unique_scores) > 0 else 0; rank1 = [c for c, s in v_data.items() if s == s1]
            s2 = sorted_unique_scores[1] if len(sorted_unique_scores) > 1 else 0; rank2 = [c for c, s in v_data.items() if s == s2]
            s3 = sorted_unique_scores[2] if len(sorted_unique_scores) > 2 else 0; rank3 = [c for c, s in v_data.items() if s == s3]
            def get_podium_html(cands, score, emoji):
                if not cands: return ""
                html = ""
                for c in cands:
                    img_tag = f"<div class='p-placeholder' style='background:#333; display:flex; justify-content:center; align-items:center; font-size:60px;'>{emoji}</div>"
                    if c in c_imgs: img_tag = f"<img src='data:image/png;base64,{c_imgs[c]}' class='p-img'>"
                    html += f"<div class='p-card'>{img_tag}<div class='p-name'>{c}</div></div>"
                return html
            h1 = get_podium_html(rank1, s1, "🥇"); h2 = get_podium_html(rank2, s2, "🥈"); h3 = get_podium_html(rank3, s3, "🥉")
            final_logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" class="final-logo">' if cfg.get("logo_b64") else ""
            components.html(f"""<div id="intro-layer" class="intro-overlay"><div id="intro-txt" class="intro-text"></div><div id="intro-num" class="intro-count"></div></div><div id="final-overlay" class="final-overlay"><div class="final-content">{final_logo_html}<h1 class="final-text">FÉLICITATIONS AUX GAGNANTS !</h1></div></div><audio id="applause-sound" preload="auto"><source src="https://www.soundjay.com/human/sounds/applause-01.mp3" type="audio/mpeg"></audio><div class="podium-container"><div class="column-2"><div class="winners-box rank-2" id="win-2">{h2}</div><div class="pedestal pedestal-2"><div class="rank-score">{s2} PTS</div><div class="rank-num">2</div></div></div><div class="column-1"><div class="winners-box rank-1" id="win-1">{h1}</div><div class="pedestal pedestal-1"><div class="rank-score">{s1} PTS</div><div class="rank-num">1</div></div></div><div class="column-3"><div class="winners-box rank-3" id="win-3">{h3}</div><div class="pedestal pedestal-3"><div class="rank-score">{s3} PTS</div><div class="rank-num">3</div></div></div></div><script>const wait=(ms)=>new Promise(resolve=>setTimeout(resolve,ms));const layer=document.getElementById('intro-layer'),txt=document.getElementById('intro-txt'),num=document.getElementById('intro-num'),w1=document.getElementById('win-1'),w2=document.getElementById('win-2'),w3=document.getElementById('win-3'),audio=document.getElementById('applause-sound'),finalOverlay=document.getElementById('final-overlay');function startConfetti(){{var script=document.createElement('script');script.src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js";script.onload=()=>{{var duration=15*1000;var animationEnd=Date.now()+duration;var defaults={{startVelocity:30,spread:360,ticks:60,zIndex:9999}};var random=(min,max)=>Math.random()*(max-min)+min;var interval=setInterval(function(){{var timeLeft=animationEnd-Date.now();if(timeLeft<=0){{return clearInterval(interval);}}var particleCount=50*(timeLeft/duration);confetti(Object.assign({{}},defaults,{{particleCount,origin:{{x:random(0.1,0.3),y:Math.random()-0.2}}}}));confetti(Object.assign({{}},defaults,{{particleCount,origin:{{x:random(0.7,0.9),y:Math.random()-0.2}}}}));}},250);}};document.body.appendChild(script);}}async function countdown(seconds,message){{layer.style.display='flex';layer.style.opacity='1';txt.innerText=message;for(let i=seconds;i>0;i--){{num.innerText=i;await wait(1000);}}layer.style.opacity='0';await wait(500);layer.style.display='none';}}async function runShow(){{await countdown(5,"EN TROISIÈME PLACE...");w3.classList.add('visible');document.querySelector('.pedestal-3').classList.add('visible');await wait(2000);await countdown(5,"EN SECONDE PLACE...");w2.classList.add('visible');document.querySelector('.pedestal-2').classList.add('visible');await wait(2000);await countdown(7,"ET LE VAINQUEUR EST...");w1.classList.add('visible');document.querySelector('.pedestal-1').classList.add('visible');startConfetti();try{{audio.currentTime=0;audio.play();}}catch(e){{}}await wait(4000);finalOverlay.classList.add('stage-1-black');await wait(4000);finalOverlay.classList.remove('stage-1-black');finalOverlay.classList.add('stage-2-transparent');}}window.parent.document.body.style.backgroundColor="black";runShow();</script><style>body{{margin:0;overflow:hidden;background:black;}}.podium-container{{position:absolute;bottom:0;left:0;width:100%;height:100vh;display:flex;justify-content:center;align-items:flex-end;padding-bottom:20px;}}.column-2{{width:32%;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;margin-right:-20px;z-index:2;}}.column-1{{width:36%;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;z-index:3;}}.column-3{{width:32%;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;margin-left:-20px;z-index:2;}}.winners-box{{display:flex;flex-direction:row;flex-wrap:wrap-reverse;justify-content:center;align-items:flex-end;width:450px!important;max-width:450px!important;margin:0 auto;padding-bottom:0px;opacity:0;transform:translateY(50px) scale(0.8);transition:all 1s cubic-bezier(0.175,0.885,0.32,1.275);gap:10px;}}.winners-box.visible{{opacity:1;transform:translateY(0) scale(1);}}.pedestal{{width:100%;background:linear-gradient(to bottom,#333,#000);border-radius:20px 20px 0 0;box-shadow:0 -5px 15px rgba(255,255,255,0.1);display:flex;flex-direction:column;justify-content:flex-start;align-items:center;position:relative;padding-top:20px;}}.pedestal-1{{height:350px;border-top:3px solid #FFD700;color:#FFD700;}}.pedestal-2{{height:220px;border-top:3px solid #C0C0C0;color:#C0C0C0;}}.pedestal-3{{height:150px;border-top:3px solid #CD7F32;color:#CD7F32;}}.rank-num{{font-size:120px;font-weight:900;opacity:0.2;line-height:1;}}.rank-score{{font-size:30px;font-weight:bold;text-shadow:0 2px 4px rgba(0,0,0,0.5);margin-bottom:-20px;z-index:5;opacity:0;transform:translateY(20px);transition:all 0.5s ease-out;}}.pedestal.visible .rank-score{{opacity:1;transform:translateY(0);}}.p-card{{background:rgba(20,20,20,0.8);border-radius:15px;padding:15px;width:200px;margin:10px;backdrop-filter:blur(5px);border:2px solid rgba(255,255,255,0.3);display:flex;flex-direction:column;align-items:center;box-shadow:0 5px 15px rgba(0,0,0,0.5);flex-shrink:0;}}.p-img,.p-placeholder{{width:140px;height:140px;border-radius:50%;object-fit:cover;border:4px solid white;margin-bottom:10px;}}.p-name{{font-family:Arial;font-size:22px;font-weight:bold;color:white;text-transform:uppercase;text-align:center;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;width:100%;}}.intro-overlay{{position:fixed;top:15vh;left:0;width:100vw;z-index:5000;display:flex;flex-direction:column;align-items:center;text-align:center;transition:opacity 0.5s;pointer-events:none;}}.intro-text{{color:white;font-size:40px;font-weight:bold;text-transform:uppercase;text-shadow:0 0 20px black;}}.intro-count{{color:#E2001A;font-size:100px;font-weight:900;margin-top:10px;text-shadow:0 0 20px black;}}.final-overlay{{position:fixed;top:0;left:0;width:100vw;height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;z-index:6000;pointer-events:none;opacity:0;transition:all 1.5s ease-in-out;}}.final-overlay.stage-1-black{{background-color:black;opacity:1;}}.final-overlay.stage-2-transparent{{background-color:transparent;opacity:1;justify-content:flex-start;padding-top:0;}}.final-logo{{width:400px;margin-bottom:20px;}}.final-text{{font-size:50px;color:#E2001A;text-transform:uppercase;text-shadow:0 0 20px rgba(0,0,0,0.8);margin:0;}}</style>""", height=1000, scrolling=False)

        elif cfg["session_ouverte"]:
             # ... (CODE VOTES OUVERTS INCHANGÉ) ...
             host = st.context.headers.get('host', 'localhost')
             qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
             qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
             logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="width:380px; margin-bottom:10px;">' if cfg.get("logo_b64") else ""
             recent_votes = load_json(DETAILED_VOTES_FILE, [])
             voter_names = [v['Utilisateur'] for v in recent_votes[-20:]][::-1]
             voter_string = " &nbsp;&nbsp;•&nbsp;&nbsp; ".join(voter_names) if voter_names else "En attente des premiers votes..."
             cands = cfg["candidats"]; mid = (len(cands) + 1) // 2
             left_cands = cands[:mid]; right_cands = cands[mid:]
             def gen_html_list(clist, imgs, align='left'):
                 h = ""
                 for c in clist:
                     im = '<div style="font-size:30px;">👤</div>'
                     if c in imgs: im = f'<img src="data:image/png;base64,{imgs[c]}" style="width:50px;height:50px;border-radius:50%;object-fit:cover;border:2px solid white;">'
                     h += f"""<div style="display:flex; align-items:center; justify-content:flex-start; flex-direction:row; margin:10px 0; background:rgba(255,255,255,0.1); padding:10px 20px; border-radius:50px; width:220px; margin-{align}: auto;">{im}<span style="margin-left:15px; font-size:18px; font-weight:bold; color:white; text-transform:uppercase; line-height: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{c}</span></div>"""
                 return h
             left_html = gen_html_list(left_cands, cfg.get("candidats_images", {}), 'left')
             right_html = gen_html_list(right_cands, cfg.get("candidats_images", {}), 'right')
             components.html(f"""<style>body {{ background: black; margin: 0; padding: 0; font-family: Arial, sans-serif; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }}.marquee-container {{ width: 100%; background: #E2001A; color: white; height: 50px; position: fixed; top: 0; left: 0; z-index: 1000; display: flex; align-items: center; border-bottom: 2px solid white; }}.marquee-label {{ background: #E2001A; color: white; font-weight: 900; font-size: 18px; padding: 0 20px; height: 100%; display: flex; align-items: center; z-index: 1001; }}.marquee-wrapper {{ overflow: hidden; white-space: nowrap; flex-grow: 1; height: 100%; display: flex; align-items: center; }}.marquee-content {{ display: inline-block; padding-left: 100%; animation: marquee 20s linear infinite; font-weight: bold; font-size: 18px; text-transform: uppercase; }}@keyframes marquee {{ 0% {{ transform: translate(0, 0); }} 100% {{ transform: translate(-100%, 0); }} }}.top-section {{ width: 100%; height: 35vh; margin-top: 60px; display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 10; }}.title {{ font-size: 60px; font-weight: 900; color: #E2001A; margin: 10px 0; text-transform: uppercase; letter-spacing: 3px; }}.subtitle {{ font-size: 30px; font-weight: bold; color: white; }}.bottom-section {{ width: 95%; margin: 0 auto; height: 55vh; display: flex; align-items: center; justify-content: space-between; }}.center-col {{ width: 30%; display: flex; flex-direction: column; align-items: center; }}.qr-box {{ background: white; padding: 15px; border-radius: 20px; box-shadow: 0 0 50px rgba(226, 0, 26, 0.5); }}</style><div class="marquee-container"><div class="marquee-label">DERNIERS VOTANTS :</div><div class="marquee-wrapper"><div class="marquee-content">{voter_string}</div></div></div><div class="top-section">{logo_html}<div class="title">VOTES OUVERTS</div><div class="subtitle">Scannez pour voter</div></div><div class="bottom-section"><div class="side-col">{left_html}</div><div class="center-col"><div class="qr-box"><img src="data:image/png;base64,{qr_b64}" width="300"></div></div><div class="side-col">{right_html}</div></div>""", height=900)
        else:
            logo_html = f'<img src="data:image/png;base64,{cfg["logo_b64"]}" style="width:350px; margin-bottom:10px;">' if cfg.get("logo_b64") else ""
            html_code = f"""<!DOCTYPE html><html><head>{internal_css_base}</head><body>{js_config}
            <div class="floor-grid"></div> <div id="safe-zone"></div>
            <div style='position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); z-index: 10; display:flex; flex-direction:column; align-items:center; justify-content:center; pointer-events: none;'>
                <div style='border: 5px solid #E2001A; padding: 40px; border-radius: 30px; background: rgba(0,0,0,0.85); max-width: 800px; text-align: center; box-shadow: 0 0 50px black;'>
                    {logo_html}
                    <h1 class="neon-title" style='font-size:60px; margin:0;'>MERCI !</h1>
                    <h2 style='color:white; font-size:35px; margin-top:20px; font-weight:normal; text-shadow: 0 0 10px black;'>Les votes sont clos.</h2>
                    <h3 style='color:#cccccc; font-size:25px; margin-top:10px; font-style:italic; text-shadow: 0 0 10px black;'>Veuillez patienter... Nous allons découvrir les GAGNANTS !</h3>
                </div>
            </div>
            <div id="robot-bubble" class="bubble" style="z-index: 20;">...</div>
            <div id="robot-container" style="z-index: 5; pointer-events: none;"></div>
            {import_map}<script type="module">{js_content}</script></body></html>"""
            components.html(html_code, height=1000, scrolling=False)

    elif mode == "photos_live":
        host = st.context.headers.get('host', 'localhost')
        qr_buf = BytesIO(); qrcode.make(f"https://{host}/?mode=vote").save(qr_buf, format="PNG")
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        logo_data = cfg.get("logo_b64", "")
        photos = glob.glob(f"{LIVE_DIR}/*")
        img_js = json.dumps([f"data:image/jpeg;base64,{base64.b64encode(open(f, 'rb').read()).decode()}" for f in photos[-40:]]) if photos else "[]"
        center_html_content = f"""<div id='center-box' style='position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); z-index:10; text-align:center; background:rgba(0,0,0,0.85); padding:20px; border-radius:30px; border:2px solid #E2001A; width:400px; box-shadow:0 0 50px rgba(0,0,0,0.8); pointer-events: none;'><h1 class="neon-title" style='font-size:28px; margin:0 0 15px 0;'>MUR PHOTOS LIVE</h1>{f'<img src="data:image/png;base64,{logo_data}" style="width:350px; margin-bottom:10px;">' if logo_data else ''}<div style='background:white; padding:15px; border-radius:15px; display:inline-block;'><img src='data:image/png;base64,{qr_b64}' style='width:250px;'></div><h2 style='color:white; margin-top:15px; font-size:22px; font-family:Arial; line-height:1.3; text-shadow: 0 0 10px black;'>Partagez vos sourires<br>et vos moments forts !</h2></div>"""
        
        # Z-INDEX 1 POUR LES BULLES (DEVANT LE SOL CSS, DERRIERE LE ROBOT)
        bubbles_script = f"""<script>setTimeout(function() {{ var container = document.createElement('div'); container.id = 'live-container'; container.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:1;overflow:hidden;background:transparent;pointer-events:none;'; document.body.appendChild(container); var centerDiv = document.createElement('div'); centerDiv.innerHTML = `{center_html_content}`; document.body.appendChild(centerDiv); const imgs = {img_js}; const bubbles = []; imgs.forEach((src, i) => {{ const bSize = Math.floor(Math.random() * 300) + 150; const el = document.createElement('img'); el.src = src; el.style.cssText = 'position:absolute; width:'+bSize+'px; height:'+bSize+'px; border-radius:50%; border:4px solid #E2001A; object-fit:cover; z-index:50; opacity:0.9;'; let x = Math.random() * (window.innerWidth - bSize); let y = Math.random() * (window.innerHeight - bSize); let angle = Math.random() * Math.PI * 2; let speed = 1.5 + Math.random() * 1.5; container.appendChild(el); bubbles.push({{el, x, y, vx: Math.cos(angle)*speed, vy: Math.sin(angle)*speed, size: bSize}}); }}); function animateBubbles() {{ bubbles.forEach(b => {{ b.x += b.vx; b.y += b.vy; if(b.x <= 0 || b.x + b.size >= window.innerWidth) b.vx *= -1; if(b.y <= 0 || b.y + b.size >= window.innerHeight) b.vy *= -1; b.el.style.transform = 'translate3d(' + b.x + 'px, ' + b.y + 'px, 0)'; }}); requestAnimationFrame(animateBubbles); }} animateBubbles(); }}, 500);</script>"""
        
        html_code = f"""<!DOCTYPE html><html><head>{internal_css_base}</head><body>{js_config}
        <div class="floor-grid"></div> <div id="safe-zone"></div>
        <div id="robot-bubble" class="bubble" style="z-index: 20;">...</div>
        <div id="robot-container" style="z-index: 5; pointer-events: none;"></div>
        {import_map}<script type="module">{js_content}</script>{bubbles_script}</body></html>"""
        components.html(html_code, height=1000, scrolling=False)
    
    else:
        st.markdown(f"<div class='full-screen-center'><h1 style='color:white;'>EN ATTENTE...</h1></div>", unsafe_allow_html=True)
