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
    "C'est parti pour le show ! 🚀",
    "Bip bop... J'adore ce que je vois ! 🤖",
    "N'hésitez pas à faire des selfies avec moi (de loin) ! 🤳"
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

    // --- ROBOT SETUP ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
    
    // Matériaux
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blueMat = new THREE.MeshStandardMaterial({ color: 0x3388ff, roughness: 0.2 });
    // Le glowMat sert maintenant pour le blanc des yeux
    const glowMat = new THREE.MeshBasicMaterial({ color: 0xe0ffff }); 
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x222222 });
    const pupilMat = new THREE.MeshBasicMaterial({ color: 0x000000 }); // Noir pur pour pupilles

    // Tête & Visage
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.7, 32, 32), whiteMat);
    const face = new THREE.Mesh(new THREE.CircleGeometry(0.55, 32), darkMat);
    face.position.set(0, 0, 0.68);
    head.add(face);

    // --- NOUVEAUX YEUX (Globes + Pupilles mobiles) ---
    const eyeScale = 0.18;
    // Géométrie du globe oculaire (sphère aplatie)
    const eyeBallGeo = new THREE.SphereGeometry(eyeScale, 16, 16);
    eyeBallGeo.scale(1.2, 1, 0.4); // Aplati

    // Géométrie de la pupille
    const pupilGeo = new THREE.SphereGeometry(eyeScale * 0.4, 12, 12);
    pupilGeo.scale(1, 1, 0.5);

    // Fonction pour créer un œil complet
    function createEye() {
        const eyeGroup = new THREE.Group();
        const ball = new THREE.Mesh(eyeBallGeo, glowMat);
        const pupil = new THREE.Mesh(pupilGeo, pupilMat);
        pupil.position.z = eyeScale * 0.35; // Légèrement devant le globe
        eyeGroup.add(ball);
        eyeGroup.add(pupil);
        return eyeGroup;
    }

    const leftEyeGrp = createEye();
    leftEyeGrp.position.set(-0.25, 0.15, 0.68);
    
    const rightEyeGrp = createEye();
    rightEyeGrp.position.set(0.25, 0.15, 0.68);
    
    head.add(leftEyeGrp);
    head.add(rightEyeGrp);

    // --- NOUVELLE BOUCHE ANIMÉE ---
    // Une simple pastille aplatie qui va changer d'échelle
    const mouthGeo = new THREE.SphereGeometry(0.1, 16, 8);
    mouthGeo.scale(1.5, 0.2, 0.1); // Forme de trait au repos
    const robotMouth = new THREE.Mesh(mouthGeo, glowMat);
    robotMouth.position.set(0, -0.2, 0.70);
    head.add(robotMouth);

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

    // --- PARTICULES ---
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

    // Variables pour l'animation des yeux
    let eyeTargetX = 0;
    let eyeTargetY = 0;
    let nextEyeMoveTime = 0;

    // FONCTION LISSAGE
    function smoothRotate(object, axis, targetValue, speed) {
        object.rotation[axis] += (targetValue - object.rotation[axis]) * speed;
    }

    // --- ANIMATION LOOP ---
    function animate() {
        requestAnimationFrame(animate);
        time += 0.015; 

        // Z-INDEX DYNAMIQUE
        if (robotGroup.position.z > 2) container.style.zIndex = "15";
        else container.style.zIndex = "1";

        // --- ANIMATION DES YEUX (Autonome) ---
        // Change de cible de regard aléatoirement
        if (time > nextEyeMoveTime) {
            eyeTargetY = (Math.random() - 0.5) * 0.5; // Haut/Bas
            eyeTargetX = (Math.random() - 0.5) * 0.5; // Gauche/Droite
            nextEyeMoveTime = time + 1 + Math.random() * 3; // Prochain mouvement dans 1-4s
        }
        // Applique le mouvement fluide aux deux yeux
        smoothRotate(leftEyeGrp, 'x', eyeTargetY, 0.1);
        smoothRotate(leftEyeGrp, 'y', eyeTargetX, 0.1);
        smoothRotate(rightEyeGrp, 'x', eyeTargetY, 0.1);
        smoothRotate(rightEyeGrp, 'y', eyeTargetX, 0.1);


        // --- ANIMATION DE LA BOUCHE (Si il parle) ---
        if (robotState === 'speaking') {
            // Oscillation rapide de l'échelle Y pour simuler la parole
            // Base 0.2, variation +/- 0.15, vitesse rapide (time*30)
            const talkScale = 0.2 + Math.abs(Math.sin(time * 30)) * 0.25;
            robotMouth.scale.set(1.5, talkScale, 0.1);
        } else {
            // Retour à la position neutre (trait)
            robotMouth.scale.lerp(new THREE.Vector3(1.5, 0.2, 0.1), 0.2);
        }


        // --- LOGIQUE DES ÉTATS ---

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

            if (time > nextEventTime) {
                const rand = Math.random();
                if (rand < 0.25) startTeleportSequence(); 
                else if (rand < 0.50) startInspection();
                else startSpeaking();
            }
        } 
        
        // PHASE 3 : PARLE (Freinage Doux)
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
            robotGroup.position.y += Math.sin(time * 15) * 0.008; // Tremblement plus fort
            smoothRotate(robotGroup, 'y', 0, 0.1);
            // La bouche s'ouvre en grand "O" de surprise
            robotMouth.scale.lerp(new THREE.Vector3(1.0, 0.8, 0.1), 0.1);
            
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
        // On fige la cible sur la position actuelle pour le freinage
        targetPosition.copy(robotGroup.position);
        
        const msg = messages[Math.floor(Math.random() * messages.length)];
        showBubble(msg, 6000); 
        nextEventTime = time + 10 + Math.random() * 15; 
        
        setTimeout(() => {
            if (robotState === 'speaking') {
                hideBubble();
                robotState = 'moving';
                pickNewTarget(); // Relance le mouvement
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
        let finalX = Math.max(140, Math.min(width - 140, x));
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
