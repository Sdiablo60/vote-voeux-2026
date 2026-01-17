import * as THREE from 'three';

// --- CONFIGURATION NETTE ---
// Fini les chiffres au hasard. On utilise la logique de votre site.
// Votre titre fait 12vh (12% de l'écran). On utilise cette valeur.
const POURCENTAGE_TITRE = 0.12; 

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', launchCalibration);
} else {
    launchCalibration();
}

function launchCalibration() {
    // 1. GRAND NETTOYAGE (On vire tout ce qui n'est pas le cadre)
    const oldIds = ['robot-container', 'robot-canvas-overlay', 'robot-ghost-layer', 'robot-canvas-final', 'robot-calibration-layer', 'live-container'];
    oldIds.forEach(id => { 
        const el = document.getElementById(id); 
        if (el) el.remove(); 
    });

    // 2. CRÉATION DU CALQUE DE TEST
    const canvas = document.createElement('canvas');
    canvas.id = 'robot-calibration-layer';
    document.body.appendChild(canvas);

    canvas.style.cssText = `
        position: fixed !important; top: 0 !important; left: 0 !important;
        width: 100vw !important; height: 100vh !important;
        z-index: 2147483647 !important; pointer-events: none !important;
        background: transparent !important;
    `;

    initThreeJS(canvas);
}

function initThreeJS(canvas) {
    let width = window.innerWidth;
    let height = window.innerHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 14); 

    const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setClearColor(0x000000, 0);

    // CADRE ROUGE SEUL
    const borderGeo = new THREE.BufferGeometry();
    const borderMat = new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 4 });
    const borderLine = new THREE.LineLoop(borderGeo, borderMat);
    scene.add(borderLine);

    function updateBorder() {
        const dist = camera.position.z;
        const vFOV = THREE.MathUtils.degToRad(camera.fov);
        
        // Calcul des dimensions totales visibles par la caméra
        const visibleHeight = 2 * Math.tan(vFOV / 2) * dist;
        const visibleWidth = visibleHeight * camera.aspect;

        const halfH = visibleHeight / 2;
        const halfW = visibleWidth / 2;

        // CALCUL AUTOMATIQUE : 
        // On descend du haut (halfH) d'exactement 12% de la hauteur totale
        const hauteurBandeau = visibleHeight * POURCENTAGE_TITRE;
        
        // Coordonnées exactes
        const yTop = halfH - hauteurBandeau;
        const yBottom = -halfH; // Tout en bas
        const xRight = halfW;   // Tout à droite (1.0)
        const xLeft = -halfW;   // Tout à gauche

        const points = [
            new THREE.Vector3(xLeft, yTop, 0),
            new THREE.Vector3(xRight, yTop, 0),
            new THREE.Vector3(xRight, yBottom, 0),
            new THREE.Vector3(xLeft, yBottom, 0)
        ];
        borderGeo.setFromPoints(points);
    }

    updateBorder();

    function animate() {
        requestAnimationFrame(animate);
        renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', () => {
        const w = window.innerWidth;
        const h = window.innerHeight;
        renderer.setSize(w, h);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        updateBorder();
    });
}
