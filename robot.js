import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

const messages = [
    "Salut l'équipe ! 👋",
    "Bienvenue aux Vœux 2026 ! ✨",
    "Je fais ma ronde... 🔦",
    "Qui va gagner le trophée ? 🏆",
    "On attend vos photos ! 📸",
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
    camera.position.set(0, 0, 8); // On recule un peu pour avoir plus d'espace

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
    robotGroup.scale.set(0.45, 0.45, 0.45); // TAILLE RÉDUITE (45%)
    
    // Matériaux
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blueMat = new THREE.MeshStandardMaterial({ color: 0x3388ff, roughness: 0.2 });
    const glowMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x111111 });

    // Construction du Robot
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

    // --- LOGIQUE DE NAVIGATION "AUTOUR DU TEXTE" ---
    let targetPosition = new THREE.Vector3(0, 0, 0);
    let movementSpeed = 0.02; // Vitesse de glissement
    let waitTimer = 0; // Temps d'attente à une position

    // Fonction pour choisir une nouvelle destination SANS le centre
    function pickNewTarget() {
        // Dimensions visibles approximatives à z=0
        const aspect = width / height;
        const vH = 2 * Math.tan((camera.fov * Math.PI / 180) / 2) * 8; // z=8
        const vW = vH * aspect;
        
        let valid = false;
        let x, y;
        
        // On essaye de trouver un point hors de la zone centrale
        // Zone centrale interdite : 40% de la largeur, 30% de la hauteur
        while (!valid) {
            x = (Math.random() - 0.5) * vW * 0.9; // Marge bords
            y = (Math.random() - 0.5) * vH * 0.8;
            
            // Si on est DANS le rectangle central, on recommence
            if (Math.abs(x) < vW * 0.25 && Math.abs(y) < vH * 0.2) {
                valid = false;
            } else {
                valid = true;
            }
        }
        targetPosition.set(x, y, 0);
    }

    pickNewTarget(); // Premier point

    // --- ANIMATION ---
    let time = 0;
    let teleportTimer = 0;
    let bubbleTimer = 0;
    let msgIndex = 0;
    let robotState = 'moving'; // moving, waiting, disappear, reappear

    setTimeout(showBubble, 1000);

    function animate() {
        requestAnimationFrame(animate);
        time += 0.04;
        teleportTimer += 0.01;
        bubbleTimer += 0.01;

        if (robotState === 'moving' || robotState === 'waiting') {
            // 1. Déplacement fluide vers la cible
            robotGroup.position.lerp(targetPosition, movementSpeed);
            
            // Orientation légère vers la direction (effet vol)
            const diffX = targetPosition.x - robotGroup.position.x;
            robotGroup.rotation.z = -diffX * 0.1; // Penche dans les virages
            robotGroup.rotation.y = diffX * 0.1;  // Regarde où il va

            // Mouvement de respiration (haut/bas local)
            robotGroup.position.y += Math.sin(time * 3) * 0.003;

            // Bras qui bougent
            rightArm.rotation.z = Math.cos(time * 4) * 0.3 + 0.3;
            leftArm.rotation.z = -Math.cos(time * 4) * 0.3 - 0.3;

            // Vérifier si on est arrivé
            if (robotGroup.position.distanceTo(targetPosition) < 0.5) {
                if (robotState === 'moving') {
                    robotState = 'waiting';
                    waitTimer = 0;
                }
            }

            if (robotState === 'waiting') {
                waitTimer += 0.01;
                // Après une pause, on repart ailleurs
                if (waitTimer > 2) { // Pause de 2 secondes environ
                    pickNewTarget();
                    robotState = 'moving';
                }
            }
        }

        // Bulle (toutes les 8s)
        if (bubbleTimer > 8 && robotState !== 'disappear') {
            showBubble();
            bubbleTimer = 0;
        }

        // Téléportation (OCCASIONNELLE : toutes les 20s)
        if (teleportTimer > 20) {
            startTeleport();
        }

        // --- GESTION TÉLÉPORTATION ---
        if (robotState === 'disappear') {
            robotGroup.scale.multiplyScalar(0.9);
            robotGroup.rotation.y += 0.5;
            hideBubble();
            if (robotGroup.scale.x < 0.05) {
                // On choisit une nouvelle cible loin et on s'y met direct
                pickNewTarget();
                robotGroup.position.copy(targetPosition);
                triggerSmoke(targetPosition.x, targetPosition.y);
                
                robotGroup.rotation.set(0,0,0);
                robotState = 'reappear';
            }
        } 
        else if (robotState === 'reappear') {
            robotGroup.scale.multiplyScalar(1.15);
            // Retour à la taille normale (0.45)
            if (robotGroup.scale.x >= 0.45) {
                robotGroup.scale.set(0.45, 0.45, 0.45);
                robotState = 'moving'; // Il reprend sa route
                teleportTimer = 0;
            }
        }

        updateSmoke();
        updateBubblePosition();
        renderer.render(scene, camera);
    }

    function startTeleport() {
        robotState = 'disappear';
        triggerSmoke(robotGroup.position.x, robotGroup.position.y);
    }

    function showBubble() {
        if(!bubble) return;
        bubble.innerText = messages[msgIndex];
        bubble.style.opacity = 1;
        msgIndex = (msgIndex + 1) % messages.length;
        setTimeout(() => { bubble.style.opacity = 0; }, 5000);
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

        // Limites écran pour la bulle
        let finalX = Math.max(100, Math.min(width - 100, x));
        let finalY = Math.max(50, y - 100);

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
                particleData[i].velocity.y += 0.
