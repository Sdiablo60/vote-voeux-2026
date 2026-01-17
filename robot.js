import * as THREE from 'three';

// =========================================================
// 🔴 OUTIL DE VÉRIFICATION DES BORDS 🔴
// =========================================================

// Si le code Python a bien fonctionné :
// 1. Mettez MARGE_HAUT à 0.0 -> Le trait rouge doit toucher le bandeau rouge du titre.
const MARGE_HAUT = 0.0; 

// 2. Mettez FACTEUR_LARGEUR à 1.0 -> Les traits rouges doivent toucher les bords de l'écran.
const FACTEUR_LARGEUR = 1.0; 

// =========================================================

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', launchCalibration);
} else {
    launchCalibration();
}

function launchCalibration() {
    // NETTOYAGE
    const oldIds = ['robot-container', 'robot-canvas-overlay', 'robot-ghost-layer', 'robot-canvas-final', 'robot-calibration-layer'];
    oldIds.forEach(id => { const el = document.getElementById(id); if (el) el.remove(); });

    // CRÉATION CALQUE DE TEST
    const canvas = document.createElement('canvas');
    canvas.id = 'robot-calibration-layer';
    document.body.appendChild(canvas);

    // STYLE FORCÉ
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

    // --- LE CADRE ROUGE ---
    const borderGeo = new THREE.BufferGeometry();
    const borderMat = new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 5 }); // Ligne épaisse
    const borderLine = new THREE.LineLoop(borderGeo, borderMat);
    scene.add(borderLine);

    function updateBorder() {
        const dist = camera.position.z;
        const vFOV = THREE.MathUtils.degToRad(camera.fov);
        const visibleHeight = 2 * Math.tan(vFOV / 2) * dist;
        const visibleWidth = visibleHeight * camera.aspect;

        const halfH = visibleHeight / 2;
        const halfW = visibleWidth / 2;

        // APPLICATION DES MARGES
        const yTop = halfH - MARGE_HAUT;
        const yBottom = -halfH; // Tout en bas
        const xRight = halfW * FACTEUR_LARGEUR;
        const xLeft = -xRight;

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
