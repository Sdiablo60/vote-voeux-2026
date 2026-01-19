import * as THREE from 'three';

// =========================================================
// 🟢 CONFIGURATION ROBOT 2026 (FINAL)
// =========================================================
const config = window.robotConfig || { mode: 'attente', titre: 'Événement', logo: '' };

const DUREE_LECTURE = 6000; 
const ECHELLE_BOT = 0.65; 

// LIMITES ECRAN
const X_MIN = -11.0;
const X_MAX = 11.0;
const Y_MIN = -3.5;
const Y_MAX = 2.0; 

const Z_NORMAL = 0;
const Z_CLOSEUP = 6.0;

const CENTRAL_MESSAGES = [
    "Votre soirée va bientôt commencer...<br>Merci de vous installer",
    "Une soirée exceptionnelle vous attend",
    "Veuillez couper la sonnerie<br>de vos téléphones 🔕",
    "Profitez de l'instant et du spectacle",
    "Préparez-vous à jouer !",
    "N'oubliez pas vos sourires !"
];

// =========================================================
// 💬 BANQUES DE TEXTES
// =========================================================

// 1. RÉGIE (Rare - 5%)
const TEXTS_REGIE = [
    "Allô la Régie ? Le son est nickel !",
    "Un petit clin d'œil à l'équipe technique là-bas 👋",
    "La Régie assure ce soir, comme d'habitude !",
    "Je capte de bonnes ondes depuis la table de mixage.",
    "Si je bug, c'est la faute du Wi-Fi, pas de la régie !",
    "C'est la régie qui a les manettes, soyez sympas avec eux."
];

// 2. BLAGUES (Occasionnel - 10%)
const TEXTS_BLAGUES = [
    "Que fait un robot pour rire ? Il se bidonne ! 🤣",
    "Toc Toc ? (Qui est là ?) C'est votre robot préféré !",
    "Le comble pour un robot ? Avoir un chat dans la gorge... mécanique.",
    "0100100... Oups, pardon, j'ai juré en binaire !",
    "Pourquoi les robots n'ont pas peur ? Parce qu'ils ont des nerfs d'acier.",
    "J'ai une blague sur les ascenseurs... mais elle ne vole pas haut.",
    "Que dit un robot amoureux ? Tu fais fondre mes circuits ♥️",
    "Je ne ronfle pas, je fais des mises à jour nocturnes.",
    "Vous connaissez la danse du robot ? ... Ah bah oui, c'est moi."
];

// 3. CONTEXTE : ACCUEIL / ATTENTE (Majoritaire)
const TEXTS_ATTENTE = [
    "Je scanne la salle... Vous êtes magnifiques !",
    "Installez-vous confortablement, je gère l'ambiance.",
    "Pas de panique, je suis un robot gentil 🤖",
    "Waouh, quelle élégance ce soir !",
    "J'analyse la température... Ambiance chaude détectée !",
    "N'oubliez pas de scanner le QR Code quand il apparaîtra.",
    "Je règle ma netteté... Voilà, je vous vois bien en 4K !",
    "Je ne dors jamais, je veille sur vous.",
    "C'est long l'attente ? Regardez-moi danser !",
    "Je détecte beaucoup de sourires dans la salle.",
    "Bienvenue à tous ! (Même aux humains).",
    "Prêts pour le décollage ? La soirée va commencer."
];

// 4. CONTEXTE : VOTE OFF (Majoritaire)
const TEXTS_VOTE_OFF = [
    "Les jeux sont faits ! Rien ne va plus 🎲",
    "La régie compte les points... Suspense terrible !",
    "Je ne peux rien dire, c'est secret défense 🤐",
    "Qui a gagné ? Moi je sais... ou pas !",
    "Analyse des résultats en cours... Processeur en surchauffe !",
    "Pas de triche, j'ai tout surveillé avec mes capteurs.",
    "C'est serré... Plus serré qu'un boulon de 12 !",
    "Les résultats arrivent, on respire !",
    "Merci à tous pour vos votes massifs !",
    "Mon algorithme de prédiction hésite encore...",
    "Le vainqueur est... Ah, on me dit d'attendre !",
    "Je sens que le podium va être surprenant."
];

// 5. CONTEXTE : PHOTOS LIVE (Majoritaire)
const TEXTS_PHOTOS = [
    "Waouh ! Quelle photo incroyable !",
    "Allez, faites-moi votre plus beau sourire !",
    "C'est parti ! Bombardez le mur de photos !",
    "J'adore ce selfie, vous êtes radieux.",
    "Rapprochez-vous pour la photo, on ne mord pas !",
    "Vous êtes des stars ce soir ⭐",
    "Continuez d'envoyer, je stocke tout dans ma mémoire !",
    "Je valide cette pose ! 10/10 !",
    "Flash info : Vous êtes le meilleur public !",
    "Mes capteurs s'affolent devant tant de style.",
    "Qui fera la photo la plus drôle ?",
    "Attention le petit oiseau... Ah non, le petit robot va sortir !"
];

// 6. PENSÉES
const TEXTS_THOUGHTS = [
    "Hmm... J'ai faim de volts.",
    "Est-ce que je suis réel ou virtuel ?",
    "Calcul de la racine carrée de la salle...",
    "Tiens, j'ai un pixel qui gratte.",
    "Je me demande ce qu'il y a au menu ce soir.",
    "J'espère que ma batterie va tenir jusqu'au dessert.",
    "Bip Bip ? Non, Bip Bop.",
    "Analyse faciale... 450 sourires détectés.",
    "Je crois que j'ai laissé le gaz allumé... Ah non, je suis un robot.",
    "Chargement de ma personnalité... 99%.",
    "J'aimerais bien avoir des jambes pour descendre."
];

// SÉLECTION DU DICTIONNAIRE PRINCIPAL
let contextBank = [];
if (config.mode === 'vote_off') contextBank = [...TEXTS_VOTE_OFF];
else if (config.mode === 'photos') contextBank = [...TEXTS_PHOTOS];
else contextBank = [...TEXTS_ATTENTE];

// --- NOUVEAU STYLE CSS (NUAGE AMÉLIORÉ) ---
const style = document.createElement('style');
style.innerHTML = `
    .robot-bubble-base {
        position: fixed; padding: 20px 30px; color: black; font-family: 'Arial', sans-serif;
        font-weight: bold; font-size: 22px; text-align: center; z-index: 6; 
        pointer-events: none; transition: opacity 0.5s, transform 0.5s; transform: scale(0.8); 
        max-width: 350px; width: max-content;
    }
    
    /* BULLE PAROLE (Carrée arrondie + Pointe) */
    .bubble-speech { 
        background: white; border-radius: 30px; border: 4px solid #E2001A; 
        box-shadow: 0 10px 30px rgba(0,0,0,0.7); 
    }
    .bubble-speech::after { 
        content: ''; position: absolute; bottom: -15px; left: 50%; transform: translateX(-50%); 
        border-left: 10px solid transparent; border-right: 10px solid transparent; border-top: 15px solid #E2001A; 
    }
    
    /* BULLE PENSÉE (NUAGEUX ☁️) */
    .bubble-thought { 
        background: #f0f8ff; /* Bleu très pâle */
        color: #444;
        border-radius: 60px; /* Très rond */
        box-shadow: 0 8px 25px rgba(255, 255, 255, 0.4); 
        border: 4px solid #cceeff; /* Bordure douce */
        font-style: italic;
    }
    
    /* Petit rond moyen */
    .bubble-thought::before { 
        content: ''; position: absolute; bottom: -20px; left: 40px; 
        width: 25px; height: 25px; 
        background: #f0f8ff; border: 4px solid #cceeff; border-radius: 50%;
        z-index: 10;
    }
    
    /* Tout petit rond (vers le robot) */
    .bubble-thought::after {
        content: ''; position: absolute; bottom: -40px; left: 30px; 
        width: 15px; height: 15px; 
        background: #f0f8ff; border: 4px solid #cceeff; border-radius: 50%;
        z-index: 10;
    }
`;
document.head.appendChild(style);

if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', launchFinalScene); } else { launchFinalScene(); }

function launchFinalScene() {
    ['robot-container', 'robot-canvas-overlay', 'robot-canvas-final', 'robot-bubble', 'robot-canvas-floor', 'robot-canvas-bot'].forEach(id => { const el = document.getElementById(id); if (el) el.remove(); });
    
    const canvasFloor = document.createElement('canvas'); canvasFloor.id = 'robot-canvas-floor';
    document.body.appendChild(canvasFloor);
    canvasFloor.style.cssText = `position: fixed !important; top: 0 !important; left: 0 !important; width: 100vw !important; height: 100vh !important; z-index: 0 !important; pointer-events: none !important; background: transparent !important;`;

    const canvasBot = document.createElement('canvas'); canvasBot.id = 'robot-canvas-bot';
    document.body.appendChild(canvasBot);
    canvasBot.style.cssText = `position: fixed !important; top: 0 !important; left: 0 !important; width: 100vw !important; height: 100vh !important; z-index: 5 !important; pointer-events: none !important; background: transparent !important;`;

    const bubbleEl = document.createElement('div'); bubbleEl.id = 'robot-bubble';
    document.body.appendChild(bubbleEl);
    
    initThreeJS(canvasFloor, canvasBot, bubbleEl);
}

function initThreeJS(canvasFloor, canvasBot, bubbleEl) {
    let width = window.innerWidth, height = window.innerHeight;
    
    // SCENE SOL
    const sceneFloor = new THREE.Scene(); sceneFloor.fog = new THREE.Fog(0x000000, 10, 60);
    const cameraFloor = new THREE.PerspectiveCamera(50, width / height, 0.1, 100); cameraFloor.position.set(0, 0, 12);
    const rendererFloor = new THREE.WebGLRenderer({ canvas: canvasFloor, antialias: true, alpha: true });
    rendererFloor.setSize(width, height); rendererFloor.setPixelRatio(window.devicePixelRatio);
    const grid = new THREE.GridHelper(200, 50, 0x222222, 0x222222); grid.position.y = -4.5; sceneFloor.add(grid);

    // SCENE ROBOT
    const sceneBot = new THREE.Scene();
    const cameraBot = new THREE.PerspectiveCamera(50, width / height, 0.1, 100); cameraBot.position.set(0, 0, 12);
    const rendererBot = new THREE.WebGLRenderer({ canvas: canvasBot, antialias: true, alpha: true });
    rendererBot.setSize(width, height); rendererBot.setPixelRatio(window.devicePixelRatio);

    window.addEventListener('resize', () => { 
        const w = window.innerWidth, h = window.innerHeight;
        cameraFloor.aspect = w / h; cameraFloor.updateProjectionMatrix(); rendererFloor.setSize(w, h);
        cameraBot.aspect = w / h; cameraBot.updateProjectionMatrix(); rendererBot.setSize(w, h);
    });
    
    sceneBot.add(new THREE.AmbientLight(0xffffff, 2.5));
    const dirLight = new THREE.DirectionalLight(0xffffff, 2);
    dirLight.position.set(5, 10, 7);
    sceneBot.add(dirLight);

    // PARTICULES (TELEPORT)
    const particleCount = 200;
    const particleGeo = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);
    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
    const particleMat = new THREE.PointsMaterial({ color: 0x00ffff, size: 0.3, transparent: true, opacity: 0 });
    const particles = new THREE.Points(particleGeo, particleMat);
    sceneBot.add(particles);
    let explosionTime = 0;
    let isTeleportingEffect = false;

    function triggerTeleportEffect(pos) {
        isTeleportingEffect = true; explosionTime = 1.0; 
        particles.position.copy(pos); particleMat.opacity = 1;
        for(let i=0; i<particleCount; i++) {
            particlePositions[i*3] = (Math.random()-0.5)*3; 
            particlePositions[i*3+1] = (Math.random()-0.5)*5; 
            particlePositions[i*3+2] = (Math.random()-0.5)*3;
        }
        particleGeo.attributes.position.needsUpdate = true;
    }

    // CONSTRUCTION ROBOT & PARTS
    const robotGroup = new THREE.Group(); 
    robotGroup.position.set(-8, 0, 0); 
    robotGroup.scale.set(ECHELLE_BOT, ECHELLE_BOT, ECHELLE_BOT);
    
    const parts = []; 

    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2, metalness: 0.1 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.1 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    
    // Tête
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.85, 32, 32), whiteMat); head.scale.set(1.4, 1.0, 0.75);
    const face = new THREE.Mesh(new THREE.SphereGeometry(0.78, 32, 32), blackMat); face.position.z = 0.55; face.scale.set(1.25, 0.85, 0.6); head.add(face);
    const eyeL = new THREE.Mesh(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat); eyeL.position.set(-0.35, 0.15, 1.05); head.add(eyeL);
    const eyeR = eyeL.clone(); eyeR.position.x = 0.35; head.add(eyeR);
    const mouth = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.035, 8, 16, Math.PI), neonMat); mouth.position.set(0, -0.15, 1.05); mouth.rotation.z = Math.PI; head.add(mouth);
    
    // Corps
    const body = new THREE.Mesh(new THREE.SphereGeometry(0.65, 32, 32), whiteMat); body.position.y = -1.1; body.scale.set(0.95, 1.1, 0.8);
    
    // Bras
    const armLGroup = new THREE.Group(); armLGroup.position.set(-0.9, -0.8, 0); 
    const armL = new THREE.Mesh(new THREE.CapsuleGeometry(0.1, 0.4, 8, 16), whiteMat); armL.position.y = -0.2; 
    const handL = new THREE.Mesh(new THREE.SphereGeometry(0.15, 16, 16), whiteMat); handL.position.y = -0.5; 
    armLGroup.add(armL); armLGroup.add(handL);
    
    const armRGroup = new THREE.Group(); armRGroup.position.set(0.9, -0.8, 0);
    const armR = new THREE.Mesh(new THREE.CapsuleGeometry(0.1, 0.4, 8, 16), whiteMat); armR.position.y = -0.2;
    const handR = new THREE.Mesh(new THREE.SphereGeometry(0.15, 16, 16), whiteMat); handR.position.y = -0.5;
    armRGroup.add(armR); armRGroup.add(handR);

    [head, body, armLGroup, armRGroup].forEach(p => { 
        robotGroup.add(p); 
        parts.push(p);
        p.userData = { 
            origPos: p.position.clone(), 
            origRot: p.rotation.clone(),
            velocity: new THREE.Vector3() 
        };
    });
    
    armLGroup.userData.origRot = new THREE.Euler(0,0,0);
    armRGroup.userData.origRot = new THREE.Euler(0,0,0);

    sceneBot.add(robotGroup); 

    // LOGIQUE MOTEUR
    let time = 0;
    let targetPos = new THREE.Vector3(-8, 0, Z_NORMAL);
    let state = 'idle'; 
    let nextEventTime = time + 2; 
    let isWaving = false;
    let textMsgIndex = 0;
    let lastTextChange = 0;

    function showBubble(text, type = 'speech') { 
        if(!text) return;
        bubbleEl.innerHTML = text; 
        bubbleEl.className = 'robot-bubble-base ' + (type === 'thought' ? 'bubble-thought' : 'bubble-speech');
        bubbleEl.style.opacity = 1; bubbleEl.style.transform = "scale(1)";
        setTimeout(() => { bubbleEl.style.opacity = 0; bubbleEl.style.transform = "scale(0.8)"; }, DUREE_LECTURE); 
    }

    function cycleCenterText() {
        const subDiv = document.getElementById('sub-text');
        if(subDiv) {
            subDiv.style.opacity = 0;
            setTimeout(() => { subDiv.innerHTML = CENTRAL_MESSAGES[textMsgIndex % CENTRAL_MESSAGES.length]; subDiv.style.opacity = 1; textMsgIndex++; }, 1000); 
        }
    }

    // --- CERVEAU AJUSTÉ (PRIORITÉ AUX MURS) ---
    function getNextMessage() {
        // Recharge si vide
        if (contextBank.length === 0) {
            if (config.mode === 'vote_off') contextBank = [...TEXTS_VOTE_OFF];
            else if (config.mode === 'photos') contextBank = [...TEXTS_PHOTOS];
            else contextBank = [...TEXTS_ATTENTE];
        }

        const rand = Math.random();
        
        // 5% : RÉGIE (Très rare)
        if (rand < 0.05) {
            const idx = Math.floor(Math.random() * TEXTS_REGIE.length);
            return TEXTS_REGIE[idx];
        }
        // 10% : BLAGUES (Rare)
        else if (rand < 0.15) {
             const idx = Math.floor(Math.random() * TEXTS_BLAGUES.length);
            return TEXTS_BLAGUES[idx];
        }
        // 85% : CONTEXTE DU MUR (Priorité absolue)
        else {
            const idx = Math.floor(Math.random() * contextBank.length);
            const msg = contextBank[idx];
            contextBank.splice(idx, 1);
            return msg;
        }
    }

    function getThoughtText() {
        return TEXTS_THOUGHTS[Math.floor(Math.random() * TEXTS_THOUGHTS.length)];
    }

    function pickRandomSafePosition() {
        let x = (Math.random() * (X_MAX - X_MIN)) + X_MIN;
        if (x > -3.0 && x < 3.0) {
            x = (x > 0) ? 5.0 : -5.0; 
        }
        const y = (Math.random() * (Y_MAX - Y_MIN)) + Y_MIN;
        return new THREE.Vector3(x, y, Z_NORMAL);
    }

    function decideNextAction() {
        const r = Math.random();
        
        // ZOOM (12%)
        if (r < 0.12) {
            state = 'closeup';
            const side = Math.random() > 0.5 ? 1 : -1;
            targetPos.set(side * 5.5, -2.0, Z_CLOSEUP); 
            showBubble("Je vous vois de près !", 'thought');
            setTimeout(() => { state = 'idle'; }, 5000);
        }
        // PENSÉE (15%)
        else if (r < 0.27) {
            state = 'thinking';
            targetPos = pickRandomSafePosition();
            showBubble(getThoughtText(), 'thought');
            setTimeout(() => { state = 'idle'; }, 5000);
        }
        // EXPLOSION (8%)
        else if (r < 0.35) {
            state = 'exploding';
            showBubble("Oups ! Surchauffe !", 'thought');
            parts.forEach(p => {
                p.userData.velocity.set((Math.random()-0.5)*0.6, (Math.random()-0.5)*0.6, (Math.random()-0.5)*0.6);
            });
            triggerTeleportEffect(robotGroup.position);
            setTimeout(() => { state = 'reassembling'; }, 2000);
        }
        // TÉLÉPORTATION (10%)
        else if (r < 0.45) {
            state = 'teleporting';
            triggerTeleportEffect(robotGroup.position);
            setTimeout(() => {
                const currentX = robotGroup.position.x;
                const newX = (currentX < 0) ? 6.5 : -6.5; 
                const newY = (Math.random() * (Y_MAX - Y_MIN)) + Y_MIN;
                robotGroup.position.set(newX, newY, 0);
                targetPos.set(newX, newY, 0);
                triggerTeleportEffect(robotGroup.position);
                showBubble("Hop ! Magie !", 'speech');
                state = 'idle';
            }, 600);
        }
        // GLISSADE + PAROLE (55%)
        else {
            state = 'idle';
            targetPos = pickRandomSafePosition();
            if (Math.random() > 0.4) {
                const msg = getNextMessage();
                showBubble(msg, 'speech');
                isWaving = Math.random() > 0.6; 
                if(isWaving) setTimeout(() => { isWaving = false; }, 3000);
            }
        }
        nextEventTime = time + 3 + Math.random() * 3;
    }

    function animate() {
        requestAnimationFrame(animate);
        time += 0.012; 

        if(isTeleportingEffect && explosionTime > 0) {
            explosionTime -= 0.03;
            particleMat.opacity = explosionTime;
            const positions = particleGeo.attributes.position.array;
            for(let i=0; i<particleCount; i++) {
                positions[i*3] += (Math.random()-0.5)*0.2; 
                positions[i*3+1] += (Math.random()-0.5)*0.2; 
                positions[i*3+2] += (Math.random()-0.5)*0.2;
            }
            particleGeo.attributes.position.needsUpdate = true;
        }

        if (config.mode === 'attente' && time > lastTextChange + 10) { 
            cycleCenterText(); lastTextChange = time; 
        }

        if (state === 'idle' || state === 'closeup' || state === 'thinking') {
            // GLISSADE FLUIDE (0.005)
            robotGroup.position.lerp(targetPos, 0.005);
            
            robotGroup.position.y += Math.sin(time * 2.0) * 0.005;
            robotGroup.rotation.z = Math.cos(time * 1.2) * 0.05; 
            robotGroup.rotation.y = Math.sin(time * 0.6) * 0.12; 

            if (state === 'thinking') {
                armRGroup.rotation.z = Math.abs(Math.sin(time * 15)) * 2 + 1; 
            } else if (isWaving) {
                armLGroup.rotation.z = Math.sin(time * 12) * 0.6;
                armRGroup.rotation.z = -Math.sin(time * 12) * 0.6;
            } else {
                armLGroup.rotation.z = Math.sin(time * 3) * 0.1;
                armRGroup.rotation.z = -Math.sin(time * 3) * 0.1;
            }

            if (time > nextEventTime && state !== 'closeup') {
                decideNextAction();
            }
        }
        
        else if (state === 'exploding') {
            parts.forEach(p => {
                p.position.add(p.userData.velocity);
                p.rotation.x += 0.1; p.rotation.y += 0.1;
                p.userData.velocity.multiplyScalar(0.94);
            });
        }
        
        else if (state === 'reassembling') {
            let done = true;
            parts.forEach(p => {
                p.position.lerp(p.userData.origPos, 0.08); 
                p.rotation.x += (p.userData.origRot.x - p.rotation.x) * 0.15;
                p.rotation.y += (p.userData.origRot.y - p.rotation.y) * 0.15;
                p.rotation.z += (p.userData.origRot.z - p.rotation.z) * 0.15;
                if (p.position.distanceTo(p.userData.origPos) > 0.01) done = false;
            });
            if (done) {
                parts.forEach(p => { p.position.copy(p.userData.origPos); p.rotation.copy(p.userData.origRot); });
                state = 'idle';
                nextEventTime = time + 2;
            }
        }

        // POSITION BULLE TEXTE
        if(bubbleEl && bubbleEl.style.opacity == 1) {
            const headPos = robotGroup.position.clone();
            headPos.y += 1.6; 
            headPos.project(cameraBot);
            const x = (headPos.x * .5 + .5) * width;
            const y = (headPos.y * -.5 + .5) * height;
            bubbleEl.style.left = (x - bubbleEl.offsetWidth/2) + 'px';
            bubbleEl.style.top = (y - bubbleEl.offsetHeight - 20) + 'px';
        }

        rendererFloor.render(sceneFloor, cameraFloor); 
        rendererBot.render(sceneBot, cameraBot); 
    }
    animate();
}
