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

// --- PALETTE DE COULEURS ---
const colorPalette = [
    new THREE.Color(0x3388ff), // Bleu Tech
    new THREE.Color(0xff8800), // Orange
    new THREE.Color(0x8a2be2), // Violet
    new THREE.Color(0xE2001A)  // Rouge Corporate
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
    const coloredMat = new THREE.MeshStandardMaterial({ color: 0x3388ff, roughness: 0.2 }); 
    const glowMat = new THREE.MeshBasicMaterial({ color: 0xe0ffff }); 
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x222222 });
    const pupilMat = new THREE.MeshBasicMaterial({ color: 0x000000 });

    // TÊTE
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.7, 32, 32), whiteMat);
    
    // Visage (Masque courbé pour éviter le "nez")
    const faceGeo = new THREE.SphereGeometry(0.71, 32, 32, 0, Math.PI * 2, 0, 0.65);
    const face = new THREE.Mesh(faceGeo, darkMat);
    face.rotation.x = -Math.PI / 2; 
    head.add(face);

    // --- HABILLAGE (POUR EVITER L'EFFET CHAUVE) ---
    
    // 1. Oreilles / Casque (Cylindres sur les côtés)
    const earGeo = new THREE.CylinderGeometry(0.2, 0.2, 0.1, 32);
    earGeo.rotateZ(Math.PI / 2); // Orienter vers le côté
    
    const leftEar = new THREE.Mesh(earGeo, coloredMat);
    leftEar.position.set(-0.68, 0, 0); // Collé sur le côté gauche
    head.add(leftEar);

    const rightEar = new THREE.Mesh(earGeo, coloredMat);
    rightEar.position.set(0.68, 0, 0); // Collé sur le côté droit
    head.add(rightEar);

    // 2. Bande centrale (Petite crête technologique sur le dessus)
    // Une bande fine qui traverse le haut du crâne
    const crestGeo = new THREE.TorusGeometry(0.71, 0.05, 4, 32, Math.PI); 
    const crest = new THREE.Mesh(crestGeo, coloredMat);
    crest.rotation.y = Math.PI / 2; // Dans l'axe avant-arrière
    crest.position.set(0, 0, 0);
    head.add(crest);


    // --- YEUX PLUS MIGNONS (Pupilles plus grosses) ---
    const eyeScale = 0.12; 
    const eyeBallGeo = new THREE.SphereGeometry(eyeScale, 16, 16);
    eyeBallGeo.scale(1.2, 1, 0.6); 
    
    // Pupille agrandie (x0.7 au lieu de x0.4) pour faire moins "regard fixe effrayant"
    const pupilGeo = new THREE.SphereGeometry(eyeScale * 0.7, 12, 12);
    pupilGeo.scale(1, 1, 0.5);

    function createEye() {
        const eyeGroup = new THREE.Group();
        const ball = new THREE.Mesh(eyeBallGeo, glowMat);
        const pupil = new THREE.Mesh(pupilGeo, pupilMat);
        pupil.position.z = eyeScale * 0.55; 
        eyeGroup.add(ball);
        eyeGroup.add(pupil);
        return eyeGroup;
    }
    const leftEyeGrp = createEye();
    leftEyeGrp.position.set(-0.20, 0.10, 0.68); 
    const rightEyeGrp = createEye();
    rightEyeGrp.position.set(0.20, 0.10, 0.68);
    
    head.add(leftEyeGrp);
    head.add(rightEyeGrp);

    // --- ANTENNE (Sur le dessus, sortant de la crête) ---
    const antennaPole = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.6), whiteMat);
    antennaPole.position.set(0, 1.0, 0); 
    head.add(antennaPole);
    const antennaTip = new THREE.Mesh(new THREE.SphereGeometry(0.08), coloredMat);
    antennaTip.position.set(0, 1.35, 0); 
    head.add(antennaTip);

    // --- ONDES RADIO ---
    const waveGroup = new THREE.Group();
    waveGroup.position.set(0, 1.35, 0);
    head.add(waveGroup);
    const waveMat = new THREE.MeshBasicMaterial({ color: 0x00ffff, transparent: true, opacity: 0, side: THREE.DoubleSide });
    const waves = [];
    for(let i=0; i<3; i++) {
        const wave = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.03, 8, 32), waveMat.clone());
        wave.rotation.x = Math.PI / 2; 
        wave.scale.set(0,0,0);
        waves.push(wave);
        waveGroup.add(wave);
    }

    // Corps & Bras
    const body = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.55, 0.9, 32), whiteMat);
    body.position.y = -0.9;
    function createArm(x) {
        const g = new THREE.Group();
        g.position.set(x, -0.7, 0);
        const s = new THREE.Mesh(new THREE.SphereGeometry(0.2), coloredMat); 
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

    // --- PARTICULES (Fumée) ---
    const particleCount = 150; 
    const particlesGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    for(let i=0; i<particleCount*3; i++) positions[i] = 999;
    particlesGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particleMat = new THREE.PointsMaterial({ color: 0xaaeeff, size: 0.2, transparent: true, opacity: 0.8 });
    const particleSystem = new THREE.Points(particlesGeo, particleMat);
    scene.add(particleSystem);
    let particleData = Array(particleCount).fill().map(() => ({ velocity: new THREE.Vector3(), active: false }));

    // --- VARIABLES ---
    let time = 0;
    let targetPosition = new THREE.Vector3(3.5, 0, 0); 
    robotGroup.position.copy(targetPosition);
    let robotState = 'intro'; 
    let introIndex = 0;
    let nextEventTime = 0;
    let bubbleTimeout = null;
    let eyeTargetX = 0; let eyeTargetY = 0; let nextEyeMoveTime = 0;
    
    // Variables Couleur & Ondes
    let colorIndex = 0;
    let colorTimer = 0;
    let isReceivingTransmission = false;
    let transmissionTimer = 0;
    let nextTransmissionTime = 25;

    function smoothRotate(object, axis, targetValue, speed) {
        object.rotation[axis] += (targetValue - object.rotation[axis]) * speed;
    }

    // --- ANIMATION LOOP ---
    function animate() {
        requestAnimationFrame(animate);
        time += 0.015; 

        // 1. CHANGEMENT DE COULEUR (Toutes les 30s)
        colorTimer += 0.015;
        if (colorTimer > 30) { 
            colorIndex = (colorIndex + 1) % colorPalette.length;
            colorTimer = 0;
        }
        coloredMat.color.lerp(colorPalette[colorIndex], 0.005); 

        // 2. Z-INDEX DYNAMIQUE
        if (robotGroup.position.z > 2) container.style.zIndex = "15";
        else container.style.zIndex = "1";

        // 3. YEUX AUTONOMES
        if (time > nextEyeMoveTime) {
            eyeTargetY = (Math.random() - 0.5) * 0.5;
            eyeTargetX = (Math.random() - 0.5) * 0.5;
            nextEyeMoveTime = time + 1 + Math.random() * 3;
        }
        smoothRotate(leftEyeGrp, 'x', eyeTargetY, 0.1);
        smoothRotate(leftEyeGrp, 'y', eyeTargetX, 0.1);
        smoothRotate(rightEyeGrp, 'x', eyeTargetY, 0.1);
        smoothRotate(rightEyeGrp, 'y', eyeTargetX, 0.1);

        // 4. GESTION ONDES RADIO
        if (time > nextTransmissionTime && !isReceivingTransmission && robotState === 'moving') {
            isReceivingTransmission = true;
            transmissionTimer = 0;
            waves.forEach((w, i) => {
                w.scale.set(0.01, 0.01, 0.01);
                w.material.opacity = 1;
                w.userData.startTime = transmissionTimer + i * 0.3;
            });
        }

        if (isReceivingTransmission) {
            transmissionTimer += 0.03;
            let allWavesDone = true;
            waves.forEach(w => {
                if(transmissionTimer >= w.userData.startTime) {
                     const localTime = transmissionTimer - w.userData.startTime;
                     const scale = 0.1 + localTime * 3.0; 
                     w.scale.set(scale, scale, scale);
                     w.material.opacity = Math.max(0, 1 - localTime * 1.0);
                     if(w.material.opacity > 0) allWavesDone = false;
                } else {
                     allWavesDone = false; 
                }
            });
            if (allWavesDone && transmissionTimer > 2.0) {
                isReceivingTransmission = false;
                nextTransmissionTime = time + 20 + Math.random() * 30; 
            }
        }

        // --- ETATS DU ROBOT ---

        // PHASE 1 : INTRO
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
        
        // PHASE 2 : PATROUILLE
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

            if (time > nextEventTime && !isReceivingTransmission) {
                const rand = Math.random();
                if (rand < 0.25) startTeleportSequence(); 
                else if (rand < 0.50) startInspection();
                else startSpeaking();
            }
        } 
        
        // PHASE 3 : PARLE
        else if (robotState === 'speaking') {
            robotGroup.position.lerp(targetPosition, 0.001); 
            robotGroup.position.y += Math.sin(time * 3) * 0.001;
            smoothRotate(robotGroup, 'y', 0, 0.05);
            smoothRotate(robotGroup, 'z', 0, 0.05);
            rightArm.rotation.z = Math.cos(time * 4) * 0.4 + 0.4; 
        }

        // PHASE 4 : INSPECTION
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

        // PHASE 5 : SEQUENCE TELEPORTATION
        else if (robotState === 'teleport_pre') {
            robotGroup.position.y += Math.sin(time * 15) * 0.008; 
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
        const msg = messages[Math.floor(Math.random() * messages.length)];
        showBubble(msg, 6000); 
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
