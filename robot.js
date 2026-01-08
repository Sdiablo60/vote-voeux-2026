import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// Messages
const messages = [
    "Salut tout le monde ! 👋",
    "Bienvenue aux Vœux 2026 ! ✨",
    "Préparez vos smartphones 📱",
    "Qui va gagner le trophée ? 🏆",
    "Ça va être génial ! 🎬",
    "N'oubliez pas de voter !",
    "Quelle ambiance ce soir ! 🎉"
];

// Vérification de sécurité avant de lancer
if (container) {
    try {
        initRobot(container);
    } catch (e) {
        console.error("Erreur lancement robot:", e);
    }
}

function initRobot(container) {
    // Dimensions
    let width = container.clientWidth || window.innerWidth;
    let height = container.clientHeight || window.innerHeight;
    
    // SCENE
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 1, 7);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // LUMIERES
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.0); // Lumière forte
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 2.0);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // --- CONSTRUCTION ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.6, 0.6, 0.6); // Taille 60%
    
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
    
    robotGroup.position.y = -0.5; // Un peu plus bas pour ne pas cacher le titre
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

    // Affiche la 1ere bulle rapidement
    setTimeout(showBubble, 1000);

    function animate() {
        requestAnimationFrame(animate);
        time += 0.05;
        teleportTimer += 0.01;
        bubbleTimer += 0.01;

        // IDLE
        if (robotState === 'idle') {
            robotGroup.position.y = -0.5 + Math.sin(time) * 0.1;
            rightArm.rotation.z = Math.cos(time * 5) * 0.5 + 0.5; 
            rightArm.rotation.x = Math.sin(time * 5) * 0.2;
        }

        // BULLE (Toutes les 6 secondes)
        if (bubbleTimer > 6 && robotState === 'idle') { 
            showBubble();
            bubbleTimer = 0;
        }

        // TELEPORTATION (Toutes les 5.5 secondes)
        if (teleportTimer > 5.5 && robotState === 'idle') {
            startTeleport();
        }

        // ETATS
        if (robotState === 'disappear') {
            robotGroup.scale.multiplyScalar(0.9);
            robotGroup.rotation.y += 0.4;
            hideBubble();
            
            if (robotGroup.scale.x < 0.05) {
                // Déplacement LARGE (-5 à +5)
                const randomX = (Math.random() * 10) - 5; 
                robotGroup.position.x = randomX;
                
                triggerSmoke(randomX, -0.5);
                robotGroup.rotation.y = 0;
                robotState = 'reappear';
            }
        } 
        else if (robotState === 'reappear') {
            robotGroup.scale.multiplyScalar(1.15);
            if (robotGroup.scale.x >= 0.6) {
                robotGroup.scale.set(0.6, 0.6, 0.6);
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
        setTimeout(() => { bubble.style.opacity = 0; }, 4000); // Reste 4s
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

        // Ajustement si trop au bord
        let finalX = x;
        if (finalX < 120) finalX = 120;
        if (finalX > width - 120) finalX = width - 120;

        bubble.style.left = finalX + 'px';
        bubble.style.top = (y - 130) + 'px';
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
