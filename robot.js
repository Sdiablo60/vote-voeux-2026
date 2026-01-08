import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// --- 1. NOUVEAUX MESSAGES (Blagues & Sympathie) ---
const messages = [
    // Interactions
    "Salut l'équipe ! 👋",
    "Vous êtes rayonnants ce soir ! ✨",
    "Qui veut du popcorn ? 🍿",
    "Je scanne la salle... que des stars ! 🤩",
    "N'oubliez pas de voter pour votre favori ! 🗳️",
    "Silence... Moteur... Ça tourne ! 🎬",
    
    // Blagues / Humour Robot
    "Toc Toc ! Qui est là ? ... Sarah Connor ! 🤖",
    "J'ai un bug... Je n'arrive pas à m'arrêter de sourire ! 😄",
    "Vous savez pourquoi je n'ai pas froid ? J'ai un antivirus ! 🦠",
    "C'est l'histoire d'un pixel qui dit à un autre... 'T'as mauvaise mine !' 😂",
    "Mon film préféré ? 'WALL-E', évidemment ! ❤️",
    "Je ne suis pas tactile, j'ai peur des courts-circuits ! ⚡",
    "Il paraît que la 3D, c'est la vie... littéralement pour moi ! 🧊",
    
    // Ambiance
    "Quelle ambiance de folie ! 🎉",
    "Ça va être serré pour le trophée ! 🏆",
    "J'espère qu'il y a une prise pour me recharger au buffet... 🔌",
    "Prêts pour le grand spectacle ? 🚀"
];

// Messages pour l'inspection (quand il vient voir de près)
const inspectionMessages = [
    "Je viens vérifier si vous souriez ! 📸",
    "Hé ! Je te vois toi au fond ! 👀",
    "Inspection technique... tout est OK ! ✅",
    "Je voulais juste vous faire un coucou de près ! 👋",
    "Wow, quelle résolution vos visages ! 4K ? 8K ? 📺"
];

// --- SCÉNARIO D'INTRO ---
const introScript = [
    { time: 1.0, text: "Hum... C'est allumé ? 🎤", action: "look_around" },
    { time: 5.0, text: "Y'a quelqu'un dans cet écran ? 🤔", action: "approach" },
    { time: 8.5, text: "TOC ! TOC ! OUVREZ ! ✊", action: "knock" },
    { time: 12.0, text: "WOUAH ! 😱 Vous êtes nombreux !", action: "recoil" },
    { time: 16.0, text: "Bienvenue au Concours Vidéo 2026 ! ✨", action: "present" },
    { time: 20.0, text: "Installez-vous, le show va commencer ! ⏳", action: "wait" }
];

if (container) {
    try { initRobot(container); } catch (e) { console.error(e); }
}

function initRobot(container) {
    let width = window.innerWidth;
    let height = window.innerHeight;
    
    // SCENE
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 8); 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // LUMIERES
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.0);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 2.0);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // --- ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
    
    // Matériaux
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blueMat = new THREE.MeshStandardMaterial({ color: 0x3388ff, roughness: 0.2 });
    const glowMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x111111 });

    // Modélisation
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.7, 32, 32), whiteMat);
    const face = new THREE.Mesh(new THREE.CircleGeometry(0.55, 32), darkMat);
    face.position.set(0, 0, 0.68);
    head.add(face);

    const eyeGeo = new THREE.CircleGeometry(0.12, 32);
    const leftEye = new THREE.Mesh(eyeGeo, glowMat);
    leftEye.position.set(-0.25, 0.1, 0.70);
    head.add(leftEye);
    const rightEye = new THREE.Mesh(eyeGeo, glowMat);
    rightEye.position.set(0.25, 0.1, 0.70);
    head.add(rightEye);

    const body = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.55, 0.9, 32), whiteMat);
    body.position.y = -0.9;

    function createArm(x) {
        const g = new THREE.Group();
        g.position.set(x, -0.7, 0);
        const s = new THREE.Mesh(new THREE.SphereGeometry(0.2), blueMat);
        g.add(s);
        const a = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.5), whiteMat);
        a.position.y = -0.3;
        g.add(a);
        return g;
    }
    const leftArm = createArm(-0.6);
    const rightArm = createArm(0.6);

    robotGroup.add(head);
    robotGroup.add(body);
    robotGroup.add(leftArm);
    robotGroup.add(rightArm);
    scene.add(robotGroup);

    // --- VARIABLES DE NAVIGATION ---
    let time = 0;
    let targetPosition = new THREE.Vector3(3.5, 0, 0); 
    robotGroup.position.copy(targetPosition);
    
    let robotState = 'intro'; 
    let introIndex = 0;
    let nextEventTime = 0;
    
    let lastMsgIndex = -1;
    let lastInspectMsgIndex = -1;
    let bubbleTimeout = null;

    // --- FONCTION DE LISSAGE (Smooth Stop) ---
    // Cette fonction sert à faire tourner le robot doucement vers une valeur cible
    function smoothRotate(object, axis, targetValue, speed) {
        object.rotation[axis] += (targetValue - object.rotation[axis]) * speed;
    }

    // --- ANIMATION ---
    function animate() {
        requestAnimationFrame(animate);
        time += 0.015; 

        // GESTION Z-INDEX DYNAMIQUE
        if (robotGroup.position.z > 2) {
            container.style.zIndex = "15";
        } else {
            container.style.zIndex = "1";
        }

        // --- PHASE 1 : INTRO ---
        if (robotState === 'intro') {
            if (introIndex < introScript.length) {
                const step = introScript[introIndex];
                if (time >= step.time) {
                    showBubble(step.text, 5000);
                    introIndex++;
                }
            } else if (time > 24) { 
                robotState = 'moving';
                pickNewTarget();
                nextEventTime = time + 5;
            }

            // Mouvements Intro
            if (time < 5.0) { 
                robotGroup.rotation.y = Math.sin(time) * 0.3;
            }
            else if (time >= 5.0 && time < 8.5) { 
                robotGroup.position.lerp(new THREE.Vector3(0, 0, 5), 0.02);
                smoothRotate(robotGroup, 'y', 0, 0.05); // Regarde droit
            } 
            else if (time >= 8.5 && time < 12.0) { 
                robotGroup.position.z = 5 + Math.sin(time * 20) * 0.02; 
                rightArm.rotation.x = -Math.PI/2 + Math.sin(time * 15) * 0.3; 
            } 
            else if (time >= 12.0 && time < 24) { 
                robotGroup.position.lerp(new THREE.Vector3(3.5, 0, 0), 0.03);
                rightArm.rotation.x *= 0.9;
                smoothRotate(robotGroup, 'y', -0.2, 0.05);
            }
        } 
        
        // --- PHASE 2 : PATROUILLE ---
        else if (robotState === 'moving') {
            // Mouvement très fluide vers la cible
            robotGroup.position.lerp(targetPosition, 0.008);
            
            // Orientation douce vers le mouvement
            const targetRotY = (targetPosition.x - robotGroup.position.x) * 0.05;
            const targetRotZ = -(targetPosition.x - robotGroup.position.x) * 0.02;
            
            smoothRotate(robotGroup, 'y', targetRotY, 0.05);
            smoothRotate(robotGroup, 'z', targetRotZ, 0.05);
            
            // Respiration
            robotGroup.position.y += Math.sin(time * 1.5) * 0.001;
            
            leftArm.rotation.x = Math.sin(time * 2) * 0.1;
            rightArm.rotation.x = -Math.sin(time * 2) * 0.1;

            if (robotGroup.position.distanceTo(targetPosition) < 0.5) {
                pickNewTarget();
            }

            if (time > nextEventTime) {
                const rand = Math.random();
                if (rand < 0.30) { 
                    startInspection(); 
                } else {
                    startSpeaking();   
                }
            }
        } 
        
        // --- PHASE 3 : PARLE (Freinage Doux) ---
        else if (robotState === 'speaking') {
            // 1. Freinage progressif de la position
            // Au lieu de figer X et Y, on continue de lerper TRÈS lentement vers la cible actuelle
            // ce qui crée un arrêt en douceur
            robotGroup.position.lerp(targetPosition, 0.001); // Facteur très faible
            
            // 2. Respiration continue (ne pas figer la vie)
            robotGroup.position.y += Math.sin(time * 3) * 0.001;
            
            // 3. Rotation douce vers le public (0,0,0)
            smoothRotate(robotGroup, 'y', 0, 0.05);
            smoothRotate(robotGroup, 'z', 0, 0.05);
            
            // 4. Gestuelle
            rightArm.rotation.z = Math.cos(time * 4) * 0.4 + 0.4; 
        }

        // --- PHASE 4 : INSPECTION ---
        else if (robotState === 'inspecting') {
            const inspectPos = new THREE.Vector3(Math.sin(time)*2, 0, 4.5);
            robotGroup.position.lerp(inspectPos, 0.02);
            smoothRotate(robotGroup, 'y', Math.sin(time) * 0.2, 0.05);
            
            if (time > nextEventTime) {
                robotState = 'moving';
                pickNewTarget(); 
                nextEventTime = time + 10 + Math.random() * 10;
            }
        }

        updateBubblePosition();
        renderer.render(scene, camera);
    }

    function pickNewTarget() {
        const aspect = width / height;
        const vW = 7 * aspect; 
        let x, y;
        if (Math.random() > 0.5) {
            x = 3.0 + Math.random() * (vW * 0.4 - 3.0); 
        } else {
            x = -3.0 - Math.random() * (vW * 0.4 - 3.0); 
        }
        y = (Math.random() - 0.5) * 3; 
        targetPosition.set(x, y, 0);
    }

    function startSpeaking() {
        // Sauvegarde de l'état pour savoir quoi faire après
        if(robotState === 'intro') return;

        robotState = 'speaking';
        
        // On met à jour la "cible" à la position actuelle pour que le "lerp" du freinage
        // se fasse sur place et pas vers l'ancienne destination lointaine
        targetPosition.copy(robotGroup.position);

        let newIndex;
        do {
            newIndex = Math.floor(Math.random() * messages.length);
        } while (newIndex === lastMsgIndex);
        lastMsgIndex = newIndex;

        showBubble(messages[newIndex], 6000); 
        
        nextEventTime = time + 10 + Math.random() * 15; 
        
        setTimeout(() => {
            if (robotState === 'speaking') {
                hideBubble();
                robotState = 'moving';
                // On doit redonner une cible lointaine pour qu'il reparte
                pickNewTarget();
            }
        }, 6000);
    }

    function startInspection() {
        robotState = 'inspecting';
        
        let newIndex;
        do {
            newIndex = Math.floor(Math.random() * inspectionMessages.length);
        } while (newIndex === lastInspectMsgIndex);
        lastInspectMsgIndex = newIndex;

        showBubble(inspectionMessages[newIndex], 4000);
        nextEventTime = time + 6; 
    }

    function showBubble(text, duration) {
        if(!bubble) return;
        if (bubbleTimeout) { clearTimeout(bubbleTimeout); bubbleTimeout = null; }
        bubble.innerText = text;
        bubble.style.opacity = 1;
        if(duration) {
             bubbleTimeout = setTimeout(() => { hideBubble(); }, duration);
        }
    }

    function hideBubble() {
        if(bubble) bubble.style.opacity = 0;
    }

    function updateBubblePosition() {
        if(!bubble || bubble.style.opacity == 0) return;
        const headPos = robotGroup.position.clone();
        headPos.y += 0.8; 
        headPos.project(camera);
        const x = (headPos.x * .5 + .5) * width;
        const y = (headPos.y * -.5 + .5) * height;
        let finalX = Math.max(140, Math.min(width - 140, x));
        let finalY = Math.max(50, y - 80);
        bubble.style.left = finalX + 'px';
        bubble.style.top = finalY + 'px';
        bubble.style.transform = 'translate(-50%, 0)';
    }

    window.addEventListener('resize', () => {
        width = window.innerWidth;
        height = window.innerHeight;
        renderer.setSize(width, height);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
    });

    // Initialise le timer
    nextEventTime = 20; 
    animate();
}
