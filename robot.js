import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// --- STOCK DE MESSAGES GÉNÉRAUX (30 phrases) ---
const messages = [
    "Salut l'équipe ! 👋",
    "Tout le monde est bien installé ? 💺",
    "Je vérifie les objectifs... 🧐",
    "Qui a le plus beau sourire ce soir ? 📸",
    "Silence... Moteur... Ça tourne ! 🎬",
    "N'oubliez pas de voter pour votre favori ! 🗳️",
    "Quelle ambiance de folie ! 🎉",
    "Je suis Clap-E, votre assistant préféré ! 🤖",
    "Il fait chaud sous les projecteurs, non ? 💡",
    "J'espère qu'il y a des petits fours... 🍪",
    "Psst... Vous me voyez bien ? 👀",
    "C'est parti pour le show ! 🚀",
    "Wow, cette vidéo était incroyable ! 🎞️",
    "Un petit coucou aux organisateurs ! 👋",
    "Je scane la salle... Vous êtes magnifiques ! ✨",
    "Vous avez pensé à charger vos téléphones ? 🔋",
    "Moi aussi je voudrais participer au concours ! 🥺",
    "Ça manque un peu de robots dans ces vidéos... 🤖",
    "Allez, on fait du bruit pour les candidats ! 👏",
    "Je crois que j'ai vu un chat passer... 🐱",
    "Ma batterie est à 100%, prêt à faire la fête ! ⚡",
    "Le niveau est très haut cette année ! 📈",
    "N'hésitez pas à vous rapprocher de l'écran ! 📺",
    "J'adore regarder vos réactions ! 😄",
    "C'est quand la pause ? J'ai besoin d'huile... 🛢️",
    "Attention, je vous observe... (gentiment) 👁️",
    "Qui veut un autographe numérique ? ✍️",
    "La régie, tout va bien ? 👍",
    "On se croirait à Cannes ! 🌴",
    "Prêts pour le verdict final ? 🏆"
];

// --- MESSAGES SPÉCIFIQUES POUR L'INSPECTION (QUAND IL S'APPROCHE) ---
const inspectionMessages = [
    "Je viens voir de plus près... 🧐",
    "Tiens, c'est quoi ce détail ? 🔍",
    "Inspection technique des pixels... ⚙️",
    "Vous me voyez mieux comme ça ? 👀",
    "Hé ! Salut toi ! 👋",
    "Je vérifie si vous êtes attentifs ! 🤓",
    "Zoom avant ! 🔭",
    "Pas de triche dans le public hein ? 👮"
];

// --- SCÉNARIO D'INTRO ---
const introScript = [
    { time: 1.0, text: "Hum... C'est allumé ? 🎤", action: "look_around" },
    { time: 5.0, text: "Y'a quelqu'un dans cet écran ? 🤔", action: "approach" },
    { time: 8.5, text: "TOC ! TOC ! OUVREZ ! ✊", action: "knock" },
    { time: 12.0, text: "WOUAH ! 😱 Vous êtes nombreux !", action: "recoil" },
    { time: 16.0, text: "Bienvenue au Concours Vidéo 2026 ! ✨", action: "present" },
    { time: 20.0, text: "Installez-vous, ça va bientôt commencer ! ⏳", action: "wait" }
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
    
    // Historique pour éviter les répétitions
    let lastMsgIndex = -1;
    let lastInspectMsgIndex = -1;
    
    let bubbleTimeout = null;

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
            } else if (time > 24) { // Fin de l'intro prolongée
                robotState = 'moving';
                pickNewTarget();
                nextEventTime = time + 5;
            }

            // Mouvements Intro
            if (time < 5.0) { // Regarde
                robotGroup.rotation.y = Math.sin(time) * 0.3;
            }
            else if (time >= 5.0 && time < 8.5) { // Approche
                robotGroup.position.lerp(new THREE.Vector3(0, 0, 5), 0.02);
                robotGroup.rotation.y *= 0.95; 
            } 
            else if (time >= 8.5 && time < 12.0) { // Toc Toc
                robotGroup.position.z = 5 + Math.sin(time * 20) * 0.02; 
                rightArm.rotation.x = -Math.PI/2 + Math.sin(time * 15) * 0.3; 
            } 
            else if (time >= 12.0 && time < 24) { // Recul et attente
                robotGroup.position.lerp(new THREE.Vector3(3.5, 0, 0), 0.03);
                rightArm.rotation.x *= 0.9;
                robotGroup.rotation.y = -0.2; 
            }
        } 
        
        // --- PHASE 2 : PATROUILLE ---
        else if (robotState === 'moving') {
            robotGroup.position.lerp(targetPosition, 0.008);
            robotGroup.rotation.y += (targetPosition.x - robotGroup.position.x) * 0.05 - robotGroup.rotation.y * 0.05;
            robotGroup.rotation.z = -(targetPosition.x - robotGroup.position.x) * 0.02;
            robotGroup.position.y += Math.sin(time * 1.5) * 0.001;
            
            leftArm.rotation.x = Math.sin(time * 2) * 0.1;
            rightArm.rotation.x = -Math.sin(time * 2) * 0.1;

            if (robotGroup.position.distanceTo(targetPosition) < 0.5) {
                pickNewTarget();
            }

            if (time > nextEventTime) {
                const rand = Math.random();
                if (rand < 0.35) { // Augmenté à 35% de chance d'inspection
                    startInspection(); 
                } else {
                    startSpeaking();   
                }
            }
        } 
        
        // --- PHASE 3 : PARLE ---
        else if (robotState === 'speaking') {
            robotGroup.position.y += Math.sin(time * 3) * 0.001;
            robotGroup.rotation.lerp(new THREE.Vector3(0,0,0), 0.05); 
            rightArm.rotation.z = Math.cos(time * 4) * 0.4 + 0.4; 
        }

        // --- PHASE 4 : INSPECTION ---
        else if (robotState === 'inspecting') {
            const inspectPos = new THREE.Vector3(Math.sin(time)*2, 0, 4.5);
            robotGroup.position.lerp(inspectPos, 0.02);
            robotGroup.rotation.y = Math.sin(time) * 0.2; 
            
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
        robotState = 'speaking';
        
        // Choix aléatoire sans répétition immédiate
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
            }
        }, 6000);
    }

    function startInspection() {
        robotState = 'inspecting';
        
        // Choix aléatoire message inspection sans répétition
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
        
        if (bubbleTimeout) {
            clearTimeout(bubbleTimeout);
            bubbleTimeout = null;
        }

        bubble.innerText = text;
        bubble.style.opacity = 1;
        
        if(duration) {
             bubbleTimeout = setTimeout(() => { 
                 hideBubble(); 
             }, duration);
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

        let finalX = Math.max(120, Math.min(width - 120, x));
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

    animate();
}
