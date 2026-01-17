import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- RÉGLAGES DE COMPORTEMENT ---
const LIMITE_HAUTE_Y = 6.53; 
const DUREE_LECTURE = 7000; 
const VITESSE_MOUVEMENT = 0.008; // Réduit (anciennement 0.02) pour plus de douceur
const TEMPS_PAUSE_MIN = 4000; // Pause de 4s minimum après un trajet

// --- INJECTION DU STYLE CSS (Inchangé) ---
const style = document.createElement('style');
style.innerHTML = `
    .robot-bubble-base {
        position: fixed; padding: 15px 20px; color: black; font-family: 'Arial', sans-serif;
        font-weight: bold; font-size: 18px; text-align: center; z-index: 2147483647;
        pointer-events: none; transition: opacity 0.5s, transform 0.3s; max-width: 250px;
        display: flex; align-items: center; justify-content: center;
    }
    .bubble-speech { background: white; border-radius: 20px; border: 3px solid #E2001A; box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
    .bubble-speech::after { content: ''; position: absolute; bottom: -15px; left: 50%; transform: translateX(-50%); border-left: 10px solid transparent; border-right: 10px solid transparent; border-top: 15px solid #E2001A; }
    .bubble-thought { background: white; border-radius: 50%; border: 3px solid #00ffff; box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
    .bubble-thought::before { content: ''; position: absolute; bottom: -10px; left: 30%; width: 15px; height: 15px; background: white; border: 2px solid #00ffff; border-radius: 50%; }
    .bubble-thought::after { content: ''; position: absolute; bottom: -22px; left: 20%; width: 8px; height: 8px; background: white; border: 2px solid #00ffff; border-radius: 50%; }
`;
document.head.appendChild(style);

// --- DICTIONNAIRE (Enrichi) ---
const MESSAGES_BAG = {
    attente: [
        "Bienvenue à tous ! ✨", "Ravi de vous voir pour le " + config.titre + " !",
        "Est-ce que tout le monde est bien installé ? 🤔", "Hé la régie ! Tout est prêt ? 🚀",
        "Coucou la technique ! Vous avez pensé à mon huile ? 👷", "Je sens une énergie incroyable ici ! ⚡"
    ],
    vote_off: [
        "Les votes sont CLOS ! 🛑", "Suspens... Calcul en cours... 🧮",
        "La régie ! Ne faites pas durer le plaisir ! ⏳", "Le suspense est insoutenable... 😬"
    ],
    photos: [
        "Ouistiti ! 📸 Souriez !", "Hé la régie, envoyez des photos ! 📲",
        "Selfie time ! ✨", "Clic-clac ! J'adore cette photo ! 😍"
    ],
    reflexions: [
        "Chargement du module 'Humour' : 45%...", "Est-ce que j'ai bien éteint ma borne ? 🔋",
        "Calcul de la trajectoire d'une mouche virtuelle...", "Plus de RAM... Il me faut plus de RAM...",
        "Je me demande si les humains rêvent de moutons électriques ? 🐑"
    ],
    toctoc: ["Toc ! Toc ! Y'a quelqu'un ? 🚪", "Toc ! Toc ! Est-ce que mon écran est propre ? ✨"],
    blagues: ["Pourquoi les robots n'ont-ils jamais peur ? Nerfs d'acier ! 🦾", "Ma boisson préférée ? Le jus de douille ! 🔩"],
    explosion: ["Surchauffe ! 🔥", "Oups, j'ai perdu la tête ! 🤯"],
    cache_cache: ["Coucou ! 👋", "Me revoilà ! 🚀"]
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
    scene.add(new THREE.AmbientLight(0xffffff, 2.0));

    // --- ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
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
        p.userData = { origPos: p.position.clone(), origRot: p.rotation.clone(), velocity: new THREE.Vector3(), rotVel: new THREE.Vector3() };
        robotGroup.add(p);
    });
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
    let targetPos = new THREE.Vector3(5, 2, 0);

    function showBubble(text, type = 'speech') { 
        if(!bubble) return; 
        bubble.innerText = text;
        bubble.className = 'robot-bubble-base ' + (type === 'thought' ? 'bubble-thought' : 'bubble-speech');
        bubble.style.opacity = 1; 
        setTimeout(() => { if(bubble) bubble.style.opacity = 0; }, DUREE_LECTURE); 
    }

    function pickNewTarget() {
        const side = Math.random() > 0.5 ? 1 : -1;
        const x = side * (4.5 + Math.random() * 3); 
        const y = (Math.random() - 0.5) * 6; 
        targetPos.set(x, y, 0);
        if(targetPos.y > LIMITE_HAUTE_Y - 2.5) targetPos.y = LIMITE_HAUTE_Y - 3;
        // Fixe le moment du prochain mouvement pour créer une pause
        nextMoveTime = Date.now() + TEMPS_PAUSE_MIN + Math.random() * 4000;
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
            const introScript = [{ time: 1, text: "Bonjour !" }, { time: 5, text: "Oh, vous êtes là !" }, { time: 9, text: "Bienvenue au " + config.titre }];
            if (introIdx < introScript.length && time > introScript[introIdx].time) { showBubble(introScript[introIdx].text); introIdx++; }
            if(time > 15) { robotState = 'moving'; pickNewTarget(); nextEvt = time + 5; }
            robotGroup.position.lerp(new THREE.Vector3(4, 1, 0), VITESSE_MOUVEMENT);
        } 
        else if (robotState === 'moving' || robotState === 'approaching' || robotState === 'thinking') {
            // N'avance vers la cible que si on n'est pas en pause temporelle
            if (Date.now() > nextMoveTime || robotState === 'approaching') {
                robotGroup.position.lerp(targetPos, VITESSE_MOUVEMENT);
            }
            
            robotGroup.rotation.y = Math.sin(time)*0.2;

            if(robotGroup.position.distanceTo(targetPos) < 0.5 && robotState !== 'thinking') {
                if (robotState === 'approaching') {
                    head.rotation.x = Math.sin(time*20) * 0.2; 
                    setTimeout(() => { robotState = 'moving'; pickNewTarget(); }, 3000);
                } else if (Date.now() > nextMoveTime) {
                    pickNewTarget(); 
                }
            }

            if(time > nextEvt) {
                const r = Math.random();
                if(r < 0.08) { // EXPLOSION (Plus rare)
                    robotState = 'exploding'; showBubble(getUniqueMessage('explosion'));
                    parts.forEach(p => { p.userData.velocity.set((Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4); p.userData.rotVel.set(Math.random()*0.1, Math.random()*0.1, Math.random()*0.1); });
                    setTimeout(() => { robotState = 'reassembling'; }, 3500);
                } else if(r < 0.18) { // RÉFLEXION
                    robotState = 'thinking'; targetPos.copy(robotGroup.position);
                    showBubble(getUniqueMessage('reflexions'), 'thought');
                    setTimeout(() => { robotState = 'moving'; pickNewTarget(); }, 6000);
                } else if(r < 0.35) { // TOC TOC
                    robotState = 'approaching'; targetPos.set((Math.random()-0.5)*3, (Math.random()-0.5)*2, 7);
                    showBubble(getUniqueMessage('toctoc'));
                } else {
                    showBubble(getUniqueMessage(config.mode));
                }
                nextEvt = time + 18; // Augmentation du délai entre actions
            }
        }
        else if (robotState === 'exploding') {
            parts.forEach(p => { p.position.add(p.userData.velocity); p.rotation.x += p.userData.rotVel.x; p.userData.velocity.multiplyScalar(0.98); });
        }
        else if (robotState === 'reassembling') {
            let finished = true;
            parts.forEach(p => { p.position.lerp(p.userData.origPos, 0.1); p.rotation.x += (p.userData.origRot.x - p.rotation.x) * 0.1; if (p.position.distanceTo(p.userData.origPos) > 0.01) finished = false; });
            if(finished) { robotState = 'moving'; nextEvt = time + 2; pickNewTarget(); }
        }

        // Bulle (Calcul précis au-dessus de la tête)
        if(bubble && bubble.style.opacity == 1) {
            const headPos = robotGroup.position.clone(); headPos.y += 1.3; headPos.project(camera);
            const bX = (headPos.x * 0.5 + 0.5) * window.innerWidth;
            const bY = (headPos.y * -0.5 + 0.5) * window.innerHeight;
            bubble.style.left = (bX - bubble.offsetWidth / 2) + 'px';
            bubble.style.top = (bY - bubble.offsetHeight - 20) + 'px';
            if(parseFloat(bubble.style.top) < 140) bubble.style.top = '140px';
        }
        renderer.render(scene, camera);
    }
    animate();
}
