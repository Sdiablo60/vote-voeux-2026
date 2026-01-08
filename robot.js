import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

const messages = [
    "Salut l'équipe ! 👋",
    "Bienvenue aux Vœux 2026 ! ✨",
    "Je fais une petite pause... ☕",
    "Qui va gagner le trophée ? 🏆",
    "J'adore vos sourires 📸",
    "N'oubliez pas de voter !",
    "Quelle belle soirée ! 🎉"
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
    robotGroup.scale.set(0.45, 0.45, 0.45); // Taille 45%
    
    // Matériaux
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blueMat = new THREE.MeshStandardMaterial({ color: 0x3388ff, roughness: 0.2 });
    const glowMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x111111 });

    // Tête
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.7, 32, 32), whiteMat);
    const face = new THREE.Mesh(new THREE.CircleGeometry(0.55, 32), darkMat);
    face.position.set(0, 0, 0.68);
    head.add(face);

    // Yeux
    const eyeGeo = new THREE.CircleGeometry(0.12, 32);
    const leftEye = new THREE.Mesh(eyeGeo, glowMat);
    leftEye.position.set(-0.25, 0.1, 0.70);
    head.add(leftEye);
    const rightEye = new THREE.Mesh(eyeGeo, glowMat);
    rightEye.position.set(0.25, 0.1, 0.70);
    head.add(rightEye);

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
    const particleCount = 80;
    const particlesGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    for(let i=0; i<particleCount*3; i++) positions[i] = 999;
    particlesGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particleMat = new THREE.PointsMaterial({ color: 0x88ccff, size: 0.15, transparent: true, opacity: 0.6 });
    const particleSystem = new THREE.Points(particlesGeo, particleMat);
    scene.add(particleSystem);
    let particleData = Array(particleCount).fill().map(() => ({ velocity: new THREE.Vector3(), active: false }));

    // --- LOGIQUE DE NAVIGATION ---
    let targetPosition = new THREE.Vector3(0, 0, 0);
    let restDuration = 0;
    let restTimerCurrent = 0;

    // Fonction pour choisir une destination n'importe où (sauf au centre exact)
    function pickNewTarget(forceSide = null) {
        const aspect = width / height;
        const vH = 7; // Hauteur visible approx
        const vW = vH * aspect;
        
        let valid = false;
        let x, y;
        
        // Si on force un côté (pour le repos à droite par exemple)
        if (forceSide === 'right') {
            x = (Math.random() * (vW * 0.4 - 1.5)) + 1.5; // Entre 1.5 et bord droit
            y = (Math.random() - 0.5) * vH * 0.8;
            valid = true;
        } else {
            // Sinon, aléatoire total
            while (!valid) {
                x = (Math.random() - 0.5) * vW * 0.9; 
                y = (Math.random() - 0.5) * vH * 0.8;
                
                // Si on tombe pile au centre (zone du texte), on refuse
                if (Math.abs(x) < 2.0 && Math.abs(y) < 1.0) {
                    valid = false;
                } else {
                    valid = true;
                }
            }
        }
        targetPosition.set(x, y, 0);
    }

    pickNewTarget(); // Premier départ

    // --- ANIMATION ---
    let time = 0;
    let teleportTimer = 0;
    let bubbleTimer = 0;
    let msgIndex = 0;
    let robotState = 'moving'; // moving, resting, speaking, disappear, reappear

    setTimeout(() => { if(robotState !== 'disappear') startSpeaking(); }, 2000);

    function animate() {
        requestAnimationFrame(animate);
        time += 0.02; // Temps global ralenti
        
        // --- GESTION DES ETATS ---

        // 1. EN MOUVEMENT (Vers la cible)
        if (robotState === 'moving') {
            teleportTimer += 0.01;
            bubbleTimer += 0.01;

            // Mouvement TRES FLUIDE (Lerp factor faible = 0.005)
            // Cela crée l'effet de glissement sans à-coups
            robotGroup.position.lerp(targetPosition, 0.005);
            
            // Orientation douce vers la cible
            const diffX = targetPosition.x - robotGroup.position.x;
            const diffY = targetPosition.y - robotGroup.position.y;
            
            robotGroup.rotation.y += (diffX * 0.1 - robotGroup.rotation.y) * 0.02; // Tourne la tête lentement
            robotGroup.rotation.z = -diffX * 0.05; // Penche un peu

            // Flottement sinusoïdal (effet vague)
            robotGroup.position.y += Math.sin(time * 2) * 0.002;

            // Bras
            rightArm.rotation.x = Math.sin(time * 3) * 0.2;
            leftArm.rotation.x = -Math.sin(time * 3) * 0.2;

            // Vérifier si arrivé (distance < 0.8 pour ne pas attendre d'être pile dessus)
            if (robotGroup.position.distanceTo(targetPosition) < 0.8) {
                // Arrivé ! On décide quoi faire.
                // 40% de chance de se reposer, sinon on repart ailleurs
                if (Math.random() < 0.4) {
                    startResting();
                } else {
                    pickNewTarget();
                }
            }

            // Déclencheurs
            if (bubbleTimer > 10) startSpeaking();
            if (teleportTimer > 25) startTeleport(); // Téléportation rare
        }

        // 2. EN REPOS (Se pose sur le côté)
        else if (robotState === 'resting') {
            restTimerCurrent += 0.01;
            
            // Flottement stationnaire "zen"
            robotGroup.position.y += Math.sin(time * 1.5) * 0.001;
            robotGroup.rotation.y *= 0.95; // Revient de face
            robotGroup.rotation.z *= 0.95; // Se redresse

            // Bras ballants doucement
            rightArm.rotation.z = Math.sin(time * 2) * 0.05;
            leftArm.rotation.z = -Math.sin(time * 2) * 0.05;

            // Fin du repos ?
            if (restTimerCurrent > restDuration) {
                pickNewTarget(); // Repart vers une nouvelle destination
                robotState = 'moving';
            }
        }

        // 3. PARLE (Immobile temporaire)
        else if (robotState === 'speaking') {
            robotGroup.position.y += Math.sin(time * 4) * 0.002;
            rightArm.rotation.z = Math.cos(time * 8) * 0.5 + 0.5; // Coucou
        }

        // 4. DISPARITION
        else if (robotState === 'disappear') {
            robotGroup.scale.multiplyScalar(0.92);
            robotGroup.rotation.y += 0.4;
            
            if (robotGroup.scale.x < 0.05) {
                // Nouvelle position au hasard
                pickNewTarget();
                // On le place directement là-bas pour l'apparition
                robotGroup.position.copy(targetPosition);
                // Effet de fumée à l'arrivée
                triggerSmoke(targetPosition.x, targetPosition.y);
                
                robotGroup.rotation.set(0,0,0);
                robotState = 'reappear';
            }
        } 
        
        // 5. REAPPARITION
        else if (robotState === 'reappear') {
            robotGroup.scale.multiplyScalar(1.1);
            if (robotGroup.scale.x >= 0.45) {
                robotGroup.scale.set(0.45, 0.45, 0.45);
                robotState = 'moving';
                teleportTimer = 0;
            }
        }

        updateSmoke();
        updateBubblePosition();
        renderer.render(scene, camera);
    }

    function startResting() {
        // On choisit une cible "Repos" (souvent à droite)
        if (Math.random() > 0.3) {
            // 70% de chance d'aller se poser à droite
            pickNewTarget('right');
        } else {
            // Sinon on reste là où on est
        }
        
        // On lui donne une durée de repos (entre 3 et 6 secondes)
        restDuration = 3 + Math.random() * 3;
        restTimerCurrent = 0;
        robotState = 'resting';
    }

    function startSpeaking() {
        // Si on est en train de disparaître, on annule
        if (robotState === 'disappear' || robotState === 'reappear') return;

        let previousState = robotState;
        robotState = 'speaking';
        bubbleTimer = 0;
        showBubble();
        
        setTimeout(() => {
            hideBubble();
            // On reprend l'état d'avant (Moving ou Resting)
            if (robotState === 'speaking') {
                robotState = 'moving'; 
            }
        }, 6000);
    }

    function startTeleport() {
        if (robotState === 'speaking') return;
        hideBubble();
        triggerSmoke(robotGroup.position.x, robotGroup.position.y);
        robotState = 'disappear';
    }

    function showBubble() {
        if(!bubble) return;
        bubble.innerText = messages[msgIndex];
        bubble.style.opacity = 1;
        msgIndex = (msgIndex + 1) % messages.length;
    }

    function hideBubble() {
        if(bubble) bubble.style.opacity = 0;
    }

    function updateBubblePosition() {
        if(!bubble || bubble.style.opacity == 0) return;
        
        const headPos = new THREE.Vector3(robotGroup.position.x, robotGroup.position.y + 0.7, robotGroup.position.z);
        headPos.project(camera);
        
        const x = (headPos.x * .5 + .5) * width;
        const y = (headPos.y * -.5 + .5) * height;

        // Limites pour que la bulle reste à l'écran
        let finalX = Math.max(120, Math.min(width - 120, x));
        let finalY = Math.max(60, y - 100);

        bubble.style.left = finalX + 'px';
        bubble.style.top = finalY + 'px';
        bubble.style.transform = 'translate(-50%, 0)';
    }

    function triggerSmoke(x, y) {
        const posAttr = particleSystem.geometry.attributes.position;
        for(let i=0; i<particleCount; i++) {
            if (!particleData[i].active) {
                particleData[i].active = true;
                posAttr.setXYZ(i, x + (Math.random()-0.5)*0.5, y + (Math.random()-0.5)*0.5, (Math.random()-0.5)*0.5);
                particleData[i].velocity.set((Math.random()-0.5)*0.1, (Math.random()-0.5)*0.1, (Math.random()-0.5)*0.1);
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
                particleData[i].velocity.y += 0.005;
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
