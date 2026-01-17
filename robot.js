import * as THREE from 'three';

// --- CONFIGURATION ---
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- TEXTES DU ROBOT ---
const MESSAGES_BAG = {
    attente: ["Bienvenue !", "Installez-vous", "Ça va commencer..."],
    vote_off: ["C'est fini !", "On compte les voix...", "Suspense..."],
    photos: ["Ouistiti ! 📸", "Envoyez vos photos !", "Souriez !"],
    danse: ["Allez on danse !", "Bougez avec moi ! 💃"],
    explosion: ["Boum !", "Quelle ambiance !"],
    cache_cache: ["Coucou !", "Je vous vois !"]
};

// --- INITIALISATION ---
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', launchRobotOnly);
} else {
    launchRobotOnly();
}

function launchRobotOnly() {
    // 1. NETTOYAGE COMPLET
    const oldIds = ['robot-container', 'robot-canvas-overlay', 'robot-ghost-layer', 'robot-canvas-final', 'robot-calibration-layer'];
    oldIds.forEach(id => { const el = document.getElementById(id); if (el) el.remove(); });

    // 2. CRÉATION CANVAS PLEIN ÉCRAN
    const canvas = document.createElement('canvas');
    canvas.id = 'robot-canvas-final';
    document.body.appendChild(canvas);

    canvas.style.cssText = `
        position: fixed !important; top: 0 !important; left: 0 !important;
        width: 100vw !important; height: 100vh !important;
        z-index: 10; /* Devant le fond, derrière les interfaces */
        pointer-events: none !important;
        background: transparent !important;
    `;

    // 3. BULLE DE TEXTE
    let bubble = document.getElementById('robot-bubble-text');
    if (!bubble) {
        bubble = document.createElement('div');
        bubble.id = 'robot-bubble-text';
        document.body.appendChild(bubble);
        bubble.style.cssText = `
            position: fixed; opacity: 0; background: white; color: black;
            padding: 15px 25px; border-radius: 30px; font-family: sans-serif; 
            font-weight: bold; font-size: 20px; pointer-events: none; z-index: 100;
            transition: opacity 0.5s, transform 0.5s; transform: scale(0.8);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3); text-align: center; min-width: 120px;
        `;
        // Petite flèche sous la bulle
        const arrow = document.createElement('div');
        arrow.style.cssText = `
            position: absolute; bottom: -8px; left: 50%; transform: translateX(-50%);
            width: 0; height: 0; border-left: 10px solid transparent;
            border-right: 10px solid transparent; border-top: 10px solid white;
        `;
        bubble.appendChild(arrow);
    }

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
    renderer.setClearColor(0x000000, 0);

    // Lumières pour un beau rendu
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2); 
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.0);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);
    const backLight = new THREE.DirectionalLight(0x00ffff, 0.5); // Lumière bleue arrière
    backLight.position.set(-5, 5, -10);
    scene.add(backLight);

    // =========================================================
    // --- CONSTRUCTION DU ROBOT ---
    // =========================================================
    const robotGroup = new THREE.Group();
    // On le grossit un peu puisqu'il est seul
    robotGroup.scale.set(1.0, 1.0, 1.0); 
    
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2, metalness: 0.1 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.1, metalness: 0.5 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff }); 
    const greyMat = new THREE.MeshStandardMaterial({ color: 0x888888 });

    function createPart(geo, mat, x, y, z, parent) {
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(x, y, z);
        if(parent) parent.add(mesh);
        return mesh;
    }

    // Tête
    const head = createPart(new THREE.SphereGeometry(0.85, 32, 32), whiteMat, 0, 0, 0, robotGroup);
    head.scale.set(1.4, 1.0, 0.75);
    // Visage noir
    createPart(new THREE.SphereGeometry(0.78, 32, 32), blackMat, 0, 0, 0.55, head).scale.set(1.25, 0.85, 0.6);
    // Yeux
    createPart(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat, -0.35, 0.15, 1.05, head);
    createPart(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat, 0.35, 0.15, 1.05, head);
    // Sourire (Tourné vers le haut)
    const mouth = createPart(new THREE.TorusGeometry(0.1, 0.035, 8, 16, Math.PI), neonMat, 0, -0.15, 1.05, head);
    mouth.rotation.z = Math.PI;
    
    // Oreilles / Antennes
    createPart(new THREE.CylinderGeometry(0.25, 0.25, 0.1, 16), whiteMat, -1.1, 0, 0, head).rotation.z = Math.PI/2;
    createPart(new THREE.CylinderGeometry(0.25, 0.25, 0.1, 16), whiteMat, 1.1, 0, 0, head).rotation.z = Math.PI/2;

    // Corps
    const body = createPart(new THREE.SphereGeometry(0.65, 32, 32), whiteMat, 0, -1.1, 0, robotGroup);
    body.scale.set(0.95, 1.1, 0.8);
    // Anneau cou
    createPart(new THREE.TorusGeometry(0.62, 0.03, 16, 32), greyMat, 0, 0, 0, body).rotation.x = Math.PI/2;

    // Bras
    const leftArm = createPart(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat, -0.8, -0.8, 0, robotGroup); leftArm.rotation.z = 0.15;
    const rightArm = createPart(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat, 0.8, -0.8, 0, robotGroup); rightArm.rotation.z = -0.15;

    scene.add(robotGroup);
    
    // Position initiale : Centré horizontalement (0), légèrement descendu (-1)
    robotGroup.position.set(0, -1, 0);

    // =========================================================
    // --- GESTION PAROLE (BULLE) ---
    // =========================================================
    let lastTalkTime = 0;
    
    function updateBubble() {
        const now = Date.now();
        // Parle toutes les 4 à 8 secondes
        if (now - lastTalkTime > 4000 + Math.random() * 4000) {
            const msgs = MESSAGES_BAG[config.mode] || MESSAGES_BAG['attente'];
            const msg = msgs[Math.floor(Math.random() * msgs.length)];
            
            // Affiche le texte
            bubble.firstChild.nodeValue = msg; // Garde la flèche (qui est un enfant)
            bubble.innerText = msg;
            bubble.appendChild(bubble.querySelector('div')); // Remet la flèche
            
            bubble.style.opacity = 1;
            bubble.style.transform = 'scale(1)';
            lastTalkTime = now;

            // Cache après 3 secondes
            setTimeout(() => {
                bubble.style.opacity = 0;
                bubble.style.transform = 'scale(0.8)';
            }, 3000);
        }

        // Position de la bulle : Suit la tête du robot
        if (bubble.style.opacity == 1) {
            const headPos = robotGroup.position.clone();
            headPos.y += 1.2; // Au-dessus de la tête
            headPos.project(camera);
            
            const x = (headPos.x * .5 + .5) * width;
            const y = (-(headPos.y * .5) + .5) * height;

            bubble.style.left = (x - bubble.offsetWidth / 2) + 'px';
            bubble.style.top = (y - bubble.offsetHeight - 10) + 'px';
        }
    }

    // =========================================================
    // --- ANIMATION ---
    // =========================================================
    let time = 0;
    
    function animate() {
        requestAnimationFrame(animate);
        time += 0.015;
        
        // Mouvement de flottaison (Haut/Bas)
        robotGroup.position.y = -1 + Math.sin(time) * 0.15;
        
        // Légère rotation (Regarde un peu à gauche et à droite)
        robotGroup.rotation.y = Math.sin(time * 0.5) * 0.15;
        robotGroup.rotation.z = Math.sin(time * 0.3) * 0.05;

        // Bras qui bougent un peu
        leftArm.rotation.z = 0.15 + Math.sin(time * 1.2) * 0.05;
        rightArm.rotation.z = -0.15 - Math.sin(time * 1.2) * 0.05;

        updateBubble();
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
