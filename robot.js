import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// --- MESSAGES ---
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
    "C'est parti pour le show ! 🚀",
    "Bip bop... J'adore ce que je vois ! 🤖",
    "N'hésitez pas à faire des selfies avec moi ! 🤳"
];

const preTeleportMessages = [
    "Vous savez que je peux me téléporter ? ⚡",
    "Attention... Tour de magie ! 🎩",
    "Et hop ! Je disparais ! 💨",
    "Je vais voir ce qu'il se passe là-bas... 🔭",
    "3... 2... 1... Disparition ! ⏱️"
];

const postTeleportMessages = [
    "Coucou ! Je suis là ! 👋",
    "Me revoilà ! Surprise ! 🎁",
    "C'était rapide, non ? 🚀",
    "Tadaaa ! ✨",
    "Vous ne m'avez pas vu venir ? 😎"
];

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
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.1);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 2.5);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);
    // Lumière bleue douce pour l'ambiance écran
    const screenLight = new THREE.PointLight(0x00ffff, 0.5, 2);
    screenLight.position.set(0, 0, 1.5);
    scene.add(screenLight);

    // --- ROBOT CONSTRUCTION ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
    
    // MATERIAUX
    // Coque blanche brillante (plastique)
    const whiteShellMat = new THREE.MeshStandardMaterial({ 
        color: 0xffffff, 
        roughness: 0.1, 
        metalness: 0.1 
    });
    // Ecran noir brillant (verre)
    const blackScreenMat = new THREE.MeshStandardMaterial({ 
        color: 0x050505, 
        roughness: 0.0, 
        metalness: 0.8 
    });
    // Glow Bleu (Yeux/Bouche)
    const glowMat = new THREE.MeshBasicMaterial({ color: 0x00ffff }); 
    // Détails gris
    const greyMat = new THREE.MeshStandardMaterial({ color: 0xcccccc });

    // 1. TÊTE (Forme "Squircle" arrondie)
    // On utilise une sphère qu'on déforme pour faire un cube arrondi
    const headGeo = new THREE.SphereGeometry(0.8, 64, 64); 
    const head = new THREE.Mesh(headGeo, whiteShellMat);
    head.scale.set(1.2, 0.85, 0.85); // Élargie et un peu aplatie
    
    // 2. ÉCRAN NOIR (Visage)
    // Une sphère un peu plus petite qui ressort devant
    const faceGeo = new THREE.SphereGeometry(0.7, 64, 64);
    const face = new THREE.Mesh(faceGeo, blackScreenMat);
    face.scale.set(1.05, 0.8, 0.5); // Aplatie en profondeur
    face.position.set(0, 0, 0.42); // Poussée vers l'avant
    head.add(face);

    // 3. YEUX (Arches Joyeuses ^ ^)
    // On utilise un Torus coupé pour faire l'arche
    const eyeGeo = new THREE.TorusGeometry(0.12, 0.03, 8, 32, Math.PI); 
    
    const leftEye = new THREE.Mesh(eyeGeo, glowMat);
    leftEye.position.set(-0.25, 0.1, 0.82); // Devant l'écran noir
    leftEye.rotation.z = 0; // Arche vers le haut (content)
    head.add(leftEye);

    const rightEye = new THREE.Mesh(eyeGeo, glowMat);
    rightEye.position.set(0.25, 0.1, 0.82);
    rightEye.rotation.z = 0;
    head.add(rightEye);

    // 4. BOUCHE (Sourire u)
    const mouthGeo = new THREE.TorusGeometry(0.08, 0.03, 8, 32, Math.PI);
    const mouth = new THREE.Mesh(mouthGeo, glowMat);
    mouth.position.set(0, -0.15, 0.80);
    mouth.rotation.z = Math.PI; // Inversé pour faire un U
    head.add(mouth);

    // 5. OREILLES (Disques sur les cotés)
    const earGeo = new THREE.CylinderGeometry(0.25, 0.25, 0.1, 32);
    earGeo.rotateZ(Math.PI / 2);
    
    const leftEar = new THREE.Mesh(earGeo, whiteShellMat);
    leftEar.position.set(-0.95, 0, 0);
    head.add(leftEar);
    
    const rightEar = new THREE.Mesh(earGeo, whiteShellMat);
    rightEar.position.set(0.95, 0, 0);
    head.add(rightEar);

    // 6. CORPS (Œuf)
    const bodyGeo = new THREE.SphereGeometry(0.65, 32, 32);
    const body = new THREE.Mesh(bodyGeo, whiteShellMat);
    body.scale.set(0.9, 1.1, 0.8); // Forme d'oeuf
    body.position.set(0, -1.0, 0); // Sous la tête
    
    // Détail Gris (Ventre/Ceinture)
    const beltGeo = new THREE.TorusGeometry(0.6, 0.02, 16, 64);
    const belt = new THREE.Mesh(beltGeo, greyMat);
    belt.rotation.x = Math.PI / 2;
    belt.position.set(0, -0.1, 0);
    body.add(belt);

    // 7. BRAS (Simples et mignons)
    const armGeo = new THREE.CapsuleGeometry(0.12, 0.6, 4, 16);
    
    const leftArm = new THREE.Mesh(armGeo, whiteShellMat);
    leftArm.position.set(-0.75, -0.8, 0);
    leftArm.rotation.z = 0.2; // Légèrement écarté
    
    const rightArm = new THREE.Mesh(armGeo, whiteShellMat);
    rightArm.position.set(0.75, -0.8, 0);
    rightArm.rotation.z = -0.2;

    robotGroup.add(head);
    robotGroup.add(body);
    robotGroup.add(leftArm);
    robotGroup.add(rightArm);
    scene.add(robotGroup);

    // --- PARTICULES (Fumée Téléportation) ---
    const particleCount = 200; 
    const particlesGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    for(let i=0; i<particleCount*3; i++) positions[i] = 999;
    particlesGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particleMat = new THREE.PointsMaterial({ color: 0x00ffff, size: 0.15, transparent: true, opacity: 0.8 });
    const particleSystem = new THREE.Points(particlesGeo, particleMat);
    scene.add(particleSystem);
    let particleData = Array(particleCount).fill().map(() => ({ velocity: new THREE.Vector3(), active: false }));

    // --- VARIABLES LOGIQUES ---
    let time = 0;
    let targetPosition = new THREE.Vector3(3.5, 0, 0); 
    robotGroup.position.copy(targetPosition);
    let robotState = 'intro'; 
    let introIndex = 0;
    let nextEventTime = 0;
    let bubbleTimeout = null;
    let lastMsgIndex = -1;

    // Fonction de lissage
    function smoothRotate(object, axis, targetValue, speed) {
        object.rotation[axis] += (targetValue - object.rotation[axis]) * speed;
    }

    // --- ANIMATION LOOP ---
    function animate() {
        requestAnimationFrame(animate);
        time += 0.015; 

        // Gestion Z-Index (Passe devant/derrière)
        if (robotGroup.position.z > 2) container.style.zIndex = "15";
        else container.style.zIndex = "1";

        // Animation de flottement global
        const floatY = Math.sin(time * 2) * 0.002;
        robotGroup.position.y += floatY;

        // ETATS DU ROBOT
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
            // Scénario Intro
            if (time < 5.0) robotGroup.rotation.y = Math.sin(time) * 0.3;
            else if (time >= 5.0 && time < 8.5) { 
                robotGroup.position.lerp(new THREE.Vector3(0, 0, 5), 0.02);
                smoothRotate(robotGroup, 'y', 0, 0.05);
            } 
            else if (time >= 8.5 && time < 12.0) { 
                // Toc Toc (Le bras bouge)
                robotGroup.position.z = 5 + Math.sin(time * 20) * 0.02; 
                rightArm.rotation.x = -Math.PI/2 + Math.sin(time * 15) * 0.3; 
            } 
            else if (time >= 12.0 && time < 24) { 
                // Recul
                robotGroup.position.lerp(new THREE.Vector3(3.5, 0, 0), 0.03);
                rightArm.rotation.x *= 0.9;
                smoothRotate(robotGroup, 'y', -0.2, 0.05);
            }
        } 
        
        else if (robotState === 'moving') {
            robotGroup.position.lerp(targetPosition, 0.008);
            
            // Le robot penche légèrement vers sa destination
            const targetRotY = (targetPosition.x - robotGroup.position.x) * 0.05;
            const targetRotZ = -(targetPosition.x - robotGroup.position.x) * 0.03;
            smoothRotate(robotGroup, 'y', targetRotY, 0.05);
            smoothRotate(robotGroup, 'z', targetRotZ, 0.05);
            
            // Animation des bras (marche/vol)
            leftArm.rotation.x = Math.sin(time * 3) * 0.15;
            rightArm.rotation.x = -Math.sin(time * 3) * 0.15;

            if (robotGroup.position.distanceTo(targetPosition) < 0.5) pickNewTarget();

            if (time > nextEventTime) {
                const rand = Math.random();
                if (rand < 0.25) startTeleportSequence(); 
                else if (rand < 0.50) startInspection();
                else startSpeaking();
            }
        } 
        
        else if (robotState === 'speaking') {
            robotGroup.position.lerp(targetPosition, 0.001); 
            smoothRotate(robotGroup, 'y', 0, 0.05); // Regarde face
            smoothRotate(robotGroup, 'z', 0, 0.05);
            // Animation de la bouche (le Torus vibre un peu en échelle)
            const talkScale = 1 + Math.sin(time * 20) * 0.2;
            mouth.scale.set(1, talkScale, 1);
            // Bras qui s'ouvre
            rightArm.rotation.z = Math.cos(time * 4) * 0.4 + 0.4; 
        }

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

        else if (robotState === 'teleport_pre') {
            robotGroup.position.y += Math.sin(time * 15) * 0.01; // Tremble
            smoothRotate(robotGroup, 'y', 0, 0.1);
            if (time > nextEventTime) {
                hideBubble();
                triggerSmoke(robotGroup.position.x, robotGroup.position.y);
                robotState = 'disappear';
            }
        }
        else if (robotState === 'disappear') {
            robotGroup.scale.multiplyScalar(0.85);
            robotGroup.rotation.y += 0.8;
            if (robotGroup.scale.x < 0.01) {
                pickNewTarget();
                robotGroup.position.copy(targetPosition);
                triggerSmoke(targetPosition.x, targetPosition.y);
                robotState = 'reappear';
            }
        }
        else if (robotState === 'reappear') {
            robotGroup.scale.multiplyScalar(1.2);
            if (robotGroup.scale.x >= 0.45) {
                robotGroup.scale.set(0.45, 0.45, 0.45);
                robotGroup.rotation.set(0,0,0);
                const msg = postTeleportMessages[Math.floor(Math.random() * postTeleportMessages.length)];
                showBubble(msg, 3000);
                robotState = 'teleport_post';
                nextEventTime = time + 3;
            }
        }
        else if (robotState === 'teleport_post') {
            if (time > nextEventTime) {
                hideBubble();
                robotState = 'moving';
                nextEventTime = time + 10;
            }
        }

        // Reset bouche si ne parle pas
        if(robotState !== 'speaking') {
             mouth.scale.set(1, 1, 1);
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
        targetPosition.copy(robotGroup.position);
        let newIndex;
        do { newIndex = Math.floor(Math.random() * messages.length); } while (newIndex === lastMsgIndex);
        lastMsgIndex = newIndex;

        showBubble(messages[newIndex], 6000); 
        nextEventTime = time + 10 + Math.random() * 15; 
        
        setTimeout(() => {
            if (robotState === 'speaking') {
                hideBubble();
                robotState = 'moving';
                pickNewTarget();
            }
        }, 6000);
    }

    function startInspection() {
        robotState = 'inspecting';
        showBubble("Je viens voir de plus près... 🧐", 3000);
        nextEventTime = time + 6; 
    }

    function startTeleportSequence() {
        robotState = 'teleport_pre';
        const msg = preTeleportMessages[Math.floor(Math.random() * preTeleportMessages.length)];
        showBubble(msg, 2500);
        nextEventTime = time + 2.5;
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
        for(let i=0; i<particleCount; i++) {
            if (!particleData[i].active || true) { 
                particleData[i].active = true;
                posAttr.setXYZ(i, x + (Math.random()-0.5)*1.5, y + (Math.random()-0.5)*1.5, (Math.random()-0.5)*1.5);
                particleData[i].velocity.set(
                    (Math.random()-0.5)*0.1, 
                    (Math.random()-0.5)*0.1 + 0.05,
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
                particleData[i].velocity.y += 0.002;
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
