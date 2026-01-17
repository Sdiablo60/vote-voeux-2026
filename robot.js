import * as THREE from 'three';

// --- CONFIGURATION ---
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- TEXTES DU ROBOT ---
const MESSAGES_BAG = {
    attente: ["Bienvenue !", "Installez-vous bien", "Ravi de vous voir !", "Ça va être génial !"],
    vote_off: ["Les jeux sont faits !", "On calcule tout ça...", "Qui va gagner ?", "Patience..."],
    photos: ["Ouistiti ! 📸", "Souriez pour la photo !", "Magnifique !", "Envoyez vos clichés !"],
    danse: ["Bougez avec moi ! 💃", "Quelle énergie !"],
    explosion: ["Boum !", "Incroyable !"],
    cache_cache: ["Coucou !", "Je vous vois !"]
};

// --- INITIALISATION ---
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', launchAnimatedRobot);
} else {
    launchAnimatedRobot();
}

function launchAnimatedRobot() {
    // 1. NETTOYAGE
    const oldIds = ['robot-container', 'robot-canvas-overlay', 'robot-ghost-layer', 'robot-canvas-final', 'robot-calibration-layer'];
    oldIds.forEach(id => { const el = document.getElementById(id); if (el) el.remove(); });

    // 2. CRÉATION CANVAS
    const canvas = document.createElement('canvas');
    canvas.id = 'robot-canvas-final';
    document.body.appendChild(canvas);

    canvas.style.cssText = `
        position: fixed !important; top: 0 !important; left: 0 !important;
        width: 100vw !important; height: 100vh !important;
        z-index: 2147483647 !important; pointer-events: none !important;
        background: transparent !important;
    `;

    // 3. CRÉATION BULLE DE TEXTE
    let bubble = document.createElement('div');
    bubble.id = 'robot-bubble-dynamic';
    document.body.appendChild(bubble);
    bubble.style.cssText = `
        position: fixed; opacity: 0; background: white; color: black;
        padding: 15px 25px; border-radius: 30px; font-family: 'Arial', sans-serif; 
        font-weight: bold; font-size: 20px; pointer-events: none; z-index: 2147483647;
        transition: opacity 0.5s, transform 0.5s; transform: scale(0.8);
        box-shadow: 0 8px 20px rgba(0,0,0,0.4); text-align: center; min-width: 150px;
    `;
    // Flèche de la bulle
    const arrow = document.createElement('div');
    arrow.style.cssText = `
        position: absolute; bottom: -10px; left: 50%; transform: translateX(-50%);
        width: 0; height: 0; border-left: 12px solid transparent;
        border-right: 12px solid transparent; border-top: 12px solid white;
    `;
    bubble.appendChild(arrow);

    initThreeJS(canvas, bubble);
}

function initThreeJS(canvas, bubble) {
    let width = window.innerWidth;
    let height = window.innerHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 14); 

    const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);

    // LUMIÈRES
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.5); 
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // --- CONSTRUCTION DU ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(1.1, 1.1, 1.1); 
    
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.1, metalness: 0.2 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.1 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff }); 
    const greyMat = new THREE.MeshStandardMaterial({ color: 0x888888 });

    function createPart(geo, mat, x, y, z, parent) {
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(x, y, z);
        if(parent) parent.add(mesh);
        return mesh;
    }

    const head = createPart(new THREE.SphereGeometry(0.85, 32, 32), whiteMat, 0, 0, 0, robotGroup);
    head.scale.set(1.4, 1.0, 0.75);
    createPart(new THREE.SphereGeometry(0.78, 32, 32), blackMat, 0, 0, 0.55, head).scale.set(1.25, 0.85, 0.6);
    createPart(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat, -0.35, 0.15, 1.05, head);
    createPart(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat, 0.35, 0.15, 1.05, head);
    const mouth = createPart(new THREE.TorusGeometry(0.1, 0.035, 8, 16, Math.PI), neonMat, 0, -0.15, 1.05, head);
    mouth.rotation.z = Math.PI;
    createPart(new THREE.CylinderGeometry(0.25, 0.25, 0.1, 16), whiteMat, -1.1, 0, 0, head).rotation.z = Math.PI/2;
    createPart(new THREE.CylinderGeometry(0.25, 0.25, 0.1, 16), whiteMat, 1.1, 0, 0, head).rotation.z = Math.PI/2;

    const body = createPart(new THREE.SphereGeometry(0.65, 32, 32), whiteMat, 0, -1.1, 0, robotGroup);
    body.scale.set(0.95, 1.1, 0.8);
    createPart(new THREE.TorusGeometry(0.62, 0.03, 16, 32), greyMat, 0, 0, 0, body).rotation.x = Math.PI/2;

    const leftArm = createPart(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat, -0.8, -0.8, 0, robotGroup);
    const rightArm = createPart(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat, 0.8, -0.8, 0, robotGroup);

    scene.add(robotGroup);
    
    // Position initiale légèrement vers le bas
    robotGroup.position.set(0, -1, 0);

    // --- ANIMATION ---
    let time = 0;
    let lastMsgTime = 0;

    function animate() {
        requestAnimationFrame(animate);
        time += 0.02;

        // 1. FLOTTAISON (Haut / Bas)
        robotGroup.position.y = -1 + Math.sin(time) * 0.25;

        // 2. ROTATION (Regard gauche / droite)
        robotGroup.rotation.y = Math.sin(time * 0.5) * 0.3;
        robotGroup.rotation.z = Math.sin(time * 0.8) * 0.05;

        // 3. MOUVEMENT DES BRAS
        leftArm.rotation.z = 0.2 + Math.sin(time * 1.5) * 0.1;
        rightArm.rotation.z = -0.2 - Math.sin(time * 1.5) * 0.1;

        // 4. GESTION DES MESSAGES
        if (Date.now() - lastMsgTime > 6000) {
            const msgs = MESSAGES_BAG[config.mode] || MESSAGES_BAG['attente'];
            bubble.firstChild.nodeValue = msgs[Math.floor(Math.random() * msgs.length)];
            bubble.style.opacity = 1;
            bubble.style.transform = 'scale(1)';
            lastMsgTime = Date.now();
            setTimeout(() => {
                bubble.style.opacity = 0;
                bubble.style.transform = 'scale(0.8)';
            }, 3500);
        }

        // 5. POSITION DE LA BULLE (Suit la tête)
        if (bubble.style.opacity == 1) {
            const headPos = robotGroup.position.clone();
            headPos.y += 1.3;
            headPos.project(camera);
            const bx = (headPos.x * 0.5 + 0.5) * width;
            const by = (-headPos.y * 0.5 + 0.5) * height;
            bubble.style.left = (bx - bubble.offsetWidth / 2) + 'px';
            bubble.style.top = (by - bubble.offsetHeight - 20) + 'px';
        }

        renderer.render(scene, camera);
    }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); 
        camera.aspect = width / height; 
        camera.updateProjectionMatrix();
    });

    animate();
}
