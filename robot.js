import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// --- CONFIGURATION ---
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- TEXTES (BIBLIOTHÈQUE ÉTENDUE) ---
const MESSAGES_BAG = {
    attente: [
        // Salutations
        "Salut tout le monde ! 👋", "Bienvenue à tous ! ✨", "Installez-vous confortablement ! 💺",
        "Ravi de vous voir si nombreux !", "Quel public magnifique ce soir ! 🤩",
        
        // Ambiance / Show
        "Ça va être un show INCROYABLE ! 🚀", "Préparez le pop-corn ! 🍿", 
        "J'espère que vous êtes prêts ! 🔥", "L'ambiance monte... 🌡️",
        "Je sens que ça va être légendaire.", "C'est parti pour le show ! 🎬",
        
        // Technique / Régie
        "J'envoie des ondes positives à la Régie... 📡", "La Régie, le son est bon ? 🔊",
        "Un petit coucou à l'équipe technique ! 👷", "Ça s'active en coulisses ! ⚙️",
        "Je vérifie mes circuits... Bip Boup. ✅", "Qui a débranché mon chargeur ? 🔌",
        "Si je bug, c'est la faute du Wi-Fi ! 📶", "Hé la régie ! On m'entend bien ? 🎤",
        
        // Interaction Public
        "Vous me voyez bien au fond ? 👀", "Qui a le plus beau sourire ? 📸",
        "Faites du bruit pour les participants ! 👏", "Ne soyez pas timides !",
        "Je vous ai à l'œil... 😉", "N'oubliez pas de voter tout à l'heure ! 🗳️"
    ],
    
    vote_off: [
        // Suspense
        "Les votes sont CLOS ! 🛑", "Rien ne va plus ! 🎲", "Les jeux sont faits.",
        "Le podium arrive... 🏆", "Suspens insoutenable... 😬", 
        "Mon processeur chauffe pour calculer ! 🧮", "Qui va gagner ? 🤔",
        "Patience, patience... ⏳", "Le résultat est... ah non, j'attends.",
        
        // Taquinerie Régie
        "Mais que fait la régie ? 😴", "Ils comptent à la main ou quoi ? ✍️",
        "La régie transpire... 💦", "Allez la technique, on se réveille ! ☕",
        "C'est long non ? Vous trouvez pas ? 🕒", "Il faut changer les piles de l'ordi ? 🔋",
        "On attend le feu vert du chef ! 🚦", "Promis, ça arrive avant 2030."
    ],
    
    photos: [
        // Encouragements
        "C'est l'heure des photos ! 📸", "Envoyez vos selfies ! 🤳", "Bombardez l'écran ! 💣",
        "Je veux être sur la photo ! 🤖", "Souriez ! 😁", "Montrez vos dents ! 🦷",
        "On partage, on partage ! 📲", "Montrez vos plus beaux profils !",
        "Allez, une petite grimace ! 🤪", "C'est instantané ! ⚡",
        
        // Compliments
        "Wouah ! Quelle classe ! 😎", "Vous êtes photogéniques ! ✨",
        "J'adore cette photo ! ❤️", "Encore ! Encore ! 🔄",
        "Le cadrage est parfait. 👌", "Des stars, vous êtes des stars. ⭐"
    ],
    
    cache_cache: [
        "Coucou ! Je suis là ! 👋", "Vous m'aviez perdu ? 👻",
        "Bouh ! Surprise ! 🎃", "Je suis trop rapide pour vous ! ⚡",
        "On joue à cache-cache ? 🙈", "Me revoilà ! 🔙",
        "Je suis passé par les câbles ! 🕳️"
    ]
};

// --- GESTIONNAIRE DE MESSAGES UNIQUES ---
const usedMessages = {};
function getUniqueMessage(category) {
    if (!MESSAGES_BAG[category]) return "...";
    if (!usedMessages[category]) usedMessages[category] = [];
    
    // Si tout a été dit, on vide la mémoire pour recommencer
    if (usedMessages[category].length >= MESSAGES_BAG[category].length) {
        usedMessages[category] = [];
    }
    
    // On filtre pour ne garder que ceux pas encore dits
    let available = MESSAGES_BAG[category].filter(m => !usedMessages[category].includes(m));
    // Double sécurité
    if (available.length === 0) available = MESSAGES_BAG[category];
    
    let msg = available[Math.floor(Math.random() * available.length)];
    usedMessages[category].push(msg);
    return msg;
}

// Séquence d'Intro
const introScript = [
    { time: 1.0, text: "Bonjour à tous ! 👋", action: "look_around" },
    { time: 4.5, text: "Je suis Clap-E, votre robot ! 🤖", action: "present" },
    { time: 8.0, text: "Je vois que la salle est pleine ! 👀", action: "look_around" },
    { time: 11.5, text: "Un grand merci à la Régie ! 📡", action: "knock" },
    { time: 15.0, text: "Bienvenue : " + config.titre + " ! ✨", action: "present" },
    { time: 19.0, text: "Installez-vous, ça va commencer ! ⏳", action: "wait" }
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

    const ambientLight = new THREE.AmbientLight(0xffffff, 1.1); scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 2.5); dirLight.position.set(5, 10, 7); scene.add(dirLight);
    const screenLight = new THREE.PointLight(0x00ffff, 0.5, 4); screenLight.position.set(0, 0, 2); scene.add(screenLight);

    // --- ROBOT GÉOMÉTRIQUE ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
    
    const whiteShellMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2, metalness: 0.1 });
    const blackScreenMat = new THREE.MeshStandardMaterial({ color: 0x000000, roughness: 0.1, metalness: 0.5 });
    const neonBlueMat = new THREE.MeshBasicMaterial({ color: 0x00ffff }); 
    const greyMat = new THREE.MeshStandardMaterial({ color: 0xbbbbbb });

    const headGeo = new THREE.SphereGeometry(0.85, 64, 64); 
    const head = new THREE.Mesh(headGeo, whiteShellMat); head.scale.set(1.4, 1.0, 0.75);
    const faceGeo = new THREE.SphereGeometry(0.78, 64, 64);
    const face = new THREE.Mesh(faceGeo, blackScreenMat); face.scale.set(1.25, 0.85, 0.6); face.position.set(0, 0, 0.55); head.add(face);

    const eyeGeo = new THREE.TorusGeometry(0.12, 0.035, 8, 32, Math.PI); 
    const leftEye = new THREE.Mesh(eyeGeo, neonBlueMat); leftEye.position.set(-0.35, 0.15, 1.05); head.add(leftEye);
    const rightEye = new THREE.Mesh(eyeGeo, neonBlueMat); rightEye.position.set(0.35, 0.15, 1.05); head.add(rightEye);
    const mouthGeo = new THREE.TorusGeometry(0.1, 0.035, 8, 32, Math.PI);
    const mouth = new THREE.Mesh(mouthGeo, neonBlueMat); mouth.position.set(0, -0.15, 1.05); mouth.rotation.z = Math.PI; head.add(mouth);

    const earGeo = new THREE.CylinderGeometry(0.25, 0.25, 0.1, 32); earGeo.rotateZ(Math.PI / 2); 
    const leftEar = new THREE.Mesh(earGeo, whiteShellMat); leftEar.position.set(-1.1, 0, 0); head.add(leftEar);
    const rightEar = new THREE.Mesh(earGeo, whiteShellMat); rightEar.position.set(1.1, 0, 0); head.add(rightEar);

    const bodyGeo = new THREE.SphereGeometry(0.65, 32, 32);
    const body = new THREE.Mesh(bodyGeo, whiteShellMat); body.scale.set(0.95, 1.1, 0.8); body.position.set(0, -1.1, 0); 
    const beltGeo = new THREE.TorusGeometry(0.62, 0.03, 16, 64);
    const belt = new THREE.Mesh(beltGeo, greyMat); belt.rotation.x = Math.PI / 2; body.add(belt);

    const armGeo = new THREE.CapsuleGeometry(0.13, 0.5, 4, 16);
    const leftArm = new THREE.Mesh(armGeo, whiteShellMat); leftArm.position.set(-0.8, -0.8, 0); leftArm.rotation.z = 0.15; 
    const rightArm = new THREE.Mesh(armGeo, whiteShellMat); rightArm.position.set(0.8, -0.8, 0); rightArm.rotation.z = -0.15;

    robotGroup.add(head); robotGroup.add(body); robotGroup.add(leftArm); robotGroup.add(rightArm);
    scene.add(robotGroup);

    // --- VARIABLES LOGIQUES ---
    let time = 0;
    // Position de départ à droite
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

    // --- LOGIQUE DE DÉPLACEMENT ---
    function pickNewTarget() {
        const aspect = width / height; 
        const vW = 7 * aspect; 
        
        // Zone interdite au centre : X doit être < -3.5 ou > 3.5
        const side = Math.random() > 0.5 ? 1 : -1; // 1=Droite, -1=Gauche
        
        const safeMin = 3.8; 
        const safeMax = vW * 0.55; 
        
        let x = side * (safeMin + Math.random() * (safeMax - safeMin));
        let y = (Math.random() - 0.5) * 4.0;
        
        targetPosition.set(x, y, 0);
    }

    function startCloseUpInteraction() {
        robotState = 'closeup';
        targetPosition.set(0, -0.5, 5.0); // Avance au centre
        showBubble("👀", 2000);
        
        setTimeout(() => {
            if (robotState === 'closeup') {
                const msg = getUniqueMessage(config.mode);
                showBubble(msg, 3500);
                setTimeout(() => {
                    hideBubble();
                    robotState = 'moving';
                    pickNewTarget();
                }, 3500);
            }
        }, 2000);
    }

    function startHideAndSeek() {
        robotState = 'hiding';
        // Sort de l'écran
        if(Math.random() > 0.5) targetPosition.set(robotGroup.position.x, -10, 0);
        else targetPosition.set(robotGroup.position.x * 3, 0, 0);
        
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

    function startSpeaking() {
        robotState = 'speaking';
        targetPosition.copy(robotGroup.position); 
        
        const msg = getUniqueMessage(config.mode);
        showBubble(msg, 4000); 
        nextEventTime = time + 3 + Math.random() * 5; 
        
        setTimeout(() => { if (robotState === 'speaking') { hideBubble(); robotState = 'moving'; pickNewTarget(); } }, 4000);
    }

    // --- ANIMATION LOOP ---
    function animate() {
        requestAnimationFrame(animate);
        time += 0.015; 
        robotGroup.position.y += Math.sin(time * 2) * 0.002;

        if (robotState === 'intro') {
            if (introIndex < introScript.length) {
                const step = introScript[introIndex];
                if (time >= step.time) { showBubble(step.text, 3000); introIndex++; }
            } else if (time > 22) { robotState = 'moving'; pickNewTarget(); nextEventTime = time + 3; }
            
            if (time < 5.0) robotGroup.rotation.y = Math.sin(time) * 0.3;
            else if (time < 12.0) { robotGroup.position.lerp(new THREE.Vector3(0, 0, 5), 0.02); } 
            else { robotGroup.position.lerp(new THREE.Vector3(4.0, 0, 0), 0.03); }
        } 
        
        else if (robotState === 'moving') {
            robotGroup.position.lerp(targetPosition, 0.018);
            smoothRotate(robotGroup, 'y', (targetPosition.x - robotGroup.position.x) * 0.05, 0.05);
            smoothRotate(robotGroup, 'z', -(targetPosition.x - robotGroup.position.x) * 0.03, 0.05);
            
            if (robotGroup.position.distanceTo(targetPosition) < 0.5) pickNewTarget();
            
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
            rightArm.rotation.z = Math.sin(time * 10) * 0.5 - 0.5; 
        }

        else if (robotState === 'hiding') {
            robotGroup.position.lerp(targetPosition, 0.05); 
        }
        
        else if (robotState === 'speaking') {
            robotGroup.position.lerp(targetPosition, 0.001); 
            smoothRotate(robotGroup, 'y', 0, 0.05); 
            mouth.scale.set(1, 1 + Math.sin(time * 20) * 0.2, 1); 
        }

        // --- GESTION DE LA BULLE (CORRECTIF BORDURE) ---
        if(bubble && bubble.style.opacity == 1) {
            const headPos = robotGroup.position.clone(); headPos.y += 0.8; headPos.project(camera);
            const x = (headPos.x * .5 + .5) * width; const y = (headPos.y * -.5 + .5) * height;
            
            // Padding ajusté : 
            // 200px minimum à gauche (pour pas coller)
            // width - 200px max à droite (pour pas couper la bulle)
            const safeX = Math.max(200, Math.min(width - 250, x));
            
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
