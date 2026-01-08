import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// Messages
const messages = [
    "Salut tout le monde ! 👋",
    "Bienvenue aux Vœux 2026 ! ✨",
    "Je vole ! 🚀",
    "Qui va gagner le trophée ? 🏆",
    "Silence... on tourne ! 🎬",
    "N'oubliez pas de voter !",
    "Quelle ambiance ce soir ! 🎉"
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
    camera.position.set(0, 0, 8); // Reculé pour voir plus large

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
    robotGroup.scale.set(0.7, 0.7, 0.7); // Taille ajustée
    
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
    const particleCount = 100;
    const particlesGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    for(let i=0; i<particleCount*3; i++) positions[i] = 999;
    particlesGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particleMat = new THREE.PointsMaterial({ color: 0x88ccff, size: 0.2, transparent: true, opacity: 0.6 });
    const particleSystem = new THREE.Points(particlesGeo, particleMat);
    scene.add(particleSystem);
    let particleData = Array(particleCount).fill().map(() => ({ velocity: new THREE.Vector3(), active: false }));

    // --- ANIMATION ---
    let time = 0;
    let teleportTimer = 0;
    let bubbleTimer = 0;
    let msgIndex = 0;
    let robotState = 'idle';
    
    // Variables pour le vol fluide
    let targetY = 0;
    let targetX = 0;

    // 1ere bulle rapide
    setTimeout(showBubble, 1500);

    function animate() {
        requestAnimationFrame(animate);
        time += 0.03; // Vitesse générale
        teleportTimer += 0.01;
        bubbleTimer += 0.01;

        // --- MOUVEMENT DE VOL "IDLE" ---
        if (robotState === 'idle') {
            // Vol plané (courbe en 8)
            // Il bouge un peu autour de sa position actuelle
            robotGroup.position.y += Math.sin(time * 2) * 0.005; 
            robotGroup.position.x += Math.cos(time * 1.5) * 0.005;
            
            // Légère rotation du corps pour simuler le vol
            robotGroup.rotation.z = Math.cos(time * 1.5) * 0.05; 
            robotGroup.rotation.x = Math.sin(time * 2) * 0.05;

            // Bras
            rightArm.rotation.z = Math.cos(time * 5) * 0.5 + 0.5; 
            rightArm.rotation.x = Math.sin(time * 5) * 0.2;
            leftArm.rotation.x = -Math.sin(time * 5) * 0.2; // L'autre bras bouge aussi
        }

        // Bulle toutes les 6s
        if (bubbleTimer > 6 && robotState === 'idle') { 
            showBubble();
            bubbleTimer = 0;
        }

        // Téléportation toutes les 7s
        if (teleportTimer > 7 && robotState === 'idle') {
            startTeleport();
        }

        // --- Séquence Téléportation ---
        if (robotState === 'disappear') {
            robotGroup.scale.multiplyScalar(0.9);
            robotGroup.rotation.y += 0.5;
            hideBubble();
            
            if (robotGroup.scale.x < 0.05) {
                // CALCUL DE LA NOUVELLE POSITION (Plein écran)
                // Calcul basé sur le champ de vision caméra (approx pour z=0)
                const aspect = width / height;
                const visibleHeight = 2 * Math.tan((camera.fov * Math.PI / 180) / 2) * Math.abs(camera.position.z);
                const visibleWidth = visibleHeight * aspect;

                // On garde une marge de sécurité (0.8) pour pas qu'il sorte de l'écran
                const randomX = (Math.random() - 0.5) * visibleWidth * 0.8;
                const randomY = (Math.random() - 0.5) * visibleHeight * 0.6; // Un peu moins haut
                
                robotGroup.position.set(randomX, randomY, 0);
                
                triggerSmoke(randomX, randomY);
                robotGroup.rotation.set(0,0,0); // Reset rotations
                robotState = 'reappear';
            }
        } 
        else if (robotState === 'reappear') {
            robotGroup.scale.multiplyScalar(1.15);
            if (robotGroup.scale.x >= 0.7) {
                robotGroup.scale.set(0.7, 0.7, 0.7);
                robotState = 'idle';
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
        setTimeout(() => { bubble.style.opacity = 0; }, 4000);
    }

    function hideBubble() {
        if(bubble) bubble.style.opacity = 0;
    }

    function updateBubblePosition() {
        if(!bubble || bubble.style.opacity == 0) return;
        
        const headPos = new THREE.Vector3(robotGroup.position.x, robotGroup.position.y + 0.9, robotGroup.position.z);
        headPos.project(camera);
        
        const x = (headPos.x * .5 + .5) * width;
        const y = (headPos.y * -.5 + .5) * height;

        // Ajustement pour ne pas sortir de l'écran
        let finalX = x;
        if (finalX < 150) finalX = 150;
        if (finalX > width - 150) finalX = width - 150;

        bubble.style.left = finalX + 'px';
        bubble.style.top = (y - 140) + 'px'; // Au dessus de la tête
        bubble.style.transform = 'translateX(-50%)';
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
                if (posAttr.getY(i) > 5) { // Monte plus haut avant de disparaitre
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
