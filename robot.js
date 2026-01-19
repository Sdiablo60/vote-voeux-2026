import * as THREE from 'three';

// =========================================================
// 🟢 CONFIGURATION ROBOT 2026 (FINAL - LOGIQUE MULTI-MURS)
// =========================================================
const config = window.robotConfig || { mode: 'attente', titre: 'Événement', logo: '' };

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
// 📜 SÉQUENCES PRIORITAIRES (INTRODUCTION)
// =========================================================

// --- SÉQUENCE : ACCUEIL ---
const SEQ_ACCUEIL = [
    "Bonsoir à toutes et à tous ! Je suis Clap-E, votre assistant virtuel.",
    "Quel plaisir de voir autant de monde réuni. Vous êtes tous très élégants ce soir !",
    "C'est un honneur d'apparaître sur cet écran. Mon processeur est ravi !",
    "Je ne serai pas seul : un animateur humain sera présent pour vous guider.",
    "Nous formerons un duo de choc : lui sur scène pour l'humain, et moi ici pour le digital !",
    "Voici le programme : Accueil, Votes, Analyse des scores, Podium... et Photos Live !",
    "Tout va se passer ici. Mais pour l'instant, installez-vous et profitez de l'ambiance.",
    "Je reste ici pour veiller sur vous. Excellente soirée à toutes et à tous !"
];

// --- SÉQUENCE : VOTE OFF (Annonce fermeture) ---
const SEQ_VOTE_OFF = [
    "Mesdames et Messieurs, votre attention s'il vous plaît : les votes sont officiellement clos !",
    "Merci à tous pour votre participation massive. C'était intense !",
    "Actuellement, mon processeur tourne à plein régime pour analyser les résultats.",
    "Je vérifie chaque voix, je calcule chaque point... La précision est ma devise.",
    "Le suspense est à son comble. Les vainqueurs seront révélés très bientôt.",
    "Et n'oubliez pas : une superbe soirée dansante vous attend juste après le podium !",
    "En attendant, détendez-vous, les résultats arrivent !"
];

// --- SÉQUENCE : PHOTOS LIVE (Consignes) ---
const SEQ_PHOTOS = [
    "Et maintenant, place au fun ! Le Mur Photos Live est officiellement ouvert !",
    "C'est le moment de briller ! Sortez vos smartphones et scannez le QR Code au centre.",
    "Le principe est simple : prenez une photo, validez, et hop ! Elle apparaît ici instantanément.",
    "Selfies, grimaces, photos de groupe... Lâchez-vous ! Il n'y a aucune limite de nombre.",
    "Faites vivre cet écran géant avec vos plus beaux sourires. C'est votre mur !",
    "Alors, qui sera le premier à envoyer sa photo ? Je vous regarde !"
];

// --- INITIALISATION DE LA FILE D'ATTENTE ---
let startupQueue = [];
let repeatInterval = 600; // Par défaut 10 min
let maxRepeatTime = Infinity; // Par défaut illimité

if (config.mode === 'attente') {
    startupQueue = [...SEQ_ACCUEIL];
    repeatInterval = 600; // 10 minutes
} 
else if (config.mode === 'vote_off') { // "vote_off" correspond au mode votes fermés (mais pas encore podium)
    startupQueue = [...SEQ_VOTE_OFF];
    repeatInterval = 300; // Rappel toutes les 5 minutes que c'est fini
}
else if (config.mode === 'photos') {
    startupQueue = [...SEQ_PHOTOS];
    repeatInterval = 300; // Rappel toutes les 5 minutes
    maxRepeatTime = 1800; // Arrêt des répétitions après 30 minutes
}

// =========================================================
// 💬 BANQUES DE TEXTES (ALEATOIRE - Après l'intro)
// =========================================================

const TEXTS_REGIE = [
    "Un grand merci à notre équipe technique en régie qui assure ce soir !",
    "Régie, le son est cristallin, ne changez rien !",
    "Je suis en liaison directe avec la régie... Tout est sous contrôle.",
    "Lumières, caméras, action ! La régie est au top.",
    "Si je brille autant, c'est grâce aux ingénieurs lumière !"
];

const TEXTS_BLAGUES = [
    "Vous savez pourquoi je suis un bon animateur ? J'ai un processeur Intel Core i-Humour.",
    "J'ai voulu mettre une cravate, mais elle glissait sur mon métal.",
    "Je ne transpire pas sous les projecteurs, c'est mon avantage !",
    "Une petite blague ? Que fait un robot qui a froid ? Il met un pull-over.",
    "Je suis le seul ici à ne pas boire de champagne... Juste un peu d'huile."
];

const TEXTS_ATTENTE = [
    "Mesdames, Messieurs, la magie va bientôt opérer.",
    "Je scanne la salle... Vous êtes tous rayonnants ce soir !",
    "Une soirée mémorable nous attend. Préparez-vous !",
    "Ravi de vous voir si nombreux. L'ambiance monte déjà !",
    "Je règle mes capteurs sur 'Fête'... Voilà, c'est parti !",
    "N'oubliez pas : tout à l'heure, ce sera à vous de voter !",
    "L'élégance est au rendez-vous ce soir. Félicitations à tous.",
    "Je reste ici pour veiller au bon déroulement de la soirée."
];

const TEXTS_VOTE_OFF = [
    "Analyse des données en cours... Veuillez patienter.",
    "C'est serré... Plus serré qu'un boulon de 12 !",
    "Qui seront les grands gagnants ? Le suspense est insoutenable...",
    "Nous allons bientôt connaître les résultats. Restez concentrés !",
    "Ne partez pas ! La piste de danse n'attend que vous juste après.",
    "Gardez votre énergie, la soirée dansante s'annonce grandiose !",
    "Les jeux sont faits. Que les meilleurs gagnent !",
    "Je sens l'excitation monter... Les résultats arrivent très vite.",
    "Préparez vos chaussures de danse, la nuit ne fait que commencer !"
];

const TEXTS_PHOTOS = [
    "Waouh ! Quelle photo incroyable !",
    "Allez, faites-moi votre plus beau sourire !",
    "Continuez d'envoyer, je stocke tout dans ma mémoire !",
    "C'est magique : prenez une photo, validez, et elle s'affiche ici.",
    "Immortalisez cette soirée exceptionnelle.",
    "Selfies, photos de groupe, grimaces... Tout est permis !",
    "Regardez comme vous êtes beaux sur grand écran !",
    "Allez, sortez vos téléphones et faites crépiter les flashs !",
    "J'attends vos clichés ! Montrez-nous l'ambiance de votre table.",
    "Ce mur est le vôtre. Remplissez-le de souvenirs mémorables."
];

const TEXTS_THOUGHTS = [
    "Hmm... J'espère que mon nœud papillon virtuel est droit.",
    "Je calcule le niveau de joie dans la salle... 100% !",
    "Si j'avais des jambes, j'irais danser avec eux.",
    "Tiens, cette lumière me fait un teint d'acier magnifique.",
    "Je me demande si je peux goûter aux petits fours...",
    "Bip Bop... Rechargement de ma bonne humeur... Terminé.",
    "Je n'oublierai jamais cette soirée.",
    "Analyser tant de visages heureux, c'est ma passion.",
    "J'espère qu'ils aiment ma voix de synthèse."
];

let contextBank = [];
if (config.mode === 'vote_off') contextBank = [...TEXTS_VOTE_OFF];
else if (config.mode === 'photos') contextBank = [...TEXTS_PHOTOS];
else contextBank = [...TEXTS_ATTENTE];

// --- STYLE CSS ---
const style = document.createElement('style');
style.innerHTML = `
    .robot-bubble-base {
        position: fixed; padding: 20px 30px; color: black; font-family: 'Arial', sans-serif;
        font-weight: bold; font-size: 22px; text-align: center; z-index: 6; 
        pointer-events: none; transition: opacity 0.5s, transform 0.5s; transform: scale(0.8); 
        max-width: 450px; width: max-content; line-height: 1.3;
    }
    .bubble-speech { 
        background: white; border-radius: 30px; border: 4px solid #E2001A; 
        box-shadow: 0 10px 30px rgba(0,0,0,0.7); 
    }
    .bubble-speech::after { 
        content: ''; position: absolute; bottom: -15px; left: 50%; transform: translateX(-50%); 
        border-left: 10px solid transparent; border-right: 10px solid transparent; border-top: 15px solid #E2001A; 
    }
    .bubble-thought { 
        background: #f0f8ff; color: #444; border-radius: 60px; 
        box-shadow: 0 8px 25px rgba(255, 255, 255, 0.4); 
        border: 4px solid #cceeff; font-style: italic; font-size: 20px;
    }
    .bubble-thought::before { 
        content: ''; position: absolute; bottom: -20px; left: 40px; width: 25px; height: 25px; 
        background: #f0f8ff; border: 4px solid #cceeff; border-radius: 50%; z-index: 10;
    }
    .bubble-thought::after {
        content: ''; position: absolute; bottom: -40px; left: 30px; width: 15px; height: 15px; 
        background: #f0f8ff; border: 4px solid #cceeff; border-radius: 50%; z-index: 10;
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
    
    const sceneFloor = new THREE.Scene(); sceneFloor.fog = new THREE.Fog(0x000000, 10, 60);
    const cameraFloor = new THREE.PerspectiveCamera(50, width / height, 0.1, 100); cameraFloor.position.set(0, 0, 12);
    const rendererFloor = new THREE.WebGLRenderer({ canvas: canvasFloor, antialias: true, alpha: true });
    rendererFloor.setSize(width, height); rendererFloor.setPixelRatio(window.devicePixelRatio);
    const grid = new THREE.GridHelper(200, 50, 0x222222, 0x222222); grid.position.y = -4.5; sceneFloor.add(grid);

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

    const robotGroup = new THREE.Group(); 
    robotGroup.position.set(-8, 0, 0); 
    robotGroup.scale.set(ECHELLE_BOT, ECHELLE_BOT, ECHELLE_BOT);
    
    const parts = []; 
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2, metalness: 0.1 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.1 });
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
    [head, body, armLGroup, armRGroup].forEach(p => { 
        robotGroup.add(p); parts.push(p);
        p.userData = { origPos: p.position.clone(), origRot: p.rotation.clone(), velocity: new THREE.Vector3() };
    });
    armLGroup.userData.origRot = new THREE.Euler(0,0,0);
    armRGroup.userData.origRot = new THREE.Euler(0,0,0);
    sceneBot.add(robotGroup); 

    // LOGIQUE MOTEUR ET TEMPS
    let time = 0; // Temps Animation (Vagues)
    let clock = new THREE.Clock(); // Temps Réel (Logique)
    let lastPresentationTime = 0; // Dernier temps de fin de présentation
    let targetPos = new THREE.Vector3(-8, 0, Z_NORMAL);
    let state = 'idle'; 
    let nextEventTime = 2; // Premier event à 2 sec
    let isWaving = false;
    let textMsgIndex = 0;
    let lastTextChange = 0;

    function showBubble(text, type = 'speech') { 
        if(!text) return;
        bubbleEl.innerHTML = text; 
        bubbleEl.className = 'robot-bubble-base ' + (type === 'thought' ? 'bubble-thought' : 'bubble-speech');
        bubbleEl.style.opacity = 1; bubbleEl.style.transform = "scale(1)";
        const dureeCalculee = Math.max(5000, text.length * 80);
        setTimeout(() => { 
            bubbleEl.style.opacity = 0; 
            bubbleEl.style.transform = "scale(0.8)"; 
        }, dureeCalculee); 
    }

    function cycleCenterText() {
        const subDiv = document.getElementById('sub-text');
        if(subDiv) {
            subDiv.style.opacity = 0;
            setTimeout(() => { subDiv.innerHTML = CENTRAL_MESSAGES[textMsgIndex % CENTRAL_MESSAGES.length]; subDiv.style.opacity = 1; textMsgIndex++; }, 1000); 
        }
    }

    function getNextMessage() {
        if (contextBank.length === 0) {
            if (config.mode === 'vote_off') contextBank = [...TEXTS_VOTE_OFF];
            else if (config.mode === 'photos') contextBank = [...TEXTS_PHOTOS];
            else contextBank = [...TEXTS_ATTENTE];
        }
        const rand = Math.random();
        if (rand < 0.05) return TEXTS_REGIE[Math.floor(Math.random() * TEXTS_REGIE.length)];
        else if (rand < 0.15) return TEXTS_BLAGUES[Math.floor(Math.random() * TEXTS_BLAGUES.length)];
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
        if (x > -3.0 && x < 3.0) x = (x > 0) ? 5.0 : -5.0; 
        const y = (Math.random() * (Y_MAX - Y_MIN)) + Y_MIN;
        return new THREE.Vector3(x, y, Z_NORMAL);
    }

    // --- CERVEAU INTELLIGENT ---
    function decideNextAction() {
        const elapsedTime = clock.getElapsedTime(); // Temps en secondes depuis le chargement

        // 1. GESTION DES PRÉSENTATIONS PRIORITAIRES (Multi-modes)
        // Vérifie si on doit recharger la séquence (Intervalle respecté + Pas dépassé la limite globale)
        if (startupQueue.length === 0 && 
            (elapsedTime - lastPresentationTime > repeatInterval) && 
            (elapsedTime < maxRepeatTime)) {
            
            if (config.mode === 'attente') startupQueue = [...SEQ_ACCUEIL];
            else if (config.mode === 'vote_off') startupQueue = [...SEQ_VOTE_OFF];
            else if (config.mode === 'photos') startupQueue = [...SEQ_PHOTOS];
        }

        // Si la file d'attente contient des phrases, on est en mode PRESENTATION
        if (startupQueue.length > 0) {
            state = 'presenting'; 
            const msg = startupQueue.shift();
            showBubble(msg, 'speech');
            
            targetPos = pickRandomSafePosition();
            isWaving = true; 
            setTimeout(() => { isWaving = false; }, 3000);

            if (startupQueue.length === 0) lastPresentationTime = elapsedTime;

            // Temps de lecture long pour les infos importantes
            nextEventTime = elapsedTime + 8; 
            return; // ARRÊT (VERROUILLAGE)
        }

        // 2. MODE LIBRE
        const r = Math.random();
        
        // 5% : ZOOM
        if (r < 0.05) {
            state = 'closeup';
            const side = Math.random() > 0.5 ? 1 : -1;
            targetPos.set(side * 5.5, -2.0, Z_CLOSEUP); 
            showBubble("Je vous vois de très près !", 'thought');
            setTimeout(() => { state = 'idle'; }, 5000);
        }
        // 15% : PENSÉE
        else if (r < 0.20) {
            state = 'thinking';
            targetPos = pickRandomSafePosition();
            showBubble(getThoughtText(), 'thought');
            setTimeout(() => { state = 'idle'; }, 5000);
        }
        // 3% : SURCHAUFFE
        else if (r < 0.23) {
            state = 'exploding';
            showBubble("Oups ! Surchauffe !", 'thought');
            parts.forEach(p => {
                p.userData.velocity.set((Math.random()-0.5)*0.6, (Math.random()-0.5)*0.6, (Math.random()-0.5)*0.6);
            });
            triggerTeleportEffect(robotGroup.position);
            setTimeout(() => { state = 'reassembling'; }, 2000);
        }
        // 7% : TÉLÉPORTATION
        else if (r < 0.30) {
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
        // 70% : GLISSADE + PAROLE
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
        // Prochaine action aléatoire
        nextEventTime = elapsedTime + 4 + Math.random() * 4;
    }

    function animate() {
        requestAnimationFrame(animate);
        time += 0.012; 
        const elapsedTime = clock.getElapsedTime();

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

        if (state === 'idle' || state === 'closeup' || state === 'thinking' || state === 'presenting') {
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

            // Utilisation du temps réel pour décider
            if (elapsedTime > nextEventTime && state !== 'closeup') {
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
                nextEventTime = elapsedTime + 2;
            }
        }

        if(bubbleEl && bubbleEl.style.opacity == 1) {
            const headPos = robotGroup.position.clone();
            headPos.y += 1.6; headPos.project(cameraBot);
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
