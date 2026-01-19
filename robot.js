 import * as THREE from 'three';


// =========================================================

// 🟢 CONFIGURATION ROBOT 2026 (INTELLIGENT & NON-INTRUSIF)

// =========================================================

const config = window.robotConfig || { mode: 'attente', titre: 'Événement', logo: '' };


const DUREE_LECTURE = 5500; 

const ECHELLE_BOT = 0.65; 


// LIMITES ECRAN (Le robot ne sort jamais de ces bornes)

// X : Largeur (-12 à 12)

// Y : Hauteur (-3.5 à 2.2 pour ne pas toucher le titre en haut)

const X_MIN = -11.5;

const X_MAX = 11.5;

const Y_MIN = -3.5;

const Y_MAX = 2.2; // Plafond abaissé pour ne pas cacher le titre


const Z_NORMAL = 0;

const Z_CLOSEUP = 6.5; // Proche de l'écran


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

    "Je vous observe... Vous êtes magnifiques !",

    "Je m'appelle Clap-E, votre serviteur !",

    "Pas de panique, je suis un robot gentil.",

    "Toc toc... Quelqu'un m'entend ?",

    "Vous êtes très élégants ce soir !",

    "Il fait bon ici, mes circuits sont à température optimale.",

    "J'analyse l'ambiance... Résultat : 100% !",

    "N'oubliez pas de scanner le QR Code !",

    "Je règle ma netteté... Voilà, je vous vois bien !",

    "Je ne dors jamais, je veille sur vous.",

    "C'est long l'attente ? Je suis là pour vous divertir !",

    "Je capte de bonnes ondes ici."

];


const TEXTS_VOTE_OFF = [

    // Classiques

    "Les jeux sont faits !",

    "La régie compte les points... Suspense !",

    "Je ne peux rien dire, c'est secret défense.",

    "Qui a gagné ? Moi je sais... ou pas !",

    "Analyse des résultats en cours... 📊",

    "Pas de triche, j'ai tout surveillé.",

    "C'est serré... Plus serré qu'un boulon de 12 !",

    "Ça arrive, encore un peu de patience.",

    "Merci à tous pour vos votes !",

    

    // Régie

    "Allô la Régie ? On en est où des scores ?",

    "La Régie me dit dans l'oreillette que c'est presque prêt.",

    "Hey la Régie ! N'oubliez pas de m'envoyer le vainqueur !",

    "Le grand ordinateur central chauffe pour calculer !",

    "Régie, vous me recevez ? 5 sur 5.",

    

    // Blagues

    "C'est l'histoire d'un robot qui rentre dans un bar... Et paf le bug !",

    "Que fait un robot quand il s'ennuie ? Il se range !",

    "Toc Toc ? (C'est Clap-E !)",

    "Je ne suis pas programmé pour l'impatience...",

    "Vous savez danser le Robot ? Moi oui !",

    "J'ai une blague sur les ascenseurs... mais elle ne vole pas haut.",

    "0100100... Oups pardon, je parle en binaire sous le stress."

];


const TEXTS_PHOTOS = [

    "Waouh ! Quelle photo !",

    "Allez, faites-moi un sourire !",

    "C'est parti pour la soirée !",

    "J'adore cette photo !",

    "Rapprochez-vous pour le selfie !",

    "Vous êtes des stars ce soir.",

    "Continuez d'envoyer vos photos !",

    "Je valide cette pose !",

    "Flash info : Vous êtes le meilleur public !",

    "Mes capteurs s'affolent devant tant de style."

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

        font-weight: bold; font-size: 20px; text-align: center; z-index: 6; 

        pointer-events: none; transition: opacity 0.3s, transform 0.3s; transform: scale(0.9); 

        max-width: 320px; width: max-content;

    }

    /* Bulle Parole (Carrée arrondie + Pointe) */

    .bubble-speech { background: white; border-radius: 30px; border: 4px solid #E2001A; box-shadow: 0 10px 25px rgba(0,0,0,0.6); }

    .bubble-speech::after { content: ''; position: absolute; bottom: -15px; left: 50%; transform: translateX(-50%); border-left: 10px solid transparent; border-right: 10px solid transparent; border-top: 15px solid #E2001A; }

    

    /* Bulle Pensée (Nuage + Ronds) */

    .bubble-thought { 

        background: #f0f8ff; border-radius: 40px; border: 3px solid #00aaff; 

        box-shadow: 0 10px 25px rgba(0,0,0,0.5); font-style: italic; color: #333;

    }

    .bubble-thought::before { 

        content: 'o'; position: absolute; bottom: -25px; left: 40%; 

        font-size: 30px; color: #00aaff; font-style: normal; font-weight: bold;

        text-shadow: 2px 2px 0 #fff;

    }

    .bubble-thought::after {

        content: 'o'; position: absolute; bottom: -15px; left: 45%; 

        font-size: 15px; color: #00aaff; font-style: normal; font-weight: bold;

        text-shadow: 1px 1px 0 #fff;

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

    robotGroup.position.set(-8, 0, 0); // Départ sur le coté

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


    // Ajout au groupe et sauvegarde pour explosion

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

    let targetPos = new THREE.Vector3(-8, 0, Z_NORMAL); // Cible actuelle

    let state = 'idle'; // idle, thinking, closeup, exploding, reassembling, teleporting

    let nextEventTime = time + 3; // Premier événement rapide

    let isWaving = false;

    let textMsgIndex = 0;

    let lastTextChange = 0;


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

            // Recharge

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


    function getThoughtText() {

        return TEXTS_THOUGHTS[Math.floor(Math.random() * TEXTS_THOUGHTS.length)];

    }


    // --- CERVEAU DU ROBOT ---

    function pickRandomSafePosition() {

        // X : entre MIN et MAX

        let x = (Math.random() * (X_MAX - X_MIN)) + X_MIN;

        

        // INTERDICTION CENTRE : Si X tombe entre -4 et 4, on le pousse

        if (x > -4.5 && x < 4.5) {

            x = (x > 0) ? 6.5 : -6.5; 

        }


        // Y : entre MIN et MAX

        const y = (Math.random() * (Y_MAX - Y_MIN)) + Y_MIN;

        

        return new THREE.Vector3(x, y, Z_NORMAL);

    }


    function decideNextAction() {

        const r = Math.random();

        

        // 1. ZOOM PUBLIC (15%) - Se met sur le coté pour regarder

        if (r < 0.15) {

            state = 'closeup';

            const side = Math.random() > 0.5 ? 1 : -1;

            // Se met très en avant, mais décalé (6 ou -6) pour ne pas cacher le centre

            targetPos.set(side * 7.5, -1.5, Z_CLOSEUP); 

            showBubble("Je vous vois de près !", 'thought');

            setTimeout(() => { targetPos.z = Z_NORMAL; state = 'idle'; }, 4500);

        }

        

        // 2. REFLEXION (20%)

        else if (r < 0.35) {

            state = 'thinking';

            targetPos = pickRandomSafePosition(); // Bouge doucement

            showBubble(getThoughtText(), 'thought');

            setTimeout(() => { state = 'idle'; }, 5000);

        }


        // 3. EXPLOSION (10%)

        else if (r < 0.45) {

            state = 'exploding';

            showBubble("Oups ! Surchauffe !", 'thought');

            parts.forEach(p => {

                p.userData.velocity.set((Math.random()-0.5)*0.6, (Math.random()-0.5)*0.6, (Math.random()-0.5)*0.6);

            });

            triggerTeleportEffect(robotGroup.position);

            setTimeout(() => { state = 'reassembling'; }, 2000);

        }


        // 4. TELEPORTATION (15%) - Change de coté

        else if (r < 0.60) {

            state = 'teleporting';

            triggerTeleportEffect(robotGroup.position);

            

            setTimeout(() => {

                // Si à gauche, va à droite, sinon inverse

                const currentX = robotGroup.position.x;

                const newX = (currentX < 0) ? 7.5 : -7.5; 

                const newY = (Math.random() * (Y_MAX - Y_MIN)) + Y_MIN;

                

                robotGroup.position.set(newX, newY, 0);

                targetPos.set(newX, newY, 0); // Reste là bas

                

                triggerTeleportEffect(robotGroup.position);

                showBubble("Hop ! Magie !", 'speech');

                state = 'idle';

            }, 600);

        }


        // 5. MOUVEMENT STANDARD + PAROLE (40%)

        else {

            state = 'idle';

            targetPos = pickRandomSafePosition();

            

            // Parfois parle, parfois juste bouge

            if (Math.random() > 0.3) {

                const msg = getNextMessage();

                showBubble(msg, 'speech');

                isWaving = Math.random() > 0.6; 

                if(isWaving) setTimeout(() => { isWaving = false; }, 3000);

            }

        }


        // Prochaine décision dans 5 à 9 secondes (plus dynamique)

        nextEventTime = time + 5 + Math.random() * 4;

    }


    function animate() {

        requestAnimationFrame(animate);

        time += 0.012; // Légèrement plus rapide pour fluidité


        // PARTICULES EFFECT

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


        // TEXTE CENTRAL (ATTENTE)

        if (config.mode === 'attente' && time > lastTextChange + 10) { 

            cycleCenterText(); lastTextChange = time; 

        }


        // LOGIQUE D'ETATS & MOUVEMENTS

        if (state === 'idle' || state === 'closeup' || state === 'thinking') {

            // Mouvement Fluide (Lerp) vers targetPos

            // Facteur 0.03 pour une bonne inertie

            robotGroup.position.lerp(targetPos, 0.03);

            

            // Floating effect (respiration permanente)

            robotGroup.position.y += Math.sin(time * 2.5) * 0.008;

            

            // Rotation subtile

            robotGroup.rotation.z = Math.cos(time * 1.5) * 0.08; // Tangage

            robotGroup.rotation.y = Math.sin(time * 0.8) * 0.15; // Regard gauche/droite


            if (state === 'thinking') {

                // Gratte la tête ? (Rotation rapide bras droit)

                armRGroup.rotation.z = Math.abs(Math.sin(time * 15)) * 2 + 1; 

            } else if (isWaving) {

                armLGroup.rotation.z = Math.sin(time * 12) * 0.6;

                armRGroup.rotation.z = -Math.sin(time * 12) * 0.6;

            } else {

                // Bras ballants naturels

                armLGroup.rotation.z = Math.sin(time * 3) * 0.1;

                armRGroup.rotation.z = -Math.sin(time * 3) * 0.1;

            }


            // Gestion de l'événement suivant

            if (time > nextEventTime && state !== 'closeup') {

                decideNextAction();

            }

        }

        

        else if (state === 'exploding') {

            parts.forEach(p => {

                p.position.add(p.userData.velocity);

                p.rotation.x += 0.1; p.rotation.y += 0.1;

                p.userData.velocity.multiplyScalar(0.94); // Freinage

            });

        }

        

        else if (state === 'reassembling') {

            let done = true;

            parts.forEach(p => {

                p.position.lerp(p.userData.origPos, 0.1); // Retour rapide

                p.rotation.x += (p.userData.origRot.x - p.rotation.x) * 0.15;

                p.rotation.y += (p.userData.origRot.y - p.rotation.y) * 0.15;

                p.rotation.z += (p.userData.origRot.z - p.rotation.z) * 0.15;

                

                if (p.position.distanceTo(p.userData.origPos) > 0.01) done = false;

            });

            if (done) {

                // Force reset exact

                parts.forEach(p => { p.position.copy(p.userData.origPos); p.rotation.copy(p.userData.origRot); });

                state = 'idle';

                nextEventTime = time + 2;

            }

        }


        // POSITION BULLE TEXTE (Suivi du robot)

        if(bubbleEl && bubbleEl.style.opacity == 1) {

            const headPos = robotGroup.position.clone();

            headPos.y += 1.6; // Un peu au dessus de la tête

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
