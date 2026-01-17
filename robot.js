import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- PARAMÈTRES DE STRUCTURE ---
const LIMITE_HAUTE_Y = 6.53; 
const DUREE_LECTURE = 7000; 

// --- DICTIONNAIRE GÉANT ET INTELLIGENT ---
const MESSAGES_BAG = {
    attente: [
        "Bienvenue à tous ! ✨", "Ravi de vous voir pour le " + config.titre + " !",
        "Est-ce que tout le monde est bien installé ? 🤔", "Hé la régie ! Tout est prêt pour le décollage ? 🚀",
        "Je parie que la soirée va être mémorable !", "Dites, vous trouvez que j'ai pris du poids ? C'est ma mise à jour... 🤖",
        "Coucou la technique ! Vous avez pensé à mon huile ? 👷", "Regardez-moi dans les yeux... je suis magnifique, non ?",
        "Je sens une énergie incroyable dans cette salle ! ⚡", "Régie ! Envoyez un peu de musique pour mes circuits !",
        "Si je bug, ne m'en voulez pas, je suis encore en version bêta... 😅", "Quelqu'un a le code Wi-Fi ? C'est pour un ami... 📶"
    ],
    vote_off: [
        "Les votes sont CLOS ! 🛑 Plus rien ne bouge.", "Suspens... Les chiffres remontent vers mon processeur... 🧮",
        "La régie ! On attend les résultats, ne faites pas durer le plaisir ! ⏳", "Qui va monter sur le podium selon vous ? 🤔",
        "C'était serré ! Mon ventilateur s'est emballé pendant le calcul !", "Le suspense est insoutenable... comme une batterie à 1% ! 😬",
        "Mes calculs sont formels : le gagnant est... ah, on me dit d'attendre. 🤐", "Vérification des votes en cours... Pas de triche, je vous surveille ! 👀"
    ],
    photos: [
        "Ouistiti ! 📸 Souriez pour l'éternité !", "Hé la régie, envoyez des photos ! On veut voir les sourires ! 📲",
        "Vous êtes beaucoup plus photogéniques que mon code source ! ✨", "Selfie time ! N'oubliez pas mon meilleur profil !",
        "Regardez ce mur, c'est une véritable galerie d'art ! ✨", "Clic-clac ! J'adore cette photo, qui est-ce ? 😍",
        "Mon capteur optique détecte beaucoup de bonheur ici ! 🌈", "Encore une photo ! La régie, on ne s'arrête pas !"
    ],
    toctoc: [
        "Toc ! Toc ! Y'a quelqu'un derrière cette vitre ? 🚪", "Toc ! Toc ! C'est le robot de la soirée !",
        "Toc ! Toc ! Est-ce que mon écran est propre ? ✨", "Toc ! Toc ! Vous m'entendez quand je fais ça ?"
    ],
    blagues: [
        "Pourquoi les robots n'ont-ils jamais peur ? Parce qu'ils ont des nerfs d'acier ! 🦾",
        "Que dit un robot qui a fini sa soupe ? J'en veux un r'octet ! 🥣",
        "Quelle est la boisson préférée des robots ? Le jus de douille ! 🔩",
        "Régie, vous savez pourquoi mon code est parfait ? Parce qu'il n'a pas de bugs, il a des 'fonctionnalités imprévues' !"
    ],
    explosion: [
        "Surchauffe système ! Trop d'émotions ! 🔥", "J'ai perdu la tête... littéralement ! 🤯", 
        "Oups, j'ai dû rater un point-virgule dans mon code ! 💻"
    ],
    cache_cache: [
        "Coucou ! 👋 Je suis plus rapide que la fibre !", "Me revoilà ! Vous m'avez manqué ? 🚀",
        "Hop ! On ne me voit plus... et hop ! Me revoici ! ✨"
    ]
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

// --- SCRIPT D'INTRODUCTION ---
const introScript = [
    { time: 0.0, action: "hide_start" },
    { time: 1.0, action: "enter_stage" }, 
    { time: 4.0, text: "C'est calme ici... 🤔", action: "look_around" }, 
    { time: 7.0, text: "OH ! BONJOUR ! 😳 Vous êtes nombreux !", action: "surprise" }, 
    { time: 10.0, text: "Bienvenue au " + config.titre + " ! ✨", action: "wave" },
    { time: 14.0, text: "Prêts pour la soirée ? 🎉", action: "ask" }
];

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

    // --- ANIMATION ET LOGIQUE DE ZONE ---
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let time = 0, introIdx = 0, nextEvt = 0;
    let targetPos = (robotState === 'intro') ? new THREE.Vector3(-15, 0, 0) : new THREE.Vector3(5, 2, 0);

    function showBubble(text, duration = DUREE_LECTURE) { 
        if(!bubble) return; 
        bubble.innerText = text; bubble.style.opacity = 1; 
        setTimeout(() => { if(bubble) bubble.style.opacity = 0; }, duration); 
    }

    // FONCTION CRITIQUE : Évite le centre (X: -3.5 à 3.5 / Y: -3 à 3)
    function pickNewTarget() {
        const side = Math.random() > 0.5 ? 1 : -1;
        const x = side * (4 + Math.random() * 3); // X sera soit < -4 soit > 4
        const y = (Math.random() - 0.5) * 8; 
        targetPos.set(x, y, 0);
        if(targetPos.y > LIMITE_HAUTE_Y - 2) targetPos.y = LIMITE_HAUTE_Y - 3;
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
                if(step.text) showBubble(step.text);
                if(step.action === "enter_stage") targetPos.set(5, 2, 0); // Arrive sur le côté
                if(step.action === "surprise") { robotGroup.position.z = 4; }
                introIdx++;
            }
            if(introIdx === introScript.length) { robotState = 'moving'; pickNewTarget(); nextEvt = time + 5; }
            robotGroup.position.lerp(targetPos, 0.03);
        } 
        else if (robotState === 'moving' || robotState === 'approaching') {
            robotGroup.position.lerp(targetPos, 0.02);
            robotGroup.rotation.y = Math.sin(time)*0.2;

            if(robotGroup.position.distanceTo(targetPos) < 0.5) {
                if (robotState === 'approaching') {
                    // Action "Toc Toc"
                    head.rotation.x = Math.sin(time*20) * 0.2; // Toque
                    robotState = 'moving';
                    setTimeout(() => pickNewTarget(), 3000);
                } else {
                    pickNewTarget();
                }
            }

            if(time > nextEvt) {
                const r = Math.random();
                if(r < 0.10) { // EXPLOSION
                    robotState = 'exploding'; showBubble(getUniqueMessage('explosion'));
                    parts.forEach(p => {
                        p.userData.velocity.set((Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4);
                        p.userData.rotVel.set(Math.random()*0.1, Math.random()*0.1, Math.random()*0.1);
                    });
                    setTimeout(() => { robotState = 'reassembling'; }, 3500);
                } else if(r < 0.20) { // TÉLÉPORTATION / CACHE-CACHE
                    robotGroup.visible = false; showBubble(getUniqueMessage('cache_cache'), 2000);
                    setTimeout(() => { 
                        pickNewTarget();
                        robotGroup.position.copy(targetPos);
                        robotGroup.visible = true; 
                        robotState = 'moving'; 
                    }, 1500);
                } else if(r < 0.40) { // TOC TOC (S'APPROCHE)
                    robotState = 'approaching';
                    targetPos.set((Math.random()-0.5)*4, (Math.random()-0.5)*3, 7); // Vient devant
                    showBubble(getUniqueMessage('toctoc'));
                } else if(r < 0.55) { // BLAGUE
                    showBubble(getUniqueMessage('blagues'));
                } else {
                    showBubble(getUniqueMessage(config.mode));
                }
                nextEvt = time + 14; 
            }
        }
        else if (robotState === 'exploding') {
            parts.forEach(p => { p.position.add(p.userData.velocity); p.rotation.x += p.userData.rotVel.x; p.userData.velocity.multiplyScalar(0.98); });
        }
        else if (robotState === 'reassembling') {
            let finished = true;
            parts.forEach(p => {
                p.position.lerp(p.userData.origPos, 0.1);
                p.rotation.x += (p.userData.origRot.x - p.rotation.x) * 0.1;
                if (p.position.distanceTo(p.userData.origPos) > 0.01) finished = false;
            });
            if(finished) { robotState = 'moving'; nextEvt = time + 2; }
        }

        // Bulle Position avec sécurité bords
        if(bubble && bubble.style.opacity == 1) {
            const p = robotGroup.position.clone(); if(robotState !== 'exploding') p.y += 1.2; p.project(camera);
            let bX = (p.x * 0.5 + 0.5) * window.innerWidth;
            let bY = (p.y * -0.5 + 0.5) * window.innerHeight;
            bubble.style.left = Math.min(Math.max(bX, 150), window.innerWidth - 150) + 'px';
            bubble.style.top = (bY < 130 ? 140 : bY) + 'px';
        }
        renderer.render(scene, camera);
    }
    animate();
}
