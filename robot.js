import * as THREE from 'three';

// =========================================================
// 🔴 TEST DE CALIBRAGE : CADRE SEUL 🔴
// =========================================================

// On utilise la valeur exacte de votre CSS app.py (height: 12vh)
const HAUTEUR_TITRE_POURCENTAGE = 0.12; 

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', launchCalibrationOnly);
} else {
    launchCalibrationOnly();
}

function launchCalibrationOnly() {
    // 1. NETTOYAGE TOTAL
    // On supprime absolument tout pour ne garder que le cadre de test
    const oldIds = ['robot-container', 'robot-canvas-overlay', 'robot-ghost-layer', 'robot-canvas-final', 'robot-calibration-layer', 'live-container'];
    oldIds.forEach(id => { 
        const el = document.getElementById(id); 
        if (el) el.remove(); 
    });

    // 2. CRÉATION DU CANVAS DE TEST
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

    // --- LE CADRE ROUGE (ET RIEN D'AUTRE) ---
    const borderGeo = new THREE.BufferGeometry();
    const borderMat = new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 4 });
    const borderLine = new THREE.LineLoop(borderGeo, borderMat);
    scene.add(borderLine);

    function updateBorder() {
        const dist = camera.position.z;
        const vFOV = THREE.MathUtils.degToRad(camera.fov);
        
        // Dimensions totales vues par la caméra
        const visibleHeight = 2 * Math.tan(vFOV / 2) * dist;
        const visibleWidth = visibleHeight * camera.aspect;

        const halfH = visibleHeight / 2;
        const halfW = visibleWidth / 2;

        // CALCUL : Le haut de l'écran (halfH) moins 12% de la hauteur totale
        const yTop = halfH - (visibleHeight * HAUTEUR_TITRE_POURCENTAGE);
        
        const yBottom = -halfH; 
        const xRight = halfW;   
        const xLeft = -halfW;   

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
