import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// --- CONFIGURATION REÇUE DE PYTHON ---
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- TEXTES INTELLIGENTS ---
const MESSAGES = {
    attente: [
        "Salut l'équipe ! 👋", "Tout le monde est bien installé ? 💺", 
        "Je vérifie les objectifs... 🧐", "Qui a le plus beau sourire ? 📸",
        "N'oubliez pas de voter ! 🗳️", "Quelle ambiance de folie ! 🎉",
        "Je suis Clap-E, votre assistant ! 🤖", "Il fait chaud sous les spots ! 💡",
        "Vous me voyez bien ? 👀", "C'est parti pour le show ! 🚀"
    ],
    vote_off: [
        "Les votes sont CLOS ! 🛑", "Rien ne va plus ! 🎲",
        "Le podium arrive... 🏆", "Mais que fait la régie ? 😴",
        "Suspens insoutenable... 😬", "Je calcule les résultats... 🧮",
        "Qui a gagné selon vous ? 🤔", "Patience, patience... ⏳"
    ],
    photos: [
        "C'est l'heure des photos ! 📸", "Envoyez vos selfies ! 🤳",
        "Je veux être sur la photo ! 🤖", "Souriez ! 😁",
        "On partage, on partage ! 📲", "Montrez vos plus beaux profils !",
        "Allez, une petite grimace ! 🤪", "C'est instantané ! ⚡"
    ]
};

// Séquence d'intro (Seulement pour l'accueil)
const introScript = [
    { time: 1.0, text: "Hum... C'est allumé ? 🎤", action: "look_around" },
    { time: 5.0, text: "Y'a quelqu'un dans cet écran ? 🤔", action: "approach" },
    { time: 8.5, text: "TOC ! TOC ! OUVREZ ! ✊", action: "knock" },
    { time: 12.0, text: "WOUAH ! 😱 Vous êtes nombreux !", action: "recoil" },
    { time: 16.0, text: "Bienvenue : " + config.titre + " ! ✨", action: "present" },
    { time: 20.0, text: "Installez-vous, le show va commencer ! ⏳", action: "wait" }
];

if (container) {
    try { initRobot(container); } catch (e) { console.error(e); }
}

function initRobot(container) {
    let width = window.innerWidth;
    let height = window.innerHeight;
    
    // Positionnement Fixe
    container.style.position = 'fixed'; container.style.top = '0'; container.style.left = '0';
    container.style.width = '100%'; container.style.height = '100%';
    container.style.zIndex = '1'; container.style.pointerEvents = 'none';
    
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

    // --- ROBOT "CLAP-E" (VOTRE CODE) ---
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

    // Yeux et Bouche (Position corrigée)
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
    let targetPosition = new THREE.Vector3(3.5, 0, 0); 
    robotGroup.position.copy(targetPosition);
    let robotState = 'intro'; 
    let introIndex = 0;
    let nextEventTime = 0;
    let bubbleTimeout = null;

    // Si pas en mode accueil, on saute l'intro
    if (config.mode !== 'attente') {
        robotState = 'moving';
        targetPosition.set(0,0,0);
        robotGroup.position.set(0,0,0);
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

    function startSpeaking() {
        robotState = 'speaking';
        targetPosition.copy(robotGroup.position);
        
        // CHOIX MESSAGE INTELLIGENT
        let list = MESSAGES[config.mode] || MESSAGES.attente;
        let txt = list[Math.floor(Math.random() * list.length)];

        showBubble(txt, 5000); 
        nextEventTime = time + 8 + Math.random() * 10; 
        
        setTimeout(() => { if (robotState === 'speaking') { hideBubble(); robotState = 'moving'; pickNewTarget(); } }, 5000);
    }

    function pickNewTarget() {
        const aspect = width / height; const vW = 7 * aspect; 
        let x = (Math.random() > 0.5) ? 3.0 + Math.random() * (vW * 0.4 - 3.0) : -3.0 - Math.random() * (vW * 0.4 - 3.0);
        targetPosition.set(x, (Math.random() - 0.5) * 3, 0);
    }

    // --- ANIMATION LOOP ---
    function animate() {
        requestAnimationFrame(animate);
        time += 0.015; 
        robotGroup.position.y += Math.sin(time * 2) * 0.002;

        if (robotState === 'intro') {
            if (introIndex < introScript.length) {
                const step = introScript[introIndex];
                if (time >= step.time) { showBubble(step.text, 3500); introIndex++; }
            } else if (time > 24) { robotState = 'moving'; pickNewTarget(); nextEventTime = time + 5; }
            
            if (time < 5.0) robotGroup.rotation.y = Math.sin(time) * 0.3;
            else if (time < 12.0) { robotGroup.position.lerp(new THREE.Vector3(0, 0, 5), 0.02); } 
            else { robotGroup.position.lerp(new THREE.Vector3(3.5, 0, 0), 0.03); }
        } 
        
        else if (robotState === 'moving') {
            robotGroup.position.lerp(targetPosition, 0.008);
            smoothRotate(robotGroup, 'y', (targetPosition.x - robotGroup.position.x) * 0.05, 0.05);
            smoothRotate(robotGroup, 'z', -(targetPosition.x - robotGroup.position.x) * 0.03, 0.05);
            if (robotGroup.position.distanceTo(targetPosition) < 0.5) pickNewTarget();
            if (time > nextEventTime) startSpeaking();
        } 
        
        else if (robotState === 'speaking') {
            robotGroup.position.lerp(targetPosition, 0.001); 
            smoothRotate(robotGroup, 'y', 0, 0.05);
            mouth.scale.set(1, 1 + Math.sin(time * 20) * 0.2, 1); 
        }

        if(bubble && bubble.style.opacity == 1) {
            const headPos = robotGroup.position.clone(); headPos.y += 0.8; headPos.project(camera);
            const x = (headPos.x * .5 + .5) * width; const y = (headPos.y * -.5 + .5) * height;
            bubble.style.left = Math.max(100, Math.min(width-100, x)) + 'px';
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
