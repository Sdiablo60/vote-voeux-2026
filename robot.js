import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// --- RÉCUPÉRATION DE LA CONFIGURATION INJECTÉE PAR APP.PY ---
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- PARAMÈTRE DE BORDURE ---
const LIMITE_HAUTE_Y = 6.53; 

// --- DICTIONNAIRE DE PHRASES PAR MUR ---
const MESSAGES_BAG = {
    // 🏠 MUR ACCUEIL
    attente: [
        "Bienvenue ! ✨", 
        "Installez-vous confortablement.", 
        "Ravi de vous voir au " + config.titre + " !", 
        "La soirée va être belle !", 
        "Je vérifie les derniers réglages... 🛠️", 
        "Prêts pour le show ?",
        "J'adore l'ambiance ici !", 
        "Coucou la technique ! 👷"
    ],
    // 🔒 MUR VOTES FERMÉS
    vote_off: [
        "Les votes sont CLOS ! 🛑", 
        "Les jeux sont faits.", 
        "Le podium arrive... 🏆", 
        "Suspens... Qui va gagner ?", 
        "Calcul des scores en cours... 🧮", 
        "La régie prépare les résultats ! ⚡"
    ],
    // 📸 MUR PHOTOS LIVE
    photos: [
        "Ouistiti ! 📸", 
        "Souriez pour le mur !", 
        "On partage vos plus beaux moments ! 📲", 
        "Vous êtes magnifiques !", 
        "Selfie time ! ✨",
        "Clic-clac, c'est dans la boîte !",
        "Envoyez vos photos, je les adore !"
    ],
    // ACTIONS SPÉCIALES (Commun à tous les murs)
    explosion: [
        "Surchauffe système ! 🔥", 
        "J'ai perdu la tête... 🤯", 
        "Rassemblement magnétique... 🧲", 
        "Oups, petite erreur de calcul !"
    ],
    cache_cache: [
        "Coucou ! 👋", 
        "Me revoilà !", 
        "Magie numérique ! ⚡", 
        "Je suis partout à la fois ! 🚀"
    ]
};

const usedMessages = {};
function getUniqueMessage(category) {
    const bag = MESSAGES_BAG[category] || MESSAGES_BAG['attente'];
    if (!usedMessages[category]) usedMessages[category] = [];
    if (usedMessages[category].length >= bag.length) usedMessages[category] = [];
    
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
    { time: 7.0, text: "OH ! BONJOUR ! 😳", action: "surprise" }, 
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
    const explosionLight = new THREE.PointLight(0xffaa00, 0, 20);
    explosionLight.position.set(0, 0, 5);
    scene.add(explosionLight);

    // --- CONSTRUCTION DU ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x000000, roughness: 0.1 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.85, 32, 32), whiteMat);
    head.scale.set(1.4, 1.0, 0.75);
    const face = new THREE.Mesh(new THREE.SphereGeometry(0.78, 32, 32), blackMat);
    face.position.z = 0.55; face.scale.set(1.25, 0.85, 0.6); head.add(face);
    
    const mouth = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.035, 8, 16, Math.PI), neonMat);
    mouth.position.set(0, -0.15, 1.05); mouth.rotation.z = Math.PI; head.add(mouth);
    const eyeL = new THREE.Mesh(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat);
    eyeL.position.set(-0.35, 0.15, 1.05); head.add(eyeL);
    const eyeR = eyeL.clone(); eyeR.position.x = 0.35; head.add(eyeR);

    const body = new THREE.Mesh(new THREE.SphereGeometry(0.65, 32, 32), whiteMat);
    body.position.y = -1.1; body.scale.set(0.95, 1.1, 0.8);
    
    const leftArm = new THREE.Mesh(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat);
    leftArm.position.set(-0.8, -0.8, 0); leftArm.rotation.z = 0.15;
    const rightArm = new THREE.Mesh(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat);
    rightArm.position.set(0.8, -0.8, 0); rightArm.rotation.z = -0.15;

    [head, body, leftArm, rightArm].forEach(p => {
        p.userData = { origPos: p.position.clone(), origRot: p.rotation.clone(), velocity: new THREE.Vector3() };
    });
    robotGroup.add(head); robotGroup.add(body); robotGroup.add(leftArm); robotGroup.add(rightArm);
    scene.add(robotGroup);
    const parts = [head, body, leftArm, rightArm];

    // --- SPOTS SCÈNE (AVEC BORDURE VALIDÉE 6.53) ---
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
    let time = 0, targetPos = new THREE.Vector3(-15, 0, 0), robotState = 'intro', introIdx = 0, nextEvt = 0;

    function showBubble(text, duration) { 
        if(!bubble) return; 
        bubble.innerText = text; bubble.style.opacity = 1; 
        setTimeout(() => { if(bubble) bubble.style.opacity = 0; }, duration); 
    }

    function animate() {
        requestAnimationFrame(animate);
        time += 0.015;

        // Spots Update
        stageSpots.forEach(s => {
            if(time > s.nextToggle) { s.isOn = !s.isOn; s.nextToggle = time + Math.random()*3 + 1; }
            s.beam.material.opacity += ((s.isOn ? 0.15 : 0) - s.beam.material.opacity) * 0.1;
            s.g.lookAt(robotGroup.position);
        });

        if (robotState === 'intro') {
            const step = introScript[introIdx];
            if (step && time >= step.time) {
                if(step.text) showBubble(step.text, 3500);
                if(step.action === "enter_stage") targetPos.set(4, 0, 0);
                if(step.action === "surprise") { robotGroup.position.z = 4; robotGroup.position.y = 0.5; }
                introIdx++;
            }
            if(introIdx === introScript.length) { robotState = 'moving'; nextEvt = time + 5; }
            robotGroup.position.lerp(targetPos, 0.03);
        } 
        else if (robotState === 'moving') {
            robotGroup.position.lerp(targetPos, 0.02);
            robotGroup.rotation.y = Math.sin(time)*0.2;
            
            // Atteint la cible ?
            if(robotGroup.position.distanceTo(targetPos) < 0.5) {
                targetPos.set((Math.random()-0.5)*12, (Math.random()-0.5)*5, 0);
                // Sécurité bordure haute
                if(targetPos.y > LIMITE_HAUTE_Y - 2) targetPos.y = LIMITE_HAUTE_Y - 3;
            }

            // Événements aléatoires (Parole, Explosion, Téléport)
            if(time > nextEvt) {
                const r = Math.random();
                if(r < 0.15) { // EXPLOSION
                    robotState = 'exploding'; showBubble(getUniqueMessage('explosion'), 3000);
                    parts.forEach(p => p.userData.velocity.set((Math.random()-0.5)*0.5, (Math.random()-0.5)*0.5, (Math.random()-0.5)*0.5));
                    setTimeout(() => { robotState = 'moving'; }, 4000);
                } else if(r < 0.3) { // TÉLÉPORTATION
                    robotGroup.visible = false; showBubble(getUniqueMessage('cache_cache'), 1500);
                    setTimeout(() => { 
                        robotGroup.position.set((Math.random()-0.5)*10, (Math.random()-0.5)*5, 0); 
                        robotGroup.visible = true; robotState = 'moving'; 
                    }, 1000);
                } else { // PAROLE ADAPTÉE AU MUR
                    showBubble(getUniqueMessage(config.mode), 4000);
                }
                nextEvt = time + 10;
            }
        }
        else if (robotState === 'exploding') {
            parts.forEach(p => { p.position.add(p.userData.velocity); p.rotation.x+=0.1; });
            if(time % 4 > 3.8) parts.forEach(p => p.position.lerp(p.userData.origPos, 0.2));
        }

        // Bulle : Positionnement et sécurité
        if(bubble && bubble.style.opacity == 1) {
            const p = robotGroup.position.clone(); p.y += 1.2; p.project(camera);
            bubble.style.left = (p.x * 0.5 + 0.5) * window.innerWidth + 'px';
            let bY = (p.y * -0.5 + 0.5) * window.innerHeight;
            // Ne jamais coller la bulle au titre rouge (Y < 120px)
            bubble.style.top = (bY < 120 ? 130 : bY) + 'px';
        }
        renderer.render(scene, camera);
    }
    animate();
}
