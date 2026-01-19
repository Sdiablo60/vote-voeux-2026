import * as THREE from 'three';

// =========================================================
// 🟢 CONFIGURATION ROBOT 2026 (FINAL STABLE)
// =========================================================
const config = window.robotConfig || { mode: 'attente', titre: 'Événement', logo: '' };

// Configuration
const DUREE_LECTURE = 6000; 
const ECHELLE_BOT = 0.65; 
const X_LIMIT = 9.5;   
const Y_TOP = 1.7;     
const Y_BOTTOM = -2.8; 
const Z_NORMAL = 0;
const Z_CLOSEUP = 5.5; 
const X_CLOSEUP_OFFSET = 4.5; 

const CENTRAL_MESSAGES = [
    "Votre soirée va bientôt commencer...<br>Merci de vous installer",
    "Une soirée exceptionnelle vous attend",
    "Veuillez couper la sonnerie<br>de vos téléphones 🔕",
    "Profitez de l'instant et du spectacle",
    "Préparez-vous à jouer !",
    "N'oubliez pas vos sourires !"
];

// --- 1. BANQUES DE TEXTES ---
const TEXTS_ATTENTE = [
    "Installez-vous confortablement !", "Je vérifie mes fiches...", "Vous êtes rayonnants ce soir.",
    "J'espère que vous avez révisé !", "La pression monte...", "Regardez-moi, je suis beau non ?",
    "N'oubliez pas le QR Code.", "Je mets l'ambiance.", "Qui veut un autographe ?",
    "Patience, ça va être génial.", "Je scanne la salle... 100% bonheur !", "Est-ce que ma cravate est droite ?",
    "N'oubliez pas d'éteindre vos téléphones.", "Je capte une énergie incroyable.", "Vous êtes prêts ? Moi oui !",
    "J'ai vu quelqu'un que je connais.", "Si je bugue, c'est pas ma faute.", "J'ai mis mon beau costume."
];
const TEXTS_VOTE_OFF = [
    "Les jeux sont faits !", "Bureau de vote fermé.", "Stop ! On ne touche plus à rien !",
    "Qui sera le grand gagnant ?", "Merci pour votre participation !", "Je vois des chiffres défiler...",
    "Analyse : 99% terminé...", "La technologie travaille pour vous.", "L'ordinateur chauffe !",
    "C'est serré...", "J'espère que votre favori a gagné.", "Résultats par fibre optique.",
    "Je ne suis pas corruptible.", "Dépouillement en cours...", "Même moi je ne sais pas !",
    "Quel suspense !", "Ça calcule..."
];
const TEXTS_PHOTOS = [
    "Waouh ! Quelle photo !", "Celle-ci est ma préférée !", "Faites-moi un sourire !",
    "On veut voir toute la salle !", "Flash ! Ah non, c'est mon œil.", "Ne soyez pas timides !",
    "Selfie de groupe !", "Qui fera la grimace ?", "J'enregistre tout.",
    "Vous êtes des stars.", "Envoyez vos photos !", "Attention, le petit oiseau va sortir.",
    "Vous êtes photogéniques.", "Encore une !", "C'est de l'art moderne.",
    "Quel style !", "Vous êtes tous beaux.", "La caméra vous aime."
];
const TEXTS_JOKES = [
    "Que fait un robot qui s'ennuie ? Il se range !", "Toc toc ? C'est Clap-E !",
    "0100110... Oups pardon !", "J'ai une blague sur les ascenseurs...",
    "Pourquoi les plongeurs plongent en arrière ? Sinon plouf bateau.", "Tagada Tagada (Fraise sur cheval).",
    "Comble de l'électricien ? Pas au courant.", "Chat content ? Miau-gnifique."
];
const TEXTS_REGIE = [
    "Allô la Régie ? On en est où ?", "La Régie me dit que c'est prêt.", "Hey la Régie ! Les infos ?",
    "Régie, vous me recevez ?", "Un instant, point technique.", "La régie confirme : tout est OK.",
    "Allô ? Oui je transmets.", "Message régie : Vous êtes au top !", "Je vérifie mes niveaux d'huile."
];
const TEXTS_THOUGHTS = [
    "J'ai faim de volts.", "Réel ou virtuel ?", "Calcul de la racine carrée...",
    "Ça gratte un pixel.", "Qu'y a-t-il au menu ?", "J'espère que ma batterie tiendra.",
    "Bip Bip ? Non, Bip Bop.", "450 sourires détectés.", "J'ai laissé le gaz allumé ?",
    "Pourquoi deux yeux ?", "Chargement personnalité... 99%.", "Je voudrais des jambes."
];

let currentBank = [];
if (config.mode === 'vote_off') currentBank = [...TEXTS_VOTE_OFF];
else if (config.mode === 'photos') currentBank = [...TEXTS_PHOTOS];
else currentBank = [...TEXTS_ATTENTE];

// --- SCENARIO ACCUEIL (LINÉAIRE) ---
const SCENARIO_STEPS = [
    {t:"Wouah... Quelle grande salle !", k:'thought', a:'move'},
    {t:"Eh oh... Il y a quelqu'un ?", k:'thought', a:'move'},
    {t:"Bon... Apparemment je suis seul.", k:'thought', a:'move'},
    {t:"Oh ! Mais... Il y a un public en fait !", k:'speech', a:'closeup', d:8000},
    {t:"Pourquoi toutes ces personnes sont réunies ?", k:'thought', a:'move'},
    {t:"Bonjour ! Je m'appelle Clap-E !", k:'speech', a:'wave'},
    {t:"Il y a une soirée ? Je peux me joindre à vous ?", k:'speech', a:'move'},
    {t:"Chut ! Je reçois un appel de l'organisateur...", k:'speech', a:'phone'},
    {t:"C'est vrai ?! C'est confirmé ?!", k:'speech', a:'jump', d:4000},
    {t:"Incroyable ! Je suis votre animateur préféré ce soir !", k:'speech', a:'move'},
    {t:"Ouhlà... Je stresse...", k:'thought', a:'explode', d:5000},
    {t:"Ça va mieux ! Vous allez bien ce soir ?", k:'speech', a:'move'},
    {t:"Je vous informe qu'un vote va être organisé !", k:'speech', a:'move'},
    {t:"Je compte sur vous pour respecter les règles !", k:'speech', a:'move'},
    {t:"Allô Régie ? Oui... D'accord.", k:'speech', a:'phone'},
    {t:"La Régie me confirme : Le début est imminent !", k:'speech', a:'move'}
];

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
    // Nettoyage complet
    ['robot-canvas-bot', 'robot-canvas-floor', 'robot-bubble'].forEach(id => { const el = document.getElementById(id); if(el) el.remove(); });

    // Création
    const cvFloor = document.createElement('canvas'); cvFloor.id = 'robot-canvas-floor';
    const cvBot = document.createElement('canvas'); cvBot.id = 'robot-canvas-bot';
    const bubble = document.createElement('div'); bubble.id = 'robot-bubble'; bubble.className = 'robot-bubble-base';
    
    [cvFloor, cvBot].forEach(cv => {
        cv.style.cssText = "position:fixed; top:0; left:0; width:100vw; height:100vh; pointer-events:none;";
        document.body.appendChild(cv);
    });
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

    // --- ROBOT ---
    const robot = new THREE.Group(); 
    robot.scale.set(ECHELLE_BOT, ECHELLE_BOT, ECHELLE_BOT);
    robot.position.set(-8, 0, 0); // Départ sûr
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

    const parts = [head, body, armL, armR]; // Parts pour explosion
    parts.forEach(p => {
        p.userData = { basePos: p.position.clone(), baseRot: p.rotation.clone(), velocity: new THREE.Vector3() };
    });

    // PARTICULES
    const pGeo = new THREE.BufferGeometry();
    const pPos = new Float32Array(200 * 3);
    pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
    const pMat = new THREE.PointsMaterial({ color: 0x00ffff, size: 0.2, transparent: true, opacity: 0 });
    const particles = new THREE.Points(pGeo, pMat);
    sceneBot.add(particles);

    // --- LOGIQUE ---
    let time = 0;
    let targetPos = new THREE.Vector3(-8, 0, Z_NORMAL);
    let state = 'move'; 
    let scenarioIdx = 0;
    let textMsgIdx = 0;
    let lastCenterUpdate = 0;

    // Flags animation
    let isWaving = false, isJumping = false, isPhoning = false;
    let isExploding = false, isReassembling = false;

    // Helpers
    const safeX = () => {
        // Ping Pong : Si à gauche on va à droite
        const side = robot.position.x < 0 ? 1 : -1;
        return side * (Math.random() * 4 + 5); 
    };
    const safeY = () => (Math.random() * (Y_TOP - Y_BOTTOM)) + Y_BOTTOM;

    function triggerParticles() {
        particles.position.copy(robot.position);
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

    // CERVEAU PRINCIPAL : Appelé quand une action est FINIE
    function pickNewAction() {
        // Reset flags
        isWaving = false; isJumping = false; isPhoning = false; state = 'move';

        // 1. SCENARIO ACCUEIL
        if (config.mode === 'attente' && scenarioIdx < SCENARIO_STEPS.length) {
            const step = SCENARIO_STEPS[scenarioIdx];
            showText(step.t, step.k);
            
            let waitTime = step.d || 7000; // Temps par défaut 7s

            if (step.a === 'closeup') {
                state = 'closeup';
                const side = robot.position.x > 0 ? 1 : -1;
                targetPos.set(side * X_CLOSEUP_OFFSET, -1.0, Z_CLOSEUP);
            } else if (step.a === 'explode') {
                isExploding = true;
                parts.forEach(p => p.userData.velocity.setRandom().subScalar(0.5).multiplyScalar(0.5));
                triggerParticles();
                setTimeout(() => { isExploding = false; isReassembling = true; }, 2000);
            } else {
                targetPos.set(safeX(), safeY(), Z_NORMAL);
                if (step.a === 'wave') isWaving = true;
                if (step.a === 'jump') isJumping = true;
                if (step.a === 'phone') isPhoning = true;
            }
            
            scenarioIdx++;
            setTimeout(pickNewAction, waitTime);
            return;
        }

        // 2. MODE ALEATOIRE
        const r = Math.random();
        let duration = 8000; 

        if (r < 0.15) { // CLOSEUP
            state = 'closeup';
            const side = robot.position.x > 0 ? 1 : -1;
            targetPos.set(side * X_CLOSEUP_OFFSET, -1.0, Z_CLOSEUP);
            showText("Je vous vois de près !", "thought");
            duration = 7000;
        } else if (r < 0.25) { // REGIE
            isPhoning = true;
            targetPos.set(safeX(), safeY(), Z_NORMAL);
            showText(TEXTS_REGIE[Math.floor(Math.random()*TEXTS_REGIE.length)], "speech");
        } else if (r < 0.40) { // PENSEE
            targetPos.set(safeX(), safeY(), Z_NORMAL);
            showText(TEXTS_THOUGHTS[Math.floor(Math.random()*TEXTS_THOUGHTS.length)], "thought");
        } else if (r < 0.50) { // EXPLOSION
            isExploding = true;
            showText("Oups ! Surchauffe !", "thought");
            parts.forEach(p => p.userData.velocity.setRandom().subScalar(0.5).multiplyScalar(0.5));
            triggerParticles();
            setTimeout(() => { isExploding = false; isReassembling = true; }, 2000);
            duration = 5000;
        } else if (r < 0.60) { // TELEPORT
            triggerParticles();
            setTimeout(() => {
                robot.position.set(safeX(), safeY(), Z_NORMAL);
                targetPos.copy(robot.position);
                triggerParticles();
                showText("Hop ! Magie !", "speech");
            }, 600);
            duration = 4000;
        } else { // STANDARD
            targetPos.set(safeX(), safeY(), Z_NORMAL);
            if(Math.random() > 0.4) {
                const arr = (Math.random() > 0.8) ? TEXTS_JOKES : currentBank;
                showText(arr[Math.floor(Math.random()*arr.length)], "speech");
                if(Math.random() > 0.7) isWaving = true;
                else if(Math.random() > 0.8) isJumping = true;
            }
        }

        setTimeout(pickNewAction, duration);
    }

    // BOUCLE D'ANIMATION
    function animate() {
        requestAnimationFrame(animate);
        time += 0.01;

        // Texte Central (Accueil)
        if (config.mode === 'attente' && time > lastCenterUpdate + 10) {
            const el = document.getElementById('sub-text');
            if(el) { el.style.opacity = 0; setTimeout(() => { el.innerHTML = CENTRAL_MESSAGES[textMsgIdx++ % CENTRAL_MESSAGES.length]; el.style.opacity = 1; }, 1000); }
            lastCenterUpdate = time;
        }

        // Particules
        if (pMat.opacity > 0) {
            pMat.opacity -= 0.02;
            const pos = pGeo.attributes.position.array;
            for(let i=0; i<200; i++) pos[i] += (Math.random()-0.5)*0.1;
            pGeo.attributes.position.needsUpdate = true;
        }

        // États Spéciaux
        if (isExploding) {
            parts.forEach(p => { p.position.add(p.userData.velocity); p.rotation.x += 0.1; });
        } else if (isReassembling) {
            parts.forEach(p => {
                p.position.lerp(p.userData.basePos, 0.1);
                p.rotation.x += (p.userData.baseRot.x - p.rotation.x)*0.1;
                p.rotation.y += (p.userData.baseRot.y - p.rotation.y)*0.1;
                p.rotation.z += (p.userData.baseRot.z - p.rotation.z)*0.1;
            });
        } else {
            // MOUVEMENT STANDARD (GLISSE)
            // Lerp constant vers la cible
            robot.position.lerp(targetPos, 0.015);
            // Flottement
            robot.position.y += Math.sin(time * 2) * 0.005;
            
            // Rotation douce
            const dx = targetPos.x - robot.position.x;
            robot.rotation.y += (dx * 0.05 - robot.rotation.y) * 0.05;
            robot.rotation.z = Math.cos(time) * 0.05;

            // Animations Bras
            if (isPhoning) {
                armR.rotation.z = 2.5; armR.rotation.x = 0.5;
            } else if (isWaving) {
                armL.rotation.z = Math.sin(time * 15) * 0.5; armR.rotation.z = -Math.sin(time * 15) * 0.5;
            } else {
                armL.rotation.z = Math.sin(time * 3) * 0.1; armR.rotation.z = -Math.sin(time * 3) * 0.1; armR.rotation.x = 0;
            }
            if(isJumping) robot.position.y += Math.abs(Math.sin(time*10))*0.1;
        }

        // Bulle Position
        if (bubble.style.opacity === '1') {
            const v = head.position.clone().applyMatrix4(robot.matrixWorld);
            v.y += 1.4; v.project(camBot);
            const x = (v.x * .5 + .5) * width;
            const y = (-(v.y * .5) + .5) * height;
            bubble.style.left = x + 'px'; bubble.style.top = (y - 50) + 'px';
        }

        renFloor.render(sceneFloor, camFloor);
        renBot.render(sceneBot, camBot);
    }

    // Démarrage
    pickNewAction();
    animate();
}
