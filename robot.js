import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- PARAMÈTRES DE STRUCTURE ---
const LIMITE_HAUTE_Y = 6.53; 
const DUREE_LECTURE = 7000; 
const VITESSE_MOUVEMENT = 0.008; 
const ECHELLE_BOT = 0.6; 

// --- STYLE CSS (Bulles et Nuages) ---
const style = document.createElement('style');
style.innerHTML = `
    .robot-bubble-base {
        position: fixed; padding: 15px 20px; color: black; font-family: 'Arial', sans-serif;
        font-weight: bold; font-size: 19px; text-align: center; z-index: 2147483647;
        pointer-events: none; transition: opacity 0.5; transform: scale(0.9); max-width: 280px;
    }
    .bubble-speech { background: white; border-radius: 20px; border: 3px solid #E2001A; box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
    .bubble-speech::after { content: ''; position: absolute; bottom: -15px; left: 50%; transform: translateX(-50%); border-left: 10px solid transparent; border-right: 10px solid transparent; border-top: 15px solid #E2001A; }
    .bubble-thought { background: white; border-radius: 50%; border: 3px solid #00ffff; box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
    .bubble-thought::before { content: ''; position: absolute; bottom: -10px; left: 30%; width: 15px; height: 15px; background: white; border: 2px solid #00ffff; border-radius: 50%; }
`;
document.head.appendChild(style);

// --- SCRIPT D'INTRODUCTION THÉÂTRALE (Mur Accueil uniquement) ---
const introScript = [
    { time: 1, text: "Euh... C'est quoi cet endroit ? 🧐", type: "thought" },
    { time: 5, text: "Je ne reconnais pas ces serveurs... 💾", type: "thought" },
    { time: 9, text: "Attendez une seconde...", type: "speech" },
    { time: 12, text: "OH ! Mais vous êtes là ! 😳 Bonjour !", type: "speech", action: "surprise" },
    { time: 16, text: "Pourquoi vous êtes tous réunis ce soir ? 🤔", type: "speech" },
    { time: 20, text: "Bip Bip... Un appel ? 📞", type: "speech" },
    { time: 23, text: "Allô ? La régie ? Oui c'est moi.", type: "speech" },
    { time: 27, text: "SÉRIEUX ?! Je vais être l'animateur ce soir ? 🤩", type: "speech" },
    { time: 31, text: "OK ! On va passer une soirée de folie ! ✨", type: "speech" }
];

// --- DICTIONNAIRE DE PHRASES (Mode Animateur) ---
const MESSAGES_BAG = {
    attente: [
        "N'oubliez pas, je suis votre animateur attitré ! 🤖", "Hé la régie, mon micro est bien branché ?",
        "Je sens que cette soirée va être légendaire ! ✨", "N'hésitez pas à scanner le QR code pour interagir !",
        "Je suis en train de scanner votre enthousiasme : 100% !"
    ],
    vote_off: [
        "Les votes sont clos ! En tant qu'animateur, je sens monter le suspense... 😬",
        "La régie me dit dans l'oreillette que les résultats arrivent !",
        "Qui va décrocher la victoire ce soir ? 🏆"
    ],
    photos: [
        "En tant qu'animateur, je veux voir tous vos sourires sur ce mur ! 📸",
        "Envoyez vos photos, je les analyse en temps réel ! 📲",
        "Quel photographe ce public ! ✨"
    ],
    reflexions: [
        "J'espère que mon costume en métal est bien repassé. ✨", "Animateur... ça paye bien en Gigaoctets ?",
        "La régie a l'air stressée, je vais faire une blague tout à l'heure. 🔧"
    ],
    toctoc: ["Toc ! Toc ! Est-ce que le son passe bien ? 🔊", "Toc ! Toc ! C'est moi, votre robot préféré !"]
};

const usedMessages = {};
function getUniqueMessage(category) {
    const bag = MESSAGES_BAG[category] || MESSAGES_BAG['attente'];
    if (!usedMessages[category] || usedMessages[category].length >= bag.length) usedMessages[category] = [];
    let available = bag.filter(m => !usedMessages[category].includes(m));
    let msg = available[Math.floor(Math.random() * available.length)];
    usedMessages[category].push(msg);
    return msg;
}

if (container) {
    container.style.cssText = "position:fixed; top:0; left:0; width:100vw; height:100vh; z-index:2147483647; pointer-events:none;";
    initRobot(container);
}

function initRobot(container) {
    let width = window.innerWidth, height = window.innerHeight;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 12); 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);
    scene.add(new THREE.AmbientLight(0xffffff, 2.5));

    // --- ROBOT ---
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
    parts.forEach(p => { robotGroup.add(p); p.userData.origPos = p.position.clone(); p.userData.origRot = p.rotation.clone(); p.userData.velocity = new THREE.Vector3(); });
    scene.add(robotGroup);

    // --- SPOTS ---
    const stageSpots = [];
    function createSpot(color, x, y) {
        const g = new THREE.Group(); g.position.set(x, y, 0);
        const beam = new THREE.Mesh(new THREE.ConeGeometry(0.4, 15, 32, 1, true), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false }));
        beam.rotateX(-Math.PI/2); beam.position.z = -7.5; g.add(beam);
        scene.add(g);
        return { g, beam, isOn: false, nextToggle: Math.random()*5 };
    }
    [-6, -2, 2, 6].forEach((x, i) => stageSpots.push(createSpot([0xff0000, 0x00ff00, 0x0088ff, 0xffaa00][i%4], x, LIMITE_HAUTE_Y)));

    // --- LOGIQUE ANIMATION ---
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let time = 0, nextEvt = 0, nextMoveTime = 0, introIdx = 0;
    let targetPos = new THREE.Vector3(-12, 0, -3); // Commence hors écran

    function showBubble(text, type = 'speech') { 
        if(!bubble) return; 
        bubble.innerText = text; bubble.className = 'robot-bubble-base ' + (type === 'thought' ? 'bubble-thought' : 'bubble-speech');
        bubble.style.opacity = 1; bubble.style.transform = "scale(1)";
        setTimeout(() => { if(bubble) bubble.style.opacity = 0; bubble.style.transform = "scale(0.9)"; }, DUREE_LECTURE); 
    }

    function pickNewTarget() {
        const side = Math.random() > 0.5 ? 1 : -1;
        const x = side * (4.5 + Math.random() * 3); 
        const y = (Math.random() - 0.5) * 6; 
        const z = (Math.random() * 5) - 3;
        targetPos.set(x, y, z);
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
                if(step.action === "surprise") { targetPos.set(0, 0, 7); } // Se rapproche d'un coup
                introIdx++;
            }
            if(introIdx === 1) targetPos.set(-4, 2, -2); // Entre doucement
            if(time > 35) { robotState = 'moving'; pickNewTarget(); nextEvt = time + 10; }
            robotGroup.position.lerp(targetPos, 0.015);
        } 
        else if (robotState === 'moving' || robotState === 'approaching' || robotState === 'thinking') {
            if (Date.now() > nextMoveTime || robotState === 'approaching') {
                robotGroup.position.lerp(targetPos, VITESSE_MOUVEMENT);
            }
            robotGroup.rotation.y = Math.sin(time)*0.2;

            if(robotGroup.position.distanceTo(targetPos) < 0.5 && robotState !== 'thinking') {
                if (robotState === 'approaching') {
                    head.rotation.x = Math.sin(time*20) * 0.2; 
                    setTimeout(() => { robotState = 'moving'; pickNewTarget(); }, 4000);
                } else if (Date.now() > nextMoveTime) { pickNewTarget(); }
            }

            if(time > nextEvt) {
                const r = Math.random();
                if(r < 0.08) { // Explosion
                    robotState = 'exploding'; showBubble(getUniqueMessage('explosion'));
                    parts.forEach(p => p.userData.velocity.set((Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4));
                    setTimeout(() => { robotState = 'reassembling'; }, 3500);
                } else if(r < 0.18) { // Réflexion
                    robotState = 'thinking'; targetPos.copy(robotGroup.position);
                    showBubble(getUniqueMessage('reflexions'), 'thought');
                    setTimeout(() => { robotState = 'moving'; pickNewTarget(); }, 7000);
                } else if(r < 0.35) { // Toc Toc
                    robotState = 'approaching'; targetPos.set((Math.random()-0.5)*2, (Math.random()-0.5)*2, 8);
                    showBubble(getUniqueMessage('toctoc'));
                } else {
                    showBubble(getUniqueMessage(config.mode));
                }
                nextEvt = time + 20; 
            }
        }
        else if (robotState === 'exploding') {
            parts.forEach(p => { p.position.add(p.userData.velocity); p.rotation.x += 0.05; p.userData.velocity.multiplyScalar(0.98); });
        }
        else if (robotState === 'reassembling') {
            let finished = true;
            parts.forEach(p => { p.position.lerp(p.userData.origPos, 0.1); p.rotation.x += (p.userData.origRot.x - p.rotation.x) * 0.1; if (p.position.distanceTo(p.userData.origPos) > 0.01) finished = false; });
            if(finished) { robotState = 'moving'; nextEvt = time + 2; pickNewTarget(); }
        }

        if(bubble && bubble.style.opacity == 1) {
            const headPos = robotGroup.position.clone(); headPos.y += 1.3 + (robotGroup.position.z * 0.05); headPos.project(camera);
            const bX = (headPos.x * 0.5 + 0.5) * window.innerWidth;
            const bY = (headPos.y * -0.5 + 0.5) * window.innerHeight;
            bubble.style.left = (bX - bubble.offsetWidth / 2) + 'px';
            bubble.style.top = (bY - bubble.offsetHeight - 25) + 'px';
            if(parseFloat(bubble.style.top) < 140) bubble.style.top = '140px';
        }
        renderer.render(scene, camera);
    }
    animate();
}
