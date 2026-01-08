import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// Messages que le robot va dire
const messages = [
    "Salut l'équipe ! 👋",
    "Bienvenue aux Voeux 2026 ! ✨",
    "Préparez vos téléphones 📱",
    "Qui va gagner ce soir ? 🏆",
    "J'adore le cinéma 🎬",
    "Votez pour le meilleur !",
    "Attention... Action ! 🎥"
];

if (container) {
    initRobot(container);
}

function initRobot(container) {
    let width = container.clientWidth || window.innerWidth;
    let height = container.clientHeight || window.innerHeight;
    
    // SCENE
    const scene = new THREE.Scene();
    // scene.background = new THREE.Color(0x000000); // Optionnel, le CSS gère déjà le noir

    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 1, 7); // Caméra un peu plus basse pour voir le robot de face

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio); // Pour que ce soit net sur mobile
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // LUMIERES
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 2);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // --- ROBOT ---
    const robotGroup = new THREE.Group();
    
    // >>> MODIFICATION TAILLE ICI <<<
    robotGroup.scale.set(0.6, 0.6, 0.6); // Robot à 60% de sa taille
    
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
    
    // Position de départ
    robotGroup.position.y = 0; 
    scene.add(robotGroup);

    // --- PARTICULES (FUMÉE) ---
    const particleCount = 100;
    const particlesGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    for(let i=0; i<particleCount*3; i++) positions[i] = 999;
    particlesGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particleMat = new THREE.PointsMaterial({ color: 0x88ccff, size: 0.2, transparent: true, opacity: 0.6 });
    const particleSystem = new THREE.Points(particlesGeo, particleMat);
    scene.add(particleSystem);
    let particleData = Array(particleCount).fill().map(() => ({ velocity: new THREE.Vector3(), active: false }));

    // --- LOGIQUE D'ANIMATION ---
    let time = 0;
    let teleportTimer = 0;
    let bubbleTimer = 0;
    let msgIndex = 0;
    let robotState = 'idle'; 

    // Lancer la première bulle tout de suite !
    setTimeout(showBubble, 1000);

    function animate() {
        requestAnimationFrame(animate);
        time += 0.05;
        teleportTimer += 0.01;
        bubbleTimer += 0.01;

        // 1. Mouvement "Idle" (Respiration + Bras)
        if (robotState === 'idle') {
            robotGroup.position.y = Math.sin(time) * 0.15; // Flotte haut/bas
            
            // Bras droit fait coucou
            rightArm.rotation.z = Math.cos(time * 5) * 0.5 + 0.5; 
            rightArm.rotation.x = Math.sin(time * 5) * 0.2;
        }

        // 2. Gestion de la Bulle (Toutes les 4 secondes)
        if (bubbleTimer > 4 && robotState === 'idle') { 
            showBubble();
            bubbleTimer = 0;
        }

        // 3. Téléportation (Toutes les 5 secondes - plus rapide)
        if (teleportTimer > 5 && robotState === 'idle') {
            startTeleport();
        }

        // 4. Séquence Disparition / Réapparition
        if (robotState === 'disappear') {
            robotGroup.scale.multiplyScalar(0.9); // Rétrécit
            robotGroup.rotation.y += 0.4; // Tourne
            hideBubble();
            
            if (robotGroup.scale.x < 0.05) {
                // Une fois invisible, on le déplace
                // Position X aléatoire entre -3 et +3
                const randomX = (Math.random() * 6) - 3; 
                robotGroup.position.x = randomX;
                
                // Explose la fumée à la nouvelle position
                triggerSmoke(randomX, 0);
                
                // Reset rotation et prépare réapparition
                robotGroup.rotation.y = 0;
                robotState = 'reappear';
            }
        } 
        else if (robotState === 'reappear') {
            robotGroup.scale.multiplyScalar(1.15); // Grandit
            // On limite la taille max à 0.6 (sa taille définie au début)
            if (robotGroup.scale.x >= 0.6) {
                robotGroup.scale.set(0.6, 0.6, 0.6);
                robotState = 'idle';
                teleportTimer = 0; // Reset du timer
            }
        }

        updateSmoke();
        updateBubblePosition();
        renderer.render(scene, camera);
    }

    function startTeleport() {
        robotState = 'disappear';
        // Fumée au point de départ
        triggerSmoke(robotGroup.position.x, robotGroup.position.y);
    }

    function showBubble() {
        if(!bubble) return;
        bubble.innerText = messages[msgIndex];
        bubble.style.opacity = 1;
        
        // Change le message pour la prochaine fois
        msgIndex = (msgIndex + 1) % messages.length;
        
        // Cache la bulle après 3 secondes
        setTimeout(() => { bubble.style.opacity = 0; }, 3000);
    }

    function hideBubble() {
        if(bubble) bubble.style.opacity = 0;
    }

    function updateBubblePosition() {
        if(!bubble || bubble.style.opacity == 0) return;
        
        // Calcul pour coller la bulle au dessus de la tête (même quand il bouge)
        // On prend la position du robot + un décalage Y pour la tête
        const headPos = new THREE.Vector3(robotGroup.position.x, robotGroup.position.y + 0.9, robotGroup.position.z);
        
        // On projette cette position 3D sur l'écran 2D
        headPos.project(camera);
        
        const x = (headPos.x * .5 + .5) * width;
        const y = (headPos.y * -.5 + .5) * height;

        // On applique au CSS (-100 pour monter la bulle au dessus)
        bubble.style.left = x + 'px';
        bubble.style.top = (y - 120) + 'px'; 
    }

    function triggerSmoke(x, y) {
        const posAttr = particleSystem.geometry.attributes.position;
        for(let i=0; i<particleCount; i++) {
            if (!particleData[i].active) {
                particleData[i].active = true;
                posAttr.setXYZ(i, x + (Math.random()-0.5)*0.5, y + (Math.random()-0.5)*0.5, (Math.random()-0.5)*0.5);
                particleData[i].velocity.set(
                    (Math.random()-0.5)*0.1, 
                    (Math.random()-0.5)*0.1, 
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
                particleData[i].velocity.y += 0.005; // La fumée monte
                
                // Si trop haut, on cache
                if (posAttr.getY(i) > 3) { 
                    particleData[i].active = false; 
                    posAttr.setXYZ(i, 999,999,999); 
                }
            }
        }
        posAttr.needsUpdate = true;
    }

    window.addEventListener('resize', () => {
        width = container.clientWidth || window.innerWidth;
        height = container.clientHeight || window.innerHeight;
        renderer.setSize(width, height);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
    });

    animate();
}
