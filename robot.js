import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- CONFIGURATION ---
const LIMITE_HAUTE_Y = 6.53; 

if (container) {
    // FORCE LE CONTAINER À ÊTRE VISIBLE
    container.style.cssText = `
        position: fixed !important; 
        top: 0 !important; 
        left: 0 !important; 
        width: 100vw !important; 
        height: 100vh !important; 
        z-index: 2147483647 !important; 
        pointer-events: none !important;
        border: 2px solid yellow; /* BORDURE DE TEST : Si vous voyez un cadre jaune, le script tourne */
    `;
    initRobot(container);
}

function initRobot(container) {
    const width = window.innerWidth;
    const height = window.innerHeight;
    
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 12); 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0xffffff, 2.5));

    // --- ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.6, 0.6, 0.6); // Un peu plus grand pour le test
    
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x000000 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.85, 32, 32), whiteMat);
    head.scale.set(1.4, 1.0, 0.75);
    const face = new THREE.Mesh(new THREE.SphereGeometry(0.78, 32, 32), blackMat);
    face.position.z = 0.55; face.scale.set(1.25, 0.85, 0.6); head.add(face);
    
    const eyeL = new THREE.Mesh(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat);
    eyeL.position.set(-0.35, 0.15, 1.05); head.add(eyeL);
    const eyeR = eyeL.clone(); eyeR.position.x = 0.35; head.add(eyeR);

    const body = new THREE.Mesh(new THREE.SphereGeometry(0.65, 32, 32), whiteMat);
    body.position.y = -1.1; body.scale.set(0.95, 1.1, 0.8);
    
    robotGroup.add(head); robotGroup.add(body);
    scene.add(robotGroup);

    // POSITIONNEMENT DIRECT AU CENTRE (SANS INTRO) POUR TESTER
    robotGroup.position.set(0, 0, 0);

    function animate() {
        requestAnimationFrame(animate);
        robotGroup.rotation.y += 0.01; // Il tourne sur lui-même
        renderer.render(scene, camera);
    }
    animate();
}
