import * as THREE from 'three';

// =========================================================
// 🟢 CONFIGURATION ROBOT 2026 (CLEAN)
// =========================================================
const LIMITE_HAUTE_Y = 6.53; 
const config = window.robotConfig || { mode: 'attente', titre: 'Événement', logo: '' };

const DUREE_LECTURE = 7000; 
const VITESSE_MOUVEMENT = 0.008; 
const ECHELLE_BOT = 0.6; 

// --- INJECTION STYLE BULLES ---
const style = document.createElement('style');
style.innerHTML = `
    .robot-bubble-base {
        position: fixed; padding: 15px 20px; color: black; font-family: 'Arial', sans-serif;
        font-weight: bold; font-size: 19px; text-align: center; z-index: 2147483647;
        pointer-events: none; transition: opacity 0.5s, transform 0.3s; transform: scale(0.9); max-width: 280px;
    }
    .bubble-speech { background: white; border-radius: 20px; border: 3px solid #E2001A; box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
    .bubble-speech::after { content: ''; position: absolute; bottom: -15px; left: 50%; transform: translateX(-50%); border-left: 10px solid transparent; border-right: 10px solid transparent; border-top: 15px solid #E2001A; }
    .bubble-thought { background: white; border-radius: 50%; border: 3px solid #00ffff; box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
    .bubble-thought::before { content: ''; position: absolute; bottom: -10px; left: 30%; width: 15px; height: 15px; background: white; border: 2px solid #00ffff; border-radius: 50%; }
`;
document.head.appendChild(style);

// --- SCRIPT INTRO ---
const introScript = [
    { time: 1, text: "Euh... C'est quoi cet endroit ? 🧐", type: "thought" },
    { time: 5, text: "Je ne reconnais pas ces serveurs... 💾", type: "thought" },
    { time: 9, text: "Attendez une seconde...", type: "speech" },
    { time: 12, text: "OH ! Mais vous êtes là ! 😳 Bonjour !", type: "speech", action: "surprise" },
    { time: 16, text: "Pourquoi vous êtes tous réunis ce soir ? 🤔", type: "speech" },
    { time: 20, text: "Bip Bip... Un appel ? 📞", type: "speech" },
    { time: 23, text: "Allô ? La régie ? Oui c'est moi.", type: "speech" },
    { time: 27, text: "SÉRIEUX ?! Je vais être l'animateur ce soir ? 🤩", type: "speech", action: "update_title" },
    { time: 31, text: "OK ! On va passer une soirée de folie ! ✨", type: "speech" }
];

const MESSAGES_BAG = {
    attente: ["Je suis votre animateur ! 🤖", "Hé la régie, mon micro est ok ?", "Je scanne votre enthousiasme : 100% !"],
    vote_off: ["Les votes sont clos ! Le suspense est à son comble... 😬", "La régie me dit que les résultats arrivent !"],
    photos: ["Faites-moi voir vos plus beaux sourires ! 📸", "Régie, envoyez les photos ! 📲"],
    reflexions: ["J'espère que mon costume en métal est bien repassé. ✨", "Animateur... ça paye bien en Gigaoctets ?"],
    toctoc: ["Toc ! Toc ! Est-ce que le son passe bien ? 🔊", "C'est moi, votre robot préféré !"]
};

// --- INITIALISATION ---
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', launchFinalScene);
} else {
    launchFinalScene();
}

function launchFinalScene() {
    const oldIds = ['robot-container', 'robot-canvas-overlay', 'robot-canvas-final', 'robot-bubble'];
    oldIds.forEach(id => { const el = document.getElementById(id); if (el) el.remove(); });

    const canvas = document.createElement('canvas');
    canvas.id = 'robot-canvas-final';
    document.body.appendChild(canvas);
    canvas.style.cssText = `position: fixed !important; top: 0 !important; left: 0 !important; width: 100vw !important; height: 100vh !important; z-index: 10; pointer-events: none !important; background: transparent !important;`;

    const bubbleEl = document.createElement('div');
    bubbleEl.id = 'robot-bubble';
    document.body.appendChild(bubbleEl);

    initThreeJS(canvas, bubbleEl);
}

function initThreeJS(canvas, bubbleEl) {
    let width = window.innerWidth;
    let height = window.innerHeight;
    
    const scene = new THREE.Scene();
    
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 12); 

    const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);

    window.addEventListener('resize', onWindowResize, false);
    function onWindowResize() {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    }

    scene.add(new THREE.AmbientLight(0xffffff, 2.0));

    const robotGroup = new THREE.Group();
    robotGroup.scale.set(ECHELLE_BOT, ECHELLE_BOT, ECHELLE_BOT);
    
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x000000, roughness: 0.1 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });

    const head = new THREE.Mesh(new THREE.SphereGeometry(0.85, 32, 32), whiteMat);
    head.scale.set(1.4, 1.0, 0.75);
    const face = new THREE.Mesh(new THREE.SphereGeometry(0.78, 32, 32), blackMat);
    face.position.z = 0.55; face.scale.set(1.25, 0.85, 0.6); head.add(face);
    
    const eyeGeo = new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI);
    const eyeL = new THREE.Mesh(eyeGeo, neonMat); eyeL.position.set(-0.35, 0.15, 1.05); head.add(eyeL);
    const eyeR = eyeL.clone(); eyeR.position.x = 0.35; head.add(eyeR);
    const mouth = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.035, 8, 16, Math.PI), neonMat);
    mouth.position.set(0, -0.15, 1.05); mouth.rotation.z = Math.PI; head.add(mouth);

    const body = new THREE.Mesh(new THREE.SphereGeometry(0.65, 32, 32), whiteMat);
    body.position.y = -1.1; body.scale.set(0.95, 1.1, 0.8);
    const leftArm = new THREE.Mesh(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat);
    leftArm.position.set(-0.8, -0.8, 0); leftArm.rotation.z = 0.15;
    const rightArm = new THREE.Mesh(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat);
    rightArm.position.set(0.8, -0.8, 0); rightArm.rotation.z = -0.15;

    const parts = [head, body, leftArm, rightArm];
    parts.forEach(p => { 
        robotGroup.add(p); 
        p.userData.origPos = p.position.clone(); 
        p.userData.origRot = p.rotation.clone(); 
        p.userData.velocity = new THREE.Vector3(); 
    });
    scene.add(robotGroup);

    const stageSpots = [];
    function createSpot(color, x, y) {
        const g = new THREE.Group(); g.position.set(x, y, 0);
        const beam = new THREE.Mesh(new THREE.ConeGeometry(0.4, 15, 32, 1, true), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false }));
        beam.rotateX(-Math.PI/2); beam.position.z = -7.5; g.add(beam);
        scene.add(g); return { g, beam, isOn: false, nextToggle: Math.random()*5 };
    }
    [-8, -3, 3, 8].forEach((x, i) => stageSpots.push(createSpot([0xff0000, 0x00ff00, 0x0088ff, 0xffaa00][i%4], x, LIMITE_HAUTE_Y)));

    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let time = 0, nextEvt = 0, nextMoveTime = 0, introIdx = 0;
    let targetPos = new THREE.Vector3(-12, 0, -3); 

    function showBubble(text, type = 'speech') { 
        bubbleEl.innerText = text; bubbleEl.className = 'robot-bubble-base ' + (type === 'thought' ? 'bubble-thought' : 'bubble-speech');
        bubbleEl.style.opacity = 1; bubbleEl.style.transform = "scale(1)";
        setTimeout(() => { bubbleEl.style.opacity = 0; bubbleEl.style.transform = "scale(0.9)"; }, DUREE_LECTURE); 
    }

    function pickNewTarget() {
        const dist = camera.position.z; 
        const vFOV = THREE.MathUtils.degToRad(camera.fov);
        const visibleHeight = 2 * Math.tan(vFOV / 2) * dist;
        const visibleWidth = visibleHeight * camera.aspect;
        
        const xLimit = (visibleWidth / 2) - 2.0;
        const side = Math.random() > 0.5 ? 1 : -1;
        targetPos.set(side * (Math.random() * xLimit), (Math.random() - 0.5) * 6, (Math.random() * 5) - 3);

        if(targetPos.y > LIMITE_HAUTE_Y - 2.5) targetPos.y = LIMITE_HAUTE_Y - 3;
        nextMoveTime = Date.now() + 6000;
    }

    function animate() {
        requestAnimationFrame(animate);
        time += 0.015;

        stageSpots.forEach(s => {
            if(time > s.nextToggle) { s.isOn = !s.isOn; s.nextToggle = time + Math.random()*3 + 1; }
            s.beam.material.opacity += ((s.isOn ? 0.12 : 0) - s.beam.material.opacity) * 0.1;
            s.g.lookAt(robotGroup.position);
        });

        if (robotState === 'intro') {
            const step = introScript[introIdx];
            if (step && time >= step.time) {
                showBubble(step.text, step.type);
                if(step.action === "surprise") { targetPos.set(4, 0, 7); } 
                if(step.action === "update_title") {
                    const welcomeDiv = window.parent.document.getElementById('welcome-text');
                    if(welcomeDiv) {
                        const logoHtml = config.logo ? `<img src="data:image/png;base64,${config.logo}" style="width:250px; margin-bottom:10px;">` : "";
                        welcomeDiv.style.fontSize = "45px";
                        welcomeDiv.innerHTML = `${logoHtml}<br>BIENVENUE AU<br><span style="color:#E2001A; font-size:65px;">${config.titre}</span>`;
                    }
                }
                introIdx++;
            }
            if(introIdx === 1) targetPos.set(-4, 2, -2);
            if(time > 35) { robotState = 'moving'; pickNewTarget(); nextEvt = time + 10; }
            robotGroup.position.lerp(targetPos, 0.015);
        } 
        else if (robotState === 'moving' || robotState === 'approaching' || robotState === 'thinking') {
            if (Date.now() > nextMoveTime || robotState === 'approaching') { robotGroup.position.lerp(targetPos, VITESSE_MOUVEMENT); }
            robotGroup.rotation.y = Math.sin(time)*0.2;
            
            if(robotGroup.position.distanceTo(targetPos) < 0.5 && robotState !== 'thinking') {
                if (robotState === 'approaching') {
                    if (targetPos.x > 0) { targetPos.x = -5; } else { robotState = 'moving'; pickNewTarget(); }
                } else if (Date.now() > nextMoveTime) { pickNewTarget(); }
            }
            
            if(time > nextEvt) {
                const r = Math.random();
                if(r < 0.08) { 
                    robotState = 'exploding'; showBubble("Surchauffe ! 🔥"); 
                    parts.forEach(p => p.userData.velocity.set((Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4)); 
                    setTimeout(() => { robotState = 'reassembling'; }, 3500);
                } else if(r < 0.18) { 
                    robotState = 'thinking'; targetPos.copy(robotGroup.position); showBubble("Analyse du bonheur ambiant : 100%...", 'thought'); 
                    setTimeout(() => { robotState = 'moving'; pickNewTarget(); }, 7000);
                } else if(r < 0.35) { 
                    robotState = 'approaching'; targetPos.set(5, (Math.random()-0.5)*2, 8); showBubble("Toc ! Toc ! Vous m'entendez ? ✨");
                } else { 
                    const bag = MESSAGES_BAG[config.mode] || MESSAGES_BAG['attente'];
                    showBubble(bag[Math.floor(Math.random()*bag.length)]);
                }
                nextEvt = time + 20; 
            }
        }
        else if (robotState === 'exploding') { parts.forEach(p => { p.position.add(p.userData.velocity); p.rotation.x += 0.05; p.userData.velocity.multiplyScalar(0.98); }); }
        else if (robotState === 'reassembling') {
            let finished = true;
            parts.forEach(p => { p.position.lerp(p.userData.origPos, 0.1); p.rotation.x += (p.userData.origRot.x - p.rotation.x) * 0.1; if (p.position.distanceTo(p.userData.origPos) > 0.01) finished = false; });
            if(finished) { robotState = 'moving'; nextEvt = time + 2; pickNewTarget(); }
        }

        if(bubbleEl && bubbleEl.style.opacity == 1) {
            const headPos = robotGroup.position.clone(); headPos.y += 1.3 + (robotGroup.position.z * 0.05); headPos.project(camera);
            const bX = (headPos.x * 0.5 + 0.5) * window.innerWidth;
            const bY = (headPos.y * -0.5 + 0.5) * window.innerHeight;
            bubbleEl.style.left = (bX - bubbleEl.offsetWidth / 2) + 'px';
            bubbleEl.style.top = (bY - bubbleEl.offsetHeight - 25) + 'px';
            if(parseFloat(bubbleEl.style.top) < 140) bubbleEl.style.top = '140px';
        }
        renderer.render(scene, camera);
    }
    animate();
}
