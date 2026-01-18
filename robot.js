import * as THREE from 'three';

// =========================================================
// 🟢 CONFIGURATION ROBOT 2026 (FINAL v18 - SOL & ROBOT VISIBLES)
// =========================================================
const config = window.robotConfig || { mode: 'attente', titre: 'Événement', logo: '' };

const DUREE_LECTURE = 6000; 
const ECHELLE_BOT = 0.6; 
const MUTE_LIMIT_X = 9.5; 

// Vitesses
const SPEED_HOVER = 0.005;   
const SPEED_IMPULSE = 0.05;  

const CENTRAL_MESSAGES = [
    "Votre soirée va bientôt commencer...<br>Merci de vous installer",
    "Une soirée exceptionnelle vous attend",
    "Veuillez couper la sonnerie<br>de vos téléphones 🔕",
    "Profitez de l'instant et du spectacle",
    "Préparez-vous à jouer !",
    "N'oubliez pas vos sourires !"
];

// --- BANQUES DE TEXTES ---
const TEXTS_ATTENTE = [
    "Clap-E vérifie les niveaux... Tout est OK !",
    "Je vole, je vole ! 🤖",
    "Toc toc... C'est encore Clap-E !",
    "Vous êtes très élégants ce soir !",
    "Il fait bon ici, ou c'est mes réacteurs ?",
    "Clap-E scanne la salle... Ambiance : 100% positive.",
    "Qui a le meilleur sourire ce soir ? Je cherche...",
    "N'oubliez pas de scanner le QR Code !",
    "Faites coucou à la caméra ! C'est moi !",
    "Calcul de la trajectoire... Fait.",
    "42. La réponse est toujours 42.",
    "Je suis plus rapide que l'éclair (ou presque).",
    "Prêts pour le décollage avec Clap-E Airlines ?",
    "C'est long l'attente ? Courage !",
    "Retenez bien mon nom : C'est Clap-E !"
];

const TEXTS_VOTE_OFF = [
    "Votes clos ! Clap-E a verrouillé les urnes. 🛑",
    "La régie compte... Moi je fais des loopings.",
    "Patience, ça arrive !",
    "Je ne peux rien dire, c'est top secret ! 🤫",
    "C'est plus serré qu'un boulon de 12 !",
    "Clap-E calcule les probabilités... Suspense.",
    "J'espère que le meilleur a gagné !",
    "Analyse des résultats en cours... 📊",
    "Pas de triche, Clap-E a tout vu.",
    "Alors ? Stressés ? Moi je surchauffe !",
    "Les résultats arrivent par fibre optique...",
    "Merci à tous d'avoir participé."
];

const TEXTS_PHOTOS = [
    "Prenez une photo avec Clap-E ! 📸",
    "Allez, un petit selfie ?",
    "Rapprochez-vous pour la photo !",
    "Wouah ! Quelle belle photo !",
    "Clap-E adore celle-ci... (Chut !)",
    "Regardez ce sourire ! Magnifique !",
    "C'est parti pour la soirée danse ! 💃",
    "Regardez mon style aérien !",
    "Continuez d'envoyer vos photos !",
    "Je valide cette pose ! Top model !",
    "Attention le petit oiseau va sortir...",
    "Cadrez bien mes antennes svp.",
    "Vous êtes rayonnants ce soir.",
    "Attention, Clap-E va traverser l'écran !",
    "Envoyez-nous vos plus belles grimaces !",
    "Flash info : Vous êtes le meilleur public !"
];

let currentTextBank = [];
if (config.mode === 'vote_off') currentTextBank = [...TEXTS_VOTE_OFF];
else if (config.mode === 'photos') currentTextBank = [...TEXTS_PHOTOS];
else currentTextBank = [...TEXTS_ATTENTE];

// --- STYLE CSS ---
const style = document.createElement('style');
style.innerHTML = `
    .robot-bubble-base {
        position: fixed; padding: 20px 25px; color: black; font-family: 'Arial', sans-serif;
        font-weight: bold; font-size: 22px; text-align: center; z-index: 6; 
        pointer-events: none; transition: opacity 0.1s, transform 0.3s; transform: scale(0.9); 
        max-width: 350px; width: max-content;
    }
    .bubble-speech { background: white; border-radius: 30px; border: 4px solid #E2001A; box-shadow: 0 10px 25px rgba(0,0,0,0.6); }
    .bubble-speech::after { content: ''; position: absolute; bottom: -15px; left: 50%; transform: translateX(-50%); border-left: 10px solid transparent; border-right: 10px solid transparent; border-top: 15px solid #E2001A; }
    .bubble-thought { background: white; border-radius: 50%; border: 4px solid #00ffff; box-shadow: 0 10px 25px rgba(0,0,0,0.5); font-style: italic; color: #555; }
    .bubble-thought::before { content: ''; position: absolute; bottom: -10px; left: 30%; width: 15px; height: 15px; background: white; border: 2px solid #00ffff; border-radius: 50%; }
`;
document.head.appendChild(style);

// --- SCENARIO 1 : ACCUEIL ---
const introScript_Attente = [
    { time: 0.5, text: "", action: "teleport_in_left" }, 
    { time: 4, text: "Wouah... C'est grand ici !", type: "thought", action: "fly_hover_right" }, 
    { time: 12, text: "Je crois que je suis le premier...", type: "thought", action: "fly_hover_left" }, 
    { time: 20, text: "OH ! Il y a du monde ! 😳", type: "speech", action: "stop_left_front" }, 
    { time: 27, text: "Bonjour ! Je suis Clap-E ! 👋", type: "speech", action: "wave_hands" },
    { time: 35, text: "Bienvenue à tous !", type: "speech", action: "fly_right_up" }, 
    { time: 42, text: "", action: "impulse_cross_left" }, 
    { time: 46, text: "Ouhlà ! Ça décoiffe !", type: "speech", action: "stop_right_front" },
    { time: 54, text: "Vous êtes bien réels ? 😅", type: "speech" }, 
    { time: 62, text: "Je scanne la salle...", type: "thought", action: "fly_scan" }, 
    { time: 70, text: "Hum, que des stars ce soir. 😎", type: "speech" },
    { time: 78, text: "Excusez-moi, appel régie...", type: "speech", action: "phone_pose" }, 
    { time: 86, text: "Allô ? Oui, ici Clap-E.", type: "speech" },
    { time: 94, text: "C'est confirmé ?! Super !", type: "speech", action: "fly_loop" },
    { time: 102, text: "Je suis votre animateur officiel ! 🎤", type: "speech" },
    { time: 110, text: "Bienvenue à : " + config.titre + " !", type: "speech" },
    { time: 118, text: "Je dois filer préparer mes fiches...", type: "speech" }, 
    { time: 124, text: "", action: "impulse_exit_right" }, 
    { time: 135, text: "Me revoilà ! 😅", type: "speech", action: "teleport_in_left" }, 
    { time: 142, text: "C'était moins une !", type: "speech", action: "fly_hover_center_high" },
    { time: 150, text: "Installez-vous bien, je veille.", type: "speech" }
];

// --- SCENARIO 2 : VOTE OFF ---
const introScript_VoteOff = [
    { time: 0.5, text: "", action: "teleport_in_right" }, 
    { time: 5, text: "Oula... C'est fini !", type: "speech", action: "wave_hands" },
    { time: 12, text: "Désolé, les votes sont clos ! 🛑", type: "speech", action: "fly_left_up" },
    { time: 20, text: "La régie compte les points...", type: "speech" },
    { time: 27, text: "", action: "impulse_cross_right" }, 
    { time: 31, text: "Soyez patients, ça arrive !", type: "speech", action: "stop_left_front" }, 
    { time: 38, text: "C'était serré... 🤫", type: "speech" }
];

// --- SCENARIO 3 : PHOTOS LIVE ---
const introScript_Photos = [
    { time: 0.5, text: "", action: "teleport_in_left" }, 
    { time: 5, text: "Hé ! C'est ici le studio photo ? 📸", type: "speech", action: "dance_start" }, 
    { time: 10, text: "", action: "dance_stop" },
    { time: 12, text: "Coucou ! Je suis Clap-E ! 👋", type: "speech", action: "wave_hands" }, 
    { time: 18, text: "Poussez-vous, je veux voir !", type: "speech", action: "fly_right_up" }, 
    { time: 26, text: "Oh ! Superbe celle-ci !", type: "speech", action: "look_bubbles" }, 
    { time: 33, text: "", action: "impulse_cross_left" }, 
    { time: 37, text: "J'ai failli percuter une bulle !", type: "speech", action: "stop_right_front" }, 
    { time: 45, text: "Un petit selfie avec Clap-E ?", type: "speech", action: "pose_selfie" }, 
    { time: 51, text: "Bon, je file voir la régie...", type: "speech" }, 
    { time: 57, text: "", action: "impulse_exit_left" }, 
    { time: 66, text: "Me revoilà ! ✨", type: "speech", action: "teleport_in_right" }, 
    { time: 73, text: "Allez, tous ensemble !", type: "speech", action: "pose_selfie" } 
];

let currentIntroScript = introScript_Attente;
if (config.mode === 'vote_off') currentIntroScript = introScript_VoteOff;
if (config.mode === 'photos') currentIntroScript = introScript_Photos;

if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', launchFinalScene); } else { launchFinalScene(); }

function launchFinalScene() {
    ['robot-container', 'robot-canvas-overlay', 'robot-canvas-final', 'robot-bubble', 'robot-canvas-floor', 'robot-canvas-bot'].forEach(id => { const el = document.getElementById(id); if (el) el.remove(); });
    
    // CANVAS UNIQUE (Z-INDEX 0 = FOND)
    const canvas = document.createElement('canvas'); canvas.id = 'robot-canvas-final';
    document.body.appendChild(canvas);
    canvas.style.cssText = `position: fixed !important; top: 0 !important; left: 0 !important; width: 100vw !important; height: 100vh !important; z-index: 0 !important; pointer-events: none !important; background: transparent !important;`;

    const bubbleEl = document.createElement('div'); bubbleEl.id = 'robot-bubble';
    document.body.appendChild(bubbleEl);
    
    initThreeJS(canvas, bubbleEl);
}

function initThreeJS(canvas, bubbleEl) {
    let width = window.innerWidth, height = window.innerHeight;
    const scene = new THREE.Scene();
    // BROUILLARD (FOG) pour fondre le sol
    scene.fog = new THREE.Fog(0x000000, 10, 60);
    
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 12); 
    const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setSize(width, height); renderer.setPixelRatio(window.devicePixelRatio);
    window.addEventListener('resize', () => { camera.aspect = window.innerWidth / window.innerHeight; camera.updateProjectionMatrix(); renderer.setSize(window.innerWidth, window.innerHeight); });
    
    scene.add(new THREE.AmbientLight(0xffffff, 2.0));

    // --- SOL 3D RESTAURÉ ---
    // Couleur 0x444444 pour être visible mais sombre
    const grid = new THREE.GridHelper(200, 50, 0x444444, 0x444444); 
    grid.position.y = -2.5; 
    scene.add(grid);

    // PARTICULES
    const particleCount = 500;
    const particleGeo = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);
    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
    const particleMat = new THREE.PointsMaterial({ color: 0x00ffff, size: 0.3, transparent: true, opacity: 0 });
    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);
    const teleportLight = new THREE.PointLight(0x00ffff, 0, 20);
    scene.add(teleportLight);

    let explosionTime = 0;
    let isExploding = false;

    function triggerTeleport(pos) {
        isExploding = true; explosionTime = 1.0; 
        particles.position.copy(pos); teleportLight.position.copy(pos); teleportLight.intensity = 8;
        particleMat.opacity = 1;
        for(let i=0; i<particleCount; i++) {
            particlePositions[i*3] = (Math.random()-0.5)*3; particlePositions[i*3+1] = (Math.random()-0.5)*5; particlePositions[i*3+2] = (Math.random()-0.5)*3;
        }
        particleGeo.attributes.position.needsUpdate = true;
    }

    // --- ROBOT (CODE COMPLET RESTAURÉ) ---
    const robotGroup = new THREE.Group(); 
    robotGroup.position.set(-35, 0, 0); 
    robotGroup.scale.set(ECHELLE_BOT, ECHELLE_BOT, ECHELLE_BOT);
    
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x000000, roughness: 0.1 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.85, 32, 32), whiteMat); head.scale.set(1.4, 1.0, 0.75);
    const face = new THREE.Mesh(new THREE.SphereGeometry(0.78, 32, 32), blackMat); face.position.z = 0.55; face.scale.set(1.25, 0.85, 0.6); head.add(face);
    const eyeL = new THREE.Mesh(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat); eyeL.position.set(-0.35, 0.15, 1.05); head.add(eyeL);
    const eyeR = eyeL.clone(); eyeR.position.x = 0.35; head.add(eyeR);
    const mouth = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.035, 8, 16, Math.PI), neonMat); mouth.position.set(0, -0.15, 1.05); mouth.rotation.z = Math.PI; head.add(mouth);
    const body = new THREE.Mesh(new THREE.SphereGeometry(0.65, 32, 32), whiteMat); body.position.y = -1.1; body.scale.set(0.95, 1.1, 0.8);
    
    const armLGroup = new THREE.Group(); armLGroup.position.set(-0.9, -0.8, 0); 
    const armL = new THREE.Mesh(new THREE.CapsuleGeometry(0.1, 0.4, 8, 16), whiteMat); armL.position.y = -0.2; 
    const handL = new THREE.Mesh(new THREE.SphereGeometry(0.15, 16, 16), whiteMat); handL.position.y = -0.5; 
    armLGroup.add(armL); armLGroup.add(handL);

    const armRGroup = new THREE.Group(); armRGroup.position.set(0.9, -0.8, 0);
    const armR = new THREE.Mesh(new THREE.CapsuleGeometry(0.1, 0.4, 8, 16), whiteMat); armR.position.y = -0.2;
    const handR = new THREE.Mesh(new THREE.SphereGeometry(0.15, 16, 16), whiteMat); handR.position.y = -0.5;
    armRGroup.add(armR); armRGroup.add(handR);

    [head, body, armLGroup, armRGroup].forEach(p => { robotGroup.add(p); });
    armLGroup.userData.origRot = armLGroup.rotation.clone(); armRGroup.userData.origRot = armRGroup.rotation.clone();
    
    scene.add(robotGroup);

    const stageSpots = [];
    [-8, -3, 3, 8].forEach((x, i) => {
        const g = new THREE.Group(); g.position.set(x, 6.5, 0);
        const beam = new THREE.Mesh(new THREE.ConeGeometry(0.4, 15, 32, 1, true), new THREE.MeshBasicMaterial({ color: [0xff0000, 0x00ff00, 0x0088ff, 0xffaa00][i%4], transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false }));
        beam.rotateX(-Math.PI/2); beam.position.z = -7.5; g.add(beam);
        scene.add(g); stageSpots.push({ g, beam, isOn: false, nextToggle: Math.random()*5 });
    });

    let robotState = 'intro';
    let isWaving = false;
    let isImpulsing = false; 
    let time = 0, nextEvt = 0, nextMoveTime = 0, introIdx = 0;
    let targetPos = new THREE.Vector3(-35, 0, 0); 
    let lastPos = new THREE.Vector3();
    let lastTextChange = 0;
    let textMsgIndex = 0;
    let subtitlesActive = false; 

    function showBubble(text, type = 'speech') { 
        if(isImpulsing || Math.abs(robotGroup.position.x) > MUTE_LIMIT_X) return;
        if(!text) return;
        bubbleEl.innerHTML = text; 
        bubbleEl.className = 'robot-bubble-base ' + (type === 'thought' ? 'bubble-thought' : 'bubble-speech');
        bubbleEl.style.opacity = 1; bubbleEl.style.transform = "scale(1)";
        setTimeout(() => { bubbleEl.style.opacity = 0; bubbleEl.style.transform = "scale(0.9)"; }, DUREE_LECTURE); 
    }

    function cycleCenterText() {
        const subDiv = document.getElementById('sub-text');
        if(subDiv && subtitlesActive) {
            subDiv.style.opacity = 0;
            setTimeout(() => { subDiv.innerHTML = CENTRAL_MESSAGES[textMsgIndex % CENTRAL_MESSAGES.length]; subDiv.style.opacity = 1; textMsgIndex++; }, 1000); 
        }
    }

    function pickNewTarget() {
        const r = Math.random();
        if (r < 0.3) { 
            isImpulsing = true;
            const startSide = Math.random() > 0.5 ? -18 : 18;
            robotGroup.position.set(startSide, (Math.random()-0.5)*4, (Math.random()-0.5)*2);
            targetPos.set(-startSide, (Math.random()-0.5)*6, (Math.random()-0.5)*4);
        } else { 
            isImpulsing = false;
            const side = Math.random() > 0.5 ? 1 : -1;
            const randomX = side * (8.0 + Math.random() * 4.0);
            targetPos.set(randomX, (Math.random()-0.5)*5, (Math.random()*4)-2);
        }
        if(targetPos.y > 4.5) targetPos.y = 4.0;
        nextMoveTime = Date.now() + 5000; 
    }

    function getNextMessage() {
        if (currentTextBank.length === 0) {
            if (config.mode === 'vote_off') currentTextBank = [...TEXTS_VOTE_OFF];
            else if (config.mode === 'photos') currentTextBank = [...TEXTS_PHOTOS];
            else currentTextBank = [...TEXTS_ATTENTE];
        }
        const idx = Math.floor(Math.random() * currentTextBank.length);
        const msg = currentTextBank[idx];
        currentTextBank.splice(idx, 1);
        return msg;
    }

    function animate() {
        requestAnimationFrame(animate);
        time += 0.015;
        const currentSpeed = robotGroup.position.distanceTo(lastPos);

        if(isExploding && explosionTime > 0) {
            explosionTime -= 0.02;
            particleMat.opacity = explosionTime;
            teleportLight.intensity = explosionTime * 5;
            const positions = particleGeo.attributes.position.array;
            for(let i=0; i<particleCount; i++) { 
                positions[i*3] += (Math.random()-0.5)*0.3; 
                positions[i*3+1] += (Math.random()-0.5)*0.3; 
                positions[i*3+2] += (Math.random()-0.5)*0.3; 
            }
            particleGeo.attributes.position.needsUpdate = true;
        }

        stageSpots.forEach(s => {
            if(time > s.nextToggle) { s.isOn = !s.isOn; s.nextToggle = time + Math.random()*3 + 1; }
            s.beam.material.opacity += ((s.isOn ? 0.12 : 0) - s.beam.material.opacity) * 0.1;
            s.g.lookAt(robotGroup.position);
        });

        if (robotState === 'intro') {
            const step = currentIntroScript[introIdx];
            if (step && time >= step.time) {
                let allowText = true;
                if(step.action && step.action.includes("impulse")) { isImpulsing = true; allowText = false; }
                else { isImpulsing = false; }

                if (allowText && (currentSpeed < SPEED_THRESHOLD || step.action?.includes("fast") || step.action?.includes("normal") || step.action?.includes("teleport"))) {
                    if(step.text) showBubble(step.text, step.type);
                }
                
                if(step.action === "fly_hover_right") targetPos.set(11, 2, -1);
                if(step.action === "fly_hover_left") targetPos.set(-11, -2, 1);
                if(step.action === "fly_right_up") targetPos.set(12, 4, -2);
                if(step.action === "fly_left_up") targetPos.set(-12, 4, -2);
                if(step.action === "fly_scan") targetPos.set(-10, 3, 3);
                if(step.action === "fly_loop") targetPos.set(10, 2, -3);
                if(step.action === "fly_hover_center_high") targetPos.set(0, 4, 0);

                if(step.action === "stop_left_front") targetPos.set(-10, 0, 4);
                if(step.action === "stop_right_front") targetPos.set(10, 0, 4);
                if(step.action === "toc_toc_approach") targetPos.set(11, 0, 8.5); 
                if(step.action === "backup_a_bit") targetPos.set(11, 0, 5);
                if(step.action === "wave_hands") { isWaving = true; setTimeout(() => { isWaving = false; }, 3000); }
                if(step.action === "pose_selfie") { robotState = 'posing'; setTimeout(() => { robotState = 'intro'; }, 3000); }
                if(step.action === "look_bubbles") { targetPos.set(-12, 4, 0); } 
                if(step.action === "phone_call") targetPos.set(11, 0, 2);
                if(step.action === "surprise") targetPos.set(11, 0, 6);
                if(step.action === "start_subtitles") { subtitlesActive = true; cycleCenterText(); lastTextChange = time; }
                if(step.action === "listen_intense") targetPos.set(-11, 0, 5);
                if(step.action === "announce_pose") targetPos.set(-5, 1, 6); 
                if(step.action === "center_breath") targetPos.set(0, 0, 3);

                if(step.action === "impulse_cross_left") { robotGroup.position.set(18, 2, -2); targetPos.set(-18, -2, 2); isImpulsing = true; }
                if(step.action === "impulse_cross_right") { robotGroup.position.set(-18, -1, 2); targetPos.set(18, 3, -2); isImpulsing = true; }
                if(step.action === "impulse_exit_left") { targetPos.set(-25, 0, 0); isImpulsing = true; }
                if(step.action === "impulse_exit_right") { targetPos.set(25, 0, 0); isImpulsing = true; }

                if(step.action === "teleport_in_left") { robotGroup.position.set(-11, 0, 0); targetPos.set(-11, 0, 0); triggerTeleport(new THREE.Vector3(-11, 0, 0)); }
                if(step.action === "teleport_in_right") { robotGroup.position.set(11, 0, 0); targetPos.set(11, 0, 0); triggerTeleport(new THREE.Vector3(11, 0, 0)); }
                if(step.action === "enter_teleport_right_visible") { robotGroup.position.set(11, 0, 0); targetPos.set(11, 0, 0); triggerTeleport(new THREE.Vector3(11, 0, 0)); }
                if(step.action === "enter_teleport_left_visible") { robotGroup.position.set(-11, 0, 0); targetPos.set(-11, 0, 0); triggerTeleport(new THREE.Vector3(-11, 0, 0)); }

                if(step.action === "dance_start") { robotState = 'dancing_intro'; setTimeout(() => { if(robotState === 'dancing_intro') robotState = 'intro'; }, 5000); }
                if(step.action === "dance_stop") { robotState = 'intro'; robotGroup.rotation.set(0, 0, 0); }
                
                introIdx++;
            }
            
            if(introIdx >= currentIntroScript.length) { robotState = 'infinite_loop'; pickNewTarget(); nextEvt = time + 10; }
            
            if(robotState !== 'dancing_intro' && robotState !== 'posing') {
                const spd = isImpulsing ? SPEED_IMPULSE : SPEED_HOVER; 
                robotGroup.position.lerp(targetPos, spd);
            }
        } 
        
        else if (robotState === 'infinite_loop' || robotState === 'approaching' || robotState === 'thinking') {
            if (config.mode === 'attente' && subtitlesActive && time > lastTextChange + 12) { cycleCenterText(); lastTextChange = time; }
            
            const spd = isImpulsing ? SPEED_IMPULSE : SPEED_HOVER;
            robotGroup.position.lerp(targetPos, spd);
            
            robotGroup.rotation.z = (targetPos.x - robotGroup.position.x) * -0.05; 
            robotGroup.rotation.x = (targetPos.y - robotGroup.position.y) * 0.05; 
            
            if(robotGroup.position.distanceTo(targetPos) < 1.0) {
                if(isImpulsing) { isImpulsing = false; }
                pickNewTarget();
            }
            
            if(time > nextEvt && !isImpulsing) { 
                const r = Math.random();
                if(r < 0.05) { robotState = 'exploding'; showBubble("Surchauffe ! 🔥"); setTimeout(() => { robotState = 'reassembling'; }, 3500); nextEvt = time + 25; }
                else if (config.mode === 'photos' && r < 0.20) { robotState = 'dancing'; showBubble("J'adore ce son !", 'speech'); setTimeout(() => { robotState = 'infinite_loop'; robotGroup.rotation.set(0,0,0); pickNewTarget(); }, 6000); nextEvt = time + 20; }
                else if (config.mode !== 'attente' && r < 0.50) { isWaving = true; setTimeout(() => { isWaving = false; }, 3000); nextEvt = time + 8; }
                else if (currentSpeed < SPEED_THRESHOLD) { 
                    const msg = getNextMessage(); 
                    showBubble(msg, 'speech'); 
                    nextEvt = time + 15; 
                } else { nextEvt = time + 2; }
            }
        }
        
        else if (robotState === 'exploding') { parts.forEach(p => { p.position.add(p.userData.velocity); p.rotation.x += 0.05; p.userData.velocity.multiplyScalar(0.98); }); }
        else if (robotState === 'reassembling') {
            let finished = true;
            parts.forEach(p => { p.position.lerp(p.userData.origPos, 0.1); if (p.position.distanceTo(p.userData.origPos) > 0.05) finished = false; });
            if(finished) { parts.forEach(p => { p.position.copy(p.userData.origPos); p.rotation.copy(p.userData.origRot); }); robotState = 'infinite_loop'; nextEvt = time + 5; pickNewTarget(); }
        }
        else if (robotState === 'dancing' || robotState === 'dancing_intro') {
            robotGroup.rotation.y += 0.15; robotGroup.position.y = Math.abs(Math.sin(time * 5)) * 0.5; 
        }
        else if (robotState === 'posing') {
            robotGroup.rotation.y = 0; robotGroup.rotation.z = Math.sin(time * 2) * 0.1; isWaving = true; 
        }
        
        if (isWaving && robotState !== 'exploding' && robotState !== 'reassembling') {
            armLGroup.rotation.z = Math.sin(time * 10) * 0.5; armRGroup.rotation.z = -Math.sin(time * 10) * 0.5;
        } else {
            armLGroup.rotation.copy(armLGroup.userData.origRot); armRGroup.rotation.copy(armRGroup.userData.origRot);
        }

        if(bubbleEl && bubbleEl.style.opacity == 1) {
            if (isImpulsing || Math.abs(robotGroup.position.x) > MUTE_LIMIT_X) {
                bubbleEl.style.opacity = 0;
            } else {
                const headPos = robotGroup.position.clone(); headPos.y += 1.3; headPos.project(camera);
                const bX = (headPos.x * 0.5 + 0.5) * window.innerWidth;
                const bY = (headPos.y * -0.5 + 0.5) * window.innerHeight;
                let leftPos = (bX - bubbleEl.offsetWidth / 2);
                bubbleEl.style.left = leftPos + 'px';
                bubbleEl.style.top = (bY - bubbleEl.offsetHeight - 25) + 'px';
                if(parseFloat(bubbleEl.style.top) < 140) bubbleEl.style.top = '140px';
            }
        }
        
        lastPos.copy(robotGroup.position);
        renderer.render(scene, camera); 
    }
    animate();
}
