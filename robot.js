import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// --- CONFIGURATION ---
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- TEXTES (SAC DE PHRASES SANS RÉPÉTITION IMMÉDIATE) ---
const MESSAGES_BAG = {
    attente: [
        "Salut tout le monde ! 👋", "Tout le monde est bien installé ? 💺", 
        "Je vérifie les objectifs... 🧐", "Qui a le plus beau sourire ? 📸",
        "N'oubliez pas de voter ! 🗳️", "Quelle ambiance de folie ! 🎉",
        "Je suis Clap-E, votre assistant ! 🤖", "Il fait chaud sous les spots ! 💡",
        "Vous me voyez bien ? 👀", "C'est parti pour le show ! 🚀",
        "J'envoie des ondes positives à la Régie... 📡", "La Régie, tout est OK ? 👍",
        "Un petit coucou à l'équipe technique ! 👷", "Ça s'active en coulisses ! 🎬"
    ],
    vote_off: [
        "Les votes sont CLOS ! 🛑", "Rien ne va plus ! 🎲",
        "Le podium arrive... 🏆", "Mais que fait la régie ? 😴",
        "Suspens insoutenable... 😬", "Je calcule les résultats... 🧮",
        "Qui a gagné selon vous ? 🤔", "Patience, patience... ⏳",
        "La régie transpire... 💦", "Allez, on affiche les scores ! 📊"
    ],
    photos: [
        "C'est l'heure des photos ! 📸", "Envoyez vos selfies ! 🤳",
        "Je veux être sur la photo ! 🤖", "Souriez ! 😁",
        "On partage, on partage ! 📲", "Montrez vos plus beaux profils !",
        "Allez, une petite grimace ! 🤪", "C'est instantané ! ⚡"
    ],
    cache_cache: [
        "Coucou ! Je suis là ! 👋", "Vous m'aviez perdu ? 👻",
        "Bouh ! Surprise ! 🎃", "Je suis trop rapide pour vous ! ⚡",
        "On joue à cache-cache ? 🙈"
    ]
};

// Gestionnaire de messages uniques
const usedMessages = {};
function getUniqueMessage(category) {
    if (!MESSAGES_BAG[category]) return "...";
    if (!usedMessages[category]) usedMessages[category] = [];
    
    // Reset si tout a été dit
    if (usedMessages[category].length >= MESSAGES_BAG[category].length) {
        usedMessages[category] = [];
    }
    
    // Filtre les messages non utilisés
    let available = MESSAGES_BAG[category].filter(m => !usedMessages[category].includes(m));
    let msg = available[Math.floor(Math.random() * available.length)];
    usedMessages[category].push(msg);
    return msg;
}

// Séquence d'Intro
const introScript = [
    { time: 1.0, text: "Bonjour à tous ! 👋", action: "look_around" },
    { time: 4.5, text: "Je suis Clap-E, votre robot ! 🤖", action: "present" },
    { time: 8.0, text: "Je vois que la salle est pleine ! 👀", action: "look_around" },
    { time: 12.0, text: "Un grand merci à la Régie pour l'invitation ! 📡", action: "knock" },
    { time: 16.0, text: "Bienvenue : " + config.titre + " ! ✨", action: "present" },
    { time: 20.0, text: "Installez-vous, ça va commencer ! ⏳", action: "wait" }
];

if (container) {
    try { initRobot(container); } catch (e) { console.error(e); }
}

function initRobot(container) {
    let width = window.innerWidth;
    let height = window.innerHeight;
    
    // Positionnement Fixe (Au dessus du reste, mais laisse passer les clics)
    container.style.position = 'fixed'; 
    container.style.top = '0'; 
    container.style.left = '0';
    container.style.width = '100%'; 
    container.style.height = '100%';
    container.style.zIndex = '10'; 
    container.style.pointerEvents = 'none';
    
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 8); 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // Lumières
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.1); scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 2.5); dirLight.position.set(5, 10, 7); scene.add(dirLight);
    const screenLight = new THREE.PointLight(0x00ffff, 0.5, 4); screenLight.position.set(0, 0, 2); scene.add(screenLight);

    // --- CONSTRUCTION DU ROBOT GÉOMÉTRIQUE (CLAP-E) ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
    
    const whiteShellMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2, metalness: 0.1 });
    const blackScreenMat = new THREE.MeshStandardMaterial({ color: 0x000000, roughness: 0.1, metalness: 0.5 });
    const neonBlueMat = new THREE.MeshBasicMaterial({ color: 0x00ffff }); 
    const greyMat = new THREE.MeshStandardMaterial({ color: 0xbbbbbb });

    // Tête & Visage
    const headGeo = new THREE.SphereGeometry(0.85, 64, 64); 
    const head = new THREE.Mesh(headGeo, whiteShellMat); head.scale.set(1.4, 1.0, 0.75);
    const faceGeo = new THREE.SphereGeometry(0.78, 64, 64);
    const face = new THREE.Mesh(faceGeo, blackScreenMat); face.scale.set(1.25, 0.85, 0.6); face.position.set(0, 0, 0.55); head.add(face);

    // Yeux & Bouche
    const eyeGeo = new THREE.TorusGeometry(0.12, 0.035, 8, 32, Math.PI); 
    const leftEye = new THREE.Mesh(eyeGeo, neonBlueMat); leftEye.position.set(-0.35, 0.15, 1.05); head.add(leftEye);
    const rightEye = new THREE.Mesh(eyeGeo, neonBlueMat); rightEye.position.set(0.35, 0.15, 1.05); head.add(rightEye);
    const mouthGeo = new THREE.TorusGeometry(0.1, 0.035, 8, 32, Math.PI);
    const mouth = new THREE.Mesh(mouthGeo, neonBlueMat); mouth.position.set(0, -0.15, 1.05); mouth.rotation.z = Math.PI; head.add(mouth);

    // Oreilles & Corps
    const earGeo = new THREE.CylinderGeometry(0.25, 0.25, 0.1, 32); earGeo.rotateZ(Math.PI / 2); 
    const leftEar = new THREE.Mesh(earGeo, whiteShellMat); leftEar.position.set(-1.1, 0, 0); head.add(leftEar);
    const rightEar = new THREE.Mesh(earGeo, whiteShellMat); rightEar.position.set(1.1, 0, 0); head.add(rightEar);

    const bodyGeo = new THREE.SphereGeometry(0.65, 32, 32);
    const body = new THREE.Mesh(bodyGeo, whiteShellMat); body.scale.set(0.95, 1.1, 0.8); body.position.set(0, -1.1, 0); 
    const beltGeo = new THREE.TorusGeometry(0.62, 0.03, 16, 64);
    const belt = new THREE.Mesh(beltGeo, greyMat); belt.rotation.x = Math.PI / 2; body.add(belt);

    // Bras
    const armGeo = new THREE.CapsuleGeometry(0.13, 0.5, 4, 16);
    const leftArm = new THREE.Mesh(armGeo, whiteShellMat); leftArm.position.set(-0.8, -0.8, 0); leftArm.rotation.z = 0.15; 
    const rightArm = new THREE.Mesh(armGeo, whiteShellMat); rightArm.position.set(0.8, -0.8, 0); rightArm.rotation.z = -0.15;

    robotGroup.add(head); robotGroup.add(body); robotGroup.add(leftArm); robotGroup.add(rightArm);
    scene.add(robotGroup);

    // --- LOGIQUE DE DÉPLACEMENT ---
    let time = 0;
    // Départ sécurisé à droite
    let targetPosition = new THREE.Vector3(4.0, 0, 0); 
    robotGroup.position.copy(targetPosition);
    
    let robotState = 'intro'; 
    let introIndex = 0;
    let nextEventTime = 0;
    let bubbleTimeout = null;

    if (config.mode !== 'attente') {
        robotState = 'moving';
        targetPosition.set(4.0, 0, 0); 
        robotGroup.position.set(4.0, 0, 0);
    }

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

    // --- COEUR DU SYSTÈME : CHOIX DE CIBLE INTELLIGENT ---
    function pickNewTarget() {
        const aspect = width / height; 
        const vW = 7 * aspect; 
        
        // 1. Choix du coté (Gauche ou Droite) - Jamais le centre
        const side = Math.random() > 0.5 ? 1 : -1; 
        
        // 2. Définition des zones sûres (Loin du centre)
        // Le centre est à 0. On veut être au moins à 3.8 unités du centre.
        const safeMin = 3.8; 
        const safeMax = vW * 0.55; // Bord de l'écran
        
        let x = side * (safeMin + Math.random() * (safeMax - safeMin));
        let y = (Math.random() - 0.5) * 4.0; // Hauteur variable
        
        targetPosition.set(x, y, 0);
    }

    // --- ACTIONS SPÉCIALES ---
    
    // Zoom avant (vient coller sa tête à l'écran au centre)
    function startCloseUpInteraction() {
        robotState = 'closeup';
        targetPosition.set(0, -0.5, 5.5); // Très proche (Z=5.5)
        
        // Reste 2 secondes puis parle
        setTimeout(() => {
            if (robotState === 'closeup') {
                const msg = getUniqueMessage(config.mode);
                showBubble(msg, 3500);
                
                // Repart après avoir parlé
                setTimeout(() => {
                    hideBubble();
                    robotState = 'moving';
                    pickNewTarget();
                }, 3500);
            }
        }, 2000);
    }

    // Cache-Cache (Sort de l'écran)
    function startHideAndSeek() {
        robotState = 'hiding';
        // Sort soit par le bas, soit sur le côté
        if(Math.random() > 0.5) targetPosition.set(robotGroup.position.x, -10, 0); 
        else targetPosition.set(robotGroup.position.x * 3, 0, 0); 
        
        // Revient après 4 secondes
        setTimeout(() => {
            if (robotState === 'hiding') {
                robotState = 'moving';
                pickNewTarget(); 
                setTimeout(() => {
                    const msg = getUniqueMessage('cache_cache');
                    showBubble(msg, 3000);
                }, 1500); 
            }
        }, 4000);
    }

    // Parler (Reste sur place sur le coté)
    function startSpeaking() {
        robotState = 'speaking';
        targetPosition.copy(robotGroup.position); 
        
        const msg = getUniqueMessage(config.mode);
        showBubble(msg, 4000); 
        nextEventTime = time + 3 + Math.random() * 5; 
        
        setTimeout(() => { if (robotState === 'speaking') { hideBubble(); robotState = 'moving'; pickNewTarget(); } }, 4000);
    }

    // --- BOUCLE D'ANIMATION ---
    function animate() {
        requestAnimationFrame(animate);
        time += 0.015; 
        robotGroup.position.y += Math.sin(time * 2) * 0.002;

        if (robotState === 'intro') {
            if (introIndex < introScript.length) {
                const step = introScript[introIndex];
                if (time >= step.time) { showBubble(step.text, 3000); introIndex++; }
            } else if (time > 22) { robotState = 'moving'; pickNewTarget(); nextEventTime = time + 3; }
            
            // Anim Intro
            if (time < 5.0) robotGroup.rotation.y = Math.sin(time) * 0.3;
            else if (time < 12.0) { robotGroup.position.lerp(new THREE.Vector3(0, 0, 5), 0.02); } 
            else { robotGroup.position.lerp(new THREE.Vector3(4.0, 0, 0), 0.03); }
        } 
        
        else if (robotState === 'moving') {
            robotGroup.position.lerp(targetPosition, 0.02); // Vitesse normale
            smoothRotate(robotGroup, 'y', (targetPosition.x - robotGroup.position.x) * 0.05, 0.05);
            smoothRotate(robotGroup, 'z', -(targetPosition.x - robotGroup.position.x) * 0.03, 0.05);
            
            if (robotGroup.position.distanceTo(targetPosition) < 0.5) pickNewTarget();
            
            // Déclencheur aléatoire d'événements
            if (time > nextEventTime) {
                const rand = Math.random();
                if (rand < 0.15) startHideAndSeek(); 
                else if (rand < 0.35) startCloseUpInteraction(); 
                else startSpeaking(); 
            }
        } 
        
        else if (robotState === 'closeup') {
            robotGroup.position.lerp(targetPosition, 0.04); 
            smoothRotate(robotGroup, 'y', 0, 0.1); 
            smoothRotate(robotGroup, 'z', 0, 0.1);
            rightArm.rotation.z = Math.sin(time * 10) * 0.5 - 0.5; // Coucou de la main
        }

        else if (robotState === 'hiding') {
            robotGroup.position.lerp(targetPosition, 0.05); 
        }
        
        else if (robotState === 'speaking') {
            robotGroup.position.lerp(targetPosition, 0.001); 
            smoothRotate(robotGroup, 'y', 0, 0.05); 
            mouth.scale.set(1, 1 + Math.sin(time * 20) * 0.2, 1); 
        }

        // Bulle qui suit la tête (avec marge de sécurité)
        if(bubble && bubble.style.opacity == 1) {
            const headPos = robotGroup.position.clone(); headPos.y += 0.8; headPos.project(camera);
            const x = (headPos.x * .5 + .5) * width; const y = (headPos.y * -.5 + .5) * height;
            const padding = 50;
            bubble.style.left = Math.max(padding, Math.min(width-padding, x)) + 'px';
            bubble.style.top = Math.max(padding, y - 80) + 'px';
        }

        renderer.render(scene, camera);
    }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
    });

    animate();
}
