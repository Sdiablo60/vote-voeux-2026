import * as THREE from 'three';

// =========================================================
// 🟢 CONFIGURATION ROBOT 2026 (ARCHITECTURE BLINDÉE)
// =========================================================
const config = window.robotConfig || { mode: 'attente', titre: 'Événement', logo: '' };

const DUREE_BULLE = 6000; // Temps d'affichage du texte
const ECHELLE_BOT = 0.65; 

// LIMITES DEPLACEMENT
const X_LIMIT = 9.0;
const Y_TOP = 1.6;
const Y_BOTTOM = -2.5;
const Z_NORMAL = 0;
const Z_CLOSEUP = 5.5;

const SCENARIO_ACCUEIL = [
    { text: "Wouah... Quelle grande salle !", type: 'thought', act: 'move' },
    { text: "Eh oh... Il y a quelqu'un ?", type: 'thought', act: 'move' },
    { text: "Bon... Apparemment je suis seul.", type: 'thought', act: 'move' },
    { text: "Oh ! Mais... Il y a un public en fait !", type: 'speech', act: 'closeup' },
    { text: "Pourquoi toutes ces personnes sont réunies ?", type: 'thought', act: 'move' },
    { text: "Bonjour ! Je m'appelle Clap-E !", type: 'speech', act: 'wave' },
    { text: "Il y a une soirée ? Je peux me joindre à vous ?", type: 'speech', act: 'move' },
    { text: "Chut ! Je reçois un appel de l'organisateur...", type: 'speech', act: 'phone' },
    { text: "C'est vrai ?! C'est confirmé ?!", type: 'speech', act: 'jump' },
    { text: "Incroyable ! Je suis votre animateur préféré ce soir !", type: 'speech', act: 'move' },
    { text: "Ouhlà... Je stresse...", type: 'thought', act: 'explode' },
    { text: "Ça va mieux ! Vous allez bien ce soir ?", type: 'speech', act: 'move' },
    { text: "Je vous informe qu'un vote va être organisé !", type: 'speech', act: 'move' },
    { text: "Je compte sur vous pour respecter les règles !", type: 'speech', act: 'move' },
    { text: "Allô Régie ? Oui... D'accord.", type: 'speech', act: 'phone' },
    { text: "La Régie me confirme : Le début est imminent !", type: 'speech', act: 'move' }
];

// --- BANQUES DE TEXTES ---
const TEXTS_ATTENTE = [ "Installez-vous confortablement !", "Je vérifie mes fiches...", "Vous êtes rayonnants !", "Prêts pour le vote ?", "Ambiance 100% !", "Je scanne la salle...", "J'adore ce décor." ];
const TEXTS_VOTE_OFF = [ "Les jeux sont faits !", "Bureau de vote fermé.", "Calcul en cours...", "Suspense...", "Qui a gagné ?", "Pas de triche !", "La régie travaille dur." ];
const TEXTS_PHOTOS = [ "Quelle photo !", "Souriez !", "C'est ma préférée.", "Encore une !", "Vous êtes des stars.", "Flash !", "Quel style !" ];
const TEXTS_JOKES = [ "Que fait un robot qui s'ennuie ? Il se range !", "Toc toc ? C'est Clap-E !", "0100110... Oups, pardon !", "J'ai une blague sur les ascenseurs..." ];
const TEXTS_REGIE = [ "Allô la Régie ?", "Message de la technique...", "Tout est sous contrôle.", "Je vérifie mes niveaux." ];
const TEXTS_THOUGHTS = [ "J'ai faim de volts.", "Réel ou virtuel ?", "Ça gratte un pixel.", "Bip Bop...", "Analyse en cours..." ];

let currentBank = [];
if (config.mode === 'vote_off') currentBank = [...TEXTS_VOTE_OFF];
else if (config.mode === 'photos') currentBank = [...TEXTS_PHOTOS];
else currentBank = [...TEXTS_ATTENTE];

// --- CSS ---
const style = document.createElement('style');
style.innerHTML = `
    .robot-bubble-base { position: fixed; padding: 20px 30px; color: black; font-family: sans-serif; font-weight: bold; font-size: 24px; text-align: center; z-index: 10; pointer-events: none; transition: opacity 0.5s; opacity: 0; width: max-content; max-width: 350px; transform: translateX(-50%); }
    .bubble-speech { background: white; border-radius: 30px; border: 4px solid #E2001A; }
    .bubble-speech::after { content: ''; position: absolute; bottom: -15px; left: 50%; border-width: 15px 15px 0; border-style: solid; border-color: #E2001A transparent; }
    .bubble-thought { background: #f0f8ff; border-radius: 50%; border: 4px solid #00aaff; font-style: italic; }
`;
document.head.appendChild(style);

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', main);
else main();

function main() {
    // Nettoyage préventif
    ['robot-canvas-bot', 'robot-canvas-floor', 'robot-bubble'].forEach(id => { const el = document.getElementById(id); if(el) el.remove(); });

    // Création DOM
    const cvFloor = document.createElement('canvas'); cvFloor.id = 'robot-canvas-floor';
    const cvBot = document.createElement('canvas'); cvBot.id = 'robot-canvas-bot';
    const bubble = document.createElement('div'); bubble.id = 'robot-bubble'; bubble.className = 'robot-bubble-base';
    
    [cvFloor, cvBot].forEach(cv => {
        cv.style.cssText = "position:fixed; top:0; left:0; width:100vw; height:100vh; pointer-events:none;";
        document.body.appendChild(cv);
    });
    // Z-Index correct
    cvFloor.style.zIndex = "0"; cvBot.style.zIndex = "5";
    document.body.appendChild(bubble);

    init3D(cvFloor, cvBot, bubble);
}

function init3D(cvFloor, cvBot, bubble) {
    const width = window.innerWidth;
    const height = window.innerHeight;

    // --- SCENE 1 : SOL ---
    const sceneFloor = new THREE.Scene(); sceneFloor.fog = new THREE.Fog(0x000000, 10, 50);
    const camFloor = new THREE.PerspectiveCamera(50, width/height, 0.1, 100); camFloor.position.set(0, 0, 12);
    const renFloor = new THREE.WebGLRenderer({ canvas: cvFloor, alpha: true, antialias: true });
    renFloor.setSize(width, height);
    const grid = new THREE.GridHelper(200, 50, 0x333333, 0x111111); grid.position.y = -4.5;
    sceneFloor.add(grid);

    // --- SCENE 2 : ROBOT ---
    const sceneBot = new THREE.Scene();
    const camBot = new THREE.PerspectiveCamera(50, width/height, 0.1, 100); camBot.position.set(0, 0, 12);
    const renBot = new THREE.WebGLRenderer({ canvas: cvBot, alpha: true, antialias: true });
    renBot.setSize(width, height);

    const light = new THREE.DirectionalLight(0xffffff, 2); light.position.set(5, 10, 7);
    sceneBot.add(light); sceneBot.add(new THREE.AmbientLight(0xffffff, 2));

    // --- ASSEMBLAGE ROBOT ---
    const robot = new THREE.Group(); robot.scale.set(ECHELLE_BOT, ECHELLE_BOT, ECHELLE_BOT);
    // Départ sécurisé sur le coté
    robot.position.set(-8, 0, 0);
    sceneBot.add(robot);

    const matWhite = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3 });
    const matBlack = new THREE.MeshStandardMaterial({ color: 0x111111 });
    const matNeon = new THREE.MeshBasicMaterial({ color: 0x00ffff });

    const head = new THREE.Mesh(new THREE.SphereGeometry(0.85, 32, 32), matWhite);
    const face = new THREE.Mesh(new THREE.SphereGeometry(0.78, 32, 32), matBlack); face.position.z = 0.55; face.scale.set(1.2, 0.8, 0.6); head.add(face);
    const eyeL = new THREE.Mesh(new THREE.TorusGeometry(0.12, 0.04, 16, 16), matNeon); eyeL.position.set(-0.35, 0.15, 1.05); head.add(eyeL);
    const eyeR = eyeL.clone(); eyeR.position.set(0.35, 0.15, 1.05); head.add(eyeR);
    
    const body = new THREE.Mesh(new THREE.SphereGeometry(0.65, 32, 32), matWhite); body.position.y = -1.1; body.scale.set(0.95, 1.1, 0.8);
    
    const armL = new THREE.Group(); armL.position.set(-0.9, -0.8, 0);
    const armMesh = new THREE.Mesh(new THREE.CapsuleGeometry(0.1, 0.4), matWhite); armMesh.position.y = -0.2;
    armL.add(armMesh);
    const armR = armL.clone(); armR.position.set(0.9, -0.8, 0);

    robot.add(head); robot.add(body); robot.add(armL); robot.add(armR);

    // Gestion des parts pour explosion
    const parts = [head, body, armL, armR];
    parts.forEach(p => {
        p.userData = { 
            basePos: p.position.clone(), 
            baseRot: p.rotation.clone(),
            velocity: new THREE.Vector3()
        };
    });

    // PARTICULES
    const pGeo = new THREE.BufferGeometry();
    const pPos = new Float32Array(200 * 3);
    pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
    const pMat = new THREE.PointsMaterial({ color: 0x00ffff, size: 0.2, transparent: true, opacity: 0 });
    const particles = new THREE.Points(pGeo, pMat);
    sceneBot.add(particles);

    // --- LOGIQUE MOTEUR ---
    const clock = new THREE.Clock();
    let targetPos = new THREE.Vector3(-8, 0, Z_NORMAL); // Cible initiale
    let nextDecisionTime = 0; // Immédiat
    let scenarioIdx = 0;
    
    // Etats
    let isExploding = false;
    let isReassembling = false;
    let isWaving = false;
    let isJumping = false;
    let isPhoning = false;
    let isCloseup = false;

    // Helpers
    const safeRandomX = () => {
        // Ping Pong : Si à gauche, va à droite
        const side = robot.position.x < 0 ? 1 : -1;
        return side * (Math.random() * 4 + 5); // Entre 5 et 9 du coté opposé
    };
    
    const safeRandomY = () => (Math.random() * (Y_TOP - Y_BOTTOM)) + Y_BOTTOM;

    function triggerParticles(pos) {
        particles.position.copy(pos);
        pMat.opacity = 1;
        for(let i=0; i<200; i++) {
            pPos[i*3] = (Math.random()-0.5)*3;
            pPos[i*3+1] = (Math.random()-0.5)*3;
            pPos[i*3+2] = (Math.random()-0.5)*3;
        }
        pGeo.attributes.position.needsUpdate = true;
    }

    function showText(txt, type) {
        bubble.innerText = txt;
        bubble.className = type === 'thought' ? 'robot-bubble-base bubble-thought' : 'robot-bubble-base bubble-speech';
        bubble.style.opacity = 1;
        setTimeout(() => bubble.style.opacity = 0, DUREE_LECTURE);
    }

    function decide() {
        const now = clock.getElapsedTime();
        // Reset flags
        isWaving = false; isJumping = false; isPhoning = false; isCloseup = false;

        // SCENARIO ACCUEIL
        if (config.mode === 'attente' && scenarioIdx < SCENARIO_ACCUEIL.length) {
            const step = SCENARIO_ACCUEIL[scenarioIdx];
            showText(step.text, step.type);
            
            // Comportement selon action
            if (step.act === 'closeup') {
                isCloseup = true;
                const side = robot.position.x > 0 ? 1 : -1;
                targetPos.set(side * 4.5, -1.0, Z_CLOSEUP); // Approche
            } else if (step.act === 'explode') {
                isExploding = true;
                parts.forEach(p => p.userData.velocity.setRandom().subScalar(0.5).multiplyScalar(0.5));
                triggerParticles(robot.position);
                setTimeout(() => { isExploding = false; isReassembling = true; }, 2000);
            } else {
                // Mouvements standards
                if (step.act === 'wave') isWaving = true;
                if (step.act === 'jump') isJumping = true;
                if (step.act === 'phone') isPhoning = true;
                // Toujours bouger
                targetPos.set(safeRandomX(), safeRandomY(), Z_NORMAL);
            }
            
            scenarioIdx++;
            nextDecisionTime = now + 7; // 7 secondes entre chaque étape
            return;
        }

        // MODE ALEATOIRE
        const r = Math.random();
        let duration = 8;

        if (r < 0.15) { // CLOSEUP
            isCloseup = true;
            const side = robot.position.x > 0 ? 1 : -1;
            targetPos.set(side * 4.5, -1.0, Z_CLOSEUP);
            showText("Je vous vois de près !", "thought");
            duration = 7;
        } else if (r < 0.25) { // REGIE
            isPhoning = true;
            targetPos.set(safeRandomX(), safeRandomY(), Z_NORMAL);
            showText(TEXTS_REGIE[Math.floor(Math.random()*TEXTS_REGIE.length)], "speech");
        } else if (r < 0.35) { // PENSEE
            targetPos.set(safeRandomX(), safeRandomY(), Z_NORMAL);
            showText(TEXTS_THOUGHTS[Math.floor(Math.random()*TEXTS_THOUGHTS.length)], "thought");
        } else if (r < 0.45) { // EXPLOSION
            isExploding = true;
            showText("Oups ! Surchauffe !", "thought");
            parts.forEach(p => p.userData.velocity.setRandom().subScalar(0.5).multiplyScalar(0.5));
            triggerParticles(robot.position);
            setTimeout(() => { isExploding = false; isReassembling = true; }, 2000);
            duration = 5;
        } else if (r < 0.55) { // TELEPORT
            triggerParticles(robot.position);
            setTimeout(() => {
                robot.position.set(safeRandomX(), safeRandomY(), Z_NORMAL);
                targetPos.copy(robot.position); // Stop net
                triggerParticles(robot.position);
                showText("Hop ! Magie !", "speech");
            }, 500);
            duration = 4;
        } else { // STANDARD
            targetPos.set(safeRandomX(), safeRandomY(), Z_NORMAL);
            if(Math.random() > 0.4) {
                const msg = Math.random() > 0.8 ? TEXTS_JOKES : currentBank;
                showText(msg[Math.floor(Math.random()*msg.length)], "speech");
                if(Math.random() > 0.7) isWaving = true;
                else if(Math.random() > 0.8) isJumping = true;
            }
        }

        nextDecisionTime = now + duration;
    }

    function animate() {
        requestAnimationFrame(animate);
        
        const now = clock.getElapsedTime();
        const delta = 0.015; // Vitesse fixe simulation

        // UPDATE BULLE POSITION
        if (bubble.style.opacity === '1') {
            const v = head.position.clone().applyMatrix4(robot.matrixWorld);
            v.y += 1.2;
            v.project(camBot);
            const x = (v.x * .5 + .5) * width;
            const y = (-(v.y * .5) + .5) * height;
            bubble.style.left = x + 'px';
            bubble.style.top = (y - 50) + 'px';
        }

        // PARTICULES
        if (pMat.opacity > 0) {
            pMat.opacity -= 0.02;
            const pos = pGeo.attributes.position.array;
            for(let i=0; i<pos.length; i++) pos[i] += (Math.random()-0.5)*0.1;
            pGeo.attributes.position.needsUpdate = true;
        }

        // DECISION MAKING
        if (now > nextDecisionTime && !isCloseup) {
            decide();
        }
        
        // --- COMPORTEMENTS ---
        if (isExploding) {
            parts.forEach(p => {
                p.position.add(p.userData.velocity);
                p.rotation.x += 0.1;
            });
        } else if (isReassembling) {
            let done = true;
            parts.forEach(p => {
                p.position.lerp(p.userData.basePos, 0.1);
                p.rotation.x += (p.userData.baseRot.x - p.rotation.x)*0.1;
                p.rotation.y += (p.userData.baseRot.y - p.rotation.y)*0.1;
                p.rotation.z += (p.userData.baseRot.z - p.rotation.z)*0.1;
                if(p.position.distanceTo(p.userData.basePos) > 0.01) done = false;
            });
            if (done) isReassembling = false;
        } else {
            // MOUVEMENT STANDARD (Vol)
            robot.position.lerp(targetPos, 0.01); // Fluidité
            robot.position.y += Math.sin(now * 2) * 0.005; // Flottement
            
            // Rotation vers cible
            const targetRotY = (targetPos.x - robot.position.x) * 0.05;
            robot.rotation.y += (targetRotY - robot.rotation.y) * 0.05;
            robot.rotation.z = Math.cos(now) * 0.05;

            // Animations Bras
            if (isPhoning) {
                armR.rotation.z = 2.5; armR.rotation.x = 0.5;
            } else if (isWaving) {
                armL.rotation.z = Math.sin(now * 15) * 0.5;
                armR.rotation.z = -Math.sin(now * 15) * 0.5;
            } else {
                armL.rotation.z = Math.sin(now * 3) * 0.1;
                armR.rotation.z = -Math.sin(now * 3) * 0.1;
                armR.rotation.x = 0;
            }
            
            if (isJumping) robot.position.y += Math.abs(Math.sin(now * 10)) * 0.1;
        }

        renFloor.render(sceneFloor, camFloor);
        renBot.render(sceneBot, camBot);
    }

    animate();
}
