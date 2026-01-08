import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// Messages que le robot va dire
const messages = [
    "Bienvenue !",
    "Préparez vos votes 📱",
    "Qui va gagner ? 🏆",
    "J'adore le cinéma 🎬",
    "Votez pour le meilleur !",
    "Salut tout le monde 👋"
];

if (container) {
    initRobot(container);
}

function initRobot(container) {
    let width = container.clientWidth;
    let height = container.clientHeight;
    
    // SCENE
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 1.5, 7);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // LUMIERES
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 2);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // --- ROBOT ---
    const robotGroup = new THREE.Group();
    
    // Matériaux
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blueMat = new THREE.MeshStandardMaterial({ color: 0x3388ff, roughness: 0.2 });
    const glowMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x111111 });

    // Tête
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.7, 32, 32), whiteMat);
    const face = new THREE.Mesh(new THREE.CircleGeometry(0.55, 32), darkMat);
    face.position.set(0, 0, 0.68); // Ajusté pour éviter le clignotement
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
    robotGroup.position.y = 0.5;
    scene.add(robotGroup);

    // --- PARTICULES (FUMÉE) ---
    const particleCount = 100;
    const particlesGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    for(let i=0; i<particleCount*3; i++) positions[i] = 999; // Cachées
    particlesGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particleMat = new THREE.PointsMaterial({ color: 0x88ccff, size: 0.2, transparent: true, opacity: 0.6 });
    const particleSystem = new THREE.Points(particlesGeo, particleMat);
    scene.add(particleSystem);
    let particleData = Array(particleCount).fill().map(() => ({ velocity: new THREE.Vector3(), active: false }));

    // --- ANIMATION LOGIQUE ---
    let time = 0;
    let teleportTimer = 0;
    let bubbleTimer = 0;
    let msgIndex = 0;
    let robotState = 'idle'; 

    function animate() {
        requestAnimationFrame(animate);
        time += 0.05;
        teleportTimer += 0.01;
        bubbleTimer += 0.01;

        // 1. Mouvement de base (Flottement + Bras)
        if (robotState === 'idle') {
            robotGroup.position.y = 0.5 + Math.sin(time) * 0.1;
            rightArm.rotation.z = Math.cos(time * 4) * 0.6 + 0.5; // Coucou rapide
            rightArm.rotation.x = Math.sin(time * 4) * 0.2;
        }

        // 2. Gestion de la Bulle (Toutes les 5 secondes environ)
        if (bubbleTimer > 25 && robotState === 'idle') {
            showBubble();
            bubbleTimer = 0;
        }

        // 3. Téléportation (Toutes les 8 secondes)
        if (teleportTimer > 8 && robotState === 'idle') {
            startTeleport();
        }

        // 4. États d'animation
        if (robotState === 'disappear') {
            robotGroup.scale.multiplyScalar(0.9);
            robotGroup.rotation.y += 0.5;
            hideBubble(); // Cacher la bulle quand il part
            if (robotGroup.scale.x < 0.1) {
                // Déplacement
                robotGroup.position.x = (Math.random() > 0.5) ? 2.5 : -2.5; 
                if (Math.random() > 0.7) robotGroup.position.x = 0; // Parfois au centre
                
                triggerSmoke(robotGroup.position.x, 0.5);
                robotGroup.rotation.y = 0;
                robotState = 'reappear';
            }
        } else if (robotState === 'reappear') {
            robotGroup.scale.multiplyScalar(1.1);
            if (robotGroup.scale.x >= 1) {
                robotGroup.scale.set(1,1,1);
                robotState = 'idle';
                teleportTimer = 0;
            }
        }

        updateSmoke();
        
        // Mise à jour position bulle (suivre le robot en 2D)
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
        // Cacher après 3 secondes
        setTimeout(() => { bubble.style.opacity = 0; }, 3000);
    }

    function hideBubble() {
        if(bubble) bubble.style.opacity = 0;
    }

    function updateBubblePosition() {
        if(!bubble) return;
        // Projeter la position de la tête du robot (3D) vers l'écran (2D)
        const headPos = new THREE.Vector3(robotGroup.position.x, robotGroup.position.y + 1.2, robotGroup.position.z);
        headPos.project(camera);
        
        const x = (headPos.x * .5 + .5) * container.clientWidth;
        const y = (headPos.y * -.5 + .5) * container.clientHeight;

        bubble.style.left = x + 'px';
        bubble.style.top = (y - 50) + 'px'; // Un peu au dessus de la tête
    }

    function triggerSmoke(x, y) {
        const posAttr = particleSystem.geometry.attributes.position;
        for(let i=0; i<particleCount; i++) {
            if (!particleData[i].active) {
                particleData[i].active = true;
                posAttr.setXYZ(i, x + (Math.random()-0.5), y + (Math.random()-0.5), (Math.random()-0.5));
                particleData[i].velocity.set((Math.random()-0.5)*0.2, (Math.random()-0.5)*0.2, (Math.random()-0.5)*0.2);
            }
        }
        posAttr.needsUpdate = true;
    }

    function updateSmoke() {
        const posAttr = particleSystem.geometry.attributes.position;
        for(let i=0; i<particleCount; i++) {
            if (particleData[i].active) {
                posAttr.setXYZ(i, posAttr.getX(i)+particleData[i].velocity.x, posAttr.getY(i)+particleData[i].velocity.y, posAttr.getZ(i)+particleData[i].velocity.z);
                particleData[i].velocity.y += 0.005; // Monte
                if (posAttr.getY(i) > 4) { particleData[i].active = false; posAttr.setXYZ(i, 999,999,999); }
            }
        }
        posAttr.needsUpdate = true;
    }

    window.addEventListener('resize', () => {
        const w = container.clientWidth;
        const h = container.clientHeight;
        renderer.setSize(w, h);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
    });

    animate();
}
