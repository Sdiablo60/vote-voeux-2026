import * as THREE from 'three';

// =========================================================
// 🟢 CONFIGURATION ROBOT 2026 (MOUVEMENT FLUIDE & VISIBLE)
// =========================================================
const config = window.robotConfig || { mode: 'attente', titre: 'Événement', logo: '' };

const DUREE_LECTURE = 6000; 
const ECHELLE_BOT = 0.65; 

// ZONES DE DEPLACEMENT (CAGE VIRTUELLE)
const X_LIMIT = 9.5;   
const Y_TOP = 1.9;     
const Y_BOTTOM = -2.5; 

// CONFIGURATION DU ZOOM (CLOSE-UP)
const Z_NORMAL = 0;
const Z_CLOSEUP = 5.5; 
const X_CLOSEUP_OFFSET = 4.0; // Se met à +/- 4.0 du centre (proche texte)

const CENTRAL_MESSAGES = [
    "Votre soirée va bientôt commencer...<br>Merci de vous installer",
    "Une soirée exceptionnelle vous attend",
    "Veuillez couper la sonnerie<br>de vos téléphones 🔕",
    "Profitez de l'instant et du spectacle",
    "Préparez-vous à jouer !",
    "N'oubliez pas vos sourires !"
];

// --- 1. SCÉNARIO NARRATIF (ACCUEIL) ---
const SCENARIO_ACCUEIL = [
    { type: 'thought', text: "Wouah... Quelle grande salle !", action: 'move', time: 5 },
    { type: 'thought', text: "Eh oh... Il y a quelqu'un ?", action: 'move', time: 5 },
    { type: 'thought', text: "Bon... Apparemment je suis seul.", action: 'move', time: 5 },
    { type: 'speech', text: "Oh ! Mais... Il y a un public en fait !", action: 'closeup', time: 6 }, 
    { type: 'thought', text: "Pourquoi toutes ces personnes sont réunies ?", action: 'move', time: 5 },
    { type: 'speech', text: "Bonjour ! Je m'appelle Clap-E !", action: 'wave', time: 4 },
    { type: 'speech', text: "Il y a une soirée ? Je peux me joindre à vous ?", action: 'move', time: 5 },
    { type: 'speech', text: "Chut ! Je reçois un appel de l'organisateur...", action: 'phone', time: 5 },
    { type: 'speech', text: "C'est vrai ?! C'est confirmé ?!", action: 'jump', time: 4 }, 
    { type: 'speech', text: "Incroyable ! Je suis votre animateur préféré ce soir !", action: 'move', time: 5 },
    { type: 'thought', text: "Ouhlà... Je stresse...", action: 'explode', time: 4 },
    { type: 'speech', text: "Ça va mieux ! Vous allez bien ce soir ?", action: 'move', time: 5 },
    { type: 'speech', text: "Je vous informe qu'un vote va être organisé !", action: 'move', time: 5 },
    { type: 'speech', text: "Je compte sur vous pour respecter les règles !", action: 'move', time: 5 },
    { type: 'speech', text: "Allô Régie ? Oui... D'accord.", action: 'phone', time: 4 },
    { type: 'speech', text: "La Régie me confirme : Le début est imminent !", action: 'move', time: 5 },
];

// --- 2. BANQUES DE TEXTES ---

const TEXTS_ATTENTE = [
    "Installez-vous confortablement !",
    "Je vérifie mes fiches... Ah mince, je suis numérique.",
    "Vous êtes rayonnants ce soir.",
    "J'espère que vous avez révisé pour le vote !",
    "La pression monte... ou c'est ma température ?",
    "Regardez-moi, je suis beau non ?",
    "N'oubliez pas de scanner le QR Code tout à l'heure.",
    "Je suis programmé pour mettre l'ambiance.",
    "Qui veut un autographe numérique ?",
    "Patience, ça va être génial.",
    "Je scanne la salle... 100% de bonne humeur détectée !",
    "Est-ce que ma cravate virtuelle est droite ?",
    "N'oubliez pas d'éteindre vos téléphones... Sauf pour voter !",
    "Je capte une énergie incroyable ici.",
    "Vous êtes prêts ? Moi mes circuits sont chauds !",
    "Je crois que j'ai vu quelqu'un que je connais au fond.",
    "Si je bugue, promis, c'est pas ma faute.",
    "J'ai mis mon plus beau costume de pixels pour vous."
];

const TEXTS_VOTE_OFF = [
    "Les jeux sont faits, rien ne va plus !",
    "Le bureau de vote est fermé. Clap-E a avalé la clé.",
    "Stop ! On ne touche plus à rien !",
    "Qui sera le grand gagnant ? Suspense...",
    "Merci pour votre participation massive !",
    "Je vois des chiffres défiler dans ma tête... C'est bon signe.",
    "Analyse des données : 99% terminé...",
    "Pas de panique, la technologie travaille pour vous.",
    "Le grand ordinateur central chauffe pour calculer !",
    "C'est serré... Plus serré qu'un boulon de 12 !",
    "J'espère que votre favori a gagné.",
    "Les résultats arrivent par fibre optique spéciale.",
    "Je ne suis pas corruptible, inutile d'insister !",
    "Le dépouillement est en cours...",
    "Même moi je ne connais pas encore le résultat !",
    "Quel suspense insoutenable !",
    "Ça calcule, ça calcule..."
];

const TEXTS_PHOTOS = [
    "Waouh ! Quelle photo magnifique !",
    "Celle-ci, c'est ma préférée !",
    "Allez, faites-moi votre plus beau sourire !",
    "On veut voir toute la salle sur le mur !",
    "Flash ! Ah non, c'est mon œil.",
    "Ne soyez pas timides, montrez-vous !",
    "Rapprochez-vous pour un selfie de groupe !",
    "Qui fera la grimace la plus drôle ?",
    "J'enregistre tout dans ma mémoire (et c'est du solide).",
    "Vous êtes des stars, le tapis rouge est pour vous.",
    "Envoyez vos photos, je veux voir l'ambiance !",
    "Attention, le petit oiseau va sortir... Bip Bop.",
    "Vous êtes bien plus photogéniques que mon ami le grille-pain.",
    "Encore une ! Encore une !",
    "Ça c'est de l'art moderne !",
    "Quel style ! J'adore cette pose.",
    "Vous êtes tous beaux ce soir !",
    "La caméra vous aime, et moi aussi."
];

const TEXTS_JOKES = [
    "C'est l'histoire d'un robot qui rentre dans un bar... Et paf le bug !",
    "Que fait un robot quand il s'ennuie ? Il se range !",
    "Pourquoi les plongeurs plongent-ils en arrière ? Sinon ils tombent dans le bateau.",
    "Vous connaissez la blague du petit déjeuner ? Pas de bol.",
    "Que fait une fraise sur un cheval ? Tagada Tagada !",
    "C'est l'histoire d'un pingouin qui respire par les fesses. Il s'assoit et il meurt.",
    "Quel est le comble pour un électricien ? De ne pas être au courant.",
    "Que dit un chat quand il est content ? C'est miau-gnifique.",
    "Pourquoi les poissons vivent dans l'eau salée ? Parce que le poivre les fait éternuer.",
    "Quel est le sport préféré des insectes ? Le cricket.",
    "01001110... Oups pardon, je parle en binaire pour rire.",
    "J'ai une blague sur les ascenseurs... mais elle ne vole pas haut."
];

const TEXTS_REGIE = [
    "Allô la Régie ? On en est où ?",
    "La Régie me dit dans l'oreillette que c'est presque prêt.",
    "Hey la Régie ! N'oubliez pas de m'envoyer les infos !",
    "Régie, vous me recevez ? 5 sur 5.",
    "Un instant, je fais un point technique avec la tour de contrôle.",
    "La régie me confirme que tout est sous contrôle.",
    "Allô ? Oui Régie, je transmets au public.",
    "Petit message de la régie : Vous êtes au top !",
    "La régie me demande de vérifier mes niveaux d'huile."
];

const TEXTS_THOUGHTS = [
    "Hmm... J'ai faim de volts.",
    "Est-ce que je suis réel ou virtuel ?",
    "Calcul de la racine carrée de l'univers en cours...",
    "Tiens, j'ai un pixel qui gratte.",
    "Je me demande ce qu'il y a au menu ce soir.",
    "J'espère que ma batterie va tenir.",
    "Bip Bip ? Non, Bip Bop.",
    "Analyse faciale... 450 sourires détectés.",
    "Je crois que j'ai laissé le gaz allumé... Ah non, je suis un robot.",
    "Pourquoi les humains ont-ils deux yeux ?",
    "Chargement de ma personnalité... 99%.",
    "J'aimerais bien avoir des jambes parfois."
];

let currentTextBank = [];
if (config.mode === 'vote_off') currentTextBank = [...TEXTS_VOTE_OFF];
else if (config.mode === 'photos') currentTextBank = [...TEXTS_PHOTOS];
else currentTextBank = [...TEXTS_ATTENTE];

// --- STYLE CSS ---
const style = document.createElement('style');
style.innerHTML = `
    .robot-bubble-base {
        position: fixed; padding: 18px 28px; color: black; font-family: 'Arial', sans-serif;
        font-weight: bold; font-size: 22px; text-align: center; z-index: 6; 
        pointer-events: none; transition: opacity 0.5s, transform 0.5s; transform: scale(0.9); 
        max-width: 320px; width: max-content;
    }
    .bubble-speech { background: white; border-radius: 30px; border: 4px solid #E2001A; box-shadow: 0 10px 25px rgba(0,0,0,0.6); }
    .bubble-speech::after { content: ''; position: absolute; bottom: -15px; left: 50%; transform: translateX(-50%); border-left: 10px solid transparent; border-right: 10px solid transparent; border-top: 15px solid #E2001A; }
    .bubble-thought { 
        background: #f0f8ff; border-radius: 40px; border: 3px solid #00aaff; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.5); font-style: italic; color: #333;
    }
    .bubble-thought::before { content: 'o'; position: absolute; bottom: -25px; left: 40%; font-size: 30px; color: #00aaff; font-weight: bold; text-shadow: 2px 2px 0 #fff; }
    .bubble-thought::after { content: 'o'; position: absolute; bottom: -15px; left: 45%; font-size: 15px; color: #00aaff; font-weight: bold; text-shadow: 1px 1px 0 #fff; }
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

    // PARTICULES
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

    // ROBOT
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

    // VARIABLES ETAT
    let time = 0;
    let targetPos = new THREE.Vector3(-8, 0, Z_NORMAL);
    let state = 'move'; 
    let nextEventTime = time + 3; 
    let isWaving = false, isJumping = false, isPhoning = false;
    let textMsgIndex = 0, lastTextChange = 0, scenarioIndex = 0;

    function showBubble(text, type = 'speech') { 
        if(!text) return;
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

    function getNextMessage(bank = currentTextBank) {
        if (bank.length === 0) {
            if (config.mode === 'vote_off') currentTextBank = [...TEXTS_VOTE_OFF];
            else if (config.mode === 'photos') currentTextBank = [...TEXTS_PHOTOS];
            else currentTextBank = [...TEXTS_ATTENTE];
            bank = currentTextBank;
        }
        const idx = Math.floor(Math.random() * bank.length);
        const msg = bank[idx];
        bank.splice(idx, 1);
        return msg;
    }

    function getThoughtText() { return TEXTS_THOUGHTS[Math.floor(Math.random() * TEXTS_THOUGHTS.length)]; }
    function getJokeText() { return TEXTS_JOKES[Math.floor(Math.random() * TEXTS_JOKES.length)]; }
    function getRegieText() { return TEXTS_REGIE[Math.floor(Math.random() * TEXTS_REGIE.length)]; }

    // --- CERVEAU DU ROBOT (LOGIQUE DE VOL) ---
    function pickNextSafePosition() {
        // Logique PING-PONG : Traverse l'écran
        const currentX = robotGroup.position.x;
        const goingRight = (currentX < 0);
        
        let min, max;
        // Si je suis à gauche, je vais dans la zone droite (5 à 9.5)
        if (goingRight) { min = 5.0; max = X_LIMIT; } 
        // Si je suis à droite, je vais dans la zone gauche (-9.5 à -5)
        else { min = -X_LIMIT; max = -5.0; }
        
        const x = Math.random() * (max - min) + min;
        const y = Math.random() * (Y_MAX - Y_MIN) + Y_MIN;
        return new THREE.Vector3(x, y, Z_NORMAL);
    }

    function decideNextAction() {
        // --- 1. MODE SCENARIO ---
        if (config.mode === 'attente' && scenarioIndex < SCENARIO_ACCUEIL.length) {
            const step = SCENARIO_ACCUEIL[scenarioIndex];
            showBubble(step.text, step.type);
            
            if (step.action === 'closeup') {
                state = 'closeup';
                const side = (robotGroup.position.x > 0) ? 1 : -1; 
                targetPos.set(side * X_CLOSEUP_OFFSET, -1.0, Z_CLOSEUP); 
            } else if (step.action === 'wave') {
                state = 'move'; isWaving = true; setTimeout(() => isWaving = false, 2500);
            } else if (step.action === 'jump') {
                state = 'move'; isJumping = true; setTimeout(() => isJumping = false, 2500);
            } else if (step.action === 'phone') {
                state = 'move'; isPhoning = true; setTimeout(() => isPhoning = false, 3500);
            } else if (step.action === 'explode') {
                state = 'exploding';
                parts.forEach(p => { p.userData.velocity.set((Math.random()-0.5)*0.6, (Math.random()-0.5)*0.6, (Math.random()-0.5)*0.6); });
                triggerTeleportEffect(robotGroup.position);
                setTimeout(() => { state = 'reassembling'; }, 2000);
            } else {
                state = 'move';
                targetPos = pickNextSafePosition();
            }
            scenarioIndex++;
            nextEventTime = time + step.time + 2; 
            return;
        }

        // --- 2. MODE ALEATOIRE ---
        const r = Math.random();
        
        // ZOOM PUBLIC (15%) - Se met près du centre
        if (r < 0.15) {
            state = 'closeup';
            // Determine side based on current position
            const side = (robotGroup.position.x > 0) ? 1 : -1; 
            targetPos.set(side * X_CLOSEUP_OFFSET, -1.0, Z_CLOSEUP); 
            showBubble("Je vous vois de près !", 'thought');
            
            // Force la traversée après le zoom
            setTimeout(() => { 
                state = 'move'; 
                const oppSide = (side > 0) ? -1 : 1;
                targetPos.set(oppSide * (Math.random() * 4 + 5), 0, Z_NORMAL); 
            }, 6000); // Reste un peu plus longtemps
        }
        
        // APPEL REGIE (10%)
        else if (r < 0.25) {
            state = 'move';
            targetPos = pickNextSafePosition();
            isPhoning = true; setTimeout(() => isPhoning = false, 4000);
            showBubble(getRegieText(), 'speech');
        }
        
        // REFLEXION (15%)
        else if (r < 0.40) {
            state = 'thinking';
            targetPos = pickNextSafePosition(); 
            showBubble(getThoughtText(), 'thought');
            setTimeout(() => { state = 'move'; }, 5000);
        }

        // EXPLOSION (10%)
        else if (r < 0.50) {
            state = 'exploding';
            showBubble("Oups ! Surchauffe !", 'thought');
            parts.forEach(p => { p.userData.velocity.set((Math.random()-0.5)*0.6, (Math.random()-0.5)*0.6, (Math.random()-0.5)*0.6); });
            triggerTeleportEffect(robotGroup.position);
            setTimeout(() => { state = 'reassembling'; }, 2000);
        }

        // TELEPORTATION (10%)
        else if (r < 0.60) {
            state = 'teleporting';
            triggerTeleportEffect(robotGroup.position);
            setTimeout(() => {
                const newX = (robotGroup.position.x < 0) ? (Math.random()*4 + 5) : -(Math.random()*4 + 5); 
                const newY = (Math.random() * (Y_MAX - Y_MIN)) + Y_MIN;
                robotGroup.position.set(newX, newY, 0);
                targetPos.set(newX, newY, 0); 
                triggerTeleportEffect(robotGroup.position);
                showBubble("Hop ! Magie !", 'speech');
                state = 'move';
            }, 600);
        }

        // STANDARD (40%)
        else {
            state = 'move';
            targetPos = pickNextSafePosition();
            if (Math.random() > 0.3) {
                const msg = (Math.random() > 0.8) ? getJokeText() : getNextMessage();
                showBubble(msg, 'speech');
                if (Math.random() > 0.7) { isWaving = true; setTimeout(() => isWaving = false, 3000); }
                else if (Math.random() > 0.8) { isJumping = true; setTimeout(() => isJumping = false, 2000); }
            }
        }
        nextEventTime = time + 7 + Math.random() * 3; 
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

        // --- MOUVEMENTS FLUIDES (FLYING) ---
        if (state === 'move' || state === 'closeup' || state === 'thinking') {
            // LERP VITESSE AUGMENTEE (0.015) POUR EVITER L'EFFET FIGÉ
            robotGroup.position.lerp(targetPos, 0.015);
            
            // FLOTTEMENT MARQUÉ
            robotGroup.position.y += Math.sin(time * 2.0) * 0.008; 
            
            // Rotation douce
            robotGroup.rotation.z = Math.cos(time * 1.5) * 0.05; 
            
            const diffX = targetPos.x - robotGroup.position.x;
            robotGroup.rotation.y = THREE.MathUtils.lerp(robotGroup.rotation.y, (diffX * 0.05), 0.05);

            if (isJumping) robotGroup.position.y += Math.abs(Math.sin(time * 10)) * 0.1;

            if (isPhoning) {
                armRGroup.rotation.z = 2.5; armRGroup.rotation.x = 0.5; robotGroup.rotation.z = 0.2;
            } else if (state === 'thinking') {
                armRGroup.rotation.z = Math.abs(Math.sin(time * 15)) * 2 + 1; 
            } else if (isWaving) {
                armLGroup.rotation.z = Math.sin(time * 12) * 0.6; armRGroup.rotation.z = -Math.sin(time * 12) * 0.6;
            } else {
                armLGroup.rotation.z = Math.sin(time * 3) * 0.1; armRGroup.rotation.z = -Math.sin(time * 3) * 0.1;
                armRGroup.rotation.x = 0;
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
                p.position.lerp(p.userData.origPos, 0.1); 
                p.rotation.x += (p.userData.origRot.x - p.rotation.x) * 0.15;
                p.rotation.y += (p.userData.origRot.y - p.rotation.y) * 0.15;
                p.rotation.z += (p.userData.origRot.z - p.rotation.z) * 0.15;
                if (p.position.distanceTo(p.userData.origPos) > 0.01) done = false;
            });
            if (done) {
                parts.forEach(p => { p.position.copy(p.userData.origPos); p.rotation.copy(p.userData.origRot); });
                state = 'move';
                nextEventTime = time + 2;
            }
        }

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
