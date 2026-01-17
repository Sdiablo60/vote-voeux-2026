import * as THREE from 'three';

// =========================================================
// 🔴 ZONES DE RÉGLAGE MANUEL 🔴
// =========================================================

// On remonte le trait (0.1 était trop bas, 0.0 était caché).
// 0.035 devrait le placer pile dans la zone noire, collé au titre.
const MARGE_HAUT = 0.015; 

// On garde la largeur qui semblait bonne (sinon mettez 0.98)
const FACTEUR_LARGEUR = 1.0; 

// =========================================================

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', launchCalibration);
} else {
    launchCalibration();
}

function launchCalibration() {
    const oldIds = ['robot-container', 'robot-canvas-overlay', 'robot-ghost-layer', 'robot-canvas-final', 'robot-calibration-layer'];
    oldIds.forEach(id => { const el = document.getElementById(id); if (el) el.remove(); });

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

    // Cadre rouge épais
    const borderGeo = new THREE.BufferGeometry();
    const borderMat = new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 4 });
    const borderLine = new THREE.LineLoop(borderGeo, borderMat);
    scene.add(borderLine);

    function updateBorder() {
        const dist = camera.position.z;
        const vFOV = THREE.MathUtils.degToRad(camera.fov);
        const visibleHeight = 2 * Math.tan(vFOV / 2) * dist;
        const visibleWidth = visibleHeight * camera.aspect;

        const halfH = visibleHeight / 2;
        const halfW = visibleWidth / 2;

        const yTop = halfH - MARGE_HAUT; 
        const yBottom = -halfH; 
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
