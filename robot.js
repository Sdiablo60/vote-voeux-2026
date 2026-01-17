import * as THREE from 'three';

// --- CONFIGURATION ---
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

const MESSAGES_BAG = {
    attente: ["Je suis là !", "On commence ?"],
    photos: ["Photo time !", "Souriez !"],
    vote_off: ["Terminé !"]
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', forceRobotDisplay);
} else {
    forceRobotDisplay();
}

function forceRobotDisplay() {
    // 1. NETTOYAGE
    const oldIds = ['robot-container', 'robot-canvas-overlay', 'robot-ghost-layer', 'robot-canvas-final', 'robot-calibration-layer'];
    oldIds.forEach(id => { const el = document.getElementById(id); if (el) el.remove(); });

    // 2. CRÉATION CANVAS
    const canvas = document.createElement('canvas');
    canvas.id = 'robot-canvas-final';
    document.body.appendChild(canvas);

    // 3. STYLE "BRUTAL" (Z-INDEX MAX + FLASH VERT)
    canvas.style.cssText = `
        position: fixed !important; 
        top: 0 !important; 
        left: 0 !important;
        width: 100vw !important; 
        height: 100vh !important;
        z-index: 2147483647 !important; /* AU DESSUS DE TOUT */
        pointer-events: none !important;
        background: rgba(0, 255, 0, 0.5) !important; /* FLASH VERT TEMPORAIRE */
        transition: background 1s ease-out;
    `;

    // Le flash vert disparaît après 0.5 seconde
    setTimeout(() => {
        canvas.style.background = 'transparent';
    }, 500);

    // 4. BULLE
    let bubble = document.getElementById('robot-bubble-text');
    if (!bubble) {
        bubble = document.createElement('div');
        bubble.id = 'robot-bubble-text';
        document.body.appendChild(bubble);
        bubble.style.cssText = `
            position: fixed; opacity: 0; background: white; color: black;
            padding: 10px 20px; border-radius: 20px; font-family: Arial; 
            font-weight: bold; font-size: 18px; pointer-events: none; z-index: 2147483647;
            text-align: center;
        `;
    }

    initThreeJS(canvas, bubble);
}

function initThreeJS(canvas, bubble) {
    let width = window.innerWidth;
    let height = window.innerHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    // On rapproche la caméra pour être sûr de le voir
    camera.position.set(0, 0, 12); 

    const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setClearColor(0x000000, 0);

    // ÉCLAIRAGE PUISSANT
    const ambientLight = new THREE.AmbientLight(0xffffff, 2.0); 
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.5);
    dirLight.position.set(5, 5, 5);
    scene.add(dirLight);

    // --- ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(1.2, 1.2, 1.2); // UN PEU PLUS GROS
    
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
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

    const leftArm = createPart(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat, -0.8, -0.8, 0, robotGroup); leftArm.rotation.z = 0.15;
    const rightArm = createPart(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat, 0.8, -0.8, 0, robotGroup); rightArm.rotation.z = -0.15;

    scene.add(robotGroup);
    
    // POSITION CENTRALE FORCÉE (0,0) - IMPOSSIBLE À RATER
    robotGroup.position.set(0, 0, 0);

    // --- ANIMATION ---
    let time = 0;
    
    function animate() {
        requestAnimationFrame(animate);
        time += 0.02;
        
        // Il flotte au milieu
        robotGroup.position.y = Math.sin(time) * 0.2;
        robotGroup.rotation.y = Math.sin(time * 0.5) * 0.2;

        // Gestion Bulle
        if(bubble && Math.random() > 0.99) {
             bubble.style.opacity = 1;
             bubble.innerText = "Je suis là !";
             const headPos = robotGroup.position.clone();
             headPos.y += 1.2;
             headPos.project(camera);
             const x = (headPos.x * .5 + .5) * width;
             const y = (-(headPos.y * .5) + .5) * height;
             bubble.style.left = (x - 50) + 'px';
             bubble.style.top = (y - 50) + 'px';
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
