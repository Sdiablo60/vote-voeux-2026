import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// Messages
const messages = [
    "Salut l'équipe ! 👋",
    "Bienvenue aux Vœux 2026 ! ✨",
    "On attend vos photos 📸",
    "Qui va gagner le trophée ? 🏆",
    "Silence... on tourne ! 🎬",
    "N'oubliez pas de voter !",
    "Quelle ambiance ! 🎉"
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
    camera.position.set(0, 0, 8); // Recul caméra

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
    robotGroup.scale.set(0.45, 0.45, 0.45); // TAILLE 45%
    
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
    const rightEye = new THREE.Mesh(eyeGeo, glowMat);
    rightEye.position.set(0.25, 0.1, 0.70);
    head.add(leftEye); head.add(rightEye);

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
    // On définit de quel côté de l'écran le robot se trouve
    let currentSide = (Math.random() > 0.5) ? 'left' : 'right'; 
    let targetPosition = new THREE.Vector3(0, 0, 0);
    
    // Initialiser la première position
    pickNewTargetOnSide();
    robotGroup.position.copy(targetPosition);

    function pickNewTargetOnSide() {
        // Limites visibles approx à z=0
        const aspect = width / height;
        const vH = 7; // Hauteur visible approx
        const vW = vH * aspect;
        
        // On définit deux zones sûres (Gauche et Droite)
        // Gauche : X entre -vW/2 et -1.5
        // Droite : X entre 1.5 et vW/2
        
        let minX, maxX;
        if (currentSide === 'left') {
            minX = -vW * 0.45;
            maxX = -2.0; // Ne pas dépasser vers le centre
        } else {
            minX = 2.0; // Ne pas dépasser vers le centre
            maxX = vW * 0.45;
        }

        const x = Math.random() * (maxX - minX) + minX;
        const y = (Math.random() - 0.5) * vH * 0.8; // Hauteur libre
        
        targetPosition.set(x, y, 0);
    }

    // --- ANIMATION ---
    let time = 0;
    let teleportTimer = 0;
    let bubbleTimer = 0;
    let msgIndex = 0;
    let robotState = 'moving'; // moving, speaking, disappear, reappear

    // Première bulle
    setTimeout(() => { if(robotState !== 'disappear') startSpeaking(); }, 2000);

    function animate() {
        requestAnimationFrame(animate);
        time += 0.04;
        
        // On ne compte les timers que si on n'est pas en transition
        if (robotState === 'moving') {
            teleportTimer += 0.01;
            bubbleTimer += 0.01;
        }

        // --- ETAT 1 : EN MOUVEMENT (Patrouille) ---
        if (robotState === 'moving') {
            // Glisser vers la cible
            robotGroup.position.lerp(targetPosition, 0.02);
            
            // Rotation fluide
            robotGroup.rotation.y = (targetPosition.x - robotGroup.position.x) * 0.3;
            robotGroup.rotation.z = (targetPosition.x - robotGroup.position.x) * -0.1;
            
            // Si proche de la cible, en choisir une autre (toujours du même côté)
            if (robotGroup.position.distanceTo(targetPosition) < 0.5) {
                pickNewTargetOnSide();
            }

            // Bras qui balancent
            rightArm.rotation.x = Math.sin(time * 5) * 0.2;
            leftArm.rotation.x = -Math.sin(time * 5) * 0.2;

            // Flottement
            robotGroup.position.y += Math.sin(time * 3) * 0.005;

            // DÉCLENCHEURS
            if (bubbleTimer > 8) { // Parle toutes les 8s
                startSpeaking();
            }
            if (teleportTimer > 20) { // Change de côté toutes les 20s
                startTeleport();
            }
        }

        // --- ETAT 2 : PARLE (Immobile) ---
        else if (robotState === 'speaking') {
            // Juste un flottement doux sur place, pas de déplacement X/Y
            robotGroup.position.y += Math.sin(time * 2) * 0.002;
            
            // Il regarde en face
            robotGroup.rotation.y *= 0.9; 
            robotGroup.rotation.z *= 0.9;

            // Il fait coucou
            rightArm.rotation.z = Math.cos(time * 8) * 0.5 + 0.5;
        }

        // --- ETAT 3 : DISPARITION ---
        else if (robotState === 'disappear') {
            robotGroup.scale.multiplyScalar(0.9);
            robotGroup.rotation.y += 0.5;
            
            if (robotGroup.scale.x < 0.05) {
                // CHANGEMENT DE CÔTÉ ICI
                currentSide = (currentSide === 'left') ? 'right' : 'left';
                pickNewTargetOnSide(); // Nouvelle cible sur le nouveau côté
                
                // On place le robot directement à la nouvelle cible
                robotGroup.position.copy(targetPosition);
                triggerSmoke(targetPosition.x, targetPosition.y);
                
                robotGroup.rotation.set(0,0,0);
                robotState = 'reappear';
            }
        } 
        
        // --- ETAT 4 : REAPPARITION ---
        else if (robotState === 'reappear') {
            robotGroup.scale.multiplyScalar(1.15);
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

    function startSpeaking() {
        robotState = 'speaking';
        bubbleTimer = 0;
        showBubble();
        
        // Reste immobile pendant 6 secondes pour lire
        setTimeout(() => {
            hideBubble();
            // Si on n'a pas été interrompu par une téléportation
            if (robotState === 'speaking') {
                robotState = 'moving';
            }
        }, 6000);
    }

    function startTeleport() {
        // On ne se téléporte pas si on parle
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

        // Garde la bulle dans l'écran
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
