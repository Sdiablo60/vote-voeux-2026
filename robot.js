import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// --- CONFIGURATION ---
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- TEXTES (BIBLIOTHÈQUE MASSIVE POUR EVITER LES REPETITIONS) ---
const MESSAGES_BAG = {
    attente: [
        // Salutations & Accueil
        "Bienvenue à tous pour cette soirée !", "Ravi de voir autant de visages souriants.",
        "Installez-vous, détendez-vous.", "Vous êtes magnifiques ce soir !",
        "J'adore la décoration, pas vous ?", "C'est un honneur d'être votre robot.",
        "On va passer un super moment ensemble.", "Je suis programmé pour mettre l'ambiance.",
        
        // Technique / Humour
        "Test micro... Un, deux... Un, deux.", "Mes circuits sont à température optimale.",
        "Si je clignote, c'est que je réfléchis.", "J'espère qu'il y a du courant pour moi.",
        "La Régie, vous assurez grave !", "Un clin d'oeil à l'équipe technique !",
        "Je capte une super énergie ici !", "Pas de bug prévu ce soir (j'espère).",
        
        // Teasing
        "Le concours vidéo va être épique.", "Préparez vos pronostics !",
        "Qui sera le grand gagnant ?", "J'ai hâte de voir les résultats.",
        "Restez connectés, ça va commencer.", "Le spectacle va bientôt débuter."
    ],
    vote_off: [
        "Les votes sont CLOS ! 🛑", "Rien ne va plus ! 🎲", "Le podium arrive... 🏆",
        "Mais que fait la régie ? 😴", "Suspens insoutenable... 😬", 
        "Calcul des résultats en cours... 🧮", "Qui a gagné selon vous ? 🤔",
        "Patience, ça arrive... ⏳", "La régie transpire... 💦"
    ],
    photos: [
        "C'est l'heure des photos ! 📸", "Envoyez vos selfies ! 🤳",
        "Je veux être sur la photo ! 🤖", "Souriez ! 😁",
        "On partage, on partage ! 📲", "Montrez vos plus beaux profils !",
        "Allez, une petite grimace ! 🤪"
    ],
    danse: [
        "C'est l'heure de danser ! 💃", "DJ, monte le son ! 🔊",
        "Regardez mon déhanché ! 🕺", "Je suis le roi du dancefloor !",
        "Allez, tout le monde bouge !", "C'est ma chanson ! 🎶"
    ],
    explosion: [
        "Oups ! Surchauffe système ! 🔥", "J'ai perdu la tête ! 🤯",
        "Rassemblement des pièces... 🧲", "Petit bug graphique, désolé.",
        "Je me sens éparpillé..."
    ],
    intro: [
        "Tiens ? C'est calme ici...", "Oh ! Bonjour ! Je ne vous avais pas vus !",
        "Vous êtes là pour la soirée ?", "Bienvenue au " + config.titre + " !"
    ]
};

// Gestionnaire de messages uniques
const usedMessages = {};
function getUniqueMessage(category) {
    if (!MESSAGES_BAG[category]) return "...";
    if (!usedMessages[category]) usedMessages[category] = [];
    if (usedMessages[category].length >= MESSAGES_BAG[category].length) usedMessages[category] = [];
    
    let available = MESSAGES_BAG[category].filter(m => !usedMessages[category].includes(m));
    if (available.length === 0) available = MESSAGES_BAG[category]; // Fallback
    
    let msg = available[Math.floor(Math.random() * available.length)];
    usedMessages[category].push(msg);
    return msg;
}

// Séquence d'Intro Scénarisée (Arrivée progressive)
const introScript = [
    { time: 0.0, action: "hide_start" }, // Caché au début
    { time: 1.0, action: "enter_stage" }, // Entre par la gauche
    { time: 4.0, text: "Tiens ? C'est calme ici... 🤔", action: "look_around" },
    { time: 7.0, text: "OH ! BONJOUR ! 😳", action: "surprise" }, // Réalise qu'il y a du monde
    { time: 10.0, text: "Je ne vous avais pas vus ! 👋", action: "wave" },
    { time: 14.0, text: "Bienvenue à tous ! ✨", action: "present" },
    { time: 18.0, text: "Vous êtes là pour la soirée ? 🎉", action: "ask" }
];

if (container) {
    try { initRobot(container); } catch (e) { console.error(e); }
}

function initRobot(container) {
    let width = window.innerWidth;
    let height = window.innerHeight;
    
    container.style.position = 'fixed'; container.style.top = '0'; container.style.left = '0';
    container.style.width = '100%'; container.style.height = '100%';
    container.style.zIndex = '10'; container.style.pointerEvents = 'none';
    
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 8); 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // --- ECLAIRAGE DE SCENE (SPOTLIGHTS COLORÉS) ---
    const spots = [];
    const colors = [0xff0000, 0x00ff00, 0x0000ff, 0xffff00, 0xffffff]; // Rouge, Vert, Bleu, Jaune, Blanc
    
    colors.forEach((col, i) => {
        const spot = new THREE.SpotLight(col, 20); // Intensité forte
        // Position en arc de cercle au dessus
        const x = (i - 2) * 3; 
        spot.position.set(x, 6, 2);
        spot.angle = 0.5;
        spot.penumbra = 0.5;
        spot.decay = 2;
        spot.distance = 50;
        spot.castShadow = true;
        scene.add(spot);
        scene.add(spot.target); // Important pour viser
        spots.push({ light: spot, originalX: x, speed: 0.02 + Math.random() * 0.03, timeOff: Math.random() * 100 });
    });

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5); scene.add(ambientLight);

    // --- ROBOT GÉOMÉTRIQUE (CLAP-E) ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
    
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2, metalness: 0.1 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x000000, roughness: 0.1, metalness: 0.5 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff }); 
    const greyMat = new THREE.MeshStandardMaterial({ color: 0xbbbbbb });

    function createPart(geo, mat, x, y, z, parent) {
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(x, y, z);
        mesh.userData.origPos = new THREE.Vector3(x, y, z);
        mesh.userData.origRot = new THREE.Euler(0, 0, 0);
        mesh.userData.velocity = new THREE.Vector3();
        mesh.userData.rotVelocity = new THREE.Vector3();
        if(parent) parent.add(mesh);
        return mesh;
    }

    const head = createPart(new THREE.SphereGeometry(0.85, 32, 32), whiteMat, 0, 0, 0, robotGroup);
    head.scale.set(1.4, 1.0, 0.75);
    const face = createPart(new THREE.SphereGeometry(0.78, 32, 32), blackMat, 0, 0, 0.55, head);
    face.scale.set(1.25, 0.85, 0.6);
    const leftEye = createPart(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat, -0.35, 0.15, 1.05, head);
    const rightEye = createPart(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat, 0.35, 0.15, 1.05, head);
    const mouth = createPart(new THREE.TorusGeometry(0.1, 0.035, 8, 16, Math.PI), neonMat, 0, -0.15, 1.05, head);
    mouth.rotation.z = Math.PI; mouth.userData.origRot.z = Math.PI;
    const leftEar = createPart(new THREE.CylinderGeometry(0.25, 0.25, 0.1, 16), whiteMat, -1.1, 0, 0, head);
    leftEar.rotation.z = Math.PI/2; leftEar.userData.origRot.z = Math.PI/2;
    const rightEar = createPart(new THREE.CylinderGeometry(0.25, 0.25, 0.1, 16), whiteMat, 1.1, 0, 0, head);
    rightEar.rotation.z = Math.PI/2; rightEar.userData.origRot.z = Math.PI/2;

    const body = createPart(new THREE.SphereGeometry(0.65, 32, 32), whiteMat, 0, -1.1, 0, robotGroup);
    body.scale.set(0.95, 1.1, 0.8);
    const belt = createPart(new THREE.TorusGeometry(0.62, 0.03, 16, 32), greyMat, 0, 0, 0, body);
    belt.rotation.x = Math.PI/2;

    const leftArm = createPart(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat, -0.8, -0.8, 0, robotGroup);
    leftArm.rotation.z = 0.15; leftArm.userData.origRot.z = 0.15;
    const rightArm = createPart(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat, 0.8, -0.8, 0, robotGroup);
    rightArm.rotation.z = -0.15; rightArm.userData.origRot.z = -0.15;

    const parts = [head, body, leftArm, rightArm];
    scene.add(robotGroup);

    // --- VARIABLES LOGIQUES ---
    let time = 0;
    // Si c'est l'intro (Accueil), on le met hors champ à gauche
    let startX = (config.mode === 'attente') ? -15 : 4.0;
    let targetPosition = new THREE.Vector3(startX, 0, 0); 
    robotGroup.position.copy(targetPosition);
    
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let introIndex = 0;
    let nextEventTime = 0;
    let bubbleTimeout = null;

    function smoothRotate(object, axis, targetValue, speed) {
        object.rotation[axis] += (targetValue - object.rotation[axis]) * speed;
    }

    function showBubble(text, duration) {
        if(!bubble) return;
        if (bubbleTimeout) { clearTimeout(bubbleTimeout); bubbleTimeout = null; }
        bubble.innerText = text; bubble.style.opacity = 1;
        if(duration) bubbleTimeout = setTimeout(() => { if(bubble) bubble.style.opacity = 0; }, duration);
    }

    function hideBubble() { if(bubble) bubble.style.opacity = 0; }

    function pickNewTarget() {
        const aspect = width / height; const vW = 7 * aspect; 
        const side = Math.random() > 0.5 ? 1 : -1; 
        const safeMin = 3.8; const safeMax = vW * 0.55; 
        let x = side * (safeMin + Math.random() * (safeMax - safeMin));
        let y = (Math.random() - 0.5) * 4.0;
        targetPosition.set(x, y, 0);
    }

    // --- ETATS ---

    function startExplosion() {
        robotState = 'exploding';
        const msg = getUniqueMessage('explosion');
        showBubble(msg, 3500);
        
        // Centrage sécurité
        if (Math.abs(robotGroup.position.x) > 6) {
            robotGroup.position.x = (robotGroup.position.x > 0) ? 5 : -5;
        }

        setTimeout(() => {
            parts.forEach(part => {
                part.userData.velocity.set((Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4);
                part.userData.rotVelocity.set(Math.random()*0.2, Math.random()*0.2, Math.random()*0.2);
            });
            setTimeout(() => {
                robotState = 'reassembling';
                setTimeout(() => { robotState = 'moving'; pickNewTarget(); }, 2000);
            }, 3000);
        }, 1000);
    }

    function startDance() {
        // DANSE SEULEMENT SI MODE PHOTO LIVE
        if (config.mode !== 'photos') {
            startSpeaking(); // Sinon il parle juste
            return;
        }
        
        robotState = 'dancing';
        targetPosition.copy(robotGroup.position);
        const msg = getUniqueMessage('danse');
        showBubble(msg, 4000);
        
        setTimeout(() => {
            if (robotState === 'dancing') {
                hideBubble();
                robotState = 'moving';
                pickNewTarget();
            }
        }, 6000);
    }

    function startSpeaking() {
        robotState = 'speaking';
        targetPosition.copy(robotGroup.position); 
        const msg = getUniqueMessage(config.mode);
        showBubble(msg, 4000); 
        nextEventTime = time + 3 + Math.random() * 5; 
        setTimeout(() => { if (robotState === 'speaking') { hideBubble(); robotState = 'moving'; pickNewTarget(); } }, 4000);
    }

    function startTeleport() {
        robotState = 'teleporting';
        showBubble("Hop ! Magie ! ✨", 1500);
        setTimeout(() => {
            robotGroup.visible = false;
            pickNewTarget();
            robotGroup.position.copy(targetPosition);
            setTimeout(() => { robotGroup.visible = true; robotState = 'moving'; }, 1000);
        }, 500);
    }

    function updateLights() {
        spots.forEach(s => {
            // Mouvement fluide des lumières
            s.light.target.position.x = Math.sin(time + s.timeOff) * 5;
            s.light.target.position.y = Math.cos(time * s.speed + s.timeOff) * 3;
            // Elles suivent un peu le robot
            s.light.target.position.lerp(robotGroup.position, 0.05);
            s.light.target.updateMatrixWorld();
        });
    }

    // --- ANIMATION LOOP ---
    function animate() {
        requestAnimationFrame(animate);
        time += 0.015; 
        updateLights();

        if (robotState === 'intro') {
            if (introIndex < introScript.length) {
                const step = introScript[introIndex];
                if (time >= step.time) { 
                    if(step.text) showBubble(step.text, 3500); 
                    // Actions spécifiques d'intro
                    if(step.action === "hide_start") robotGroup.position.set(-15, 0, 0);
                    if(step.action === "enter_stage") targetPosition.set(4.0, 0, 0);
                    if(step.action === "look_around") {
                        smoothRotate(robotGroup, 'y', -0.5, 0.05);
                        smoothRotate(head, 'y', 0.8, 0.05);
                    }
                    if(step.action === "surprise") {
                        // Sursaut
                        robotGroup.position.y += 0.5;
                        head.rotation.x = -0.3;
                    }
                    if(step.action === "wave") {
                        rightArm.rotation.z = Math.PI - 0.5; // Coucou
                    }
                    
                    introIndex++; 
                }
            } else if (time > 22) { robotState = 'moving'; pickNewTarget(); nextEventTime = time + 3; }
            
            // Mouvement d'entrée
            if (introIndex > 0 && introIndex < 3) {
                robotGroup.position.lerp(targetPosition, 0.02);
            }
        } 
        
        else if (robotState === 'moving') {
            robotGroup.position.y += Math.sin(time * 2) * 0.002;
            robotGroup.position.lerp(targetPosition, 0.02);
            smoothRotate(robotGroup, 'y', (targetPosition.x - robotGroup.position.x) * 0.05, 0.05);
            smoothRotate(robotGroup, 'z', -(targetPosition.x - robotGroup.position.x) * 0.03, 0.05);
            
            if (robotGroup.position.distanceTo(targetPosition) < 0.5) pickNewTarget();
            
            if (time > nextEventTime) {
                const rand = Math.random();
                if (rand < 0.15) startTeleport(); 
                else if (rand < 0.25) startExplosion(); 
                else if (rand < 0.40) startDance(); // Tente de danser (filtré dans la fonction)
                else startSpeaking(); 
            }
        } 
        
        else if (robotState === 'dancing') {
            const dSpeed = time * 10;
            robotGroup.position.y = Math.abs(Math.sin(dSpeed))*0.5 - 0.5; // Rebond
            robotGroup.rotation.z = Math.sin(dSpeed*0.5)*0.2;
            leftArm.rotation.z = Math.PI - 0.5 + Math.sin(dSpeed)*0.5;
            rightArm.rotation.z = -Math.PI + 0.5 - Math.sin(dSpeed)*0.5;
            head.rotation.y = Math.sin(dSpeed*2)*0.3;
        }

        else if (robotState === 'exploding') {
            let isMoving = false;
            parts.forEach(part => {
                if (part.userData.velocity.lengthSq() > 0) {
                    isMoving = true;
                    part.position.add(part.userData.velocity);
                    part.rotation.x += part.userData.rotVelocity.x;
                    part.userData.velocity.multiplyScalar(0.95);
                }
            });
            if (!isMoving) { robotGroup.position.x += (Math.random()-0.5) * 0.1; }
        }
        
        else if (robotState === 'reassembling') {
            parts.forEach(part => {
                part.position.lerp(part.userData.origPos, 0.08);
                part.rotation.x += (part.userData.origRot.x - part.rotation.x) * 0.08;
                part.userData.velocity.set(0,0,0);
            });
        }

        else if (robotState === 'speaking') {
            robotGroup.position.lerp(targetPosition, 0.001); 
            smoothRotate(robotGroup, 'y', 0, 0.05); 
            mouth.scale.set(1, 1 + Math.sin(time * 20) * 0.2, 1); 
        }

        if(bubble && bubble.style.opacity == 1) {
            const headPos = robotGroup.position.clone(); if(robotState !== 'exploding') headPos.y += 0.8; headPos.project(camera);
            const x = (headPos.x * .5 + .5) * width; const y = (headPos.y * -.5 + .5) * height;
            const bubbleW = 250;
            const safeX = Math.max(bubbleW/2 + 20, Math.min(width - bubbleW/2 - 20, x));
            bubble.style.left = safeX + 'px';
            bubble.style.top = Math.max(50, y - 80) + 'px';
        }

        renderer.render(scene, camera);
    }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
    });

    animate();
}
