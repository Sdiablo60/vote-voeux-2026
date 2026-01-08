import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// --- MESSAGES CLASSIQUES ---
const messages = [
    "Salut l'équipe ! 👋",
    "Tout le monde est bien installé ? 💺",
    "Je vérifie les objectifs... 🧐",
    "Qui a le plus beau sourire ce soir ? 📸",
    "Silence... Moteur... Ça tourne ! 🎬",
    "N'oubliez pas de voter ! 🗳️",
    "Quelle ambiance de folie ! 🎉",
    "Je suis Clap-E, votre assistant ! 🤖",
    "Il fait chaud sous les spots, non ? 💡",
    "J'espère qu'il y a des petits fours... 🍪",
    "Vous me voyez bien ? 👀",
    "C'est parti pour le show ! 🚀"
];

// --- MESSAGES AVANT TÉLÉPORTATION ---
const preTeleportMessages = [
    "Vous savez que je peux me téléporter ? ⚡",
    "Attention... Tour de magie ! 🎩",
    "Et hop ! Je disparais ! 💨",
    "Je vais voir ce qu'il se passe là-bas... 🔭",
    "3... 2... 1... Disparition ! ⏱️"
];

// --- MESSAGES APRÈS TÉLÉPORTATION ---
const postTeleportMessages = [
    "Coucou ! Je suis là ! 👋",
    "Me revoilà ! Surprise ! 🎁",
    "C'était rapide, non ? 🚀",
    "Tadaaa ! ✨",
    "Vous ne m'avez pas vu venir ? 😎"
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
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x222222 }); // Gris très foncé pour le visage

    // Tête
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.7, 32, 32), whiteMat);
    const face = new THREE.Mesh(new THREE.CircleGeometry(0.55, 32), darkMat);
    face.position.set(0, 0, 0.68);
    head.add(face);

    // Yeux (plus doux, ovales)
    const eyeGeo = new THREE.CapsuleGeometry(0.1, 0.15, 4, 8); 
    const leftEye = new THREE.Mesh(eyeGeo, glowMat);
    leftEye.rotation.z = Math.PI / 2; // Ovale horizontal
    leftEye.position.set(-0.25, 0.15, 0.70);
    
    const rightEye = new THREE.Mesh(eyeGeo, glowMat);
    rightEye.rotation.z = Math.PI / 2;
    rightEye.position.set(0.25, 0.15, 0.70);
    
    head.add(leftEye); head.add(rightEye);

    // --- LE SOURIRE (NOUVEAU) ---
    // Un demi-cercle (Torus) pour faire la bouche
    const smileGeo = new THREE.TorusGeometry(0.2, 0.03, 16, 32, Math.PI); 
    const smile = new THREE.Mesh(smileGeo, glowMat);
    smile.position.set(0, -0.15, 0.70); // Sous les yeux
    smile.rotation.z = Math.PI; // Tourner pour faire un U (sourire)
    head.add(smile);

    // Corps
    const body = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.55, 0.9, 32), whiteMat);
    body.position.y = -0.9;

    // Bras
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

    // --- PARTICULES (FUMÉE) ---
    // On augmente la quantité pour l'effet téléportation
    const particleCount = 150; 
    const particlesGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    for(let i=0; i<particleCount*3; i++) positions[i] = 999;
    particlesGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particleMat = new THREE.PointsMaterial({ color: 0xaaeeff, size: 0.2, transparent: true, opacity: 0.8 });
    const particleSystem = new THREE.Points(particlesGeo, particleMat);
    scene.add(particleSystem);
    let particleData = Array(particleCount).fill().map(() => ({ velocity: new THREE.Vector3(), active: false }));

    // --- VARIABLES DE NAVIGATION ---
    let time = 0;
    let targetPosition = new THREE.Vector3(3.5, 0, 0); 
    robotGroup.position.copy(targetPosition);
    
    // États: intro, moving, speaking, inspecting, teleport_pre, disappear, reappear, teleport_post
    let robotState = 'intro'; 
    let introIndex = 0;
    let nextEventTime = 0;
    
    let lastMsgIndex = -1;
    let bubbleTimeout = null;

    // --- FONCTION LISSAGE ---
    function smoothRotate(object, axis, targetValue, speed) {
        object.rotation[axis] += (targetValue - object.rotation[axis]) * speed;
    }

    // --- ANIMATION ---
    function animate() {
        requestAnimationFrame(animate);
        time += 0.015; 

        // Z-INDEX
        if (robotGroup.position.z > 2) container.style.zIndex = "15";
        else container.style.zIndex = "1";

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
            if (time < 5.0) robotGroup.rotation.y = Math.sin(time) * 0.3;
            else if (time >= 5.0 && time < 8.5) { 
                robotGroup.position.lerp(new THREE.Vector3(0, 0, 5), 0.02);
                smoothRotate(robotGroup, 'y', 0, 0.05);
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
            robotGroup.position.lerp(targetPosition, 0.008);
            
            const targetRotY = (targetPosition.x - robotGroup.position.x) * 0.05;
            const targetRotZ = -(targetPosition.x - robotGroup.position.x) * 0.02;
            smoothRotate(robotGroup, 'y', targetRotY, 0.05);
            smoothRotate(robotGroup, 'z', targetRotZ, 0.05);
            
            robotGroup.position.y += Math.sin(time * 1.5) * 0.001;
            leftArm.rotation.x = Math.sin(time * 2) * 0.1;
            rightArm.rotation.x = -Math.sin(time * 2) * 0.1;

            if (robotGroup.position.distanceTo(targetPosition) < 0.5) pickNewTarget();

            if (time > nextEventTime) {
                const rand = Math.random();
                if (rand < 0.20) startTeleportSequence(); // 20% Téléport
                else if (rand < 0.40) startInspection();  // 20% Inspection
                else startSpeaking();                     // 60% Parole standard
            }
        } 
        
        // --- PHASE 3 : PARLE (Freinage Doux) ---
        else if (robotState === 'speaking') {
            robotGroup.position.lerp(targetPosition, 0.001); 
            robotGroup.position.y += Math.sin(time * 3) * 0.001;
            smoothRotate(robotGroup, 'y', 0, 0.05);
            smoothRotate(robotGroup, 'z', 0, 0.05);
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
                nextEventTime = time + 8 + Math.random() * 8;
            }
        }

        // --- PHASE 5 : SEQUENCE TELEPORTATION ---
        
        // 5a. Annonce ("Attention...")
        else if (robotState === 'teleport_pre') {
            robotGroup.position.y += Math.sin(time * 10) * 0.005; // Tremble d'excitation
            smoothRotate(robotGroup, 'y', 0, 0.1);
            if (time > nextEventTime) {
                // Déclenchement disparition
                hideBubble();
                triggerSmoke(robotGroup.position.x, robotGroup.position.y); // FUMÉE DÉPART
                robotState = 'disappear';
            }
        }

        // 5b. Disparition (Rapide)
        else if (robotState === 'disappear') {
            robotGroup.scale.multiplyScalar(0.85); // Rétrécit vite
            robotGroup.rotation.y += 0.8; // Toupie
            
            if (robotGroup.scale.x < 0.01) {
                // Changement de position
                pickNewTarget();
                robotGroup.position.copy(targetPosition);
                
                // Préparation réapparition
                triggerSmoke(targetPosition.x, targetPosition.y); // FUMÉE ARRIVÉE
                robotState = 'reappear';
            }
        }

        // 5c. Réapparition
        else if (robotState === 'reappear') {
            robotGroup.scale.multiplyScalar(1.2); // Grandit
            if (robotGroup.scale.x >= 0.45) {
                robotGroup.scale.set(0.45, 0.45, 0.45);
                robotGroup.rotation.set(0,0,0);
                
                // Message "Coucou"
                const msg = postTeleportMessages[Math.floor(Math.random() * postTeleportMessages.length)];
                showBubble(msg, 3000);
                
                robotState = 'teleport_post';
                nextEventTime = time + 3; // Reste 3s pour qu'on le voie
            }
        }

        // 5d. Pause après téléportation
        else if (robotState === 'teleport_post') {
            if (time > nextEventTime) {
                hideBubble();
                robotState = 'moving';
                nextEventTime = time + 10;
            }
        }

        updateSmoke();
        updateBubblePosition();
        renderer.render(scene, camera);
    }

    function pickNewTarget() {
        const aspect = width / height;
        const vW = 7 * aspect; 
        let x, y;
        if (Math.random() > 0.5) x = 3.0 + Math.random() * (vW * 0.4 - 3.0); 
        else x = -3.0 - Math.random() * (vW * 0.4 - 3.0); 
        y = (Math.random() - 0.5) * 3; 
        targetPosition.set(x, y, 0);
    }

    function startSpeaking() {
        robotState = 'speaking';
        let newIndex;
        do { newIndex = Math.floor(Math.random() * messages.length); } while (newIndex === lastMsgIndex);
        lastMsgIndex = newIndex;

        showBubble(messages[newIndex], 5000); 
        nextEventTime = time + 8 + Math.random() * 10; 
        
        setTimeout(() => {
            if (robotState === 'speaking') {
                hideBubble();
                robotState = 'moving';
            }
        }, 5000);
    }

    function startInspection() {
        robotState = 'inspecting';
        showBubble("Je viens voir de plus près... 🧐", 3000);
        nextEventTime = time + 5; 
    }

    function startTeleportSequence() {
        robotState = 'teleport_pre';
        const msg = preTeleportMessages[Math.floor(Math.random() * preTeleportMessages.length)];
        showBubble(msg, 2500);
        nextEventTime = time + 2.5; // Temps de lecture avant disparition
    }

    function showBubble(text, duration) {
        if(!bubble) return;
        if (bubbleTimeout) { clearTimeout(bubbleTimeout); bubbleTimeout = null; }
        bubble.innerText = text;
        bubble.style.opacity = 1;
        if(duration) bubbleTimeout = setTimeout(() => { hideBubble(); }, duration);
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

    function triggerSmoke(x, y) {
        const posAttr = particleSystem.geometry.attributes.position;
        // On active toutes les particules pour une grosse explosion
        for(let i=0; i<particleCount; i++) {
            if (!particleData[i].active || true) { // Force activation
                particleData[i].active = true;
                // Nuage autour du point
                posAttr.setXYZ(i, x + (Math.random()-0.5)*1.5, y + (Math.random()-0.5)*1.5, (Math.random()-0.5)*1.5);
                // Vitesse explosive
                particleData[i].velocity.set(
                    (Math.random()-0.5)*0.1, 
                    (Math.random()-0.5)*0.1 + 0.05, // Tendance à monter
                    (Math.random()-0.5)*0.1
                );
            }
        }
        posAttr.needsUpdate = true;
    }

    function updateSmoke() {
        const posAttr = particleSystem.geometry.attributes.position;
        for(let i=0; i<particleCount; i++) {
            if (particleData[i].active) {
                posAttr.setXYZ(i, 
                    posAttr.getX(i) + particleData[i].velocity.x, 
                    posAttr.getY(i) + particleData[i].velocity.y, 
                    posAttr.getZ(i) + particleData[i].velocity.z
                );
                particleData[i].velocity.y += 0.002; // Monte doucement
                // Disparaît si trop haut ou timer (simulé par hauteur ici)
                if (posAttr.getY(i) > 5) { 
                    particleData[i].active = false; 
                    posAttr.setXYZ(i, 999,999,999); 
                }
            }
        }
        posAttr.needsUpdate = true;
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
