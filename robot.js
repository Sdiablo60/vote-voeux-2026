import * as THREE from 'three';

// =========================================================
// 🟢 CONFIGURATION ROBOT 2026 (SCÉNARIO "TECHNIQUE")
// =========================================================
const LIMITE_HAUTE_Y = 6.53; 
const config = window.robotConfig || { mode: 'attente', titre: 'Événement', logo: '' };

const DUREE_LECTURE = 5000; 
const VITESSE_MOUVEMENT = 0.008; 
const ECHELLE_BOT = 0.6; 

// SEUIL DE VITESSE
const SPEED_THRESHOLD = 0.03; 

// --- MESSAGES ROTATIFS ---
const CENTRAL_MESSAGES = [
    "Votre soirée va bientôt commencer...<br>Merci de vous installer",
    "Une soirée exceptionnelle vous attend",
    "Veuillez couper la sonnerie<br>de vos téléphones 🔕",
    "Profitez de l'instant et du spectacle",
    "Préparez-vous à jouer !"
];

// --- STYLE CSS ---
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

// --- NOUVEAU SCENARIO NARRATIF ---
const introScript = [
    // 1. Début classique
    { time: 1, text: "Inspection de la zone... 🧐", type: "thought", action: "move_top_left" },
    { time: 5, text: "Bonjour à tous ! 👋", type: "speech", action: "move_center" },
    
    // 2. Le départ "Technique"
    { time: 9, text: "Oups ! Je dois aller voir la technique...", type: "speech", action: "move_right_fast" },
    { time: 12, text: "Je reviens tout de suite ! 🏃‍♂️", type: "speech", action: "exit_right" },
    
    // 3. Le retour (t=18s)
    { time: 18, text: "Me revoilà ! 😅", type: "speech", action: "enter_left" },
    
    // 4. L'annonce officielle
    { time: 22, text: "J'ai eu la régie en ligne...", type: "speech", action: "move_center_close" },
    { time: 26, text: "La soirée va bientôt commencer ! 🎉", type: "speech" },
    
    // 5. Interaction Public
    { time: 30, text: "Est-ce que tout le monde est prêt ? 🎤", type: "speech" },
    { time: 34, text: "Il ne manque personne ? Regardez autour de vous ! 👀", type: "speech", action: "scan_crowd" },
    
    // 6. Titre et fin intro
    { time: 39, text: "Alors place à : " + config.titre + " ! ✨", type: "speech", action: "update_title" }
];

const MESSAGES_BAG = {
    attente: [
        "Installez-vous confortablement, on commence bientôt !", 
        "Je scanne la salle... Vous êtes magnifiques !",
        "N'oubliez pas de scanner le QR Code pour jouer tout à l'heure !",
        "Je révise mes fiches... Bip Bip..."
    ],
    vote_off: ["Les votes sont clos ! Le suspense est à son comble...", "Qui va gagner ?"],
    photos: ["Oh ! C'est vous sur cette photo ? 📸", "Envoyez-moi plus de sourires !"],
    reflexion: ["Hmm... Je me demande si...", "Calcul en cours...", "Analyse de l'ambiance..."]
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
    let width = window.innerWidth, height = window.innerHeight;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 12); 

    const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });

    scene.add(new THREE.AmbientLight(0xffffff, 2.0));

    // ROBOT
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(ECHELLE_BOT, ECHELLE_BOT, ECHELLE_BOT);
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x000000, roughness: 0.1 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });

    const head = new THREE.Mesh(new THREE.SphereGeometry(0.85, 32, 32), whiteMat);
    head.scale.set(1.4, 1.0, 0.75);
    const face = new THREE.Mesh(new THREE.SphereGeometry(0.78, 32, 32), blackMat);
    face.position.z = 0.55; face.scale.set(1.25, 0.85, 0.6); head.add(face);
    const eyeL = new THREE.Mesh(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat);
    eyeL.position.set(-0.35, 0.15, 1.05); head.add(eyeL);
    const eyeR = eyeL.clone(); eyeR.position.x = 0.35; head.add(eyeR);
    const mouth = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.035, 8, 16, Math.PI), neonMat);
    mouth.position.set(0, -0.15, 1.05); mouth.rotation.z = Math.PI; head.add(mouth);
    const body = new THREE.Mesh(new THREE.SphereGeometry(0.65, 32, 32), whiteMat);
    body.position.y = -1.1; body.scale.set(0.95, 1.1, 0.8);
    const leftArm = new THREE.Mesh(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat);
    leftArm.position.set(-0.8, -0.8, 0); leftArm.rotation.z = 0.15;
    const rightArm = new THREE.Mesh(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat);
    rightArm.position.set(0.8, -0.8, 0); rightArm.rotation.z = -0.15;
    
    [head, body, leftArm, rightArm].forEach(p => { 
        robotGroup.add(p); p.userData.origPos = p.position.clone(); p.userData.origRot = p.rotation.clone(); p.userData.velocity = new THREE.Vector3(); 
    });
    scene.add(robotGroup);

    // SPOTS
    const stageSpots = [];
    [-8, -3, 3, 8].forEach((x, i) => {
        const g = new THREE.Group(); g.position.set(x, LIMITE_HAUTE_Y, 0);
        const beam = new THREE.Mesh(new THREE.ConeGeometry(0.4, 15, 32, 1, true), new THREE.MeshBasicMaterial({ color: [0xff0000, 0x00ff00, 0x0088ff, 0xffaa00][i%4], transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false }));
        beam.rotateX(-Math.PI/2); beam.position.z = -7.5; g.add(beam);
        scene.add(g); stageSpots.push({ g, beam, isOn: false, nextToggle: Math.random()*5 });
    });

    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let time = 0, nextEvt = 0, nextMoveTime = 0, introIdx = 0;
    let targetPos = new THREE.Vector3(-12, 0, -3); 
    let lastPos = new THREE.Vector3();
    let lastTextChange = 0;
    let textMsgIndex = 0;

    function showBubble(text, type = 'speech') { 
        bubbleEl.innerHTML = text; 
        bubbleEl.className = 'robot-bubble-base ' + (type === 'thought' ? 'bubble-thought' : 'bubble-speech');
        bubbleEl.style.opacity = 1; bubbleEl.style.transform = "scale(1)";
        setTimeout(() => { bubbleEl.style.opacity = 0; bubbleEl.style.transform = "scale(0.9)"; }, DUREE_LECTURE); 
    }

    function cycleCenterText() {
        const subDiv = document.getElementById('sub-text');
        if(subDiv) {
            subDiv.style.opacity = 0;
            setTimeout(() => { subDiv.innerHTML = CENTRAL_MESSAGES[textMsgIndex % CENTRAL_MESSAGES.length]; subDiv.style.opacity = 1; textMsgIndex++; }, 1000); 
        }
    }

    function pickNewTarget() {
        const dist = camera.position.z; const vFOV = THREE.MathUtils.degToRad(camera.fov);
        const visibleHeight = 2 * Math.tan(vFOV / 2) * dist; const visibleWidth = visibleHeight * camera.aspect;
        const xLimit = (visibleWidth / 2) - 2.0;
        const side = Math.random() > 0.5 ? 1 : -1;
        const randomX = 4.0 + (Math.random() * (xLimit - 4.0)); // Evite le centre
        targetPos.set(side * randomX, (Math.random() - 0.5) * 6, (Math.random() * 5) - 3);
        if(targetPos.y > LIMITE_HAUTE_Y - 2.5) targetPos.y = LIMITE_HAUTE_Y - 3;
        nextMoveTime = Date.now() + 6000;
    }

    function animate() {
        requestAnimationFrame(animate);
        time += 0.015;
        const currentSpeed = robotGroup.position.distanceTo(lastPos);

        stageSpots.forEach(s => {
            if(time > s.nextToggle) { s.isOn = !s.isOn; s.nextToggle = time + Math.random()*3 + 1; }
            s.beam.material.opacity += ((s.isOn ? 0.12 : 0) - s.beam.material.opacity) * 0.1;
            s.g.lookAt(robotGroup.position);
        });

        // --- LOGIQUE INTRO ---
        if (robotState === 'intro') {
            const step = introScript[introIdx];
            if (step && time >= step.time) {
                showBubble(step.text, step.type);
                
                // GESTION DES MOUVEMENTS SCÉNARISÉS
                if(step.action === "move_top_left") targetPos.set(-7, 3, 0);
                if(step.action === "move_top_right") targetPos.set(7, 3, 0);
                if(step.action === "move_center") targetPos.set(0, 0, 0);
                if(step.action === "move_right_fast") targetPos.set(10, 0, 0);
                
                // SORTIE DE L'ECRAN (Vers la droite X=25)
                if(step.action === "exit_right") targetPos.set(25, 0, 0);
                
                // RETOUR DANS L'ECRAN (Téléportation à gauche X=-25 puis entrée)
                if(step.action === "enter_left") {
                    robotGroup.position.set(-25, 0, 0);
                    targetPos.set(-6, 0, 2);
                }

                if(step.action === "move_center_close") targetPos.set(0, -1, 7); // Gros plan
                if(step.action === "scan_crowd") targetPos.set(3, 1, 5); // Regarde ailleurs

                if(step.action === "update_title") {
                    const subDiv = document.getElementById('sub-text');
                    if(subDiv) { subDiv.innerHTML = config.titre; subDiv.style.opacity = 1; lastTextChange = time + 10; }
                }
                introIdx++;
            }
            // Fin de l'intro vers 45s
            if(time > 45) { robotState = 'moving'; pickNewTarget(); nextEvt = time + 10; }
            
            // Lissage du mouvement (Lerp)
            // Si on doit sortir vite, on augmente le facteur de lerp
            let speedFactor = 0.02;
            if (targetPos.x > 15 || robotGroup.position.x < -15) speedFactor = 0.05; 
            robotGroup.position.lerp(targetPos, speedFactor);
        } 
        
        // --- MODE LIBRE ---
        else if (robotState === 'moving' || robotState === 'approaching' || robotState === 'thinking') {
            if (config.mode === 'attente' && time > lastTextChange + 10) { cycleCenterText(); lastTextChange = time; }
            if (Date.now() > nextMoveTime || robotState === 'approaching') robotGroup.position.lerp(targetPos, VITESSE_MOUVEMENT);
            robotGroup.rotation.y = Math.sin(time)*0.2;
            
            if(robotGroup.position.distanceTo(targetPos) < 0.5 && robotState !== 'thinking') {
                if (robotState === 'approaching') { robotState = 'moving'; pickNewTarget(); }
                else if (Date.now() > nextMoveTime) pickNewTarget(); 
            }
            
            if(time > nextEvt) {
                const r = Math.random();
                if(r < 0.05) { // Explosion
                    robotState = 'exploding'; showBubble("Surchauffe ! 🔥"); 
                    parts.forEach(p => p.userData.velocity.set((Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4)); 
                    setTimeout(() => { robotState = 'reassembling'; }, 3500); nextEvt = time + 20;
                }
                else if (currentSpeed < SPEED_THRESHOLD) { // Parle seulement si lent
                    if(r < 0.30) { 
                        robotState = 'thinking'; targetPos.copy(robotGroup.position);
                        showBubble(MESSAGES_BAG.reflexion[Math.floor(Math.random()*MESSAGES_BAG.reflexion.length)], 'thought'); 
                        setTimeout(() => { robotState = 'moving'; pickNewTarget(); }, 7000);
                    } else {
                         const bag = (config.mode === 'photos' && r < 0.6) ? MESSAGES_BAG['photos'] : MESSAGES_BAG[config.mode] || MESSAGES_BAG['attente'];
                         if(config.mode === 'photos' && r < 0.6) {
                             robotState = 'approaching'; 
                             const side = Math.random() > 0.5 ? 5.5 : -5.5; targetPos.set(side, (Math.random()-0.5)*2, 7);
                         }
                         showBubble(bag[Math.floor(Math.random()*bag.length)]);
                    }
                    nextEvt = time + 20; 
                } else { nextEvt = time + 2; }
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
        lastPos.copy(robotGroup.position);
        renderer.render(scene, camera);
    }
    animate();
}
